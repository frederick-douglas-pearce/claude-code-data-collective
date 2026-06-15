# Security & private leak reporting

CCDC is a corpus derived from **real Claude Code sessions**. Despite sanitization and an
independent CI re-scan, a secret, credential, or piece of PII can in principle survive in a
committed file. Reporting one is welcome and is triaged ahead of everything else.

This document is about **how to reach us privately**. What happens after a report — triage,
service levels, and the tombstone / history-rewrite mechanics — lives in
[`REMOVAL.md`](REMOVAL.md) and [`GOVERNANCE.md`](GOVERNANCE.md#removal--leak-response).

## How to report

There are two channels. Pick by whether the report can be described safely in public.

- **Private — GitHub Private Vulnerability Reporting (preferred for anything sensitive).**
  Use the **"Report a vulnerability"** button on the repository's
  [**Security tab**](https://github.com/frederick-douglas-pearce/claude-code-data-collective/security/advisories/new).
  This opens a private advisory thread visible only to you and the maintainers — nothing is
  public until we publish it. Use this whenever the *location itself* is identifying, when you
  are unsure how to describe the issue without exposing the value, or when in any doubt.

- **Public — leak / removal issue.** For reports that can be described safely without
  reproducing the sensitive value, the public
  [leak / removal issue template](.github/ISSUE_TEMPLATE/leak_or_removal.yml) is fine, and is the
  right channel for a routine **contributor removal request** for your own data.

If you can't use either (no GitHub account and the matter is sensitive), open a public issue
containing **only** the location and *kind* — withhold every specific — and ask us to follow up
privately.

## What a report should contain

The same discipline applies on both channels — **even the private one**. A private advisory is
not public, but it still becomes a durable record, so keep the raw value out of it:

- **Do include:** the contribution handle — `input_sha256` (Tier 1) or `scan_id` (Tier 2) — and/or
  the file path; the *kind* of data (which credential type, or what category of PII); and your
  relationship to the data.
- **Do NOT include:** the secret or PII value itself. Point to *where* it is and *describe* it;
  never paste it.

## If a live credential leaked

**Rotate it now.** Removing it from CCDC does **not** rotate it, and CCDC cannot rotate it for
you. Treat rotation as your emergency first step, then report so we can remove the copy here.

## Scope

This file is the reporting channel for **data in the corpus** (`corpus/`, `structural/`,
`manifest.jsonl`). Vulnerabilities in the *tooling* — the sanitizer and the structural scanner —
belong upstream in
[`claude-code-sessions`](https://github.com/frederick-douglas-pearce/claude-code-sessions); report
those there. When unsure, report here and we will route it.
