# Glossary — Claude Code Data Collective (CCDC)

Terms of art that recur across CCDC's governance, licensing, and tooling docs, defined once so
a reader can land on them. Several come in **contrasting pairs** (DCO vs. CLA, version-attested
vs. re-scanned, tombstone vs. history rewrite) where the distinction is the point — those are
grouped together below.

This glossary is a **pointer, not a second definition.** Each entry gives a one-line gloss and
links the *authoritative* source — the [LICENSE](../LICENSE) for licensed terms, the upstream
[`scan.py`](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/main/tooling/format-scan/scan.py)
SECURITY CONTRACT for scanner terms, and the relevant CCDC doc otherwise. Where a term is
defined in full elsewhere, that doc stays canonical and this entry defers to it; the glossary is
canonical only for terms (like DCO/CLA) that have no single home in the corpus's own docs.

> **Status — v0.** Not legal advice. For licensed terms the [LICENSE](../LICENSE) controls; this
> is a reading aid.

---

## Licensing & rights

- **Data / Corpus** — the session data and associated files made available under the CCDC Data
  License ([LICENSE §1.1](../LICENSE)). "The Corpus" also refers to the project/repository itself.
- **Inputs / Outputs** — Anthropic Commercial Terms of art: under
  [Anthropic's Commercial Terms](https://www.anthropic.com/legal/commercial-terms) the customer
  retains its rights to **Inputs** (what you send Claude) and owns its **Outputs** (what Claude
  returns). A session transcript is *your Inputs plus Claude's Outputs*, which is the basis on
  which a contributor has the right to share it — see [ATTESTATION.md §B2](../ATTESTATION.md#b2-the-anthropic-inputsoutputs-basis).
- **Results** — any outcome of computational analysis of the Data (statistics, parsers, schemas,
  evaluations, reports), **excluding any AI Model.** A defined term in
  [LICENSE §1.5](../LICENSE); the license imposes **no** restriction on Results
  ([§2.2](../LICENSE)). Distinct from Inputs/Outputs, which describe the *source* material.
- **AI Model / Competing Model / No Competing Models** — an **AI Model** is a machine-learning
  model and any system built on it ([LICENSE §1.6](../LICENSE)); a **Competing Model** is one
  intended to substitute for or compete with Anthropic's products ([§1.7](../LICENSE)). The
  **No Competing Models** condition ([§3.2](../LICENSE)) forbids using the Data to train, fine-tune,
  or improve a Competing Model. It is a *use* restriction on the Data, **not** a restriction on
  Results.
- **Source-available / use-restricted** *(vs. "open source")* — the corpus is **public and
  source-available**, but the license carries a field-of-use restriction (No Competing Models) and
  so is **not** "open source" under the OSI definition, which forbids such restrictions. CCDC says
  "source-available," never "open source." See the [LICENSE](../LICENSE) preamble,
  [ATTESTATION.md §A](../ATTESTATION.md#a-license-acceptance), and
  [research §4](research-governance-norms.md#4-licensing-norms-for-use-restricted-ai-training-data).
- **Pass-through** — each time the Data is Shared, the CCDC license travels with it and each
  recipient gets the rights directly from the Licensor; downstream terms may not strip the
  conditions ([LICENSE §3.3](../LICENSE)).

## Contribution & attestation

- **DCO** *(Developer Certificate of Origin)* — a lightweight, *per-commit* **provenance
  certification**: the contributor attests they have the right to submit the work, signalled by a
  `Signed-off-by` trailer (`git commit -s`). It transfers **no** rights. CCDC uses a **DCO-style**
  layer over the retained `contribution.json`; see [ATTESTATION.md](../ATTESTATION.md#how-you-make-this-attestation)
  and [why a bare checkbox is not enough](https://writing.kemitchell.com/2021/07/02/DCO-Not-CLA).
- **CLA** *(Contributor License Agreement)* — a **rights grant**: the contributor grants the
  project a copyright license, sometimes including the right to **relicense**. CCDC deliberately
  does **not** use a CLA — it takes no copyright assignment and no relicensing right; contributors
  keep ownership and license under CCDC-1.0 ([ATTESTATION.md — what this does *not* do](../ATTESTATION.md#what-this-attestation-does-not-do)).
- **Attestation (contributor attestation)** — what every contributor affirms when submitting:
  license acceptance, right to contribute, and original-retained. The human backstop for what the
  mechanical gate cannot catch. Canonical text: [ATTESTATION.md](../ATTESTATION.md).
- **Sign-off / `Signed-off-by`** — the git trailer added by `git commit -s` that ties the
  attestation to the contributor's git identity. CI **requires** it on contribution PRs
  ([`ci/check_signoff.py`](../ci/check_signoff.py); [GOVERNANCE.md — the review gate](../GOVERNANCE.md#the-review-gate)).
- **Right to contribute / right to share** — the contributor's affirmation that they may publish
  the data under the CCDC license (ownership, Anthropic basis, employer policy, no third-party
  content or PII they cannot share). The full surface is [ATTESTATION.md §B](../ATTESTATION.md#b-right-to-contribute).
- **`contribution.json`** — the thin, contributor-authored metadata file (identity + license +
  attestation booleans) committed with each contribution. It declares **no** hashes, versions, or
  dates — those are CI-derived. Schema: [SCHEMA.md](../SCHEMA.md#contributionjson).
- **`contributor_id`** — a contributor's stable handle (lowercased GitHub username), also the
  `corpus/<contributor_id>/…` path segment. Format locked in [SCHEMA.md](../SCHEMA.md#contributionjson).

## Tiers & artifacts

- **Tier 1 (full) / Tier 2 (structural)** — the two accepted contribution tiers. **Tier 1** is a
  complete sanitized transcript under `corpus/` (the preferred tier — the only one that can build
  or validate a parser). **Tier 2** is a content-free structural profile under `structural/` (the
  zero-leak on-ramp). The tier is decided by the **path**, never a contributor field. See
  [README.md](../README.md#two-contribution-tiers) and [LAYOUT.md](../LAYOUT.md).
- **Sanitizer (`ccs-sanitize`)** — the upstream tool that scrubs raw session JSONL into a Tier 1
  file plus its `.scrubbed` sidecar. Lives in
  [`claude-code-sessions`](https://github.com/frederick-douglas-pearce/claude-code-sessions/tree/main/tooling/sanitizer),
  not in CCDC.
- **Structural scanner (`scan.py`) / `scan.json`** — the upstream tool whose `--json` mode emits a
  Tier 2 profile (`scan.json`): a key/type taxonomy with counts and sizes, no prompts or paths.
  [Upstream `scan.py`](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/main/tooling/format-scan/scan.py).
- **`.scrubbed` sidecar** — the metadata file `ccs-sanitize` emits next to a Tier 1 transcript
  (`sanitizer_version`, `input_sha256`, `scrubbed_at`, `residual_scan`, …). CCDC's CI **never
  trusts** it — it re-derives the secret scan independently. Fields it carries: [SCHEMA.md Tier 1](../SCHEMA.md#tier-1-full-additional-fields).
- **Content-addressed / `input_sha256` / `scan_id`** — a contribution's directory is named by the
  SHA-256 of its content: `input_sha256` (the *original unsanitized input*, Tier 1) or `scan_id`
  (the canonical `scan.json` bytes, Tier 2). It is the stable handle for indexing and removal. See
  [SCHEMA.md](../SCHEMA.md#manifestjsonl-row) and [LAYOUT.md](../LAYOUT.md).
- **`manifest.jsonl`** — the repo-root corpus index, one CI-generated row per contribution across
  both tiers. **Never hand-edited.** Schema and provenance: [SCHEMA.md](../SCHEMA.md#manifestjsonl-row).
- **`EMITTABLE_VALUE_FIELDS` / SECURITY CONTRACT** — the allowlist and contract inside the upstream
  `scan.py` that make a Tier 2 profile **zero-leak by construction** (only enumerated, non-value
  fields are emitted). The zero-leak guarantee belongs to *that scanner*, which is why the
  structural `tool` is allowlisted. Source:
  [`scan.py`](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/main/tooling/format-scan/scan.py).

## Trust & verification

- **CI re-scan / residual scan** — the Tier 1 merge gate: CI re-runs the sanitizer's **own**
  residual secret scan over every submitted `corpus/` file, never trusting the `.scrubbed`
  sidecar. Recorded on the manifest row as `verification: "ci-rescan"`. See
  [GOVERNANCE.md — the review gate](../GOVERNANCE.md#the-review-gate) and
  [`ci/validate_contribution.py`](../ci/validate_contribution.py).
- **Version-attested** *(vs. re-scanned)* — the Tier 2 trust mechanism. A structural profile
  cannot be independently re-derived (the raw input is withheld), so the row is **trusted on its
  scanner version**, not re-scanned (`verification: "version-attested"`). A real, disclosed
  downgrade from Tier 1's gate, accepted because Tier 2 output is zero-leak by construction. See
  [SCHEMA.md — Tier 2 attestation key](../SCHEMA.md#tier-2-attestation-key).
- **Attestation key** — the pair **`(tool, scan_version)`**, treated jointly, that version-attests
  a Tier 2 row. `tool` is schema-allowlisted (`"ccs-format-scan"`) as an *admission gate*; a bare
  `scan_version` is ambiguous across forks. Full treatment: [SCHEMA.md](../SCHEMA.md#tier-2-attestation-key).
- **`verification`** — the manifest field recording which trust mechanism gated a row:
  `"ci-rescan"` (Tier 1) or `"version-attested"` (Tier 2). Lets a consumer tell the tiers apart
  from the manifest alone. [SCHEMA.md](../SCHEMA.md#manifestjsonl-row).
- **Sanitizer pin / pinned commit** — CCDC pins the upstream sanitizer to an immutable commit
  ([`ci/requirements.txt`](../ci/requirements.txt)) so the residual scan is reproducible and cannot
  change silently. Rule improvements land upstream, then CCDC **bumps the pin** in a separate
  reviewed PR. [GOVERNANCE.md — sanitizer versioning](../GOVERNANCE.md#sanitizer-versioning--coverage-updates).
- **Coverage boundary / known-pattern limitation** — the gate catches only patterns the scanner
  **already knows**; a novel-format secret or arbitrary PII passes *both* local sanitize and the CI
  re-scan. So the gate defends against *tampering for known patterns*, not unknown-pattern leaks —
  which is why maintainer diff review and the removal path are load-bearing. [GOVERNANCE.md — what the gate does and does not guarantee](../GOVERNANCE.md#what-the-gate-does-and-does-not-guarantee).
- **Disclosure event** — a secret/PII hit on **already-merged** data (e.g. surfaced when the
  sanitizer pin is bumped and the corpus is re-scanned). Routed privately through the removal
  runbook, never a public CI log. [REMOVAL.md §10](../REMOVAL.md#10-sanitizer-re-scan-hits-are-disclosure-events).
- **Benevolent gatekeeper / curation** — CCDC's governance model: a single maintainer holds final
  say on inclusion and removal, and every contribution passes one enforced pre-merge gate (it is
  *not* open-write). [GOVERNANCE.md — curation model](../GOVERNANCE.md#curation-model).
- **Bus factor** — the continuity/security risk of work concentrated on one maintainer (the
  xz-utils lesson). CCDC discloses a bus factor of one as its top v0 risk and mitigates it
  structurally (reconstructable corpus, committed runbook, mechanical gate). [GOVERNANCE.md — continuity & escalation](../GOVERNANCE.md#continuity--escalation).

## Removal

- **Tombstone** *(vs. history rewrite)* — the **default** removal: delete the contribution
  directory and its manifest row from the published branch and append a `removals.jsonl` ledger
  record. Needs only repo **write** access. The data remains in git *history* (reachable only by an
  explicit old commit SHA). [REMOVAL.md §6A](../REMOVAL.md#6a-tombstone-procedure-default).
- **History rewrite** *(the exception)* — `git-filter-repo` + force-push + GitHub Support, removing
  the data from git history itself. Reserved for live-credential / serious-PII cases where presence
  in history is itself active harm; needs repo **admin**. [REMOVAL.md §6B](../REMOVAL.md#6b-history-rewrite-escalation-exception).
- **Prospective removal** — removal stops further distribution from CCDC **going forward**; it
  **cannot** retract forks, clones, or third-party caches. Stated honestly to every reporter, and
  acknowledged by every contributor. [ATTESTATION.md §B7](../ATTESTATION.md#b7-public-and-permanent-acknowledgment),
  [REMOVAL.md §9](../REMOVAL.md#9-the-honest-limits-state-these-to-every-reporter).
- **`removals.jsonl`** — the append-only ledger that records *that* a contribution was removed
  (content-address, reason class, method) **without** retaining the data or the leaked content.
  The tombstone's durable audit trail. [REMOVAL.md §7](../REMOVAL.md#7-the-removals-ledger-removalsjsonl).
- **Leak report vs. removal request** — a **leak report** (PII/secret found in the corpus) can come
  from **anyone**, no identity check; a **removal request** (a contributor taking down their own
  data) must come from the contributor and gets a lightweight identity proof. [REMOVAL.md](../REMOVAL.md#2-verify-the-requester-removal-requests-only).

---

## See also

- [LICENSE](../LICENSE) — the controlling terms for all licensed definitions.
- [ATTESTATION.md](../ATTESTATION.md) · [GOVERNANCE.md](../GOVERNANCE.md) ·
  [SCHEMA.md](../SCHEMA.md) · [REMOVAL.md](../REMOVAL.md) — the docs these terms live in.
- [`docs/research-governance-norms.md`](research-governance-norms.md) — the comparable-dataset
  norms behind the DCO/CLA, takedown, and licensing choices.
- Upstream [`claude-code-sessions`](https://github.com/frederick-douglas-pearce/claude-code-sessions)
  — the sanitizer, `scan.py`, and format reference the artifact terms point to.
