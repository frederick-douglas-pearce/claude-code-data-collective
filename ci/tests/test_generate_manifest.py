#!/usr/bin/env python3
"""Tests for CCDC manifest generation (#33) — ci/generate_manifest.py.

Run directly:
    python3 ci/tests/test_generate_manifest.py
or via pytest. Requires ci/requirements.txt (generation re-runs the gate's
validate_contribution, which imports the upstream sanitizer and jsonschema).

Fixtures reuse the validator suite's FixtureBuilder so a "contribution on disk" is
built the same content-addressed way the gate validates. `contributed_at` is injected
via a stub resolver — these tests assert generation's bookkeeping (idempotency,
removal-safety, sort/merge), not git date plumbing, which the workflow owns.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import generate_manifest as gm  # noqa: E402
import validate_contribution as vc  # noqa: E402
from test_validate_contribution import (  # noqa: E402
    HASH_A,
    HASH_B,
    GOOD_CONTRIBUTION,
    FixtureBuilder,
)


def _contribution(cid: str) -> dict:
    # The gate cross-checks contribution.json's contributor_id against the path
    # segment, so a fixture's cid and its contribution.json must agree.
    return dict(GOOD_CONTRIBUTION, contributor_id=cid)

# A fixed merge date for the stub resolver; schema-shaped (…Z).
STAMP = "2026-06-14T12:00:00Z"


def _const_resolver(stamp: str = STAMP):
    return lambda _path: stamp


class GenerateTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        # Build contributions directly under the temp root's tier trees so their
        # repo-relative paths (corpus/<cid>/<hash>/) match what generate() expects.
        self.b = FixtureBuilder(self.root)
        self.manifest = self.root / "manifest.jsonl"
        self.removals = self.root / "removals.jsonl"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _full(self, cid: str = "alice", input_sha256: str = HASH_A) -> str:
        # FixtureBuilder nests under <name>/corpus/...; use "." so the tier tree sits
        # at the temp root and the contribution path is corpus/<cid>/<hash>/.
        self.b.full(
            name=".", cid=cid, input_sha256=input_sha256,
            contribution=_contribution(cid),
        )
        return f"corpus/{cid}/{input_sha256}/session.jsonl"

    def _structural(self, cid: str = "bob") -> tuple[str, str]:
        d = self.b.structural(name=".", cid=cid, contribution=_contribution(cid))
        rel = d.relative_to(self.root).as_posix()
        return f"{rel}/scan.json", f"{rel}/"

    def _generate(self, changed: list[str]):
        return gm.generate(
            changed,
            manifest_path=self.manifest,
            removals_path=self.removals,
            contributed_at_for=_const_resolver(),
        )

    # --- happy path --------------------------------------------------------

    def test_indexes_a_new_full_contribution(self):
        changed = [self._full()]
        added, text = self._generate(changed)
        self.assertEqual(added, [f"corpus/alice/{HASH_A}/"])
        row = json.loads(text.splitlines()[0])
        self.assertEqual(row["tier"], "full")
        self.assertEqual(row["contributed_at"], STAMP)
        self.assertEqual(row["verification"], "ci-rescan")
        self.assertEqual(row["path"], f"corpus/alice/{HASH_A}/")

    def test_row_key_order_matches_schema_examples(self):
        _, text = self._generate([self._full()])
        # SCHEMA.md example order: schema_version, tier, contributor_id, path,
        # contributed_at, license, ... — insertion order, not sorted keys.
        keys = list(json.loads(text.splitlines()[0]).keys())
        self.assertEqual(keys[:5], [
            "schema_version", "tier", "contributor_id", "path", "contributed_at",
        ])
        # compact, no spaces after separators
        self.assertNotIn(", ", text)
        self.assertTrue(text.endswith("\n"))

    # --- idempotency / one row per path ------------------------------------

    def test_rerun_does_not_duplicate(self):
        changed = [self._full()]
        _, text1 = self._generate(changed)
        self.manifest.write_text(text1, encoding="utf-8")
        added2, text2 = self._generate(changed)
        self.assertEqual(added2, [])  # nothing new
        self.assertEqual(text2, text1)  # byte-identical

    def test_existing_row_contributed_at_is_not_moved(self):
        changed = [self._full()]
        # Seed the manifest with the row carrying an OLD date.
        _, text = self._generate(changed)
        old = json.loads(text.splitlines()[0])
        old["contributed_at"] = "2020-01-01T00:00:00Z"
        self.manifest.write_text(json.dumps(old) + "\n", encoding="utf-8")
        # A re-run with a different resolver date must keep the original.
        added, text2 = gm.generate(
            changed,
            manifest_path=self.manifest,
            removals_path=self.removals,
            contributed_at_for=_const_resolver("2099-12-31T00:00:00Z"),
        )
        self.assertEqual(added, [])
        self.assertEqual(json.loads(text2.splitlines()[0])["contributed_at"],
                         "2020-01-01T00:00:00Z")

    # --- sort discipline ---------------------------------------------------

    def test_rows_are_sorted_by_path(self):
        # zeta sorts after alpha regardless of insertion / push order.
        c1 = self._full(cid="zeta", input_sha256=HASH_A)
        c2 = self._full(cid="alpha", input_sha256=HASH_B)
        _, text = self._generate([c1, c2])
        paths = [json.loads(l)["path"] for l in text.splitlines()]
        self.assertEqual(paths, sorted(paths))
        self.assertEqual(paths[0], f"corpus/alpha/{HASH_B}/")

    # --- removal safety ----------------------------------------------------

    def test_deleted_dir_is_skipped(self):
        # changed-files names a contribution path, but the dir does not exist on disk
        # (the removal commit deleted it). Generation must not fail or index it.
        added, text = self._generate([f"corpus/ghost/{HASH_A}/session.jsonl"])
        self.assertEqual(added, [])
        self.assertEqual(text, "")

    def test_tombstoned_address_is_not_resurrected(self):
        # The dir still exists on disk (re-run over a pre-removal range), but its
        # content address is in the removals ledger → must stay unindexed.
        changed = [self._full()]
        self.removals.write_text(
            json.dumps({
                "removed_at": STAMP, "tier": "full", "contributor_id": "alice",
                "input_sha256": HASH_A, "method": "tombstone",
            }) + "\n",
            encoding="utf-8",
        )
        added, text = self._generate(changed)
        self.assertEqual(added, [])
        self.assertEqual(text, "")

    # --- fail-closed -------------------------------------------------------

    def test_stray_path_fails_closed(self):
        with self.assertRaises(gm.GenerationError) as ctx:
            self._generate(["corpus/loose-file.jsonl"])
        self.assertIn("not valid contributions", str(ctx.exception))

    def test_corrupt_existing_manifest_fails_loud(self):
        self.manifest.write_text("{not json}\n", encoding="utf-8")
        with self.assertRaises(gm.GenerationError):
            self._generate([self._full()])


class DriftTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.b = FixtureBuilder(self.root)
        self.manifest = self.root / "manifest.jsonl"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_in_sync_reports_no_drift(self):
        self.b.full(name=".", cid="alice", input_sha256=HASH_A,
                    contribution=_contribution("alice"))
        _, text = gm.generate(
            [f"corpus/alice/{HASH_A}/session.jsonl"],
            manifest_path=self.manifest,
            removals_path=self.root / "removals.jsonl",
            contributed_at_for=_const_resolver(),
        )
        self.manifest.write_text(text, encoding="utf-8")
        missing, orphans = gm.find_drift(self.manifest, repo_root=self.root)
        self.assertEqual(missing, [])
        self.assertEqual(orphans, [])

    def test_unindexed_dir_is_drift(self):
        # A contribution on disk that never made it into the manifest (skipped run).
        self.b.full(name=".", cid="alice", input_sha256=HASH_A,
                    contribution=_contribution("alice"))
        missing, orphans = gm.find_drift(self.manifest, repo_root=self.root)
        self.assertEqual(missing, [f"corpus/alice/{HASH_A}/"])
        self.assertEqual(orphans, [])

    def test_orphan_row_is_drift(self):
        # An indexed path with no directory on disk (should never happen normally).
        row = {"path": f"corpus/ghost/{HASH_A}/"}
        self.manifest.write_text(json.dumps(row) + "\n", encoding="utf-8")
        missing, orphans = gm.find_drift(self.manifest, repo_root=self.root)
        self.assertEqual(missing, [])
        self.assertEqual(orphans, [f"corpus/ghost/{HASH_A}/"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
