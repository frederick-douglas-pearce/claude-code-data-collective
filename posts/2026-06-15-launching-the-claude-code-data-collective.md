---
layout: post
title: "Launching the Claude Code Data Collective"
date: 2026-06-15 00:00:00-0800
description: "A small, curated, publicly hosted corpus of sanitized Claude Code session data — multi-contributor, gated by maintainer review and an independent CI re-scan, open for contributions today. Here is what it is, what it isn't, and why I built it."
categories: ["announcement"]
tags: ["claude-code", "open-data", "corpus", "sessions", "research"]
og_image: https://frederick-douglas-pearce.github.io/assets/img/launching-the-claude-code-data-collective-og.png
og_card_source: social/images/2026-06-15-linkedin-launching-the-claude-code-data-collective/og-card.png
featured: true
claude_code_version_verified: v2.1.150
---

A couple of weeks ago I published a post on how often Claude retries a failing tool call. The directional read — tools that act on mutable state, like `Bash` and `Edit`, retry; read-only ones like `Read` almost never do — came from one worked session, with the underlying heuristic sharpened against a corpus of [46 of my own sessions](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/main/posts/2026-06-08-how-often-does-claude-retry-a-tool-call.md). It was a clean enough signal that I wanted it to be checkable by someone other than me.

It isn't. That corpus is private — nobody else can see it, re-run the numbers, or challenge them. I disclosed the limit at the time, called the per-tool expectations "directional ... not statistical findings from a broad sample," and noted that a single session is below threshold for any strong claim. But naming a caveat is not the same as fixing the structural problem behind it: every credible Claude Code analytics result to date — mine included — runs on the author's private session sample. That's a ceiling.

Today I'm opening [the Claude Code Data Collective (CCDC)](https://github.com/frederick-douglas-pearce/claude-code-data-collective) to external contributions. The goal is simple: break that ceiling.

## What CCDC is

CCDC is a small, curated, publicly hosted corpus of **sanitized Claude Code session data** — contributed by multiple people, gated by maintainer review plus a mechanical CI check, and licensed for reuse.

The key word is "sanitized." Claude Code session files contain prompts, file paths, code snippets, command output, and occasionally secrets. They can't be shared raw. The upstream [`claude-code-sessions`](https://github.com/frederick-douglas-pearce/claude-code-sessions) project provides the tooling that makes sharing tractable: [`ccs-sanitize`](https://github.com/frederick-douglas-pearce/claude-code-sessions/tree/main/tooling/sanitizer) for full session transcripts, and [`scan.py`](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/main/tooling/format-scan/scan.py) for content-free structural profiles. CCDC is the downstream — the place where that sanitized output accumulates into a shared, citable, reusable asset.

## Two tiers — and a real difference between them

CCDC accepts two kinds of contribution, and the difference between them is not just cosmetic.

**Tier 1 — Full sanitized JSONL** (`corpus/`): a complete session transcript scrubbed by `ccs-sanitize`, with its `.scrubbed` sidecar. This is the high-value tier. The trust mechanism is an **independent CI re-scan**: when a Tier-1 PR arrives, CI re-derives the secret scan from the submitted `session.jsonl` and fails the PR on any residual. It never trusts the sidecar the contributor provides. That gate is the load-bearing mechanism — maintainer review does not scale to be the primary trust check, and the design does not pretend otherwise.

**Tier 2 — Structural-stats profile** (`structural/`): a content-free profile from `scan.py --json` — key/type taxonomy, counts, sizes, version histograms; no prompt text, no tool inputs or results, no paths, no UUIDs. This is the zero-leak on-ramp. Its trust mechanism is different: **version-attested, not re-scanned**. A structural profile cannot be independently re-derived without the withheld raw input, so CI confirms the attestation fields are present and well-formed but cannot replay the derivation. That is a genuine downgrade in verification strength. It is accepted because Tier-2 output is safe by construction regardless — the scanner's `EMITTABLE_VALUE_FIELDS` whitelist is the zero-leak guarantee — but consumers should know which is which. The path tells you: `corpus/` is re-scanned; `structural/` is attested.

**Full sessions are the preferred contribution.** Only they can develop or validate a parser. Tier 2 complements full sessions; it does not substitute for them. If you can share full sessions, please do.

