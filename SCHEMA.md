# Manifest & metadata schema

This document **locks** two things LAYOUT.md left deferred:

1. the **per-contribution metadata file** — its name (`contribution.json`) and fields, and
2. the **`manifest.jsonl` row schema** — the CI-generated corpus index.

The machine-readable schemas in [`schema/`](schema/) are authoritative for validation; this
document is the human-readable companion and explains the **provenance** of every field —
who supplies it and how CI verifies it. Where prose and the JSON Schemas disagree, the JSON
Schemas win.

## Design: thin declaration, CI-derived provenance

CCDC's trust model is *don't trust the contributor or the sidecar* (see LAYOUT.md). The
schema enforces that by splitting every contribution into two artifacts:

- **`contribution.json`** — **thin**, contributor-authored. It carries only what cannot be
  derived from the data: the contributor's identity, a license affirmation, and an
  attestation. It declares **no** hashes, versions, tiers, or dates — anything a contributor
  could get wrong or misrepresent is *not* theirs to assert.
- **the `manifest.jsonl` row** — **CI-generated.** CI derives every provenance field from the
  contribution's artifacts (the sidecar, `session.jsonl`, `scan.json`), its path, and the
  merge commit, and **validates** the handful of fields that overlap with `contribution.json`
  fail-closed. The contributor never writes a manifest row.

The contributor-controlled trust surface is therefore three fields and two booleans. Nothing
load-bearing for verification is contributor-asserted.

## `contribution.json`

One per contribution, committed alongside the data at the contribution directory root
(`corpus/<contributor_id>/<input_sha256>/contribution.json` or
`structural/<contributor_id>/<scan_id>/contribution.json`). Schema:
[`schema/contribution.schema.json`](schema/contribution.schema.json).

| Field | Type | Required | Meaning |
|---|---|---|---|
| `schema_version` | `"1"` | yes | Version of the `contribution.json` schema this file follows. |
| `contributor_id` | string (slug) | yes | The contributor's stable handle. **Must equal** the `<contributor_id>` path segment. Assignment is deferred (see [Still deferred](#still-deferred)); the *format* is locked here: `^[a-z0-9][a-z0-9-]{0,38}$`. |
| `license` | `"CCDC-1.0"` | yes | The contributor's affirmation that this contribution is licensed under the [CCDC Data License v1.0](LICENSE). CI validates it equals the corpus license. |
| `attestation.right_to_contribute` | `true` | yes | The contributor affirms they have the right to contribute this data. |
| `attestation.original_retained` | `true` | yes | The contributor affirms they retain the original input, so the contribution can be re-sanitized if the sanitizer's rules improve (Tier 1) / re-derived if needed. |

The file is tier-agnostic: which tier a contribution belongs to is decided by its **path**
(`corpus/` vs `structural/`), never by a field in this file — consistent with LAYOUT.md's
rule that the tier is path-routed and not contributor-controlled. CI applies the tier from the
path; `contribution.json` is identical in shape for both tiers.

No free-text/descriptive fields ship in v0 — they are a PII surface and are deferred. The file
is zero-leak by construction: it contains an opaque handle, two enum constants, and two `true`
booleans.

Example — [`schema/examples/contribution.example.json`](schema/examples/contribution.example.json):

```json
{
  "schema_version": "1",
  "contributor_id": "example-contributor",
  "license": "CCDC-1.0",
  "attestation": {
    "right_to_contribute": true,
    "original_retained": true
  }
}
```

## `manifest.jsonl` row

`manifest.jsonl` at the repo root is the corpus index: one JSON object per line, one line per
contribution, spanning both tiers. It is **generated and validated by CI** — never
hand-edited (a hand-appended index would be a merge-conflict magnet, per LAYOUT.md). Schema:
[`schema/manifest-row.schema.json`](schema/manifest-row.schema.json).

The manifest is also the corpus's **reconstruct-without-the-maintainer artifact** (PRD §8
bus-factor): together with the per-contribution sidecars and content-addressed paths, it makes
the corpus fully reconstructable from the files alone — every row carries the `path`,
`input_sha256` (Tier 1) or `scan_id` (Tier 2), and versions needed to locate and re-verify a
contribution without any out-of-band state.

### Common fields (both tiers)

