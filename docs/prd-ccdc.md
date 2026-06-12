# PRD — Claude Code Data Collective (CCDC) v0

**Status:** Design. Decomposed into issues #3–#15; no implementation started.
**Owner:** Fred Pearce
**Roadmap item:** [roadmap-ccdc.md](roadmap-ccdc.md)
**Tracking issue (epic):** [#2 — Launch Claude Code Data Collective (CCDC) v0](https://github.com/frederick-douglas-pearce/claude-code-data-collective/issues/2)
**Created:** 2026-06-11
**Last updated:** 2026-06-11

> Like [prd-sanitizer.md](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/main/.claude/specs/prd-sanitizer.md), this PRD is deliberately verbose: it records the
> rationale, the alternatives rejected, and the decision history alongside the spec. Sections
> marked **Decision** record a resolved question; **Alternatives** record what was rejected and why.
> The authoritative *task* breakdown lives in the issues; this doc is the *why* behind them.

---

## 1. Purpose

The Claude Code Data Collective (CCDC) is a small, curated, publicly hosted corpus of Claude Code
session data — contributed by multiple people, gated by a maintainer review + mechanical CI scan,
and licensed for reuse. It exists to break the single-corpus ceiling: every credible Claude Code
analytics or research result to date (including this repo's own [retry-rate post](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/main/posts/2026-06-08-how-often-does-claude-retry-a-tool-call.md))
has been built on the author's *private* session sample, which neither scales nor generalizes nor
can be independently verified.

CCDC is the natural downstream of the sanitizer ([prd-sanitizer.md](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/main/.claude/specs/prd-sanitizer.md)): the
sanitizer makes "share your sessions" tractable; CCDC operationalizes it into a shared asset that
this repo's siblings ([AgentFluent](https://github.com/frederick-douglas-pearce/agentfluent),
[CodeFluent](https://github.com/frederick-douglas-pearce/codefluent)) and the wider community can
develop, validate, and compare against.

## 2. Two contribution tiers

The defining design decision of v0 is that CCDC accepts **two tiers** of contribution, serving
different needs at very different risk levels.

### Tier 1 — Full sanitized JSONL (the original plan)
Complete session JSONL, scrubbed by `ccs-sanitize`, with a `.scrubbed` sidecar. This is the
high-value tier: it is the only one that supports **parser / diagnostic development** — the
AgentFluent / CodeFluent use case — because a parser must run against real records, not aggregates.
It carries the full PII-leakage risk surface and therefore the full governance machinery (license,
attestation, removal runbook, independent CI re-scan).

### Tier 2 — Structural-stats profile (added 2026-06-11; **structural-only for v0**)
A content-free structural profile of a session corpus, produced by
[`tooling/format-scan/scan.py`](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/main/tooling/format-scan/scan.py): the top-level `type`/key
taxonomy, content-block types, session-subdirectory shape, `meta.json` manifest key names + value
JSON-types, version counts, and tool-results file shape — **no prompt text, no tool inputs/results,
no paths, no UUIDs.** The tier is safe *by construction*: `scan.py`'s `EMITTABLE_VALUE_FIELDS =
{type, version}` whitelist and SECURITY CONTRACT guarantee it emits only key names, public taxonomy
enums, value JSON-types, counts, sizes, and directory names.

**Decision (D-CCDC-1): ship Tier 2 first, structural-only.**
Tier 2 is zero-leak, reuses already-hardened tooling (`scan.py` + the claude-code-sessions#96/#97 pytest harness),
carries **no PII-takedown obligation**, and therefore bypasses the entire Tier-1 governance
long-pole. It is the ship-first proof-of-concept that seeds early momentum while the Tier-1
governance is still being drafted. It also has standalone value: cross-machine structural coverage
across Claude Code versions is the raw material for the blog series on the session format and how
fast it is evolving.

**Alternatives rejected:**
- *Analytic stats in v0* (retry rates, token/turn/tool-call distributions). Rejected for v0 →
  deferred to a separate **v0.5** deliverable ([#14](https://github.com/frederick-douglas-pearce/claude-code-data-collective/issues/14)).
  Analytic stats are under constant pressure to emit value-bearing fields ("top 10 commands",
  "most-used MCP servers") that can re-identify or leak content — especially for a single-session
  contribution from a *named* open-source project. The safe-by-construction property belongs to the
  current whitelist, not to "stats" generically; every value-bearing field added must get
  sanitizer-grade adversarial review. Do not let `scan.py`'s safety record launder a tool that
  hasn't earned it.
- *Tier 2 only.* Rejected: histograms can't develop or validate a parser. Full sessions remain the
  **visibly preferred** contribution in all tier-facing copy to avoid the easy tier crowding out the
  valuable one.

## 3. Trust model — and its asymmetry

The Tier-1 trust mechanism is **independent CI re-scan** (sanitizer PRD **D-4**): the corpus repo's
CI never trusts the contributor's sidecar; it re-derives the secret scan from the submitted fixture
and fails the PR on any residual. Manual maintainer review does not scale and is not the trust
load-bearer; the mechanical gate is.

**Decision (D-CCDC-2): Tier 2 rows are version-attested, not re-scanned — and the launch post says so.**
A structural contribution *cannot* be independently re-derived, because re-derivation needs the raw
input the Tier-2 contributor is explicitly withholding. So Tier-2 rows are attested by
`scan_version` + `claude_code_version` and validated for attestation-field presence — not re-scanned.
This is a genuine downgrade from Tier 1's gate, it is **accepted** (structural output is zero-leak by
construction regardless of trust), and it **must be stated plainly in the launch post** so consumers
know which rows are verified vs. attested. Tracked in [#13](https://github.com/frederick-douglas-pearce/claude-code-data-collective/issues/13).

## 4. Decisions to lock before contributor #1

These bind future contributors and are hard to walk back. Each maps to a child issue.

| # | Decision | Resolution / status | Issue |
|---|----------|---------------------|-------|
| Host | GitHub repo, curation-via-PR, HF mirror deferred | **Locked:** `claude-code-data-collective`, public; HF → v1 | [#3](https://github.com/frederick-douglas-pearce/claude-code-data-collective/issues/3) |
| License | commercial-reuse permitted + no-training-competing-AI clause | Open — **needs Fred's legal sign-off** | [#5](https://github.com/frederick-douglas-pearce/claude-code-data-collective/issues/5) |
| Removal | takedown SLA + tombstone-vs-history-rewrite, keyed on `input_sha256` | Open | [#6](https://github.com/frederick-douglas-pearce/claude-code-data-collective/issues/6) |
| Manifest | mandatory per-contribution metadata schema, locked from row #1 | Open | [#7](https://github.com/frederick-douglas-pearce/claude-code-data-collective/issues/7) |
| CI gate | independent re-scan (D-4) as merge gate | Open | [#8](https://github.com/frederick-douglas-pearce/claude-code-data-collective/issues/8) |
| Attestation | right-to-share under Anthropic ToS + employer policy | Open — **needs Fred's legal sign-off** | [#9](https://github.com/frederick-douglas-pearce/claude-code-data-collective/issues/9) |

**Manifest required fields (Tier 1):** `claude_code_version`, `sanitizer_version`, `input_sha256`
(the only handle for retroactive removal), `contributor_id`, `contributed_at`, `license`.
**Tier 2 variant:** `scan_version`, `claude_code_version`, `contributor_id`, `contributed_at`,
`license`, tier marker — additive to the same versioned schema, not a retrofit.

## 5. Issue decomposition & dependency graph

Two tracks converge at the terminal launch post. **Track A** (full-JSONL governance) is the long
pole; **Track B** (structural tier) is the ship-first PoC that bypasses it.

```
A1(#3 repo+layout) ─┬─► Track A: A2(#4) A3(#5)* A4(#6) A5(#7) A7(#9)*
                      │            └─► A6(#8 CI gate) ─► A8(#10 path) ─► A9(#11 seed) ─┐
                      │                                                                     ├─► C1(#15 launch)
                      └─► Track B: B1(#12 structural tier) ─► B2(#13 attested rows) ─────┘
                          B3(#14 analytic, v0.5) — parked, off the v0 path
```
`*` = blocked on Fred's legal judgment.

| Code | Issue | Priority | Depends on |
|------|-------|----------|------------|
| A1 | #3 stand up repo + lock layout | P0 | — |
| A2 | #4 governance doc | P0 | A1 |
| A3 | #5 license (commercial + no-training) | P0 | A1 |
| A4 | #6 removal runbook | P0 | A1, A5 |
| A5 | #7 manifest schema | P0 | A1 |
| A6 | #8 CI re-scan gate | P1 | A1, A5 |
| A7 | #9 contributor attestation | P0 | A3 |
| A8 | #10 contribution path | P1 | A1, A5, A6, A7, B1, B2 |
| A9 | #11 seed corpus (long pole) | P1 | A8 |
| B1 | #12 structural-stats tier | P0 | A1 |
| B2 | #13 attested (not re-scanned) rows | P1 | A5 |
| B3 | #14 analytic tier (v0.5, parked) | P2 | B1 |
| C1 | #15 launch post (terminal) | P2 | A8, A9, B1, B2 |

## 6. v0 acceptance criteria (ship gate)

All mechanical, all in Fred's control (mirrors #2):

- [ ] Host live with a documented contribution path (#3, #10)
- [ ] Governance doc committed (#4)
- [ ] License published; attestation finalized (#5, #9)
- [ ] Removal runbook committed — executable by someone who is not Fred (#6)
- [ ] CI re-scan integrated as merge gate (#8)
- [ ] Structural tier live and documented as structural-only (#12, #13)
- [ ] ≥2 seed contributors with ≥3 sanitized sessions each merged (#11)
- [ ] Launch announcement published in `posts/` and cross-posted (#15)

## 7. Success / stall / kill criteria

- **v0 launched** (ship gate): §6 met. Mechanical.
- **v0 succeeded** (30–60 day outcome gate): ≥1 *external* (non-Fred) contribution merged; ≥1
  external citation or reuse. Network effects starting, not just Fred seeding.
- **v0 stalled** (60-day kill/pivot gate): 0 external contributions at day 60 → explicit kill/pivot
  review. Do not drift past this silently.

## 8. Bus-factor mitigation

The dominant risk (flagged independently by PM and architect) is the sustainability / PII-triage
liability. The mitigation is *not* "Fred works harder":

- Corpus is fully reconstructable from manifest + sidecars (recoverable without Fred).
- Removal runbook is a committed doc (#6), not in Fred's head.
- The mechanical CI gate (#8), not manual review, carries the trust load.
- A documented "report a leak" path exists from day one.
- **Tier 2 sidesteps the liability entirely** for the contributions that use it.

## 9. Resolved positions (do not relitigate)

- **Retry-rate 46-session corpus** (the unverifiable claim that motivates CCDC): **noted as a gap.**
  Not retro-published, no erratum. Folded into the launch post (#15) as the motivating example. Low priority.
- **Commercialization stance:** not a v0 blocker. Expectation is open-source-derived data; private-org
  data would require relationship/trust-building not required for v0. An open-source version of the
  sibling projects stays available regardless of any future monetization, which — if it ever happens —
  would be via services / consulting / paid features, decided later against a real customer base.
  Building on open-source Claude Code data has more upside than downside at this stage. The launch post
  still names who the primary beneficiaries are (incl. the maintainer's sibling projects).
- **Anthropic follow-up trigger:** **launch-post drafting** (option c). The warm channel (positive
  signal 2026-06-07) is followed up when C1 (#15) starts. Tracked as a checkbox on #2.

## 10. Out of scope for v0 (defer to v1+)

Hugging Face Datasets mirror; analytic-stats tier (#14, v0.5); automated ingestion / search /
discovery UX; sanitizer jitter mode (PRD D-3); multi-maintainer governance / committee structures;
quality-curation tooling (signal-richness scoring, dedup beyond `input_sha256`); automated
sanitizer-version-bump nudges; re-sanitization-on-rule-improvement tooling (the *expectation* that
contributors retain originals is in scope; the tooling is not).

## 11. Related

- [#2](https://github.com/frederick-douglas-pearce/claude-code-data-collective/issues/2) — epic / status board (child-issue map in its comments).
- [prd-sanitizer.md](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/main/.claude/specs/prd-sanitizer.md) — sanitizer threat model; **D-4** independent re-scan, **§12b** config safety.
- [tooling/format-scan/scan.py](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/main/tooling/format-scan/scan.py) — the Tier-2 structural scanner (its SECURITY CONTRACT is the zero-leak guarantee).
- [roadmap-v0.md](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/main/.claude/specs/roadmap-v0.md) — W2 (sanitizer) named "sanitize before sharing" as the unmet need CCDC operationalizes.
- Sibling projects: [AgentFluent](https://github.com/frederick-douglas-pearce/agentfluent), [CodeFluent](https://github.com/frederick-douglas-pearce/codefluent).
