#!/usr/bin/env python3
"""Tests for the CCDC contribution validator / CI re-scan merge gate (#8).

Run directly:
    python3 ci/tests/test_validate_contribution.py
or via pytest. Requires ci/requirements.txt (the upstream sanitizer for the
residual scan, and jsonschema). Both are fail-closed imports in the validator, so
running this suite without them surfaces a clear ContributionError rather than a
silently-skipped check.

Fixtures are built at runtime in a temp dir rather than committed: the structural
tier is content-addressed (the directory name must equal sha256(scan.json)), so
constructing fixtures in code is what keeps every hash correct by construction. The
planted secret is a single synthetic, obviously-fake constant — never a real key.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import validate_contribution as vc  # noqa: E402

# A synthetic, clearly-fake Anthropic-style key: the prefix the sanitizer's
# anthropic-key pattern matches, followed by filler. Not a real credential.
FAKE_ANTHROPIC_KEY = "sk-ant-" + "A" * 40

# Two arbitrary-but-valid 64-hex content addresses for Tier 1 fixtures, where the
# directory name is the original input's sha256 (independent of session.jsonl).
HASH_A = "a" * 64
HASH_B = "b" * 64

GOOD_CONTRIBUTION = {
    "schema_version": "1",
    "contributor_id": "example-contributor",
    "license": "CCDC-1.0",
    "attestation": {"right_to_contribute": True, "original_retained": True},
}

GOOD_SESSION_LINES = [
    json.dumps({"type": "user", "version": "2.1.150", "uuid": "u1"}),
    json.dumps({"type": "assistant", "version": "2.1.150", "uuid": "u2"}),
    # a resumed-across-upgrade line, so claude_code_versions is genuinely plural
    json.dumps({"type": "assistant", "version": "2.1.155", "uuid": "u3"}),
]


def _good_sidecar(input_sha256: str) -> str:
    return (
        f'sanitizer_version: "0.2.0"\n'
        f"input_sha256: {input_sha256}\n"
        f'scrubbed_at: "2026-06-12T00:00:00Z"\n'
        f"residual_scan: clean\n"
    )


def _good_scan() -> dict:
    return {
        "tool": "ccs-format-scan",
        "scan_version": "0.1.0",
        "summary": {"files_scanned": 2, "lines_scanned": 3},
        "versions": {"2.1.150": 5, "2.1.155": 2},
        "baseline_diff": None,
    }


class FixtureBuilder:
    """Materializes contribution dirs under a temp root."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def full(
        self,
        *,
        name: str,
        cid: str = "example-contributor",
        input_sha256: str = HASH_A,
        session_lines: list[str] | None = None,
        with_sidecar: bool = True,
        sidecar_text: str | None = None,
        contribution: dict | None = GOOD_CONTRIBUTION,
    ) -> Path:
        d = self.root / name / "corpus" / cid / input_sha256
        d.mkdir(parents=True, exist_ok=True)
        lines = GOOD_SESSION_LINES if session_lines is None else session_lines
        (d / "session.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
        if with_sidecar:
            text = sidecar_text if sidecar_text is not None else _good_sidecar(input_sha256)
            (d / "session.jsonl.scrubbed").write_text(text, encoding="utf-8")
        if contribution is not None:
            (d / "contribution.json").write_text(json.dumps(contribution), encoding="utf-8")
        return d

    def structural(
        self,
        *,
        name: str,
        cid: str = "example-contributor",
        scan: dict | None = None,
        contribution: dict | None = GOOD_CONTRIBUTION,
        scan_id_override: str | None = None,
    ) -> Path:
        scan_obj = _good_scan() if scan is None else scan
        scan_bytes = json.dumps(scan_obj, sort_keys=True).encode("utf-8")
        scan_id = scan_id_override or hashlib.sha256(scan_bytes).hexdigest()
        d = self.root / name / "structural" / cid / scan_id
        d.mkdir(parents=True, exist_ok=True)
        (d / "scan.json").write_bytes(scan_bytes)
        if contribution is not None:
            (d / "contribution.json").write_text(json.dumps(contribution), encoding="utf-8")
        return d


class ValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.b = FixtureBuilder(Path(self._tmp.name))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def assertFails(self, contrib_dir: Path, needle: str) -> None:
        with self.assertRaises(vc.ContributionError) as ctx:
            vc.validate_contribution(contrib_dir)
        self.assertIn(needle, str(ctx.exception))

    # --- Tier 1 positive control -------------------------------------------

    def test_full_good_passes_and_derives_row(self):
        row = vc.validate_contribution(self.b.full(name="full-good"))
        self.assertEqual(row["tier"], "full")
        self.assertEqual(row["verification"], "ci-rescan")
        self.assertEqual(row["path"], f"corpus/example-contributor/{HASH_A}/")
        self.assertEqual(row["input_sha256"], HASH_A)
        self.assertEqual(row["sanitizer_version"], "0.2.0")
        # plural, distinct, first-seen order
        self.assertEqual(row["claude_code_versions"], ["2.1.150", "2.1.155"])

    # --- Tier 1: the gate-of-the-gate (criterion 4) ------------------------

    def test_full_planted_secret_fails(self):
        lines = GOOD_SESSION_LINES + [
            json.dumps({"type": "user", "text": f"my key is {FAKE_ANTHROPIC_KEY}"})
        ]
        d = self.b.full(name="full-planted", session_lines=lines)
        self.assertFails(d, "residual secret")

    def test_planted_secret_message_does_not_echo_the_value(self):
        lines = GOOD_SESSION_LINES + [
            json.dumps({"type": "user", "text": FAKE_ANTHROPIC_KEY})
        ]
        d = self.b.full(name="full-planted-noecho", session_lines=lines)
        with self.assertRaises(vc.ContributionError) as ctx:
            vc.validate_contribution(d)
        # D-2: only the pattern kind surfaces, never the matched bytes.
        self.assertNotIn(FAKE_ANTHROPIC_KEY, str(ctx.exception))
        self.assertIn("anthropic-key", str(ctx.exception))

    # --- Tier 1 negative cases ---------------------------------------------

    def test_full_missing_sidecar_fails(self):
        d = self.b.full(name="full-no-sidecar", with_sidecar=False)
        self.assertFails(d, "session.jsonl.scrubbed")

    def test_full_missing_contribution_fails(self):
        d = self.b.full(name="full-no-contribution", contribution=None)
        self.assertFails(d, "contribution.json")

    def test_full_input_sha256_mismatch_fails(self):
        # sidecar asserts a different hash than the (content-addressed) path
        d = self.b.full(
            name="full-sha-mismatch",
            input_sha256=HASH_A,
            sidecar_text=_good_sidecar(HASH_B),
        )
        self.assertFails(d, "does not match the path segment")

    def test_full_empty_sanitizer_version_fails(self):
        bad = f'sanitizer_version: ""\ninput_sha256: {HASH_A}\nresidual_scan: clean\n'
        d = self.b.full(name="full-empty-sv", sidecar_text=bad)
        self.assertFails(d, "sanitizer_version")

    def test_full_bad_license_fails_schema(self):
        bad = dict(GOOD_CONTRIBUTION, license="MIT")
        d = self.b.full(name="full-bad-license", contribution=bad)
        self.assertFails(d, "schema validation")

    def test_full_attestation_false_fails_schema(self):
        bad = dict(
            GOOD_CONTRIBUTION,
            attestation={"right_to_contribute": False, "original_retained": True},
        )
        d = self.b.full(name="full-att-false", contribution=bad)
        self.assertFails(d, "schema validation")

    def test_full_contributor_id_path_mismatch_fails(self):
        bad = dict(GOOD_CONTRIBUTION, contributor_id="someone-else")
        d = self.b.full(name="full-cid-mismatch", contribution=bad)
        self.assertFails(d, "does not match the path segment")

    def test_full_no_version_in_session_fails(self):
        lines = [json.dumps({"type": "user", "uuid": "u1"})]
        d = self.b.full(name="full-no-version", session_lines=lines)
        self.assertFails(d, "no Claude Code version")

    # --- Tier 2 positive control -------------------------------------------

    def test_structural_good_passes_and_derives_row(self):
        d = self.b.structural(name="structural-good")
        row = vc.validate_contribution(d)
        self.assertEqual(row["tier"], "structural")
        self.assertEqual(row["verification"], "version-attested")
        self.assertEqual(row["tool"], "ccs-format-scan")
        self.assertEqual(row["scan_version"], "0.1.0")
        self.assertEqual(sorted(row["claude_code_versions"]), ["2.1.150", "2.1.155"])
        # content-addressed: the row's scan_id is the path segment
        self.assertTrue(row["path"].endswith(f"/{row['scan_id']}/"))

    # --- Tier 2 negative cases ---------------------------------------------

    def test_structural_scan_id_mismatch_fails(self):
        d = self.b.structural(name="structural-bad-addr", scan_id_override="c" * 64)
        self.assertFails(d, "content-addressed")

    def test_structural_bad_tool_fails(self):
        scan = dict(_good_scan(), tool="evil-fork-scan")
        d = self.b.structural(name="structural-bad-tool", scan=scan)
        self.assertFails(d, "allowlist")

    def test_structural_missing_scan_version_fails(self):
        scan = _good_scan()
        del scan["scan_version"]
        d = self.b.structural(name="structural-no-sv", scan=scan)
        self.assertFails(d, "scan_version")

    def test_structural_empty_versions_fails(self):
        scan = dict(_good_scan(), versions={})
        d = self.b.structural(name="structural-no-versions", scan=scan)
        self.assertFails(d, "versions")

    def test_structural_does_not_attempt_rescan(self):
        # A structural scan.json carrying a secret-looking string must NOT be
        # re-scanned (criterion 5) — the tier is version-attested. So a fake key
        # inside scan.json is irrelevant to whether it validates; what matters is
        # that it stays content-addressed + attested. Proves no re-scan path runs.
        scan = dict(_good_scan(), note=FAKE_ANTHROPIC_KEY)
        d = self.b.structural(name="structural-rescan-skip", scan=scan)
        row = vc.validate_contribution(d)  # passes despite the embedded string
        self.assertEqual(row["verification"], "version-attested")

    # --- dispatch / path routing -------------------------------------------

    def test_non_tier_dir_rejected(self):
        d = self.b.root / "x" / "y" / ("d" * 64)
        d.mkdir(parents=True)
        self.assertFails(d, "not a contribution directory")

    def test_bad_contributor_id_segment_rejected(self):
        d = self.b.root / "case" / "corpus" / "Bad_CID" / HASH_A
        d.mkdir(parents=True)
        self.assertFails(d, "contributor_id path segment")

    def test_bad_hash_segment_rejected(self):
        d = self.b.root / "case" / "corpus" / "example-contributor" / "nothex"
        d.mkdir(parents=True)
        self.assertFails(d, "hex digest")


class ClassifyChangedPathsTests(unittest.TestCase):
    def test_maps_changed_files_to_contribution_dirs(self):
        dirs, strays = vc.classify_changed_paths(
            [
                f"corpus/alice/{HASH_A}/session.jsonl",
                f"corpus/alice/{HASH_A}/session.jsonl.scrubbed",
                f"structural/bob/{HASH_B}/scan.json",
                "README.md",  # outside the trees — ignored
            ]
        )
        self.assertEqual(
            dirs, [f"corpus/alice/{HASH_A}", f"structural/bob/{HASH_B}"]
        )
        self.assertEqual(strays, [])

    def test_allowlisted_non_contribution_paths_are_not_strays(self):
        dirs, strays = vc.classify_changed_paths(
            ["structural/README.md", "corpus/.gitkeep"]
        )
        self.assertEqual(dirs, [])
        self.assertEqual(strays, [])

    def test_file_at_wrong_depth_is_a_stray(self):
        # the anti-silent-bypass case: a file under a tier tree but not inside a
        # contribution dir must FAIL, not be silently ignored.
        _, strays = vc.classify_changed_paths(["corpus/loose-file.jsonl"])
        self.assertEqual(len(strays), 1)
        self.assertIn("loose-file.jsonl", strays[0])

    def test_malformed_path_segments_are_strays(self):
        _, strays = vc.classify_changed_paths(
            ["corpus/Bad_CID/nothex/session.jsonl"]
        )
        self.assertEqual(len(strays), 1)


class RemovalRoutingTests(unittest.TestCase):
    """A REMOVAL.md §6A tombstone PR deletes a contribution dir. The gate must
    treat a dir that is gone from disk as a removal (nothing to re-scan, exit 0),
    not re-scan it and FAIL on the missing session.jsonl — otherwise the required
    `gate-summary` check blocks the very takedown the runbook promises (#28)."""

    def _run(self, changed_lines: list[str]) -> tuple[int, str]:
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fh:
            fh.write("\n".join(changed_lines))
            path = fh.name
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = vc.main(["--changed-files", path])
        Path(path).unlink()
        return code, buf.getvalue()

    def test_fully_deleted_contribution_is_a_noop_removal(self):
        # `nonexistent-cid/<hash>` does not exist under the repo, so every changed
        # path under it was a deletion — the dir is gone. Exit 0, no re-scan.
        code, out = self._run(
            [
                f"corpus/nonexistent-cid/{HASH_A}/session.jsonl",
                f"corpus/nonexistent-cid/{HASH_A}/session.jsonl.scrubbed",
                f"corpus/nonexistent-cid/{HASH_A}/contribution.json",
                "manifest.jsonl",  # the dropped index row (repo root — ignored)
                "removals.jsonl",  # the appended ledger record (repo root — ignored)
            ]
        )
        self.assertEqual(code, 0)
        self.assertIn("REMOVAL", out)
        self.assertIn("nothing to re-scan", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