| Field | Type | Provenance | Meaning |
|---|---|---|---|
| `schema_version` | `"1"` | CI | Version of the manifest-row schema. |
| `tier` | `"full"` \| `"structural"` | **derived** from path | `corpus/` → `full`; `structural/` → `structural`. |
| `contributor_id` | string (slug) | **validated** (path == `contribution.json`) | The contributor's handle. |
| `path` | string | CI | The contribution directory, e.g. `corpus/<cid>/<input_sha256>/`. The stable handle for the contribution. |
| `contributed_at` | string (UTC date-time) | **derived** from merge commit | When the contribution merged into CCDC. Set from the merge commit date — *not* read from any contributor-supplied field. Distinct from the sidecar's `scrubbed_at` (when it was sanitized). |
| `license` | `"CCDC-1.0"` | **validated** (== `contribution.json`) | The license the contribution is under. |
| `claude_code_versions` | array of strings | **derived** from artifact | Distinct Claude Code `version` values observed. **Always an array** — a resumed session or a whole-projects scan can span several versions (see [Why versions are plural](#why-claude_code_versions-is-an-array)). |
| `verification` | `"ci-rescan"` \| `"version-attested"` | CI | The trust mechanism that gated this row. Encodes the real difference between the tiers so a consumer can tell which is which from the manifest alone (per README). Tier 1 → `ci-rescan`; Tier 2 → `version-attested`. |

### Tier 1 (`full`) additional fields

| Field | Type | Provenance | Meaning |
|---|---|---|---|
| `input_sha256` | hex64 | **validated** (path == sidecar) | SHA-256 of the original unsanitized input, from the `.scrubbed` sidecar. CI cannot re-derive it (the raw input is withheld), so it is attested by the sidecar and cross-checked against the path. The *secret scan*, by contrast, **is** independently re-derived from `session.jsonl` — that re-scan is what `verification: ci-rescan` records. |
| `sanitizer_version` | string | **derived** from sidecar | `sanitizer_version` from the `.scrubbed` sidecar. |

`claude_code_versions` (Tier 1) is derived from the distinct `version` leaves inside
`session.jsonl` — the sidecar does not carry it (the sanitizer deliberately leaves the
session `version` field untouched in the transcript).

Example — [`schema/examples/manifest-row.full.example.json`](schema/examples/manifest-row.full.example.json):

```json
{"schema_version":"1","tier":"full","contributor_id":"example-contributor","path":"corpus/example-contributor/9f2c4e1a7b3d5c8f0a2e6b4d9c1f3a5e7d8b0c2a4f6e8d0b1c3a5e7f9d2b4c6e/","contributed_at":"2026-06-12T17:30:00Z","license":"CCDC-1.0","claude_code_versions":["1.2.3"],"verification":"ci-rescan","input_sha256":"9f2c4e1a7b3d5c8f0a2e6b4d9c1f3a5e7d8b0c2a4f6e8d0b1c3a5e7f9d2b4c6e","sanitizer_version":"0.1.0"}
```

### Tier 2 (`structural`) additional fields

| Field | Type | Provenance | Meaning |
|---|---|---|---|
| `scan_id` | hex64 | **validated** (path == `sha256(scan.json)`) | SHA-256 of the canonical `scan.json` bytes (`scan.py` emits `sort_keys=True`, so the hash is deterministic). CI re-hashes `scan.json` and confirms it equals the `<scan_id>` path segment — the structural tier is fully content-addressed. |
| `tool` | `"ccs-format-scan"` | **validated** (allowlist; == `scan.json`) | The scanner that produced `scan.json`, from its `--json` `tool` field. Schema-pinned to the canonical scanner for v0 (a one-entry allowlist). With `scan_version` it forms the **attestation key** — see [Tier 2 attestation key](#tier-2-attestation-key). |
| `scan_version` | string | **derived** from `scan.json` | The scanner's own version, from its `--json` `scan_version` field (`ccs-format-scan` ≥ 0.1.0 stamps it). |

`claude_code_versions` (Tier 2) is derived from the keys of `scan.json`'s `versions` object
(the scanner reports versions as a multi-set with counts; the manifest keeps the distinct
keys).

#### Tier 2 attestation key

A structural profile cannot be independently re-derived (re-derivation needs the raw
projects-root the contributor withholds), so the tier is **version-attested**, not re-scanned.
The attestation key is the **pair `(tool, scan_version)`**, treated jointly — never
`scan_version` alone. A bare semver is ambiguous: a forked scanner could also call itself
`0.1.0`. Pairing it with `tool` records *which* scanner produced the profile, so an honest fork
at the same version is distinct provenance rather than a collision.

The `tool` value is **allowlisted in the schema** (const `"ccs-format-scan"` for v0). This is an
*admission* gate, not just a label: the zero-leak-by-construction guarantee belongs to **that
scanner's** `EMITTABLE_VALUE_FIELDS` whitelist and SECURITY CONTRACT, **not** to "structural
profiles" generically — an unrecognized fork could emit value-bearing fields. So an unrecognized
`tool` fails validation outright; admitting another trusted scanner is a deliberate, additive
schema change (the allowlist grows under review).

**Honest limitation.** This prevents *honest* same-version forks from colliding and
*unrecognized* tools from entering, but it cannot stop a fork that **dishonestly** stamps
`tool: "ccs-format-scan"`. That residual is inherent to a version-attested-not-re-scanned tier
(PRD D-CCDC-2) and is accepted because the output is zero-leak by construction regardless of
trust. The launch post (C1) names this asymmetry.

Example — [`schema/examples/manifest-row.structural.example.json`](schema/examples/manifest-row.structural.example.json):

```json
{"schema_version":"1","tier":"structural","contributor_id":"example-contributor","path":"structural/example-contributor/3a5e7f9d2b4c6e8f0a1b3c5d7e9f2a4b6c8d0e1f3a5b7c9d1e3f5a7b9c1d3e5f/","contributed_at":"2026-06-12T17:30:00Z","license":"CCDC-1.0","claude_code_versions":["1.2.1","1.2.3"],"verification":"version-attested","scan_id":"3a5e7f9d2b4c6e8f0a1b3c5d7e9f2a4b6c8d0e1f3a5b7c9d1e3f5a7b9c1d3e5f","tool":"ccs-format-scan","scan_version":"0.1.0"}
```

## Why `claude_code_versions` is an array

LAYOUT.md's "required in principle" lists named a singular `claude_code_version`. The actual
artifacts don't support a singleton:

- **Tier 2:** `scan.py --json` reports `versions` as `{version: count}` over a whole
  projects-root, which routinely spans many Claude Code versions. There is no single version.
- **Tier 1:** a single session can be resumed across a Claude Code upgrade, so even one
  `session.jsonl` can carry more than one `version`.

Representing it as `claude_code_versions` (a distinct-value array, `minItems: 1`) is honest
about both. This is a deliberate correction to LAYOUT.md's wording, recorded here.

## Upstream dependencies

Both upstream tools in
[`claude-code-sessions`](https://github.com/frederick-douglas-pearce/claude-code-sessions)
are operational (v0), and the schema's dependencies on them are now satisfied:

- **`scan.py` stamps `tool` + `scan_version` into `--json`** (Tier 2) — ✅ resolved by
  [claude-code-sessions#122](https://github.com/frederick-douglas-pearce/claude-code-sessions/pull/122)
  (`tool: "ccs-format-scan"`, `scan_version: "0.1.0"`, with a CHANGELOG bump policy and a
  cross-repo contract test). The structural row reads both directly and treats the pair as the
  [attestation key](#tier-2-attestation-key). The field names `tool`/`scan_version` and the
  value `ccs-format-scan` are a pinned cross-repo contract — renaming any is a downstream break.
- **The `.scrubbed` sidecar is confirmed against the built sanitizer** (Tier 1). `ccs-sanitize`
  is functionally built; its `sidecar.py` emits exactly the PRD §10 fields this schema derives
  from — `sanitizer_version`, `input_sha256`, `scrubbed_at`, `config_version`,
  `residual_scan`, … (and, as the schema assumes, *no* Claude Code version, so
  `claude_code_versions` is derived from `session.jsonl`). No upstream change is needed for the
  Tier 1 fields; opening `corpus/` is gated only on CCDC's own CI re-scan gate, not on
  upstream tooling.

## Still deferred

Locked separately, outside this document:

- **`<contributor_id>` assignment** — the *format* is locked here (`^[a-z0-9][a-z0-9-]{0,38}$`);
  *how* a contributor is assigned one is part of the contribution-path work.
- **The CI gate mechanism** — how the `corpus/**` and `structural/**` path globs map to jobs,
  the independent re-scan implementation, and how CI generates `manifest.jsonl` from the
  per-contribution `contribution.json` files plus derived provenance. These schemas are the
  contract that work builds against.
