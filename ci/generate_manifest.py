#!/usr/bin/env python3
"""CCDC manifest generation — write the index row at merge time (#33).

The PR gate (`validate_contribution.py`, #8) is **validate-only**: it re-derives
every check and assembles the *would-be* `manifest.jsonl` row, but it cannot write
it. The one field a row needs that does not exist pre-merge is `contributed_at`,
the **merge-commit date** (SCHEMA.md). So row *generation* runs in a separate,
**post-merge** job (push to `main`, `.github/workflows/manifest-generate.yml`) and is
what this module does:

    for each contribution dir newly merged in this push:
        row = validate_contribution(dir)             # the SAME gate code path, re-run
        row["contributed_at"] = <dir's add-commit>   # the field the PR could not supply
        append it to manifest.jsonl                  # if not already indexed / removed

Reusing `validate_contribution()` is deliberate: generation never invents a row, it
re-derives it through the gate (re-scan and all) and only stamps the merge date the
gate left as a placeholder. A contribution that would not pass the gate cannot be
indexed.

Four invariants, mapping to the issue's acceptance criteria:

- **Per-path provenance.** `contributed_at` is the date of the commit that *added*
  the contribution directory (``git log --diff-filter=A``), resolved per path — not
  the push head. A push that batches several merges therefore stamps each row with
  its own merge date, so SCHEMA.md's "merge-commit date" stays true even when "one
  push == one commit" does not.
- **Idempotent / one row per `path`.** Existing rows are preserved *verbatim* — a
  path already in the manifest is never re-derived or overwritten, so re-running a
  push cannot duplicate a row or move an earlier `contributed_at`. Only absent paths
  are added. (Correcting an already-written row is an out-of-band maintainer op, like
  a tombstone — never something generation does silently.)
- **Removal-safe (never resurrect a tombstone).** A row is only emitted for a
  contribution directory that currently exists *and* whose content address is not in
  the [`removals.jsonl`](../removals.jsonl) ledger (REMOVAL.md §7). A removal (§6A)
  deletes the directory and its row and appends the ledger entry in one commit; both
  checks then keep the row from ever coming back, including on a workflow re-run.
- **Deterministic order (no merge-conflict churn).** The manifest is rewritten as its
  rows sorted by `path` (content-addressed, unique, stable), so the file content is a
  pure function of the set of live contributions — the reason the index is
  CI-generated and never hand-edited (LAYOUT.md). Every row in the merged output is
  re-validated against the schema before the file is written, so a corrupt manifest
  fails loudly instead of growing silently.

Run the tests with:
    python3 ci/tests/test_generate_manifest.py
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_contribution as vc  # noqa: E402

MANIFEST_PATH = vc.REPO_ROOT / "manifest.jsonl"
REMOVALS_PATH = vc.REPO_ROOT / "removals.jsonl"

# A manifest row is serialized compactly, one object per line, keys in the logical
# order _assemble_row builds them (NOT sorted) — matching SCHEMA.md's examples. dicts
# preserve insertion order, and json.loads keeps key order when rows are re-read, so
# existing rows round-trip unchanged.
_JSON_SEPARATORS = (",", ":")

# Resolves a contribution path → its merge-commit `contributed_at`. Injected so the
# tests can supply dates without a git history; the CLI binds the git-backed default.
ContributedAtResolver = Callable[[str], str]


class GenerationError(Exception):
    """Manifest generation failed. Message is operator-facing (CI log)."""


# --- ledger / manifest IO ---------------------------------------------------


def _iter_jsonl(path: Path):
    """Yield ``(lineno, obj)`` for each non-blank line of a JSONL file.

    Shared by the manifest and removals-ledger loaders so both parse identically and
    only their per-row checks differ. A missing file yields nothing; a line that does
    not parse as JSON fails closed.
    """
    if not path.exists():
        return
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except (json.JSONDecodeError, ValueError) as exc:
            raise GenerationError(
                f"{path.name} line {lineno} is not valid JSON: {exc}"
            ) from exc
        yield lineno, obj


def load_manifest(path: Path) -> list[dict]:
    """Read existing rows from a JSONL manifest (missing/empty file → no rows)."""
    rows: list[dict] = []
    for lineno, obj in _iter_jsonl(path):
        if not isinstance(obj, dict) or "path" not in obj:
            raise GenerationError(
                f"{path.name} line {lineno} is not a manifest row (no 'path')"
            )
        rows.append(obj)
    return rows


def load_removed_addresses(path: Path) -> set[str]:
    """Content addresses (`input_sha256` / `scan_id`) of every tombstoned contribution.

    The removals ledger (REMOVAL.md §7) is the durable record of what was taken down.
    Generation consults it so a re-run over a pre-removal commit range can never
    re-emit a removed row — the resurrection guard, paired with the dir-existence
    check. A missing/empty ledger means nothing has been removed.
    """
    addrs: set[str] = set()
    for lineno, obj in _iter_jsonl(path):
        if not isinstance(obj, dict):
            raise GenerationError(f"{path.name} line {lineno} is not a JSON object")
        for key in ("input_sha256", "scan_id"):
            val = obj.get(key)
            if isinstance(val, str) and val:
                addrs.add(val)
    return addrs


# --- per-path merge-commit date ---------------------------------------------


def git_introduced_at(repo_root: Path) -> ContributedAtResolver:
    """Build a resolver: contribution path → the date its directory was added to git.

    Uses ``git log --diff-filter=A`` scoped to the contribution directory, so the
    timestamp is the merge commit that introduced *that* contribution regardless of
    how many merges a single push batched. UTC, schema-shaped (``...Z``). Fails closed
    if the directory has no add-commit (an uncommitted dir must never be indexed).
    """

    def resolve(contribution_path: str) -> str:
        result = subprocess.run(
            [
                "git",
                "log",
                "--diff-filter=A",
                "-1",
                "--format=%cd",
                "--date=format-local:%Y-%m-%dT%H:%M:%SZ",
                "--",
                contribution_path,
            ],
            cwd=repo_root,
            env={**os.environ, "TZ": "UTC"},
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise GenerationError(
                f"git log failed resolving contributed_at for {contribution_path}: "
                f"{result.stderr.strip()}"
            )
        stamp = result.stdout.strip()
        if not stamp:
            raise GenerationError(
                f"no add-commit found for {contribution_path}; refusing to index an "
                "uncommitted contribution"
            )
        return stamp

    return resolve


# --- derivation / merge -----------------------------------------------------


def derive_rows(
    contrib_dirs: list[Path],
    contributed_at_for: ContributedAtResolver,
    removed_addresses: set[str],
) -> list[dict]:
    """Re-validate each *live* contribution dir and stamp its merge date.

    A directory is skipped (never indexed) when it no longer exists — the removal
    case, where the tombstone deleted it — or when its content address is in the
    removals ledger. Every surviving dir is run back through the gate's
    ``validate_contribution`` (re-scan included); the per-path ``contributed_at``
    replaces the placeholder. The stamped rows are schema-validated once, alongside
    the existing ones, in :func:`merge_rows` before the file is written — so a bad
    merge date fails closed there.
    """
    rows: list[dict] = []
    for d in contrib_dirs:
        if not d.is_dir():
            # Deleted in this push (e.g. a removal tombstone). Do not regenerate.
            continue
        row = vc.validate_contribution(d)
        address = row.get("input_sha256") or row.get("scan_id")
        if address in removed_addresses:
            # Tombstoned — its data is gone; never re-emit the row (REMOVAL.md §7).
            continue
        row["contributed_at"] = contributed_at_for(row["path"])
        rows.append(row)
    return rows


def merge_rows(existing: list[dict], new: list[dict]) -> list[dict]:
    """Combine existing + newly-derived rows: idempotent, one row per path, sorted.

    Existing rows win on a path collision — they are kept verbatim so a re-run never
    rewrites an earlier ``contributed_at``. The result is sorted by ``path`` for a
    deterministic, conflict-free file. Every row in the result is re-validated against
    the manifest-row schema so a pre-existing corrupt row fails loudly here rather than
    silently persisting.
    """
    by_path: dict[str, dict] = {}
    for row in existing:
        by_path[row["path"]] = row
    for row in new:
        by_path.setdefault(row["path"], row)  # never overwrite an indexed path
    merged = [by_path[p] for p in sorted(by_path)]
    for row in merged:
        vc.validate_manifest_row(row)
    return merged


def render_manifest(rows: list[dict]) -> str:
    """Serialize rows to JSONL text (one compact object per line, trailing newline)."""
    if not rows:
        return ""
    return "".join(json.dumps(row, separators=_JSON_SEPARATORS) + "\n" for row in rows)


def generate(
    changed_paths: list[str],
    manifest_path: Path = MANIFEST_PATH,
    removals_path: Path = REMOVALS_PATH,
    contributed_at_for: ContributedAtResolver | None = None,
) -> tuple[list[str], str]:
    """Generate manifest rows for the contributions touched by a push.

    Returns ``(added_paths, manifest_text)``. Does not write the file — the caller
    decides whether to persist (so callers can dry-run). ``added_paths`` is the set of
    contribution paths newly indexed by this call (empty when nothing changed, e.g. a
    removal-only push or a re-run).
    """
    if contributed_at_for is None:
        contributed_at_for = git_introduced_at(manifest_path.parent)

    contribution_dirs, strays = vc.classify_changed_paths(changed_paths)
    if strays:
        # main should never carry a stray — the PR gate rejects them. Fail closed.
        raise GenerationError(
            "changed paths under a tier tree are not valid contributions: "
            + "; ".join(strays)
        )

    existing = load_manifest(manifest_path)
    removed = load_removed_addresses(removals_path)
    derived = derive_rows(
        [manifest_path.parent / d for d in contribution_dirs],
        contributed_at_for,
        removed,
    )
    merged = merge_rows(existing, derived)

    existing_paths = {r["path"] for r in existing}
    added = sorted(r["path"] for r in derived if r["path"] not in existing_paths)
    return added, render_manifest(merged)


# --- drift detection (scheduled safety net) ---------------------------------


def _contribution_dirs_on_disk(repo_root: Path) -> set[str]:
    """Every live contribution path on disk, found by its contribution.json marker."""
    found: set[str] = set()
    for tier in vc.TIERS:
        for marker in (repo_root / tier).glob("*/*/contribution.json"):
            d = marker.parent
            found.add(f"{tier}/{d.parent.name}/{d.name}/")
    return found


def find_drift(
    manifest_path: Path = MANIFEST_PATH, repo_root: Path | None = None
) -> tuple[list[str], list[str]]:
    """Compare live contribution dirs on disk against indexed manifest paths.

    Returns ``(missing_from_manifest, orphan_rows)``. ``missing_from_manifest`` are
    contributions present on disk but absent from the index — the signature of a
    generation run that was skipped or whose commit-back was rejected (the silent
    staleness failure mode). ``orphan_rows`` are indexed paths with no directory —
    they should never occur, since a removal deletes both. This is a *detector*: it
    does not heal, it fails the scheduled job loudly so a human reconciles.
    """
    root = repo_root or manifest_path.parent
    on_disk = _contribution_dirs_on_disk(root)
    indexed = {r["path"] for r in load_manifest(manifest_path)}
    missing = sorted(on_disk - indexed)
    orphans = sorted(indexed - on_disk)
    return missing, orphans


# --- CLI --------------------------------------------------------------------


def _cmd_generate(args: argparse.Namespace) -> int:
    if args.changed_files == "-":
        text = sys.stdin.read()
    else:
        text = Path(args.changed_files).read_text(encoding="utf-8")

    added, manifest_text = generate(
        text.splitlines(), args.manifest, args.removals
    )

    if not added:
        print("No new contributions to index; manifest.jsonl unchanged.")
        return 0

    if args.dry_run:
        print(f"Would index {len(added)} contribution(s):")
    else:
        args.manifest.write_text(manifest_text, encoding="utf-8")
        print(f"Indexed {len(added)} contribution(s) in {args.manifest.name}:")
    for p in added:
        print(f"  + {p}")
    return 0


def _cmd_check(args: argparse.Namespace) -> int:
    missing, orphans = find_drift(args.manifest)
    if not missing and not orphans:
        print("manifest.jsonl is in sync with the contributions on disk.")
        return 0
    print("FAIL: manifest.jsonl is out of sync:", file=sys.stderr)
    for p in missing:
        print(f"  on disk but NOT indexed: {p}", file=sys.stderr)
    for p in orphans:
        print(f"  indexed but NO directory: {p}", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "CCDC manifest generation — write merged contribution rows to "
            "manifest.jsonl with the merge-commit date (#33)."
        )
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=MANIFEST_PATH,
        help="path to manifest.jsonl (default: repo-root manifest.jsonl).",
    )
    parser.add_argument(
        "--removals",
        type=Path,
        default=REMOVALS_PATH,
        help="path to removals.jsonl (default: repo-root removals.jsonl).",
    )
    parser.add_argument(
        "--changed-files",
        metavar="FILE",
        help=(
            "newline-separated changed repo paths from the push (or '-' for stdin); "
            "the contribution dirs they touch are re-validated and indexed."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="compute and report changes without writing manifest.jsonl.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "drift mode: assert every contribution on disk is indexed (and vice "
            "versa); fail loudly on mismatch. Does not write. For a scheduled job."
        ),
    )
    args = parser.parse_args(argv)

    try:
        if args.check:
            return _cmd_check(args)
        if not args.changed_files:
            parser.error("--changed-files is required unless --check is given")
        return _cmd_generate(args)
    except (vc.ContributionError, GenerationError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
