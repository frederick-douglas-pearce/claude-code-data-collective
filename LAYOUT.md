# Repository layout

This document fixes the **per-contribution file layout** for CCDC. The path conventions
below are **locked**: they bind every contribution from the first one onward and are hard to
change once data has landed. Anything marked _deferred_ is intentionally left unspecified
here and is locked separately before the corpus opens.

## Top level

```
corpus/         # Tier 1 — full sanitized session JSONL (CI re-scans every file)
structural/     # Tier 2 — content-free structural profiles (version-attested, not re-scanned)
manifest.jsonl  # the corpus index — one row per contribution (CI-generated; see "Manifest")
schema/         # JSON Schemas for contribution.json + manifest rows, with examples
README.md
LAYOUT.md       # this file
SCHEMA.md       # manifest + contribution.json field schema (locked)
```

The two tiers live in **separate top-level trees on purpose.** The CI gate runs a
fundamentally different job per tier — a fail-closed independent re-scan for `corpus/`, a
presence/format attestation check for `structural/`. Keeping the tiers in distinct trees
means *which* job runs is decided by the path — declaratively, and auditable from the diff —
never from a field a contributor controls. It also keeps the layout honest that full
sessions are the preferred tier, and leaves room for a future analytic tier as a clean,
additive third tree.

## Tier 1 — `corpus/`

```
corpus/<contributor_id>/<input_sha256>/
  ├── session.jsonl            # the sanitized session transcript
  ├── session.jsonl.scrubbed   # the ccs-sanitize sidecar (sanitizer_version, input_sha256, …)
  └── contribution.json        # contributor attestation + license affirmation (schema: SCHEMA.md)
```

- **`<contributor_id>`** — the contributor's stable handle. Assignment is deferred to the
  contribution-path work.
- **`<input_sha256>`** — the SHA-256 of the _original, unsanitized_ input file, as recorded
  in the `.scrubbed` sidecar. It is the **only handle for retroactive PII removal**, so it
  keys the directory.
- **`session.jsonl`** — canonical filename. The original session filename (a UUID) is **not**
  used in the path; the sidecar records it if needed.
- **`session.jsonl.scrubbed`** — the sidecar produced by
  [`ccs-sanitize`](https://github.com/frederick-douglas-pearce/claude-code-sessions/tree/main/tooling/sanitizer).
  It must accompany every `session.jsonl`. CI re-derives the secret scan from `session.jsonl`
  itself and **never trusts the sidecar** — the sidecar is provenance, not proof.

## Tier 2 — `structural/`

```
structural/<contributor_id>/<scan_id>/
  ├── scan.json            # scan.py --json output (content-free structural profile)
  └── contribution.json    # contributor attestation + license affirmation (schema: SCHEMA.md)
```

- **`<scan_id>`** — the SHA-256 of the canonical `scan.json` bytes.
  [`scan.py`](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/main/tooling/format-scan/scan.py)
  emits its JSON with `sort_keys=True`, so the hash is deterministic and the path is
  **content-addressed**: the same scan always lands at the same path (idempotent), and the
  corpus stays reconstructable from the files alone. A structural scan profiles a whole
  projects-root, not a single session, so it has no `input_sha256` to key on — hence a hash
  of the profile itself.
- **`scan.json`** — the content-free structural profile. It is safe **by construction**: the
  scanner's `EMITTABLE_VALUE_FIELDS` whitelist guarantees it emits only key names, public
  taxonomy enums, value JSON-types, counts, sizes, and directory names — never prompt text,
  paths, or UUIDs. Because the raw input is withheld, this tier cannot be independently
  re-scanned; rows are **version-attested** (`scan_version` + `claude_code_version`), a
  weaker gate than Tier 1's that is accepted because the output is zero-leak regardless of
  trust.

See [`structural/README.md`](structural/README.md) for the `scan.json` artifact format, the
structural-only-for-v0 scope, and why no PII-takedown obligation attaches to this tier.

## Manifest

`manifest.jsonl` at the repository root is the corpus **index** — one JSON object per line,
one line per contribution, spanning both tiers. It is **generated and validated by CI** from
the per-contribution `contribution.json` files (plus CI-derived provenance), not hand-edited
in a pull request: a single hand-appended index would be a merge-conflict magnet as concurrent
contributions land.

The manifest **field schema is now locked** in **[SCHEMA.md](SCHEMA.md)**, alongside the
`contribution.json` schema and the machine-readable JSON Schemas under [`schema/`](schema/).
The required fields are as fixed in principle, with two corrections recorded in SCHEMA.md:
`claude_code_version` becomes `claude_code_versions` (an array — a `scan.json` profiles a whole
projects-root and a resumed session can span an upgrade), and every row carries a `tier` and a
`verification` marker (`ci-rescan` for Tier 1, `version-attested` for Tier 2) so consumers can
tell the tiers apart from the manifest alone. The schema is versioned (`schema_version`) so the
structural-tier variant is additive, not a retrofit.

Both halves of "generated and validated by CI" are now implemented: the PR re-scan gate
**validates** the would-be row (issue #8, [`ci/validate_contribution.py`](ci/validate_contribution.py)),
and a post-merge job **writes** it (issue #33, [`ci/generate_manifest.py`](ci/generate_manifest.py) +
[`.github/workflows/manifest-generate.yml`](.github/workflows/manifest-generate.yml)) — re-deriving
each row through the same validator and stamping the merge-commit `contributed_at` the PR could not
supply. Generation is idempotent, append/sort-disciplined, and removal-safe (it never re-emits a
tombstoned row — see [REMOVAL.md](REMOVAL.md)).

The `manifest.jsonl` currently committed is an **empty placeholder** — no contributions have
landed yet.

## Not locked by this document

Deferred on purpose, to avoid premature lock-in:

- **`<contributor_id>` assignment** and the end-to-end contribution path — locked with the
  contribution-path work. (The `contributor_id` *format* is fixed in [SCHEMA.md](SCHEMA.md);
  only its assignment is deferred.)

The **manifest field schema** and the per-contribution metadata file's name and fields, both
previously deferred here, are now locked in [SCHEMA.md](SCHEMA.md).
