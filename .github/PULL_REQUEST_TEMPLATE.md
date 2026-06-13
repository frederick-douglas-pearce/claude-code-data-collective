<!--
This corpus carries data derived from real Claude Code sessions. Every PR —
contribution or infrastructure — must clear the Security review below.
Replicate every section; squash-merge to main.
-->

## Summary

<!-- 1-3 bullets: what this PR does and why. Reference the issue (e.g. Closes #12). -->

## Type of change

<!-- Check one. -->

- [ ] **Tier 1 contribution** — sanitized full session(s) under `corpus/`
- [ ] **Tier 2 contribution** — structural profile(s) (`scan.json`) under `structural/`
- [ ] **Infrastructure / docs** — hooks, CI, `docs/`, `README`/`LAYOUT`, governance, license

## Test plan

<!-- Check what applies; not every row applies to every PR. -->

- [ ] Hook tests pass: `python3 .claude/hooks/tests/test_hooks.py` (for `.claude/hooks/` changes)
- [ ] Layout conforms to [`LAYOUT.md`](../LAYOUT.md) (contribution path, filenames, sidecar present)
- [ ] CI re-scan / attestation check is green (once the gate exists)

## Contributor attestation

<!--
Required for Tier 1 / Tier 2 contribution PRs; mark N/A for infrastructure/docs PRs.
This is the human backstop for what the CI gate cannot catch. The full text is ATTESTATION.md;
your committed contribution.json is the retained, per-contribution record of this affirmation.
-->

- [ ] **N/A** — this is an infrastructure / docs PR, not a contribution.
- [ ] I have read [`ATTESTATION.md`](../ATTESTATION.md) and **affirm it in full** for this contribution.
- [ ] My `contribution.json` sets `license: "CCDC-1.0"`, `attestation.right_to_contribute: true`, and `attestation.original_retained: true` — the retained record of that affirmation.

## Security review

<!-- This corpus can carry secrets and PII. Confirm all that apply. -->

- [ ] **No raw session JSONL** — Tier 1 files are `ccs-sanitize` output with their `.scrubbed` sidecar; Tier 2 files are `scan.py --json` output (content-free by construction). No file came straight from `~/.claude/projects/`.
- [ ] **No secrets** in any added file, example, or commit history (Anthropic/OpenAI/GitHub/AWS/GCP keys, PEM blocks, tokens).
- [ ] **Right to share** — for a contribution: I have the right to share this data under the corpus license and any applicable employer policy (full attestation: [`ATTESTATION.md`](../ATTESTATION.md)).
- [ ] **I read my own sanitized transcript** for residual PII/secrets the gate cannot catch (contribution PRs; see [`ATTESTATION.md`](../ATTESTATION.md) §B4).
- [ ] **Closer read done** if this PR touches `.claude/hooks/`, `.github/workflows/`, or the contribution/ingest path.

## Breaking changes

<!--
Does this change a contract that contributors or downstream consumers depend on?
If yes, describe before/after. Examples:
- The per-contribution layout or manifest schema changed
- The scan.json artifact shape or a sidecar format changed
- A hook's policy or a CI gate's behavior changed
-->
