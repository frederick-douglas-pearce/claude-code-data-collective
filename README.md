# Claude Code Data Collective (CCDC)

A small, curated, publicly hosted corpus of **sanitized Claude Code session data** —
contributed by multiple people, gated by maintainer review plus a mechanical CI check, and
licensed for reuse.

CCDC exists to break the single-corpus ceiling. Nearly every credible Claude Code analytics
or research result to date has been built on its author's *private* session sample, which
neither scales, generalizes, nor can be independently verified. CCDC turns "share your
sanitized sessions" into a shared asset that tool builders and researchers can develop
against, validate against, and compare against.

> **Status — v0 scaffolding.** The repository skeleton and the locked
> [file layout](LAYOUT.md) exist. The governance doc, license, contributor attestation, CI
> re-scan gate, and seed corpus are still being finalized, so the corpus is **not yet open
> for contributions** — see [Contributing](#contributing).

## Governance model

- **Curated / benevolent-gatekeeper.** Every contribution passes a maintainer review gate
  plus a mechanical CI check before it merges. CCDC is *not* a federated or open-write
  corpus — at this data sensitivity, an enforced pre-merge gate is structurally necessary.
- **Host: GitHub, for v0.** A pull request *is* the curation queue, and the
  hook/validator machinery from the upstream project applies directly. A **Hugging Face
  Datasets mirror is deferred to v1** and is explicitly out of scope for v0; the
  [file layout](LAYOUT.md) is structured so that mirror is a later *additive* step rather
  than a migration.

## Two contribution tiers

| Tier | What you contribute | Trust mechanism | Lives under |
|------|---------------------|-----------------|-------------|
| **Tier 1 — Full sanitized JSONL** _(preferred)_ | A complete session transcript scrubbed by `ccs-sanitize`, with its `.scrubbed` sidecar | **Independent CI re-scan** — CI re-derives the secret scan from your file and never trusts your sidecar | [`corpus/`](corpus/) |
| **Tier 2 — Structural-stats profile** | A content-free structural profile of your sessions from `scan.py --json` (key/type taxonomy, counts, sizes — no prompts, no paths, no UUIDs) | **Version-attested, not re-scanned** — a structural profile cannot be re-derived without the withheld raw input, so it is attested by tool + version | [`structural/`](structural/) |

**Full sessions are the preferred contribution.** Only they can develop or validate a
parser — the primary downstream use case (for example the sibling projects
[AgentFluent](https://github.com/frederick-douglas-pearce/agentfluent) and
[CodeFluent](https://github.com/frederick-douglas-pearce/codefluent)). The structural tier
is the zero-leak, low-friction on-ramp; it complements full sessions, it does not substitute
for them.

The two tiers are version-attested vs. independently re-scanned, which is a **real
difference in verification strength**. Consumers can tell which is which from the path
(`corpus/` vs. `structural/`) and from the manifest.

See **[LAYOUT.md](LAYOUT.md)** for the exact per-contribution path conventions and where the
manifest lives, and **[structural/README.md](structural/README.md)** for the Tier 2
contribution artifact format and tier policy.

## Built on the sanitizer + format reference

CCDC is the downstream of the
[`claude-code-sessions`](https://github.com/frederick-douglas-pearce/claude-code-sessions)
project, which provides the two tools every contribution is built on and the authoritative
description of the data this corpus contains:

- **Sanitizer** — [`ccs-sanitize`](https://github.com/frederick-douglas-pearce/claude-code-sessions/tree/main/tooling/sanitizer)
  scrubs raw session JSONL for safe publication (Tier 1).
- **Structural scanner** — [`scan.py`](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/main/tooling/format-scan/scan.py)
  emits the content-free structural profile (Tier 2).
- **Format reference** — the [`reference/`](https://github.com/frederick-douglas-pearce/claude-code-sessions/tree/main/reference)
  docs are the authoritative description of the Claude Code JSONL session format.

## Contributing

**Not yet open.** The end-to-end contribution path, governance doc, license, contributor
attestation, and the CI re-scan gate are being finalized. Once live, contributing will mean:
sanitize (Tier 1) or scan (Tier 2) your sessions locally, open a pull request adding them
under the conventions in [LAYOUT.md](LAYOUT.md), and pass maintainer review plus the CI
gate. Contributors are expected to retain their original inputs so a contribution can be
re-sanitized if the sanitizer's rules improve.

## License

To be published before the corpus opens for contributions. The intended direction — not yet
final — is to permit commercial reuse while explicitly disclaiming the training of competing
AI models, keeping downstream consumers aligned with
[Anthropic's Commercial Terms](https://www.anthropic.com/legal/commercial-terms). Until a
`LICENSE` lands, no usage terms are granted.
