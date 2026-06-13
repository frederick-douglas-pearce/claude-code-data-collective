# CI — the contribution gate

This directory holds the **independent CI re-scan merge gate** (issue #8 / sanitizer
PRD decision **D-4**) — the mechanical trust mechanism that gates every contribution
PR. Manual maintainer review does not scale; this gate is the load-bearer.

- [`validate_contribution.py`](validate_contribution.py) — the validator (library +
  CLI). Run by [`.github/workflows/contribution-gate.yml`](../.github/workflows/contribution-gate.yml).
- [`requirements.txt`](requirements.txt) — pinned dependencies.
- [`tests/`](tests/) — the validator's own test suite, including the
  gate-of-the-gate (a planted fake secret that **must** fail).

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
merge-commit date (`contributed_at`), which does not exist pre-merge, and lands with
the contribution-path work (#10).

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
