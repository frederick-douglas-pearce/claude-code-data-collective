# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

`claude-code-data-collective` (CCDC) is a small, curated, publicly hosted corpus of Claude Code
session data, contributed by multiple people and gated by maintainer review plus a mechanical CI
check. It exists to break the single-corpus ceiling: most Claude Code analytics/research to date has
been built on the author's *private* session sample, which neither scales, generalizes, nor can be
independently verified.

The corpus accepts **two contribution tiers** (full detail in [`README.md`](README.md) and
[`LAYOUT.md`](LAYOUT.md)):

- **Tier 1 — full sanitized JSONL** (`corpus/`): a complete session transcript scrubbed by
  `ccs-sanitize`, with its `.scrubbed` sidecar. The high-value tier — the only one that can develop
  or validate a parser. Trust mechanism: **independent CI re-scan** (never trusts the sidecar).
- **Tier 2 — structural-stats profile** (`structural/`): a content-free `scan.py --json` profile
  (key/type taxonomy, counts, sizes — no prompts, no paths, no UUIDs). The zero-leak on-ramp. Trust
  mechanism: **version-attested, not re-scanned**.

**Full sessions are the visibly preferred tier.** Tier 2 complements it; it does not substitute for
it. Keep that framing in any tier-facing copy.

This repo is **downstream** of [`claude-code-sessions`](https://github.com/frederick-douglas-pearce/claude-code-sessions),
which owns the tooling and format docs every contribution is built on (see "Upstream relationship").

## Security posture — read this first

This corpus is derived from real Claude Code sessions. Session JSONL contains prompts, file paths,
code snippets, command output, and occasionally secrets. The rules are absolute:

- **No raw session JSONL is ever committed.** Only sanitized Tier 1 files (with a `.scrubbed`
  sidecar) or content-free Tier 2 `scan.json` profiles.
- **No secrets** in any committed file, example, or commit history.
- The committed `corpus/**/session.jsonl` files are *already sanitized* — they are safe to read.
  **Raw, unsanitized transcripts live in `~/.claude/projects/` and must never be read into context.**
  If you (Claude Code) are asked to "look at a session," read from `corpus/`, never from
  `~/.claude/projects/`. To prepare a contribution from a raw session, run the upstream
  `ccs-sanitize` (Tier 1) or `scan.py` (Tier 2) over Bash — never open the raw file with Read/Edit.

Mechanical enforcement lives in [`.claude/hooks/`](.claude/hooks/) (see its
[README](.claude/hooks/README.md)):

- `block_secret_reads.py` (PreToolUse) denies tool calls targeting known credential basenames, raw
  session JSONL under `~/.claude/projects/`, and the live sanitizer config (`.ccs-sanitize.yaml`).
  `Bash` is intentionally exempt for the raw-session rule so the sanitize/scan prep flows work.
- `detect_secrets_in_output.py` (PostToolUse) scans tool output for known credential patterns
  (Anthropic/OpenAI/GitHub PAT/AWS/GCP/PEM) and blocks further propagation.

Coverage caveats (runtime discipline is still yours): the PostToolUse scanner is pattern-based for
credentials and does **not** catch arbitrary PII (names, emails, custom identifiers), and Bash
matching is substring-based — variable indirection or globbing can defeat it. The diff-level backstop
(no raw JSONL, no secrets) is yours at commit/review time.

This repo's CI re-scan merge gate ([`ci/validate_contribution.py`](ci/validate_contribution.py),
run by [`.github/workflows/contribution-gate.yml`](.github/workflows/contribution-gate.yml)) re-derives
the secret scan from every submitted `corpus/` file — re-running the upstream sanitizer's *own*
residual scan, never trusting the `.scrubbed` sidecar — and is the load-bearing trust mechanism;
manual review does not scale. It is enforced as a **required status check** on `main` (via the
always-on `gate-summary` aggregator, #39), so a PR with a red or missing gate cannot merge. The PR
gate is validate-only by design: `manifest.jsonl` rows are written *after* merge by a separate
workflow ([`.github/workflows/manifest-generate.yml`](.github/workflows/manifest-generate.yml), #33),
because a row's `contributed_at` is the merge-commit date.

## Conventions

### Contributions

- **Layout is locked** — see [`LAYOUT.md`](LAYOUT.md). Tier 1:
  `corpus/<contributor_id>/<input_sha256>/{session.jsonl, session.jsonl.scrubbed, <metadata>}`.
  Tier 2: `structural/<contributor_id>/<scan_id>/{scan.json, <metadata>}`.
- The two tiers live in **separate top-level trees on purpose**: the CI gate runs a different job per
  tree (re-scan vs. attestation), decided by the path, not by a contributor-controlled field.
- `manifest.jsonl` (repo root) is the **CI-generated index**, one row per contribution — never
  hand-edited in a PR. The field schema is deferred and locked separately before contributor #1.
- Contributors retain their original inputs so a contribution can be re-sanitized if the sanitizer's
  rules improve.

### Docs

- `README.md` owns the cross-tier comparison and the "full sessions preferred" stance.
- `LAYOUT.md` owns the per-contribution paths and trust mechanics.
- `structural/README.md` owns the Tier 2 artifact format and Tier 2 policy.
- `docs/` holds the design rationale: [`docs/prd-ccdc.md`](docs/prd-ccdc.md) (PRD) and
  [`docs/roadmap-ccdc.md`](docs/roadmap-ccdc.md) (sequencing). Field-level `scan.json` semantics are
  authoritative in the upstream `scan.py`; link to it rather than restating it.

## Commit conventions

[Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — new contribution, new tooling/CI capability, new doc section
- `fix:` — corrections to docs, layout, tooling
- `docs:` — README/LAYOUT/CLAUDE.md/`docs/` copy
- `chore:` — CI, scaffolding, dependencies

Scopes: `feat(corpus):` / `feat(structural):` for contributions, `chore(ci):` for `.github/`,
`chore(hooks):` for `.claude/hooks/`, `docs:` for prose.

## Branching & PR workflow

`main` is always publishable. **Every change comes in through a PR** — a pull request *is* the
curation queue, and the security/CI gate runs on it. (Trivial maintainer copy-edits to README/LAYOUT
may go direct to `main`.)

- **Branches:** `feature/<issue#>-short-description` or `fix/<issue#>-short-description`.
- **Squash-merge** to `main`; every PR references its issue.
- Open PRs with the sections in [`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md):
  Summary, Type of change, Test plan, **Security review**, Breaking changes.
- Run the relevant local checks first — `python3 .claude/hooks/tests/test_hooks.py` for hook changes.

### Security gate (every PR)

- **No raw session JSONL** — only sanitized Tier 1 (with `.scrubbed` sidecar) or content-free Tier 2.
- **No secrets** in files, examples, or history.
- **Right to share** for contributions (license + employer policy), per the attestation.
- A documented **"report a leak / removal request"** path exists from day one:
  [`.github/ISSUE_TEMPLATE/leak_or_removal.yml`](.github/ISSUE_TEMPLATE/leak_or_removal.yml).

## Upstream relationship

[`claude-code-sessions`](https://github.com/frederick-douglas-pearce/claude-code-sessions) provides
the tools and format docs this corpus is built on; do not duplicate them here, link to them:

- **Sanitizer** — [`ccs-sanitize`](https://github.com/frederick-douglas-pearce/claude-code-sessions/tree/main/tooling/sanitizer)
  scrubs raw session JSONL for Tier 1.
- **Structural scanner** — [`scan.py`](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/main/tooling/format-scan/scan.py)
  emits the Tier 2 profile; its SECURITY CONTRACT / `EMITTABLE_VALUE_FIELDS` is the zero-leak
  guarantee.
- **Format reference** — [`reference/`](https://github.com/frederick-douglas-pearce/claude-code-sessions/tree/main/reference)
  is the authoritative description of the JSONL session format.

The `.claude/hooks/` here were ported from that repo and adapted (raw-session block keyed on
`~/.claude/projects/`, deny messages and links pointed at CCDC).

## Status

**v0 scaffolding — not yet open for contributions.** In place: the repo skeleton, locked layout, the
Tier 2 tier doc, the design docs, the security hooks, the license, the locked manifest/contribution
schema, the CI re-scan merge gate (#8) now **enforced as a required status check** (#39), manifest-row
generation (#33) writing past branch protection via the manifest-writer App (#35), sign-off
enforcement (#31), the end-to-end contribution path / CONTRIBUTING.md (#10), the governance doc,
contributor attestation, and the removal runbook. The contribution path is now **proven end-to-end
across both tiers**: a Tier 2 profile (#40) and the maintainer's own three Tier 1 sessions (#46) are
merged, with the CI re-scan gate, sign-off enforcement, and the manifest write-back all exercised
under the live `main-protection` ruleset (the write-back commit is authored by the manifest-writer
App, confirming its bypass of the required gate works in production). The remaining long pole before
the corpus opens is the rest of the **seed corpus** (#11): its acceptance criteria require **≥2
contributors × ≥3 sanitized sessions each, with at least one contribution from someone other than the
maintainer** — so #11 stays open pending one *external* contributor (the day-30 external-contribution
gate); that step is recruiting, not code. The private leak-intake channel (#27) is in place: GitHub
Private Vulnerability Reporting is enabled and documented in [`SECURITY.md`](SECURITY.md), with the
public issue template, [`GOVERNANCE.md`](GOVERNANCE.md), and [`REMOVAL.md`](REMOVAL.md) all routing
sensitive reports to it. Remaining pre-launch items, roughly in order: a removal-process dry-run (#28 —
the second trust/safety gate), then the corpus datasheet + sample-limitation disclosure (#25) and the
launch post (#15). Assorted non-blocking follow-ups are tracked too (#13, #24, #14). Work is tracked in
this repo's issues (epic #2).
