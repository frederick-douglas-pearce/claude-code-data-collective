#!/usr/bin/env python3
"""Tests for the CCDC sign-off gate (#31).

Run directly:
    python3 ci/tests/test_check_signoff.py
or via pytest. Pure stdlib + git on PATH — unlike the re-scan gate's suite this needs
no ci/requirements.txt, which is the point: the sign-off check is dependency-free so
its CI job can skip the heavy sanitizer install.

The git-walking tests build a throwaway repo in a temp dir at runtime (with gpg
signing disabled and a fixed identity) so commit SHAs and trailers are exact by
construction; nothing is committed to the repo under test.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import check_signoff as cs  # noqa: E402

HEX = "a" * 64  # an arbitrary valid 64-hex content address for path fixtures
SIGNED_BY = "Test User <test@example.com>"


class HasSignoffTest(unittest.TestCase):
    def test_trailer_present(self):
        self.assertTrue(
            cs.has_signoff(f"feat: thing\n\nbody\n\nSigned-off-by: {SIGNED_BY}")
        )

    def test_missing(self):
        self.assertFalse(cs.has_signoff("feat: thing\n\nno trailer here"))

    def test_lowercase_key_accepted(self):
        # git is case-sensitive emitting it, but be lenient on input.
        self.assertTrue(cs.has_signoff(f"x\n\nsigned-off-by: {SIGNED_BY}"))

    def test_inline_not_on_own_line_rejected(self):
        # The trailer must be its own line, not buried mid-sentence.
        self.assertFalse(
            cs.has_signoff(f"mentioning Signed-off-by: {SIGNED_BY} in prose blah")
        )

    def test_structureless_trailer_rejected(self):
        self.assertFalse(cs.has_signoff("x\n\nSigned-off-by:"))
        self.assertFalse(cs.has_signoff("x\n\nSigned-off-by: Just A Name"))
        self.assertFalse(cs.has_signoff("x\n\nSigned-off-by: <not-an-email>"))

    def test_multiple_trailers_ok(self):
        msg = (
            "x\n\nSigned-off-by: A One <a@ex.com>\n"
            "Signed-off-by: B Two <b@ex.com>"
        )
        self.assertTrue(cs.has_signoff(msg))


class IsContributionPrTest(unittest.TestCase):
    def test_contribution_dir_requires_signoff(self):
        self.assertTrue(
            cs.is_contribution_pr([f"corpus/alice/{HEX}/session.jsonl"])
        )

    def test_stray_under_tier_requires_signoff(self):
        # A malformed contribution attempt is still a contribution PR.
        self.assertTrue(cs.is_contribution_pr(["corpus/loose-file.jsonl"]))

    def test_infra_and_docs_exempt(self):
        self.assertFalse(
            cs.is_contribution_pr(
                ["ci/check_signoff.py", "GOVERNANCE.md", ".github/workflows/x.yml"]
            )
        )

    def test_allowlisted_tier_docs_exempt(self):
        self.assertFalse(cs.is_contribution_pr(["structural/README.md"]))


class _Repo:
    """A throwaway git repo for exercising the commit-walking helpers."""

    def __init__(self, path: Path):
        self.path = path
        self._git("init", "-q", "-b", "main")
        self._git("config", "user.name", "Test User")
        self._git("config", "user.email", "test@example.com")
        self._git("config", "commit.gpgsign", "false")

    def _git(self, *args: str) -> str:
        # Drive the module's own git wrapper so the tests exercise the real helper.
        return cs._git(list(args), repo=str(self.path))

    def commit(self, msg: str, signoff: bool = False, fname: str = "f") -> str:
        (self.path / fname).write_text(msg, encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-q", *(["-s"] if signoff else []), "-m", msg)
        return self._git("rev-parse", "HEAD").strip()

    def merge_unsigned(self, branch: str) -> None:
        # Force a real merge commit (no fast-forward), with no sign-off.
        self._git("merge", "--no-ff", "--no-edit", branch)


class CommitWalkTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = _Repo(Path(self._tmp.name))
        self.base = self.repo.commit("base: initial", signoff=True)

    def tearDown(self):
        self._tmp.cleanup()

    def test_all_signed_yields_no_unsigned(self):
        self.repo.commit("feat: a", signoff=True)
        head = self.repo.commit("feat: b", signoff=True)
        self.assertEqual(
            cs.unsigned_commits(self.base, head, repo=str(self.repo.path)), []
        )

    def test_unsigned_commit_is_flagged(self):
        self.repo.commit("feat: signed", signoff=True)
        self.repo.commit("feat: NOT signed", signoff=False)
        head = self.repo.commit("feat: signed again", signoff=True)
        bad = cs.unsigned_commits(self.base, head, repo=str(self.repo.path))
        self.assertEqual([s for _, s in bad], ["feat: NOT signed"])

    def test_base_commit_not_inspected(self):
        # Only the PR's own commits (base-exclusive) are checked.
        head = self.repo.commit("feat: a", signoff=True)
        # base itself was signed, but even if it weren't it must be out of range.
        shas = cs.pr_commits(self.base, head, repo=str(self.repo.path))
        self.assertNotIn(self.base, shas)
        self.assertIn(head, shas)

    def test_merge_commit_exempt(self):
        # Branch off base, make a signed commit, merge back with an unsigned merge
        # commit. The merge commit must NOT be flagged.
        self.repo._git("checkout", "-q", "-b", "side")
        self.repo.commit("feat: side work", signoff=True, fname="side")
        self.repo._git("checkout", "-q", "main")
        self.repo.merge_unsigned("side")
        head = self.repo._git("rev-parse", "HEAD").strip()
        self.assertEqual(
            cs.unsigned_commits(self.base, head, repo=str(self.repo.path)), []
        )

    def test_stale_base_does_not_drag_in_foreign_commits(self):
        # main advances past the branch point; an unsigned commit on main that is
        # NOT part of the PR must not be attributed to the PR (merge-base anchoring).
        branch_point = self.base
        self.repo._git("checkout", "-q", "-b", "pr")
        head = self.repo.commit("feat: pr work", signoff=True, fname="pr")
        self.repo._git("checkout", "-q", "main")
        self.repo.commit("chore: unrelated unsigned on main", signoff=False)
        advanced_base = self.repo._git("rev-parse", "HEAD").strip()
        # Pass the ADVANCED base (as GitHub would after main moved on).
        bad = cs.unsigned_commits(advanced_base, head, repo=str(self.repo.path))
        self.assertEqual(bad, [])
        self.assertNotEqual(advanced_base, branch_point)


class MainCliTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = _Repo(Path(self._tmp.name))
        self.base = self.repo.commit("base: initial", signoff=True)

    def tearDown(self):
        self._tmp.cleanup()

    def _changed_files(self, *lines: str) -> str:
        p = Path(self._tmp.name) / "changed.txt"
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return str(p)

    def _run(self, changed: str, head: str) -> int:
        return cs.main(
            [
                "--changed-files",
                changed,
                "--base",
                self.base,
                "--head",
                head,
                "--repo",
                str(self.repo.path),
            ]
        )

    def test_infra_pr_passes_even_with_unsigned_commits(self):
        head = self.repo.commit("chore: infra", signoff=False)
        changed = self._changed_files("ci/check_signoff.py")
        self.assertEqual(self._run(changed, head), 0)

    def test_contribution_pr_with_unsigned_fails(self):
        head = self.repo.commit("feat(corpus): add", signoff=False)
        changed = self._changed_files(f"corpus/alice/{HEX}/session.jsonl")
        self.assertEqual(self._run(changed, head), 1)

    def test_contribution_pr_all_signed_passes(self):
        head = self.repo.commit("feat(corpus): add", signoff=True)
        changed = self._changed_files(f"corpus/alice/{HEX}/session.jsonl")
        self.assertEqual(self._run(changed, head), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
