#!/usr/bin/env python3
"""CCDC contribution validator — the independent CI re-scan merge gate.

Issue #8 / sanitizer PRD decision **D-4**. This is *the* trust mechanism for the
corpus: manual maintainer review does not scale, so a mechanical gate re-derives
the security-load-bearing checks on every contribution PR. The cardinal rule
(CLAUDE.md "Security posture", LAYOUT.md):

    **CI never trusts the contributor's `.scrubbed` sidecar.**

For a Tier 1 (`corpus/`) contribution the gate re-runs the *same* residual secret
scan the sanitizer ran before it was allowed to write the file at all — using the
upstream sanitizer's own `scan_residual` (the full built-in pattern set, not a
re-vendored subset). An honest `session.jsonl` only exists because that scan
already passed over it, so re-running the identical scan passes honest outputs and
fails tampered / hand-edited ones. The sidecar is read for *provenance*
(`input_sha256`, `sanitizer_version`) and every value it asserts is cross-checked
against something CI can re-derive (the content-addressed path, the file itself) —
never taken on faith.

For a Tier 2 (`structural/`) contribution there is nothing to re-scan: the raw
projects-root the profile was derived from is deliberately withheld, so the tier is
**version-attested, not re-scanned** (PRD D-CCDC-2). The gate instead confirms the
profile is content-addressed (`<scan_id>` == `sha256(scan.json)`) and carries the
attestation key (`tool` on the allowlist, `scan_version` present). No re-scan is
attempted — the asymmetry is by design.

In both tiers the gate assembles the *would-be* `manifest.jsonl` row from
CI-derived provenance and validates it against the locked
`schema/manifest-row.schema.json`. This gate is **validate-only**: it does not
write `manifest.jsonl`. Row *generation* needs the merge-commit date
(`contributed_at`), which does not exist pre-merge, so it runs in a separate
post-merge job — `ci/generate_manifest.py` (#33), which re-uses this module's
`validate_contribution` to re-derive each row and only then stamps the real merge
date. `CONTRIBUTED_AT_PLACEHOLDER` is injected only so the row can be shape-checked
here; the real value is that merge-time concern.

Tier is routed by **path**, never by a contributor-controlled field (LAYOUT.md):
`corpus/<contributor_id>/<input_sha256>/` → full; `structural/<contributor_id>/
<scan_id>/` → structural.

Run the validator's own test suite with:
    python3 ci/tests/test_validate_contribution.py
(requires `ci/requirements.txt`; the upstream sanitizer import fails closed — see
`load_residual_scanner`).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = REPO_ROOT / "schema"
CONTRIBUTION_SCHEMA_PATH = SCHEMA_DIR / "contribution.schema.json"
MANIFEST_ROW_SCHEMA_PATH = SCHEMA_DIR / "manifest-row.schema.json"

# Tiers are top-level trees; the tier is decided by the path, not a field.
TIERS = ("corpus", "structural")

# Paths under a tier tree that are NOT contributions: the tier doc and the
# placeholder keepers. A PR that only touches these is a legitimate docs change,
# not a contribution — the gate passes it without finding a contribution dir.
# Anything else under a tier tree that is not inside a <cid>/<sha256>/ dir is a
# stray (a contribution at the wrong depth, a misplaced file) and FAILS.
NON_CONTRIBUTION_PATHS = frozenset(
    {
        "structural/README.md",
        "corpus/.gitkeep",
        "structural/.gitkeep",
    }
)

# Mirrors the contributor_id format locked in SCHEMA.md / the JSON Schemas.
CONTRIBUTOR_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,38}$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
# "recognized" sanitizer_version (criterion 3): present, non-empty, version-shaped.
# A hard allowlist of accepted sanitizer versions is deferred (SCHEMA.md) — this is
# a completeness check on a field the sidecar was never trusted for, not a trust
# gate. The re-scan is the trust gate.
SEMVER_PREFIX_RE = re.compile(r"^\d+\.\d+(\.\d+)?([-+.][0-9A-Za-z.-]+)?$")

# contributed_at is derived from the merge commit (SCHEMA.md) and does not exist in
# a pre-merge PR. It is stubbed ONLY so the assembled row can be validated for shape
# against manifest-row.schema.json. The real value is set when the manifest row is
# generated at merge time (ci/generate_manifest.py, #33). The gate must not let this
# stub stand in for a real provenance check — it validates everything else.
CONTRIBUTED_AT_PLACEHOLDER = "1970-01-01T00:00:00Z"

# Allowlisted scanner for the structural tier — the (tool, scan_version) attestation
# key. Const-pinned in manifest-row.schema.json; duplicated here for a legible error
# before the schema check.
ALLOWED_SCAN_TOOL = "ccs-format-scan"


class ContributionError(Exception):
    """A contribution failed validation. The message is contributor-facing.

    Carries no secret bytes: a residual-scan hit surfaces only the pattern
    *kind* (mirroring the sanitizer's D-2 invariant), never the matched value.
    """


# --- upstream residual scanner (fail-closed import) -------------------------


def load_residual_scanner():
    """Return the upstream sanitizer's ``scan_residual`` + ``ResidualSecretError``.

    The gate's whole security claim is that it re-runs the *sanitizer's own*
    residual scan (the full built-in pattern set), so the import is a hard,
    fail-closed dependency: if the pinned upstream package is not installed, the
    gate must error, never silently skip the re-scan or fall back to a weaker
    in-repo pattern copy. Pinned in ci/requirements.txt.
    """
    try:
        from ccs_sanitize.residual import ResidualSecretError, scan_residual
    except ImportError as exc:  # pragma: no cover - exercised in CI, not unit tests
        raise ContributionError(
            "the upstream sanitizer (claude-code-sessions-sanitizer) is not "
            "importable, so the independent re-scan cannot run; refusing to pass "
            "the gate. Install ci/requirements.txt. Underlying error: " + str(exc)
        ) from exc
    return scan_residual, ResidualSecretError


# --- small IO helpers -------------------------------------------------------


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContributionError(f"missing required file: {path.name}") from exc
    except (json.JSONDecodeError, ValueError) as exc:
        raise ContributionError(f"{path.name} is not valid JSON: {exc}") from exc


def _load_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContributionError(f"missing required file: {path.name}") from exc
    except yaml.YAMLError as exc:
        raise ContributionError(f"{path.name} is not valid YAML: {exc}") from exc


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


@lru_cache(maxsize=None)
def _schema_validator(schema_path: Path):
    """Compile a Draft 2020-12 validator for a committed schema, once per run.

    Cached so a PR validating several contributions reads + parses + compiles each
    schema only once. Like the residual import, a missing ``jsonschema`` is a hard,
    fail-closed error — never a skipped check. (lru_cache does not cache the raised
    exception, so the failure re-surfaces on every call.)
    """
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover - exercised in CI
        raise ContributionError(
            "the jsonschema library is not importable, so contributions cannot be "
            "schema-validated; refusing to pass the gate. Install ci/requirements.txt. "
            "Underlying error: " + str(exc)
        ) from exc
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return jsonschema.Draft202012Validator(schema)


def _jsonschema_validate(instance: Any, schema_path: Path, what: str) -> None:
    """Validate ``instance`` against a committed schema, fail-closed on the lib.

    Uses the real ``jsonschema`` library against the *locked* schema files so the
    validator can never drift from the schema contract.
    """
    validator = _schema_validator(schema_path)
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.path))
    if errors:
        first = errors[0]
        location = "/".join(str(p) for p in first.path) or "<root>"
        raise ContributionError(
            f"{what} failed schema validation at {location}: {first.message}"
        )


# --- contribution.json (shared across tiers) --------------------------------


def _validate_contribution_json(contrib_dir: Path, cid_seg: str) -> dict:
    """Load + schema-validate contribution.json and cross-check its cid to the path."""
    path = contrib_dir / "contribution.json"
    if not path.exists():
        raise ContributionError("missing required file: contribution.json")
    data = _load_json(path)
    _jsonschema_validate(data, CONTRIBUTION_SCHEMA_PATH, "contribution.json")
    # The contributor asserts contributor_id; CI binds it to the path so the two
    # cannot disagree (a row's contributor_id is "validated", not trusted — SCHEMA.md).
    if data.get("contributor_id") != cid_seg:
        raise ContributionError(
            "contribution.json contributor_id "
            f"({data.get('contributor_id')!r}) does not match the path segment "
            f"({cid_seg!r})"
        )
    return data


# --- Tier 1 (full) ----------------------------------------------------------


def _claude_code_versions(lines: list[str]) -> list[str]:
    """Distinct top-level ``version`` values across the JSONL, in first-seen order.

    Takes the same ``lines`` already read for the residual scan, so ``session.jsonl``
    is read once per contribution, not twice. A resumed session can span a Claude
    Code upgrade, so this is an array (SCHEMA.md "Why claude_code_versions is an
    array"). Lines that do not parse as JSON are skipped for version extraction — the
    residual scan ran over the raw bytes regardless, so a malformed line cannot
    smuggle content past the gate; it just doesn't contribute a version. (A dict with
    ``None`` values is an insertion-ordered set — keeps first-seen order, which the
    manifest's ``uniqueItems`` array preserves.)
    """
    versions: dict[str, None] = {}
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(obj, dict):
            v = obj.get("version")
            if isinstance(v, str) and v:
                versions.setdefault(v, None)
    return list(versions)


def _assemble_row(
    *,
    tier: str,
    path: str,
    contribution: dict,
    versions: list[str],
    verification: str,
    extra: dict,
) -> dict:
    """Build the would-be manifest row from common + tier-specific fields, validate it.

    The single assembly + schema-validation site for both tiers — and the single
    injection point for ``contributed_at``, which is stubbed here only for shape
    validation. Manifest generation (ci/generate_manifest.py, #33) re-runs this code
    path post-merge and swaps the stub for the real merge-commit value in one place
    rather than in each tier validator.
    """
    row = {
        "schema_version": "1",
        "tier": tier,
        "contributor_id": contribution["contributor_id"],
        "path": path,
        "contributed_at": CONTRIBUTED_AT_PLACEHOLDER,
        "license": contribution["license"],
        "claude_code_versions": versions,
        "verification": verification,
        **extra,
    }
    _jsonschema_validate(row, MANIFEST_ROW_SCHEMA_PATH, "derived manifest row")
    return row


def validate_full(contrib_dir: Path, cid_seg: str, hash_seg: str) -> dict:
    session = contrib_dir / "session.jsonl"
    sidecar = contrib_dir / "session.jsonl.scrubbed"
    if not session.exists():
        raise ContributionError("missing required file: session.jsonl")
    if not sidecar.exists():
        raise ContributionError(
            "missing required file: session.jsonl.scrubbed (the ccs-sanitize "
            "sidecar). Every corpus/ session.jsonl must ship its sidecar; a raw, "
            "unsanitized transcript is never accepted."
        )

    contribution = _validate_contribution_json(contrib_dir, cid_seg)

    # The trust gate: re-run the sanitizer's OWN residual scan over the submitted
    # file. Never trust the sidecar's residual_scan field. Raw lines, no
    # parse/re-serialize round-trip, so the bytes scanned are exactly the bytes
    # committed (split on "\n" to mirror the sanitizer's per-line semantics).
    scan_residual, ResidualSecretError = load_residual_scanner()
    lines = session.read_text(encoding="utf-8").split("\n")  # read once; reused below
    try:
        scan_residual(lines, [])
    except ResidualSecretError as exc:
        # exc carries only the pattern kind, never the matched bytes (D-2).
        raise ContributionError(
            "independent re-scan found a residual secret in session.jsonl "
            f"(pattern kind={exc.kind!r}); the sidecar is not trusted and the "
            "contribution is rejected. Re-sanitize the original input."
        ) from exc

    # Sidecar provenance — each field cross-checked against something re-derivable.
    sidecar_data = _load_yaml(sidecar)
    if not isinstance(sidecar_data, dict):
        raise ContributionError("session.jsonl.scrubbed is not a YAML mapping")

    input_sha256 = sidecar_data.get("input_sha256")
    if not isinstance(input_sha256, str) or not HEX64_RE.match(input_sha256):
        raise ContributionError(
            "sidecar input_sha256 is missing or not a 64-char hex digest"
        )
    # The path is content-addressed on the original input's hash; bind the sidecar
    # to it so the directory and the sidecar cannot disagree.
    if input_sha256 != hash_seg:
        raise ContributionError(
            f"sidecar input_sha256 ({input_sha256}) does not match the path "
            f"segment ({hash_seg})"
        )

    sanitizer_version = sidecar_data.get("sanitizer_version")
    if not isinstance(sanitizer_version, str) or not SEMVER_PREFIX_RE.match(
        sanitizer_version
    ):
        raise ContributionError(
            "sidecar sanitizer_version is missing or not version-shaped: "
            f"{sanitizer_version!r}"
        )

    versions = _claude_code_versions(lines)
    if not versions:
        raise ContributionError(
            "no Claude Code version found in session.jsonl (no top-level "
            "'version' field on any record)"
        )

    return _assemble_row(
        tier="full",
        path=f"corpus/{cid_seg}/{hash_seg}/",
        contribution=contribution,
        versions=versions,
        verification="ci-rescan",
        extra={"input_sha256": input_sha256, "sanitizer_version": sanitizer_version},
    )


# --- Tier 2 (structural) ----------------------------------------------------


def validate_structural(contrib_dir: Path, cid_seg: str, hash_seg: str) -> dict:
    scan_path = contrib_dir / "scan.json"
    if not scan_path.exists():
        raise ContributionError("missing required file: scan.json")

    contribution = _validate_contribution_json(contrib_dir, cid_seg)

    # No re-scan is possible (the raw projects-root is withheld) — the tier is
    # version-attested, not re-scanned (criterion 5). Instead: confirm the profile
    # is content-addressed, so the committed bytes ARE the attested artifact.
    scan_id = _sha256_file(scan_path)
    if scan_id != hash_seg:
        raise ContributionError(
            f"scan.json sha256 ({scan_id}) does not match the path segment "
            f"({hash_seg}); the structural tier is content-addressed"
        )

    scan = _load_json(scan_path)
    if not isinstance(scan, dict):
        raise ContributionError("scan.json is not a JSON object")

    tool = scan.get("tool")
    if tool != ALLOWED_SCAN_TOOL:
        raise ContributionError(
            f"scan.json tool ({tool!r}) is not on the allowlist "
            f"({ALLOWED_SCAN_TOOL!r}); admitting another scanner is a deliberate "
            "additive schema change"
        )

    scan_version = scan.get("scan_version")
    if not isinstance(scan_version, str) or not SEMVER_PREFIX_RE.match(scan_version):
        raise ContributionError(
            f"scan.json scan_version is missing or not version-shaped: "
            f"{scan_version!r}"
        )

    versions_obj = scan.get("versions")
    if not isinstance(versions_obj, dict) or not versions_obj:
        raise ContributionError(
            "scan.json has no non-empty 'versions' object to derive "
            "claude_code_versions from"
        )
    versions = [v for v in versions_obj.keys() if isinstance(v, str) and v]
    if not versions:
        raise ContributionError("scan.json 'versions' has no usable version keys")

    return _assemble_row(
        tier="structural",
        path=f"structural/{cid_seg}/{hash_seg}/",
        contribution=contribution,
        versions=versions,
        verification="version-attested",
        extra={"scan_id": scan_id, "tool": tool, "scan_version": scan_version},
    )


# --- dispatch ---------------------------------------------------------------


def validate_contribution(contrib_dir: Path) -> dict:
    """Validate one contribution directory and return its derived manifest row.

    Tier is routed from the directory's own trailing structure
    (``<tier>/<contributor_id>/<sha256>``) so the function works equally on a real
    ``corpus/...`` path and on a self-contained test fixture nested anywhere. The
    derived row's ``path`` is rebuilt from those three segments, so it always reads
    ``corpus/<cid>/<hash>/`` regardless of where the fixture lives on disk.
    """
    parts = contrib_dir.resolve().parts
    if len(parts) < 3:
        raise ContributionError(f"not a contribution directory: {contrib_dir}")
    tier_seg, cid_seg, hash_seg = parts[-3], parts[-2], parts[-1]

    if tier_seg not in TIERS:
        raise ContributionError(
            f"not a contribution directory (tier segment {tier_seg!r} is not one "
            f"of {TIERS}): {contrib_dir}"
        )
    if not CONTRIBUTOR_ID_RE.match(cid_seg):
        raise ContributionError(
            f"contributor_id path segment {cid_seg!r} is not a valid handle "
            f"({CONTRIBUTOR_ID_RE.pattern})"
        )
    if not HEX64_RE.match(hash_seg):
        raise ContributionError(
            f"content-address path segment {hash_seg!r} is not a 64-char hex digest"
        )

    if tier_seg == "corpus":
        return validate_full(contrib_dir, cid_seg, hash_seg)
    return validate_structural(contrib_dir, cid_seg, hash_seg)


# --- changed-path discovery (drives the PR gate) ----------------------------


def classify_changed_paths(paths: Iterable[str]) -> tuple[list[str], list[str]]:
    """Map changed repo paths to contribution dirs; flag strays.

    Returns ``(contribution_dirs, strays)`` where ``contribution_dirs`` is the
    sorted, de-duplicated set of ``<tier>/<cid>/<hash>`` prefixes touched, and
    ``strays`` are changed paths under a tier tree that are neither an allowlisted
    non-contribution file nor a member of a well-formed contribution dir.

    This is the anti-silent-bypass check: a PR that triggers the gate (it touched a
    tier tree) but yields zero contribution dirs is fine ONLY if every touched path
    is allowlisted (a docs/keepalive change). A contribution file at the wrong depth
    or with malformed path segments is a stray and FAILS the gate — it can never
    slip through as "nothing to validate".
    """
    contribution_dirs: set[str] = set()
    strays: list[str] = []
    for raw in paths:
        p = raw.strip()
        if not p:
            continue
        parts = PurePosixPath(p).parts
        if not parts or parts[0] not in TIERS:
            continue  # outside both tier trees — not this gate's concern
        if p in NON_CONTRIBUTION_PATHS:
            continue  # allowlisted docs / keepalive
        if len(parts) < 4:
            strays.append(
                f"{p}: under {parts[0]}/ but not inside a "
                "<contributor_id>/<sha256>/ contribution directory"
            )
            continue
        tier, cid, h = parts[0], parts[1], parts[2]
        if not CONTRIBUTOR_ID_RE.match(cid) or not HEX64_RE.match(h):
            strays.append(
                f"{p}: contribution path segments do not match "
                "<contributor_id>/<sha256>"
            )
            continue
        contribution_dirs.add(f"{tier}/{cid}/{h}")
    return sorted(contribution_dirs), strays


# --- CLI --------------------------------------------------------------------


def _run_dirs(dirs: list[Path]) -> int:
    failures = 0
    for d in dirs:
        try:
            row = validate_contribution(d)
        except ContributionError as exc:
            failures += 1
            print(f"FAIL {d}\n     {exc}", file=sys.stderr)
            continue
        print(f"PASS {row['tier']:10} {row['path']}")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "CCDC contribution validator — independent CI re-scan merge gate (#8)."
        )
    )
    parser.add_argument(
        "dirs",
        nargs="*",
        type=Path,
        help="contribution directories to validate (<tier>/<cid>/<sha256>)",
    )
    parser.add_argument(
        "--changed-files",
        metavar="FILE",
        help=(
            "read newline-separated changed repo paths from FILE (or '-' for "
            "stdin), discover the contribution dirs they touch, and validate each. "
            "Fails on any stray path under a tier tree."
        ),
    )
    args = parser.parse_args(argv)

    dirs: list[Path] = list(args.dirs)

    if args.changed_files:
        if args.changed_files == "-":
            text = sys.stdin.read()
        else:
            text = Path(args.changed_files).read_text(encoding="utf-8")
        contribution_dirs, strays = classify_changed_paths(text.splitlines())
        if strays:
            print(
                "FAIL: changed paths under a tier tree are not valid contributions:",
                file=sys.stderr,
            )
            for s in strays:
                print(f"     {s}", file=sys.stderr)
            return 1
        if not contribution_dirs:
            print(
                "No contribution directories changed (only non-contribution paths); "
                "nothing to re-scan."
            )
            return 0
        dirs.extend(REPO_ROOT / d for d in contribution_dirs)

    if not dirs:
        parser.error("no contribution directories to validate")

    failures = _run_dirs(dirs)
    if failures:
        print(f"\n{failures} contribution(s) failed validation.", file=sys.stderr)
        return 1
    print(f"\nAll {len(dirs)} contribution(s) passed validation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
