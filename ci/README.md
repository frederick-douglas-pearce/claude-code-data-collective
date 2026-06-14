# CI — the contribution gate

This directory holds the **independent CI re-scan merge gate** (issue #8 / sanitizer
PRD decision **D-4**) — the mechanical trust mechanism that gates every contribution
PR. Manual maintainer review does not scale; this gate is the load-bearer.

- [`validate_contribution.py`](validate_contribution.py) — the validator (library +
  CLI). Run by [`.github/workflows/contribution-gate.yml`](../.github/workflows/contribution-gate.yml).
- [`check_signoff.py`](check_signoff.py) — the sign-off gate (#31): fails a
  contribution PR whose commits lack a `Signed-off-by` trailer. Pure stdlib (+ git);
  also run by the contribution-gate workflow. See [Sign-off gate](#sign-off-gate).
- [`contribution_paths.py`](contribution_paths.py) — pure-stdlib path router
  (`classify_changed_paths` + the tier/allowlist/segment rules), the **single source
  of truth** for "what is a contribution", imported by both the validator and the
  sign-off gate so they cannot disagree.
- [`generate_manifest.py`](generate_manifest.py) — post-merge manifest row generation
  (#33). Run by [`.github/workflows/manifest-generate.yml`](../.github/workflows/manifest-generate.yml).
- [`requirements.txt`](requirements.txt) — pinned dependencies (the validator + manifest
  generation; the sign-off gate needs none of them).
- [`tests/`](tests/) — the validator's own test suite, including the
  gate-of-the-gate (a planted fake secret that **must** fail), plus the manifest and
  sign-off suites.

## The one rule

**CI never trusts the contributor's `.scrubbed` sidecar.** Everything the gate
accepts, it re-derives:

- **Tier 1 (`corpus/`)** is *re-scanned*. The gate re-runs the sanitizer's **own**
  residual secret scan (`ccs_sanitize.residual.scan_residual`, the full built-in
  pattern set — not a re-vendored subset) over the submitted `session.jsonl`. An
  honest file only exists because that identical scan already passed before the
  sanitizer would write it, so re-running it passes honest outputs and fails
  tampered or hand-edited ones. The sidecar is read for provenance only
  (`input_sha256`, `sanitizer_version`), and every value it asserts is cross-checked
  against something re-derivable (the content-addressed path; the file itself).
- **Tier 2 (`structural/`)** is *version-attested, not re-scanned* — the raw
  projects-root is withheld, so there is nothing to re-derive (PRD D-CCDC-2). The
  gate instead confirms the profile is content-addressed (`<scan_id>` ==
  `sha256(scan.json)`) and carries the attestation key (`tool` on the allowlist,
  `scan_version` present). **No re-scan is attempted.**

Tier is routed by **path** (`corpus/` vs `structural/`), never by a
contributor-controlled field.

In both tiers the gate assembles the *would-be* `manifest.jsonl` row from CI-derived
provenance and validates it against the locked
[`schema/manifest-row.schema.json`](../schema/manifest-row.schema.json). It is
**validate-only**: it does not write `manifest.jsonl`. Row *generation* needs the
merge-commit date (`contributed_at`), which does not exist pre-merge, so it runs in a
separate **post-merge** job — [`generate_manifest.py`](generate_manifest.py) (#33),
driven by [`.github/workflows/manifest-generate.yml`](../.github/workflows/manifest-generate.yml).
It re-uses this validator to re-derive each newly-merged row, stamps each row's
per-path merge-commit date, and commits the appended index back to `main`. See
[Manifest generation](#manifest-generation) below.

## Dependencies (pinned, fail-closed)

The validator imports the upstream sanitizer and `jsonschema`. Both imports are
**fail-closed**: if a pinned dependency is missing, the gate errors rather than
silently skipping a check or falling back to a weaker in-repo copy. The upstream
sanitizer is pinned to an immutable commit in [`requirements.txt`](requirements.txt)
so the residual scan is reproducible and cannot change under us; bump it
deliberately when adopting a newer pattern set.

## Running locally

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r ci/requirements.txt

# the test suite (incl. the planted-secret gate-of-the-gate)
python3 ci/tests/test_validate_contribution.py

# validate specific contribution directories
python3 ci/validate_contribution.py corpus/<contributor_id>/<input_sha256>/

# or drive it the way CI does, from a list of changed paths
git diff --name-only origin/main...HEAD | python3 ci/validate_contribution.py --changed-files -
```

A changed path under a tier tree that is **not** inside a well-formed
`<contributor_id>/<sha256>/` contribution directory (and is not an allowlisted
non-contribution file such as `structural/README.md`) is a **stray** and fails the
gate — a contribution can never slip through as "nothing to validate".

## Sign-off gate

[`check_signoff.py`](check_signoff.py) (#31) makes the `git commit -s` layer of the
[attestation](../ATTESTATION.md) **load-bearing**: a contribution PR whose commits lack
a `Signed-off-by` trailer fails CI. It is deliberately **not** the stock DCO App (which
requires sign-off on *every* PR and would clash with the infra/docs "N/A" escape) — it
is path-scoped to contributions, routing on the *same* `classify_changed_paths` the
re-scan uses, so the two checks agree by construction. A PR requiring sign-off is one
that yields a contribution dir **or a stray** (a malformed contribution attempt is still
a contribution PR); infra/docs PRs touching no contribution path are exempt.

The trailer is checked on the PR's own commits, anchored on the merge-base so a stale
base (main moved on) can't drag in commits the contributor didn't author. Merge commits
are exempt (DCO convention). The check is pure stdlib — its CI job skips
`requirements.txt`.

```bash
# the way CI drives it
git diff --name-only origin/main...HEAD > changed.txt
python3 ci/check_signoff.py --changed-files changed.txt \
  --base origin/main --head HEAD

# the test suite (pure stdlib + git; no requirements.txt needed)
python3 ci/tests/test_check_signoff.py
```

## Manifest generation

[`generate_manifest.py`](generate_manifest.py) writes the index row the gate could
only *validate*. It runs **post-merge** (push to `main`) because a row's
`contributed_at` is the merge-commit date, which does not exist pre-merge. For each
contribution the push touched it re-runs the gate's own `validate_contribution`
(re-scan included — defense in depth), stamps each row's **per-path** add-commit date
(`git log --diff-filter=A`, so a push batching several merges still dates each row to
*its* merge), and appends to `manifest.jsonl`. The bot then commits the index back to
`main`.

Three properties keep that safe and quiet:

- **Idempotent.** Existing rows are kept verbatim — a path already indexed is never
  re-derived or moved — so a re-run never duplicates a row. Only absent paths are
  added; the file is rewritten sorted by `path` so its content is a pure function of
  the live corpus (the reason the index is CI-generated, never hand-edited).
- **Removal-safe.** A row is emitted only for a directory that still exists *and*
  whose content address is not in [`removals.jsonl`](../removals.jsonl) — so a
  tombstone (REMOVAL.md §6A/§7) can never be resurrected, even by re-running an old
  workflow over a pre-removal commit range.
- **Drift-detected.** A scheduled `--check` run asserts every contribution on disk is
  indexed (and vice-versa) and fails loudly on mismatch — the backstop for a
  generation run that was skipped or whose commit-back was rejected.

```bash
# what would be indexed for a set of changed paths (no write)
git diff --name-only <before> <after> \
  | python3 ci/generate_manifest.py --changed-files - --dry-run

# the drift check
python3 ci/generate_manifest.py --check

# the generation test suite
python3 ci/tests/test_generate_manifest.py
```

> **Infra note.** The generation job pushes `manifest.jsonl` directly to `main` (the
> index is CI-generated, never hand-edited; a PR-per-row would be pure churn). If
> `main` has PR-required branch protection, the github-actions bot must be allowed to
> push to it (or a dedicated token wired in), or the push is rejected and the index
> silently stalls. The push step fails loudly, and the drift check is the backstop.