The full cross-tier comparison and the "full sessions preferred" stance live in [README.md](https://github.com/frederick-douglas-pearce/claude-code-data-collective/blob/main/README.md).

## What's actually in the corpus today

I want to be precise about this, because the honest answer is: not much yet.

The seed corpus is three Tier-1 sanitized sessions and one Tier-2 structural profile, all from a single contributor — me — spanning Claude Code versions in the 2.1.x line. The CI re-scan gate, the sign-off enforcement, the manifest write-back automation, and the full contribution path have all been exercised end-to-end under the live `main` branch-protection ruleset. The machinery works. But the corpus is seed content, not the intended steady state.

The [datasheet](https://github.com/frederick-douglas-pearce/claude-code-data-collective/blob/main/docs/datasheet-ccdc.md) states the generalizability caveat plainly, and I'll state it here too: **results derived from CCDC describe the corpus, not the Claude Code user population.** Even once the corpus grows, it will remain a self-selected, non-probability sample — people who chose to donate sanitized sessions, skewed toward open-source work and permissive employer policies. That is the standard caveat for donated corpora. It belongs in the introduction, not the footnotes.

The [manifest.jsonl](https://github.com/frederick-douglas-pearce/claude-code-data-collective/blob/main/manifest.jsonl) is the live, CI-generated index. Whatever the count is there is more current than anything I write here.

## The commercialization stance

I'm not going to bury this: the primary beneficiaries of CCDC are my own sibling projects, [AgentFluent](https://github.com/frederick-douglas-pearce/agentfluent) and [CodeFluent](https://github.com/frederick-douglas-pearce/codefluent) — parser and diagnostic tooling for Claude Code sessions. Those are commercial projects. CCDC is open-source-derived data feeding commercial tools, and that is expected and disclosed, not a footnote.

The [CCDC Data License, Version 1.0](https://github.com/frederick-douglas-pearce/claude-code-data-collective/blob/main/LICENSE) reflects that balance: it permits commercial reuse of the corpus, requires attribution, and prohibits using the Data to train AI models that compete with Anthropic — keeping downstream consumers aligned with [Anthropic's Commercial Terms](https://www.anthropic.com/legal/commercial-terms). The restriction is pass-through, so it survives re-hosting.

The license expressly does not restrict *Results* — analysis, parsers, schemas, evaluations, research tooling that reads or describes the data. The no-compete restriction reaches only the training of competing AI models. If you want to build tooling on top of CCDC, or publish analysis from it, the license is not in your way.

## The security model (brief version)

Two concerns dominate session-corpus work: secrets and PII. The mechanical answer to secrets is the CI re-scan gate — it re-runs the sanitizer's own residual scan on every Tier-1 submission, and a PR with a red gate cannot merge. The answer to PII is more honest: pattern-based scanning cannot catch names, internal hostnames, project codenames, or custom identifiers. That residual risk is allocated to the contributor's own read-through before submitting, documented in [ATTESTATION.md](https://github.com/frederick-douglas-pearce/claude-code-data-collective/blob/main/ATTESTATION.md) as a condition of contribution — not hidden in the fine print.

A [removal path](https://github.com/frederick-douglas-pearce/claude-code-data-collective/blob/main/REMOVAL.md) has existed from day one: report privately via [GitHub Private Vulnerability Reporting](https://github.com/frederick-douglas-pearce/claude-code-data-collective/blob/main/SECURITY.md) or publicly via the [leak/removal issue template](https://github.com/frederick-douglas-pearce/claude-code-data-collective/blob/main/.github/ISSUE_TEMPLATE/leak_or_removal.yml). SLA: acknowledge within 3 business days, remove within 7 calendar days. Removal is prospective — it stops CCDC distributing the data going forward but cannot retract forks or prior clones. That limitation is stated in the attestation. Contribute only data you are willing to have permanently public.

## How to contribute

The full walkthrough is in [CONTRIBUTING.md](https://github.com/frederick-douglas-pearce/claude-code-data-collective/blob/main/CONTRIBUTING.md). The short version:

1. Install [`ccs-sanitize`](https://github.com/frederick-douglas-pearce/claude-code-sessions/tree/main/tooling/sanitizer) (Tier 1) or [`scan.py`](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/main/tooling/format-scan/scan.py) (Tier 2) from the upstream `claude-code-sessions` repo.
2. Sanitize or scan your sessions locally. Read the output before you submit.
3. Place the files per [LAYOUT.md](https://github.com/frederick-douglas-pearce/claude-code-data-collective/blob/main/LAYOUT.md), write a thin `contribution.json`, and run the local validator.
4. Open a pull request with a signed-off commit. Fill in every section of the PR template — especially the attestation and security-review blocks.
5. CI runs the re-scan gate. A maintainer reviews the residual risks the gate can't catch. On merge, the manifest row is generated automatically.

The corpus formally opens for external contributions today. The seed corpus is in place, the CI gate is enforced as a required status check on `main`, and the contribution path is exercised end-to-end. If you use Claude Code regularly and have sessions you can share — especially if your work is open-source or your employer's policies permit it — I'd like your data in here.

## What I'm actually asking for

The retry-rate read I opened with is exactly the kind of result that should hold up on more than one person's sessions before anyone calls it a pattern. So is the session-format structure I described in the [anatomy post](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/main/posts/2026-05-26-anatomy-of-a-claude-code-session.md), the line-by-line parsing in [Part 2](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/main/posts/2026-06-04-reading-a-claude-code-session-line-by-line.md), and the subagent-trace patterns in [Part 4](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/main/posts/2026-06-11-inside-the-subagent-trace-file.md).

None of them can be independently checked against a corpus built from one contributor's private sessions. That's why CCDC exists — not as the announcement of a solved problem, but as the infrastructure for working toward one.

Let's connect if this resonates.

---

_Drafted with Claude Code (verified against v2.1.150). The ideas, the claims, and any errors are mine._
