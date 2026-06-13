# Contributor attestation — Claude Code Data Collective (CCDC)

What every contributor affirms when they submit data to CCDC. It is the human backstop for the
risks the mechanical gate **structurally cannot** catch (arbitrary PII, novel-format secrets,
employer-owned content) — so it is a gate condition, not a formality.

> **Status — v0.** This attestation is in force for the v0 corpus and binds every contribution
> from the first. Its surface follows the due-diligence scan in
> [`docs/research-governance-norms.md`](docs/research-governance-norms.md) §3. Changing it is
> governed like any other change to the corpus's rules (see [GOVERNANCE.md](GOVERNANCE.md#changing-this-document)).
> This is not legal advice.

## How you make this attestation

You do **not** sign a separate document. You affirm this attestation, in full and by reference,
through three committed, **retained** acts that travel with your contribution:

1. **Your [`contribution.json`](SCHEMA.md#contributionjson)** — committed alongside your data —
   carries the machine-readable affirmation:
   - `"license": "CCDC-1.0"` — you accept the [CCDC Data License v1.0](LICENSE) (see
     [§A](#a-license-acceptance)).
   - `"attestation": { "right_to_contribute": true }` — you affirm **all** of
     [§B](#b-right-to-contribute) below.
   - `"attestation": { "original_retained": true }` — you affirm
     [§C](#c-you-retain-the-original).
2. **A signed-off commit.** Your contribution PR's commits carry a `Signed-off-by` trailer
   (commit with `git commit -s`), tying this affirmation to your git identity at commit time.
   This is a complementary, DCO-style layer over the retained `contribution.json`: the trailer
   stays visible on the PR's commits even though a squash-merge collapses them into one on `main`,
   so the durable per-contribution record remains `contribution.json`.
3. **The contributor-attestation block in the [pull-request template](.github/PULL_REQUEST_TEMPLATE.md)**,
   which points back here and cannot be skipped for a contribution PR.

This is deliberate. A bare checkbox with no audit trail "achieves next to nothing"
([Kemitchell](https://writing.kemitchell.com/2021/07/02/DCO-Not-CLA)); folding the affirmation
into the per-contribution `contribution.json` means the signed assertion is **retained in the
repository, one record per contribution**, not a transient PR comment. The two booleans and the
license constant are the handles; **this document is the content they affirm.**

---

## A. License acceptance

You license your contribution under the **[CCDC Data License, Version 1.0](LICENSE)** (the
`"license": "CCDC-1.0"` field). In particular you understand and accept:

- The Data may be used, modified, and shared by others, **including commercially**, subject to
  attribution.
- **No Competing Models** ([LICENSE §3.2](LICENSE)): neither you nor any downstream recipient may
  use the Data to train, fine-tune, or improve an AI model that competes with Anthropic. This
  is the no-training condition; it does **not** restrict *Results* (analysis, parsers, schemas,
  research tooling).
- The license is **pass-through** and the corpus is **public and source-available, not "open
  source."** You are granting these rights to the world, not to a closed group.

## B. Right to contribute

By setting `attestation.right_to_contribute = true`, you affirm **each** of the following for
the data in this contribution:

### B1. Ownership / right to share
You own this data or are otherwise authorized to share it publicly under the CCDC Data License.
You are not under any contractual, confidentiality, or other obligation that this contribution
would breach.

### B2. The Anthropic Inputs/Outputs basis
A session transcript is **your Inputs plus Claude's Outputs.** Under
[Anthropic's Commercial Terms](https://www.anthropic.com/legal/commercial-terms), the customer
retains its rights to Inputs and owns its Outputs. You affirm that **your** access to Claude
gives you the rights you are exercising here — you are affirming your *own* rights, not relying
on CCDC to backfill them. You understand this basis is **plan-dependent** (e.g. Commercial vs.
consumer terms differ) and that it is **your** responsibility to confirm it covers you.

### B3. Employer / confidentiality
If this session arose from work for an employer or client, you have the right under any
applicable employer policy, confidentiality obligation, or agreement to contribute it. This is
the clause a provenance-only certification (a stock DCO) most lacks; sessions routinely capture
employer-owned work, and that risk is allocated to you here.

### B4. Third-party content and PII
To the best of your knowledge, the contribution contains **no secrets and no personal data**
(your own or anyone else's) — no names, emails, customer identifiers, credentials, or other PII
— beyond what the sanitizer removes, and **no third-party content you lack the right to share.**

> **Why this is on you, not the gate.** The CI re-scan re-runs the sanitizer's *own* residual
> scan and catches only patterns the scanner already knows. It does **not** detect arbitrary PII
> or novel-format secrets — that blind spot is shared by your local sanitize and the CI re-scan
> alike (see [GOVERNANCE.md](GOVERNANCE.md#what-the-gate-does-and-does-not-guarantee) and
> [`docs/research-governance-norms.md`](docs/research-governance-norms.md) §3b). This clause is
> where that residual-leak risk is formally allocated. You are expected to **read your own
> sanitized transcript** before submitting.

### B5. Org-specific scrubbing is your responsibility
Identifiers too narrow for the shared upstream sanitizer — internal hostnames, project
codenames, team handles — are **yours to scrub before submission.** Extend your *local* scrub
config to remove them (always safe — it removes more before publication). You never alter the
CI scanner config; validation config is never contributor-controlled, by design (see
[GOVERNANCE.md](GOVERNANCE.md#sanitizer-versioning--coverage-updates)).

### B6. Sanitization affirmation
Every committed Tier 1 file is the **output of [`ccs-sanitize`](https://github.com/frederick-douglas-pearce/claude-code-sessions/tree/main/tooling/sanitizer)**,
committed with its `.scrubbed` sidecar; every Tier 2 file is the **output of
[`scan.py --json`](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/main/tooling/format-scan/scan.py)**.
**No raw transcript from `~/.claude/projects/` is in this contribution.**

### B7. Public-and-permanent acknowledgment
You understand that once merged, the contribution is **public and effectively permanent.**
Removal is **prospective** — it stops further distribution from CCDC, but **forks, clones,
mirrors, and cached copies cannot be retracted.** Contribute only data you are willing to have
permanently public.

### B8. Removal-path acknowledgment
You have read the [removal path](GOVERNANCE.md#removal--leak-response) ([REMOVAL.md](REMOVAL.md))
and understand how to request removal of your own data and how leak reports are handled,
including the published service levels and their limits (above).

## C. You retain the original

By setting `attestation.original_retained = true`, you affirm you **retain your original,
pre-sanitization input.** If the sanitizer's rules improve, your contribution can then be
**re-sanitized from your retained original and resubmitted** — the normal path when the pinned
sanitizer version is bumped (see [GOVERNANCE.md](GOVERNANCE.md#sanitizer-versioning--coverage-updates)).

---

## What this attestation does *not* do

- It does **not** transfer copyright or grant CCDC a CLA-style relicensing right. You license
  the Data under CCDC-1.0; you keep ownership.
- It does **not** waive Anthropic's own terms. Recipients of the Data remain independently
  subject to Anthropic's Commercial Terms and Usage Policies to the extent those apply.
- It is **not** a warranty that the data is leak-free. It is a good-faith affirmation; the
  required maintainer diff review and the post-merge removal path are the catch-nets behind it.
- It is **not** legal advice. If you are unsure whether you may share a session — especially
  employer-related work (B3) — do not contribute it until you have confirmed.

## See also

- [SCHEMA.md](SCHEMA.md#contributionjson) — the `contribution.json` fields this attestation maps to.
- [GOVERNANCE.md](GOVERNANCE.md) — inclusion criteria, the review gate and its coverage boundary,
  and the removal path.
- [LICENSE](LICENSE) — the CCDC Data License v1.0 (the controlling terms for §A).
- [REMOVAL.md](REMOVAL.md) — removal mechanics (the basis for B8).
- [`docs/research-governance-norms.md`](docs/research-governance-norms.md) §3 — the evidentiary
  basis for why this attestation goes beyond a stock DCO.
