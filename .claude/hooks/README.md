# `.claude/hooks/` — secrets-protection hooks

These hooks are the **mechanical** half of this repo's security posture (the
narrative half lives in [`CLAUDE.md`](../../CLAUDE.md) → "Security posture").
CCDC handles raw Claude Code session JSONL during contribution prep, and that
data contains prompts, file paths, code, command output, and occasionally
secrets. The corpus only ever holds *sanitized* full sessions (Tier 1) or
*content-free* structural profiles (Tier 2) — so reading a raw session or a
raw secret into the model's context is the thing we most need to prevent.

Ported from the upstream
[`claude-code-sessions`](https://github.com/frederick-douglas-pearce/claude-code-sessions)
project's `.claude/hooks/`, adapted for this repo. They are wired in
[`../settings.json`](../settings.json).

## The two hooks

### `block_secret_reads.py` — PreToolUse (primary defense)

Denies a tool call *before* it executes when the target would leak data into
the session transcript. Three classes of target:

1. **Credential files** — `.env*`, shell rc files (`.bashrc`, `.zshrc`, …),
   SSH private keys (`id_rsa`, `id_ed25519`, …), `.pem`, and named secrets
   files (`credentials.json`, `secrets.yaml`, …). Checked for the file tools
   (`Read`/`Edit`/`Write`/`NotebookEdit`), the search tools (`Grep`/`Glob`),
   and `Bash` commands.
2. **Raw session transcripts** — anything ending in `.jsonl` under
   `~/.claude/projects/`. Checked for `Read`/`Edit`/`NotebookEdit`/`Grep`/`Glob`
   **only — not `Bash`**. The repo's own committed, sanitized
   `corpus/**/session.jsonl` files are not under that root, so they stay
   readable — only *unsanitized* transcripts in the live projects dir are
   blocked.
3. **Live sanitizer config** — `.ccs-sanitize.yaml` (the file that holds the
   literal PII strings to scrub, if a contributor runs the sanitizer here).
   Checked for `Read`/`Edit`/`NotebookEdit`/`Grep`/`Glob`/`Bash`. **`Write` is
   allowed** so `ccs-sanitize --init` and rewrite-from-scratch iteration still
   work — mirrors the raw-session asymmetry. The committed
   `.ccs-sanitize.example.yaml` schema reference is PII-free and stays freely
   readable; the pattern is anchored to the live basename. Full threat model in
   the upstream sanitizer PRD
   [§12b](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/main/.claude/specs/prd-sanitizer.md).

#### Why raw sessions are blocked for file tools but not Bash

The posture is "never read an unsanitized session into context; sanitize it
first, then contribute only the scrubbed result." So the file tools that pull a
transcript's contents into context are blocked. `Bash` is intentionally left
alone so that:

- the sanitizer CLI can read a real session over Bash to produce a scrubbed
  copy (`ccs-sanitize <raw> -o <out>`), and
- `scan.py` can read the projects root to produce a Tier 2 structural profile.

`Write` is also excluded from the raw-session rule — it overwrites rather than
surfacing existing content, so it isn't a read-leak vector.

Fails closed: an unparseable event is denied by default.

### `detect_secrets_in_output.py` — PostToolUse (secondary guard)

Scans `Read`/`Grep`/`Bash` output for known credential patterns (Anthropic,
OpenAI, GitHub PAT, AWS, GCP, PEM) and emits a `block` decision so Claude won't
echo or summarize a leaked value. **Caveat:** PostToolUse fires *after* the
tool runs, so the value is already on disk in the session JSONL — this hook
limits propagation, it does not prevent the on-disk leak. That's why
`block_secret_reads.py` (which runs *before*) is the primary defense.

## Relationship to the upstream tooling

These hooks guard the **input** side: they stop Claude from reading secrets or
raw sessions into context during day-to-day work in this repo. The upstream
[`ccs-sanitize`](https://github.com/frederick-douglas-pearce/claude-code-sessions/tree/main/tooling/sanitizer)
guards the **output** side — it scrubs a raw session into a publishable Tier 1
contribution — and
[`scan.py`](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/main/tooling/format-scan/scan.py)
produces the content-free Tier 2 profile. The eventual CI re-scan merge gate
(see the corpus issues) is the third layer: it re-derives the secret scan from
every submitted `corpus/` file and never trusts the contributor's sidecar.

## Tests

```bash
python3 .claude/hooks/tests/test_hooks.py
```

`tests/fixtures/` holds synthetic PreToolUse/PostToolUse events — both
known-bad (must block/deny) and known-good (must pass). The known-bad secret
fixtures use fake, clearly-synthetic keys, never real ones.
