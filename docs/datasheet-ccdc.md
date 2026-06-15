# Datasheet — Claude Code Data Collective (CCDC)

**What this is.** A corpus-level datasheet for CCDC as a citable research object, in the
[Datasheets for Datasets](https://arxiv.org/abs/1803.09010) / [Data Statements for NLP](https://aclanthology.org/Q18-1041/)
tradition, at Bender & Friedman **short-form** depth — one document, not the 50-question form. It
describes the corpus as a whole; the machine-readable per-contribution index is
[`manifest.jsonl`](../manifest.jsonl), and the authoritative field definitions live in
[SCHEMA.md](../SCHEMA.md). Where a section restates a decision made elsewhere, the linked document
controls.

> **Status — v0 scaffolding.** The corpus is seeded by the maintainer and has not yet opened for
> external contributions (see [README](../README.md#status)). The counts below are a point-in-time
> snapshot; [`manifest.jsonl`](../manifest.jsonl) is the live, authoritative index.

---

## Motivation

CCDC exists to break the **single-corpus ceiling**: nearly every credible Claude Code analytics or
research result to date has been built on its author's *private* session sample, which neither
scales, generalizes, nor can be independently verified. CCDC turns "share your sanitized sessions"
into a shared, multi-contributor asset that tool builders and researchers can develop against,
validate against, and compare against. Its first beneficiaries are parser/diagnostic projects that
need real session records — the sibling projects
[AgentFluent](https://github.com/frederick-douglas-pearce/agentfluent) and
[CodeFluent](https://github.com/frederick-douglas-pearce/codefluent). Full rationale, alternatives,
and decision history are in the [PRD](prd-ccdc.md).

It is the downstream of [`claude-code-sessions`](https://github.com/frederick-douglas-pearce/claude-code-sessions),
which provides the sanitizer, the structural scanner, and the authoritative session-format reference
that every contribution is built on.

## Composition

The corpus is two top-level trees, by contribution **tier** (the
[README](../README.md#two-contribution-tiers) owns the cross-tier comparison):

- **Tier 1 — full sanitized JSONL** ([`corpus/`](../corpus/)): complete Claude Code session
  transcripts scrubbed by [`ccs-sanitize`](https://github.com/frederick-douglas-pearce/claude-code-sessions/tree/main/tooling/sanitizer),
  each with its `.scrubbed` provenance sidecar. The high-value tier — the only one that can develop
  or validate a parser. Each instance is one session; fields include prompt text, file paths, code,
  and command output **after** sanitization.
- **Tier 2 — structural-stats profile** ([`structural/`](../structural/)): content-free profiles
  from [`scan.py --json`](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/main/tooling/format-scan/scan.py)
  — key/type taxonomy, counts, sizes, directory names; **no prompt text, no tool inputs/results, no
  paths, no UUIDs**. Each instance profiles a whole `~/.claude/projects/` root. The artifact format
  is documented in [`structural/README.md`](../structural/README.md).

**Snapshot at time of writing:** the seed corpus is maintainer-only — **3 Tier-1 sessions** and
**1 Tier-2 profile** from a single contributor, spanning Claude Code versions in the 2.1.x line.
This is *seed* content, not the intended steady state; the corpus is designed to grow with multiple
contributors. Always read [`manifest.jsonl`](../manifest.jsonl) for the current count and composition.

**Sensitive-content handling.** The corpus is derived from real sessions, so the raw inputs contain
prompts, paths, code, command output, and occasionally secrets. Two layers keep the *published* data
safe: Tier 1 is sanitized and then **independently re-scanned by CI** (the sidecar is never trusted —
[CI re-scan gate](../ci/README.md)); Tier 2 is **content-free by construction** (the scanner's
`EMITTABLE_VALUE_FIELDS` whitelist). Residual-PII risk that pattern-based scanning cannot catch (names,
emails, custom identifiers) is addressed by the contributor's own read-through under the
[attestation](../ATTESTATION.md) and by the [removal path](../REMOVAL.md). No raw, unsanitized
transcript is ever committed.

### Tier 2 is an unscoped, point-in-time snapshot

A Tier-2 `scan.json` profiles the contributor's **whole projects root as of scan time**, with no
bounded scope. Consequently its counts are:

- **Not directly comparable across contributors** — a per-environment census, not a normalized
  sample; the artifact carries no denominator (903 files could be two years or two weeks of use).
- **Not reproducible**, even by the contributor — the input keeps growing, so a later re-scan yields
  a different, superset snapshot. The byte-stable `<scan_id>` pins the *artifact*, not a *measurement*.
- **Only implicitly time-bounded** — the `versions` histogram brackets a Claude Code version range
  and the manifest's `contributed_at` bounds "scanned no later than"; there is no explicit scan window.

This is a property of the zero-leak contract, not an oversight (the SECURITY CONTRACT forbids the
timestamps/paths/UUIDs that would scope the input). Content-free scope metadata is under design
upstream in [claude-code-sessions#124](https://github.com/frederick-douglas-pearce/claude-code-sessions/issues/124)
/ [#125](https://github.com/frederick-douglas-pearce/claude-code-sessions/issues/125); this datasheet
is the canonical consumer-facing home for the caveat. See
[`structural/README.md`](../structural/README.md#scope--an-unscoped-point-in-time-snapshot) for the
fuller version.

## Collection process

Contributions are **donated**: contributors run the sanitizer (Tier 1) or scanner (Tier 2) over
their own session data and open a pull request, affirming the [attestation](../ATTESTATION.md)
(right to share + originals retained). A PR *is* the curation queue; nothing is crawled, scraped, or
collected without the contributor's deliberate action.

> **Self-selected, non-probability sample — the key generalizability caveat.** CCDC is a
> convenience sample of whoever chooses to donate sanitized sessions. It is **not** a random or
> representative sample of Claude Code users, projects, languages, or usage patterns, and it is
> skewed toward contributors willing and able to publish (e.g. open-source work, permissive employer
> policies). Until the corpus is both larger and multi-contributor it additionally carries
> single-contributor bias. **Results derived from CCDC describe the corpus, not the Claude Code user
> population; do not generalize to "Claude Code users" without independent justification.** This is
> the standard caveat for donated corpora and is stated here deliberately.

**Verification asymmetry (per tier).** Tier 1 rows are **independently re-scanned** by CI; Tier 2
rows are **version-attested, not re-scanned** (a structural profile cannot be re-derived without the
withheld raw input). This is a real difference in verification strength; consumers can tell which is
which from the path (`corpus/` vs. `structural/`) and the manifest's `verification` field.

## Preprocessing / cleaning / labeling

This is CCDC's differentiator — preprocessing *is* the safety model:

- **Tier 1** is the output of [`ccs-sanitize`](https://github.com/frederick-douglas-pearce/claude-code-sessions/tree/main/tooling/sanitizer),
  which scrubs raw session JSONL for safe publication; the committed `.scrubbed` sidecar records the
  sanitizer version, config version, and a residual scan. CI **re-runs the sanitizer's own residual
  scan** on every submitted file and never trusts the sidecar.
- **Tier 2** is the output of [`scan.py`](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/main/tooling/format-scan/scan.py)
  (`--json`, deterministic with `sort_keys=True`), content-free by construction.
- **Retained raw inputs.** Contributors are expected to keep their original inputs so a contribution
  can be **re-sanitized if the sanitizer's rules improve** — the Re-LAION "re-release a fixed
  version" pattern. The raw inputs are never published; only sanitized / content-free artifacts are.

Field-level semantics are authoritative in the upstream tools, not restated here.

## Uses

- **Intended:** developing and validating Claude Code session **parsers and diagnostics** (Tier 1);
  **format-evolution research** and aggregate structural analysis across versions/environments
  (Tier 2); and more generally any *Result* — analysis, schemas, evaluations, tooling — that reads or
  describes the data.
- **Use with care:** any claim that generalizes from the corpus to the broader Claude Code
  population (see the self-selected-sample caveat); any cross-contributor comparison of Tier-2 counts
  (see the unscoped-snapshot caveat).
- **Disallowed by license:** using the Data to **train AI models that compete with Anthropic**. The
  [CCDC-1.0 license](../LICENSE) permits commercial reuse and *Results* but carries this pass-through
  no-compete restriction.

## Distribution

Hosted publicly on GitHub for v0; a **Hugging Face Datasets mirror is deferred to v1** and the
[layout](../LAYOUT.md) is structured so that mirror is an additive step, not a migration. Corpus
content (everything under `corpus/` and `structural/`, plus `manifest.jsonl`) is licensed under the
**[CCDC Data License, Version 1.0](../LICENSE)** — commercial reuse permitted, attribution required,
no-compete-training restriction, **pass-through** so the terms survive re-hosting. Repository tooling
and docs are not claimed by that license.

**Croissant / schema.org (deferred to v1).** The manifest field names are kept close to schema.org
`Dataset` semantics where practical (`license`, `contributor_id` ↔ `creator`, `contributed_at` ↔
`datePublished`, `path`/`input_sha256` ↔ `distribution`/`identifier`) so that a future
[Croissant](https://github.com/mlcommons/croissant) JSON-LD export — which HF auto-generates from a
dataset card — is a cheap additive step rather than a remodel. No Croissant file ships in v0.

## Maintenance

- **Maintainer / contact:** Fred Pearce; governance, curation model, and continuity are in
  [GOVERNANCE.md](../GOVERNANCE.md). The corpus is designed to be **reconstructable from manifest +
  sidecars** and operable by someone other than the maintainer (bus-factor mitigation).
- **Removal & leak response.** A documented takedown path exists from day one: report privately via
  [`SECURITY.md`](../SECURITY.md) (GitHub Private Vulnerability Reporting) or publicly via the
  [leak/removal issue template](../.github/ISSUE_TEMPLATE/leak_or_removal.yml). SLA: acknowledge
  within **3 business days**, remove within **≤7 calendar days**. Mechanics — tombstone vs. history
  rewrite, the `removals.jsonl` ledger — are in [REMOVAL.md](../REMOVAL.md). Removal is **prospective
  and incomplete**: it stops CCDC distributing the data going forward but cannot reach forks, prior
  clones, or third-party caches, and is not a substitute for rotating a live credential.
- **Versioning & updates.** The corpus grows by merged PRs; `manifest.jsonl` is the CI-generated
  index. When the pinned sanitizer improves, the corpus is re-scanned against the new patterns and
  affected contributions can be re-sanitized from retained originals (a normal disclosure/re-release
  event, not an emergency).
- **Errata.** If a removal changes a published count or claim, it is noted so the corpus stays
  honestly described.

## See also

- [README](../README.md) · [GOVERNANCE.md](../GOVERNANCE.md) · [LICENSE](../LICENSE) ·
  [SCHEMA.md](../SCHEMA.md) · [LAYOUT.md](../LAYOUT.md) · [ATTESTATION.md](../ATTESTATION.md) ·
  [REMOVAL.md](../REMOVAL.md) · [`structural/README.md`](../structural/README.md)
- [`docs/prd-ccdc.md`](prd-ccdc.md) — design rationale and decision history (Motivation source).
- [`docs/research-governance-norms.md`](research-governance-norms.md) §1 — the documentation-norms
  scan (Datasheets / Data Statements / Dataset Cards / Croissant) behind this datasheet's shape.
- [`docs/glossary.md`](glossary.md) — terms of art used here.
