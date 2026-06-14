#!/usr/bin/env python3
"""Path-based contribution routing for CCDC CI — the single source of truth.

The corpus routes by **path, never by a contributor-controlled field** (LAYOUT.md):
a change under ``corpus/`` or ``structural/`` that lands in a well-formed
``<tier>/<contributor_id>/<sha256>/`` directory is a contribution; anything else
under a tier tree is either an allowlisted docs/keepalive file or a *stray* (a
contribution at the wrong depth / a misplaced file) that must fail CI.

This module is **pure stdlib on purpose.** It is imported by both the re-scan gate
(``validate_contribution.py``, which additionally pulls in the heavy git-installed
upstream sanitizer) and the lightweight sign-off check (``check_signoff.py``, #31),
so that the two CI routers can never disagree about what counts as a contribution.
Keeping it dependency-free lets the sign-off job run without installing
``ci/requirements.txt``.
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Iterable

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
