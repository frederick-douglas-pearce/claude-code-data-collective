# Governance — Claude Code Data Collective (CCDC)

How CCDC is curated: who decides what enters the corpus, how contributions are reviewed,
how data is removed, and what happens when the maintainer is unavailable. This is the
one-page constitution; the operational detail it points to lives in the linked docs.

> **Status — v0.** This governance is in force for the v0 corpus. It binds every
> contribution from the first. Changing it is itself governed (see
> [Changing this document](#changing-this-document)).

## Curation model

CCDC is **curated, with a benevolent gatekeeper** — *not* a federated or open-write corpus.
Every contribution passes through a single review gate before it merges. At this data
sensitivity (real session transcripts that can carry prompts, paths, and secrets), an
enforced pre-merge gate is structurally necessary, not optional.

- **Maintainer / gatekeeper:** Fred Pearce ([@frederick-douglas-pearce](https://github.com/frederick-douglas-pearce)),
  the sole maintainer for v0. The maintainer holds final say on inclusion and removal.
- **The pull request is the curation queue.** There is no side channel — contributions
  arrive as PRs against this repository, are reviewed in the open, and merge only after the
  gate passes. See [CONTRIBUTING.md](CONTRIBUTING.md) for the contributor-facing walkthrough.
- **Two maintainers are deliberately out of scope for v0.** Multi-maintainer / committee
  governance is a v1+ concern (see [`docs/prd-ccdc.md`](docs/prd-ccdc.md) §10). The bus-factor
  mitigation for a single maintainer is in [Continuity & escalation](#continuity--escalation),
  not "add a second person."

## Inclusion criteria

A contribution is eligible to merge only if **all** of the following hold. These are gate
conditions, not preferences:

1. **It is one of the two accepted tiers**, placed in the correct tree
   (see [LAYOUT.md](LAYOUT.md)):
   - **Tier 1 — full sanitized JSONL** under `corpus/`: a complete transcript scrubbed by
     [`ccs-sanitize`](https://github.com/frederick-douglas-pearce/claude-code-sessions/tree/main/tooling/sanitizer),
     with its `.scrubbed` sidecar. **The preferred tier** — only full sessions can develop or
     validate a parser.
   - **Tier 2 — structural-stats profile** under `structural/`: a content-free
     [`scan.py --json`](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/main/tooling/format-scan/scan.py)
     profile. The zero-leak on-ramp; it complements full sessions, it does not substitute for
     them. See [`structural/README.md`](structural/README.md).
2. **No raw session JSONL, and no secrets.** Only sanitized Tier 1 files or content-free
   Tier 2 profiles. Raw transcripts from `~/.claude/projects/` are never accepted.
3. **It carries a complete manifest contribution record**, per the locked field schema in
   [SCHEMA.md](SCHEMA.md). `input_sha256` is mandatory — it is the only handle for later removal.
4. **The contributor has the right to share it** and has affirmed the
   [contributor attestation](ATTESTATION.md): right to share under
   [Anthropic's Commercial Terms](https://www.anthropic.com/legal/commercial-terms) and any
   applicable employer policy, and agreement to the [CCDC Data License](LICENSE).

Eligibility is necessary, not sufficient: the maintainer may decline a contribution that
clears the mechanical gate (for example, on quality, redundancy, or residual-risk grounds).
Curation is a judgment, and the gatekeeper exercises it.

## The review gate

Every PR passes through two layers. The mechanical layer is the load-bearing trust mechanism —
**manual review does not scale and is not what the corpus's safety rests on.**

- **Mechanical CI re-scan (Tier 1).** [`ci/validate_contribution.py`](ci/validate_contribution.py),
  run by [the contribution gate workflow](.github/workflows/contribution-gate.yml), re-derives
  the secret scan from every submitted `corpus/` file by re-running the sanitizer's *own*
  residual scan. **It never trusts the contributor's `.scrubbed` sidecar.** Any residual fails
  the PR.
- **Version attestation (Tier 2).** A structural profile cannot be independently re-derived
  without the raw input the contributor is withholding, so Tier-2 rows are **attested by
  `scan_version` + `claude_code_version`, not re-scanned.** This is a real, accepted downgrade
  from Tier 1's gate — structural output is zero-leak by construction regardless of trust — and
  it is visible to consumers from the path (`structural/` vs. `corpus/`) and the manifest.
- **Maintainer review.** The maintainer confirms tier placement, manifest completeness,
  attestation, and overall fit, and merges. Critically, the maintainer also **reads the diff
  for what the mechanical gate structurally cannot catch** (see the coverage boundary below) —
  novel-format secrets, names/emails, and org-specific identifiers. In v0 this human pass is a
  **required pre-merge backstop, not optional.** Reviewers do not paste suspected secrets/PII
  into PR threads — those go through the removal path below.

The verification-strength asymmetry between the tiers is intentional and disclosed; see
[`docs/prd-ccdc.md`](docs/prd-ccdc.md) §3.

### What the gate does and does not guarantee

The CI re-scan re-runs the sanitizer's *own* residual scan, so it catches only **patterns the
scanner already knows**. A novel secret format — or any PII (names, emails, bespoke identifiers)
— that the scanner has no signature for passes *both* the contributor's local sanitize *and* the
CI re-scan, because both share the same blind spot. The gate's real guarantee is therefore
**defense against a tampered, hand-edited, or wrong-config'd file for known patterns — not
prevention of unknown-pattern leaks.** That boundary is inherent to pattern-based scanning, it is
accepted, and it is why the two catch-nets above and below it are load-bearing, not decorative:
the **required maintainer diff review** (pre-merge) and the **leak/removal path** (post-merge).
The evidence base for this is recorded in
[`docs/research-governance-norms.md`](docs/research-governance-norms.md) §3b.

### Sanitizer versioning & coverage updates

The sanitizer is shared upstream tooling
([`ccs-sanitize`](https://github.com/frederick-douglas-pearce/claude-code-sessions/tree/main/tooling/sanitizer)),
not a CCDC artifact. The CI gate **pins it to an immutable commit**
([`ci/requirements.txt`](ci/requirements.txt)), so the residual scan is reproducible and cannot
change silently. New contributors will surface patterns the current rules do not catch; here is
how that is handled — and one thing it deliberately is **not**:

- **Sanitizer config is never bundled into a contribution PR.** Validation config must never be
  contributor-controlled — a contributor able to influence the residual scanner could *weaken* it
  to pass their own leak. (The asymmetry: extending a contributor's *local* scrub is strictly
  safe; touching the *CI* scanner is not.) This is structural, not a judgment call.
- **Rule improvements flow upstream.** A new pattern is added and tested in `claude-code-sessions`,
  reviewed there, and released; CCDC then **bumps the pinned commit in a separate,
  maintainer-reviewed PR.** The affected contributor **re-sanitizes from their retained original**
  and resubmits — the reason contributors are asked to keep their originals.
- **Org-specific patterns** too narrow for the shared scanner (internal hostnames, project
  codenames) are the **contributor's pre-submission responsibility**, covered by the attestation +
  maintainer review + leak path — *not* by the mechanical gate. Contributors are encouraged to
  extend their own local scrub; they never alter the CI config.
- **On every pin bump, the corpus is re-scanned** against the new scanner, so a pattern that
  becomes known later is caught in already-merged data. Such a hit is a **disclosure event** and
  is routed through the [removal path](#removal--leak-response), not a public CI log. *(Planned
  CI job; see [`docs/research-governance-norms.md`](docs/research-governance-norms.md).)*

## Removal & leak response

The sanitizer scrubs secrets and identifiers; it is **not** a meaning-scrubber, so proprietary
or personal content can survive in prose. A removal path is therefore a day-one promise, not a
later feature.

**Report a leak / request removal:** open a
[leak-or-removal issue](.github/ISSUE_TEMPLATE/leak_or_removal.yml). Anyone may file — you do
not need to be the contributor. **Do not paste the secret or PII into the issue** (it is
public); point to *where* it is by file path and/or `input_sha256` / `scan_id` and *describe*
the kind of data. If a live credential leaked, **rotate it now** — CCDC cannot rotate it for you.

**Service levels** (calendar time from when a report is filed):

| Stage | Target |
|-------|--------|
| **Acknowledge & triage** | within **3 business days** |
| **Remove verified leaked secret/PII** | within **7 calendar days** of acknowledgment |
| **Remove valid contributor request** (own data) | within **7 calendar days** of acknowledgment |
| **Live-credential leak** | treated as urgent — actioned ahead of the above, best-effort same-week |

> ⏳ **These SLA numbers are a v0 proposal pending the maintainer's ratification** — they bind
> contributors, so confirm them before the corpus opens. The 3-day / 7-day defaults are
> deliberately conservative for a single-maintainer project.

**Mechanics** — *what* removal does (documented tombstone vs. git-history rewrite, keyed on
`input_sha256`) lives in the removal runbook, **[REMOVAL.md](REMOVAL.md)** (tracked in
[#6](https://github.com/frederick-douglas-pearce/claude-code-data-collective/issues/6); being
finalized). The runbook is a committed doc, executable by someone who is not the maintainer —
that is a hard requirement, not a convenience.

## Continuity & escalation

The dominant risk to CCDC is sustainability and PII-triage liability concentrated on one
maintainer — and, as the xz-utils incident showed, a solo maintainer of a trust-bearing
artifact is a *security* exposure, not just a continuity one.

> ⚠️ **Known v0 risk, disclosed not hidden: CCDC currently has a single maintainer and no
> named backup.** This is the project's top structural risk. Naming a second trusted human with
> admin rights, and documenting succession (repo / org / domain / credentials), is a
> pre-wider-launch goal. Until then the mitigations below are what keep the corpus safe and
> recoverable without heroics.

The mitigation is structural, not "the maintainer works harder":

- **The corpus is fully reconstructable** from the manifest + sidecars — recoverable without
  the maintainer.
- **The removal runbook is a committed doc** ([REMOVAL.md](REMOVAL.md)), not knowledge held in
  one person's head.
- **The mechanical CI gate**, not manual review, carries the trust load — so the gate keeps
  working whether or not the maintainer is watching a given PR.
- **A leak/removal path exists from day one** (above) and is the documented entry point.

**Escalation.** If a leak report gets no acknowledgment within the SLA, escalate by
@-mentioning the maintainer on the issue and, if still unanswered, opening a second issue
labeled `security` that references the first. If the maintainer becomes unavailable for an
extended period, the corpus remains safe to leave in place (the CI gate already vetted every
Tier-1 file); time-sensitive removals fall back to the documented runbook, which any party
with repository write access can execute.

## Changing this document

Governance changes come in through a PR like any other change, are described in the PR, and
require the maintainer's approval to merge. Material changes that affect already-merged
contributions (for example, a stricter inclusion rule or a changed SLA) are called out in the
PR's **Security review** section so the effect on existing contributors is explicit. The locked
file layout ([LAYOUT.md](LAYOUT.md)) and manifest schema ([SCHEMA.md](SCHEMA.md)) are
deliberately hard to change; treat amendments to them as schema migrations, not edits.

## See also

- [README.md](README.md) — what CCDC is and the cross-tier comparison.
- [ATTESTATION.md](ATTESTATION.md) — what every contributor affirms.
- [CONTRIBUTING.md](CONTRIBUTING.md) — the contributor walkthrough *(being finalized)*.
- [LAYOUT.md](LAYOUT.md) · [SCHEMA.md](SCHEMA.md) — locked per-contribution paths and field schemas.
- [REMOVAL.md](REMOVAL.md) — removal mechanics *(being finalized,
  [#6](https://github.com/frederick-douglas-pearce/claude-code-data-collective/issues/6))*.
- [LICENSE](LICENSE) — the CCDC Data License, Version 1.0.
- [`docs/prd-ccdc.md`](docs/prd-ccdc.md) · [`docs/roadmap-ccdc.md`](docs/roadmap-ccdc.md) —
  design rationale and sequencing.
- [`docs/research-governance-norms.md`](docs/research-governance-norms.md) — the due-diligence
  scan of comparable-dataset governance norms behind these decisions.
