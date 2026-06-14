#!/usr/bin/env python3
"""Enforce DCO-style ``Signed-off-by`` on CCDC contribution commits (#31).

ATTESTATION.md asks every contributor to sign off their commits (``git commit -s``)
as a complementary, DCO-style layer over the retained ``contribution.json``. This
check makes that ``-s`` layer **load-bearing rather than advisory**: a contribution
PR whose commits lack the trailer fails CI.

Scope is path-routed, deliberately *not* the stock DCO App (which would require
sign-off on every PR and clash with the infra/docs "N/A" escape in the PR template).
The routing reuses ``contribution_paths.classify_changed_paths`` — the SAME function
the re-scan gate uses — so the two CI routers can never disagree about what counts as
a contribution. A PR requires sign-off when it touches a tier tree in any way that is
not purely allowlisted docs/keepalive paths, i.e. when it yields contribution dirs
**or strays**: a malformed contribution attempt is still a contribution PR and must
carry the attestation (the re-scan gate fails it separately, for the path).

This module is pure stdlib (+ git on PATH) so the sign-off CI job runs without
installing ci/requirements.txt. Squash-merge collapses the per-commit trailers into
one on ``main``; that is expected — the durable per-contribution record is
``contribution.json`` (see ATTESTATION.md / PR #29). We check the PR's own commits,
where the trailers actually live.

Run the test suite with:
    python3 ci/tests/test_check_signoff.py
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parent))

from contribution_paths import classify_changed_paths  # noqa: E402

# A DCO trailer as emitted by ``git commit -s``: ``Signed-off-by: Real Name <addr>``
# on its own line. Case-insensitive on the key; requires a name and an
# angle-bracketed, @-bearing address so an empty or structureless trailer does not
# pass. MULTILINE so the trailer is matched anywhere in the commit body.
SIGNOFF_RE = re.compile(
    r"^\s*Signed-off-by:\s+\S.*\s+<[^@\s<>]+@[^@\s<>]+>\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def has_signoff(message: str) -> bool:
    """True if a commit message carries a well-formed ``Signed-off-by`` trailer."""
    return SIGNOFF_RE.search(message) is not None


def is_contribution_pr(changed_paths: Iterable[str]) -> bool:
    """True if the changed paths constitute a contribution (requires sign-off).

    Routes identically to the re-scan gate: any contribution dir OR any stray under
    a tier tree counts. A PR touching only allowlisted docs/keepalive paths (or
    nothing under a tier tree) is infra/docs and is exempt — mirroring the PR
    template's "N/A" escape.
    """
    contribution_dirs, strays = classify_changed_paths(changed_paths)
    return bool(contribution_dirs or strays)


def _git(args: list[str], repo: str | None = None) -> str:
    cmd = ["git"]
    if repo is not None:
        cmd += ["-C", repo]
    cmd += args
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return proc.stdout


def pr_commits(base: str, head: str, repo: str | None = None) -> list[str]:
    """Non-merge commit SHAs that are unique to ``head`` — the PR's own commits.

    Anchored on the merge-base so a stale ``base`` (``main`` advanced past the branch
    point) can never drag in commits the contributor did not author. Merge commits
    are exempt by DCO convention — a contributor cannot add a trailer to a merge of
    upstream they did not write.
    """
    merge_base = _git(["merge-base", base, head], repo=repo).strip()
    out = _git(["rev-list", "--no-merges", f"{merge_base}..{head}"], repo=repo)
    return [line.strip() for line in out.splitlines() if line.strip()]


def unsigned_commits(
    base: str, head: str, repo: str | None = None
) -> list[tuple[str, str]]:
    """``(sha, subject)`` for every PR commit missing a ``Signed-off-by`` trailer."""
    bad: list[tuple[str, str]] = []
    for sha in pr_commits(base, head, repo=repo):
        # %B is the raw commit body; its first line is the subject, so a single
        # log call serves both the trailer check and the display subject.
        message = _git(["log", "-1", "--format=%B", sha], repo=repo)
        if not has_signoff(message):
            lines = message.strip().splitlines()
            bad.append((sha, lines[0] if lines else ""))
    return bad


def _read_changed_files(source: str) -> list[str]:
    if source == "-":
        text = sys.stdin.read()
    else:
        text = Path(source).read_text(encoding="utf-8")
    return text.splitlines()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "CCDC sign-off gate — require Signed-off-by on contribution PR commits "
            "(#31). Path-scoped: infra/docs PRs are exempt."
        )
    )
    parser.add_argument(
        "--changed-files",
        metavar="FILE",
        required=True,
        help=(
            "newline-separated changed repo paths (or '-' for stdin). Used to decide "
            "whether this PR is a contribution and therefore requires sign-off."
        ),
    )
    parser.add_argument("--base", required=True, help="PR base ref/SHA")
    parser.add_argument("--head", required=True, help="PR head ref/SHA")
    parser.add_argument(
        "--repo", default=None, help="git repo dir (default: current dir)"
    )
    args = parser.parse_args(argv)

    changed = _read_changed_files(args.changed_files)
    if not is_contribution_pr(changed):
        print(
            "Not a contribution PR (no corpus/ or structural/ contribution paths) — "
            "sign-off not required."
        )
        return 0

    bad = unsigned_commits(args.base, args.head, repo=args.repo)
    if bad:
        print(
            "FAIL: contribution PR commits are missing a `Signed-off-by` trailer.\n"
            "Sign off your commits and re-push — e.g. `git commit --amend -s` (last "
            "commit) or `git rebase --signoff <base>` (all). See ATTESTATION.md.\n",
            file=sys.stderr,
        )
        for sha, subject in bad:
            print(f"  {sha[:12]}  {subject}", file=sys.stderr)
        return 1

    print("PASS: every contribution PR commit carries a `Signed-off-by` trailer.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
