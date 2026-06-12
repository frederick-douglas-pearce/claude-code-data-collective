# Roadmap — Claude Code Data Collective (CCDC) v0

**Status:** Decomposed into issues #3–#15 on 2026-06-11. Epic: [#2](https://github.com/frederick-douglas-pearce/claude-code-data-collective/issues/2).

**Purpose:** Sequencing view for CCDC v0 — what to do, in what order, blocked by what. The full
rationale lives in [prd-ccdc.md](prd-ccdc.md); the authoritative task detail lives in the issues.
This file answers "where do I start, and what's next" at a glance.

**Audience:** Future Fred (or a future Claude session) picking CCDC back up.

---

## Context (what's already in place)

- **Sanitizer** `ccs-sanitize` v0.2.0 — fail-closed orchestration, residual scan, version-stamped
  sidecars, pre-run config-gitignore guard ([prd-sanitizer.md](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/main/.claude/specs/prd-sanitizer.md)). Makes Tier 1 possible.
- **Structural scanner** [`tooling/format-scan/scan.py`](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/main/tooling/format-scan/scan.py) — content-free,
  with a hardened SECURITY CONTRACT and the claude-code-sessions#96/#97 pytest harness. Makes Tier 2 *ship-first*.
- **Format docs** `reference/` — schema, tool-invocation cycle, subagent traces.
- **Anthropic channel** — warm; positive signal 2026-06-07. Follow-up trigger: launch-post drafting.

## Two tracks

- **Track A — full-JSONL governance (long pole):** host → governance / license / attestation /
  manifest → CI gate → contribution path → seed sessions.
- **Track B — structural-stats tier (ship-first PoC):** zero-leak, reuses `scan.py`, bypasses the
  Track A governance entirely. Land it early for momentum.

Both converge at the terminal launch post.

```
A1(#3) ─┬─► A2 A3* A4 A5 A7*  ─► A6(#8) ─► A8(#10) ─► A9(#11) ─┐
          │                                                          ├─► C1(#15)
          └─► B1(#12) ─► B2(#13) ─────────────────────────────────┘
              B3(#14) parked — v0.5, off path
```
`*` = blocked on Fred's legal-judgment sign-off (license #5, attestation #9).

## Sequenced work items

### Now (this week)
1. **A1 — #3** stand up `claude-code-data-collective` (public) + lock per-contribution file layout.
   *Unblocks everything; cheap; fully in Fred's control.* **P0, no deps.**
2. **B1 — #12** structural-stats tier (structural-only). *Ship-first PoC; lands while governance
   drafts; zero risk.* **P0, deps: A1.**
3. **A3 — #5 + A7 — #9** license + attestation: *kick off, don't expect to finish.* They carry
   the only human-judgment blocker — surface the wording questions to Fred now so the legal call
   bakes in parallel instead of becoming the last-minute gate on the seed long pole.

### Next (Track A governance, parallel after A1)
- **A2 — #4** governance doc · **A4 — #6** removal runbook · **A5 — #7** manifest schema.
- **B2 — #13** structural rows attested-not-re-scanned (deps: A5).

### Then (the path comes together)
- **A6 — #8** CI re-scan merge gate (deps: A1, A5).
- **A8 — #10** documented contribution path (deps: A1, A5, A6, A7, B1, B2).

### Long pole
- **A9 — #11** seed corpus: ≥2 contributors × ≥3 sessions, ≥1 external. *Do not start before the
  path (#10) is live — it fails loudly otherwise.*

### Terminal
- **C1 — #15** launch post. Documents a working v0 with both tiers populated; names the
  commercialization stance and the Tier-2 trust asymmetry; fires the Anthropic follow-up.

### Parked (not on the v0 path)
- **B3 — #14** analytic-stats tier (v0.5). Activate when B1 ships *and* a concrete analytic use
  case exists; every value-bearing field gets sanitizer-grade leak review.

## Blocked-on-Fred decisions

- License wording (#5) and attestation language (#9) — legal judgment; dev must not invent text.
- (Confirmed 2026-06-11: repo name `claude-code-data-collective`, public; Anthropic follow-up at
  launch drafting; `ccdc` label in use.)
