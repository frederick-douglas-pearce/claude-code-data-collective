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
README.md
LAYOUT.md       # this file
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
  └── <metadata file>          # this contribution's manifest row + attestation (name + schema deferred)
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
  ├── scan.json        # scan.py --json output (content-free structural profile)
  └── <metadata file>  # this contribution's manifest row + attestation (name + schema deferred)
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
the per-contribution metadata files, not hand-edited in a pull request: a single
hand-appended index would be a merge-conflict magnet as concurrent contributions land.

The manifest **field schema is deferred** and locked separately before contributor #1. The
required fields are already fixed in principle:

- **Tier 1:** `claude_code_version`, `sanitizer_version`, `input_sha256`, `contributor_id`,
  `contributed_at`, `license`
- **Tier 2:** `scan_version`, `claude_code_version`, `contributor_id`, `contributed_at`,
  `license`, plus a tier marker

The `manifest.jsonl` currently committed is an **empty placeholder** — no contributions have
landed yet.

## Not locked by this document

Deferred on purpose, to avoid premature lock-in:

- The **manifest field schema** and the per-contribution metadata file's **name and fields**
  — locked with the manifest-schema work.
- The **CI gate mechanism** — how the `corpus/**` and `structural/**` path globs map to jobs,
  and the re-scan implementation itself — locked with the CI-gate work. Note for that work:
  the `structural/**` glob must target the `<contributor_id>/<scan_id>/` contribution depth
  (or explicitly exclude `structural/README.md`), so the tier doc is never mistaken for a
  contribution.
- **`<contributor_id>` assignment** and the end-to-end contribution path — locked with the
  contribution-path work.
