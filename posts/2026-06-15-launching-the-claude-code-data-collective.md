---
layout: post
title: "Launching the Claude Code Data Collective"
date: 2026-06-15 00:00:00-0800
description: "A public, curated corpus of sanitized Claude Code session data — and an invitation to help build it. Where it came from, what a shared corpus makes possible, and how to contribute."
categories: ["announcement"]
tags: ["claude-code", "open-data", "corpus", "sessions", "research"]
og_image: https://frederick-douglas-pearce.github.io/assets/img/launching-the-claude-code-data-collective-og.png
og_card_source: social/images/2026-06-15-linkedin-launching-the-claude-code-data-collective/og-card.png
featured: true
claude_code_version_verified: v2.1.150
---

For the last couple of months I've been writing a series that takes Claude Code apart from the inside — what's actually in a session file, how a single tool call flows through it, what a subagent leaves behind. To write any of it honestly, I had to show real session data. And real session data is a problem: a Claude Code session file is a running log of your prompts, your file paths, your code, your command output, and every so often a secret that scrolled past. You can't just post one.

So before the writing could happen, two small tools had to exist. [`ccs-sanitize`](https://github.com/frederick-douglas-pearce/claude-code-sessions/tree/main/tooling/sanitizer) scrubs a full transcript clean enough to publish. [`scan.py`](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/main/tooling/format-scan/scan.py) does something narrower and, it turns out, more interesting: it reports the _shape_ of a session — which keys appear, which types, which block kinds, which Claude Code versions produced them — without emitting a single byte of the content inside.

That second tool came from a specific, recurring headache. The Claude Code session format changes constantly, and a lot of the changes are undocumented — a new key here, a renamed field there, a whole new kind of trace file. If you're building anything that reads these files, drift like that breaks you silently. You need to watch the _structure_ of the data over time — but you can't watch it by opening the files, because they're full of things you can't safely look at. `scan.py` is the way out: it sees the structure and nothing else. (Watching for that drift eventually became a standing routine of its own.)

Here's the part that matters for what comes next: those two tools were built so that _one person could share one person's sessions_, safely. And they work. Which raises an obvious question.

## Why stop at one person's sessions?

Almost everything worth knowing about how Claude Code actually behaves gets more interesting — and more trustworthy — the moment it's drawn from many people's sessions instead of one. Every result I've published about Claude Code, the whole series included, runs on my own private sample. That's a real limit, and it isn't one you fix by being careful; you fix it by having more than one person's data.

A public, safely-sanitized corpus of real sessions is the kind of shared resource a lot of useful things get built on. A few I'd genuinely like to see exist:

- **Tooling that works on real sessions, not toy ones.** Session viewers, log explorers, token and cost dashboards, diff tools — everyone building them today tests against their own logs or hand-mocked data. A shared corpus is a common set of realistic fixtures, including the weird cases only someone else's sessions contain.
- **A public record of how the format evolves.** Sanitized sessions across many Claude Code versions are, together, the documentation the format doesn't have — a way to see how the session schema actually changed, release over release. That's useful to anyone building on top of Claude Code, not just me.
- **Honest, reproducible study of agentic coding.** How do people really drive these tools? Where do agents loop, stall, recover, or misuse a tool? Those questions deserve answers that someone _other_ than the author can check — which is only possible against data that's actually public.
- **Better tools through aggregate analysis.** The error and retry patterns in one session are an anecdote; across hundreds they're a signal that tells tool authors which tool definitions are confusing the model. That's exactly the kind of finding that shouldn't rest on one person's data.
- **A way in for people without a big private sample.** You shouldn't have to work somewhere with mountains of internal usage to do interesting session research. A shared corpus levels that — a student, an indie dev, and a curious contributor all start from the same place.

The tools to do this safely already exist. What's missing is the data — and the data only shows up if people share it.

## What CCDC is

That's the Claude Code Data Collective: a small, curated, public corpus of sanitized Claude Code sessions, built on those same two tools, that anyone can contribute to and anyone can build on.

There are two ways to contribute, depending on how cautious you want to be:

- **A full sanitized session** — the high-value kind, because it's the only thing that lets someone develop or validate a real parser. Run it through `ccs-sanitize`, read it over, open a pull request.
- **A structure-only profile** — if you'd rather share nothing but the shape. `scan.py` emits counts, key names, and types, and by construction never touches your content. It's the zero-risk on-ramp.

Full sessions are what the project really wants; the structural profile is there so that "I'm not comfortable sharing a transcript" still has a yes.

## The honest part

Because this is real session data, the safety story matters, and it's deliberately not "trust me." Every full session is automatically re-scanned for secrets before it can merge — the check re-derives the result itself rather than trusting whatever the contributor attached. The structure-only tier carries nothing but shape to begin with. The full mechanics are written up in the [repo](https://github.com/frederick-douglas-pearce/claude-code-data-collective) for anyone who wants to audit them, and a documented removal path exists from day one: if something slips through, it comes out. Contribute only what you're willing to have public — sanitized, but public.

Two more things, plainly. CCDC does feed some tools I'm building, but the [license](https://github.com/frederick-douglas-pearce/claude-code-data-collective/blob/main/LICENSE) keeps it genuinely open: commercial reuse allowed, attribution required, analysis and tooling explicitly unrestricted — the only real limit is no training of competing models. And it's small right now, mostly my own sessions, so don't read anything in it as representative of Claude Code users at large. It's a seed — which is exactly the stage where another contributor matters most.

## Contributing

If you use Claude Code and have sessions you can share — especially open-source work, where the right-to-share question is easy — I'd genuinely like your data in here. The walkthrough is in [CONTRIBUTING.md](https://github.com/frederick-douglas-pearce/claude-code-data-collective/blob/main/CONTRIBUTING.md): sanitize or scan, read it over, open a PR. It doesn't take much — and early contributors shape what this becomes.

[**github.com/frederick-douglas-pearce/claude-code-data-collective**](https://github.com/frederick-douglas-pearce/claude-code-data-collective)

---

_Drafted with Claude Code. The ideas, the claims, and any errors are mine._
