# Tier 2 — structural-stats profile

This directory holds **Tier 2** contributions: content-free *structural profiles* of a
Claude Code projects root, produced by the upstream
[`scan.py`](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/main/tooling/format-scan/scan.py)
scanner. A structural profile records the **shape** of your session data — which envelope
keys, content-block types, subdirectories, and Claude Code versions appear, and how often —
**never the content**: no prompt text, no tool inputs or results, no file paths, no UUIDs.

This page documents the Tier 2 contribution artifact, its scope, and its policy. For the
**cross-tier comparison** and how Tier 2 relates to Tier 1, see the
[repository README](../README.md#two-contribution-tiers). For the **path conventions** your
contribution must follow (`structural/<contributor_id>/<scan_id>/scan.json`), see
[LAYOUT.md](../LAYOUT.md#tier-2--structural).

> **Full sessions remain the preferred contribution.** Only Tier 1 full sanitized JSONL can
> develop or validate a parser — the primary downstream use case. Tier 2 is the zero-leak,
> low-friction on-ramp for contributors who can share *shape, not content* (for example under
> an employer policy that forbids sharing transcripts). It **complements** the full tier for
> format-coverage and aggregate research; it does not substitute for it. See the
> [README](../README.md#two-contribution-tiers) for the full framing.

## Producing your `scan.json`

The artifact is the JSON output of `scan.py --json` run over your Claude Code projects root:

```bash
# from a checkout of claude-code-sessions
python3 tooling/format-scan/scan.py --json > scan.json
```

`scan.py` defaults to `~/.claude/projects/` (honoring `$CLAUDE_CONFIG_DIR` like Claude Code
itself). It emits with `sort_keys=True`, so the output is deterministic — the same corpus
produces byte-identical JSON, which is what makes the `<scan_id>` content-address in
[LAYOUT.md](../LAYOUT.md#tier-2--structural) stable. Do **not** pass `--baseline` for a
contribution: that adds a `baseline_diff` keyed to *your* local reference checkout, which is
noise to consumers (see the field table). Usage detail lives in the upstream
[format-scan README](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/main/tooling/format-scan/README.md).

## Artifact format — `scan.json`

> **`scan.py` is the authoritative definition of this artifact, not this table.** The
> scanner's [SECURITY CONTRACT docstring and `EMITTABLE_VALUE_FIELDS` whitelist](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/32b2d77/tooling/format-scan/scan.py)
> define exactly what may and may not appear in the output. The table below orients
> contributors to what a `scan.json` *contains*; if it ever disagrees with the scanner,
> the scanner wins. Verified against `scan.py` as of 2026-06-11
> (`claude-code-sessions` @ `32b2d77`); `scan.py` is an active format-watch tool, so its
> output may grow new keys over time.

Every top-level key holds either a **count map** (a key name or public taxonomy enum →
how many times it was observed) or a small **summary object**. No value in the file is user
content.

| Top-level key | Type | What it records |
|---|---|---|
| `summary` | object | Scan totals: `files_scanned`, `lines_scanned`, `parse_errors`, `session_dirs_with_subdirectories`. Counts only. |
| `top_level_types` | map | Each top-level envelope `type` enum (`user`, `assistant`, `system`, …) → number of lines. |
| `top_level_keys` | map | Each top-level envelope key **name** (`uuid`, `parentUuid`, `message`, …) → number of lines it appears on. |
| `keys_by_type` | map of maps | Per top-level `type`, the envelope key **names** → counts. (Which keys ride with which record type.) |
| `content_block_types` | map | Each message content-block `type` (`text`, `tool_use`, `tool_result`, `thinking`) → count. |
| `tool_result_line_keys` | map | Top-level key **names** seen specifically on user lines that carry a `tool_result` → counts. |
| `session_subdirs` | map | Each session subdirectory **name** (`subagents`, `tool-results`) → number of sessions containing it. |
| `tool_results` | object | Shape of the `tool-results/` externalization files: `extensions` (file extension → count), `name_prefixes` (the tool-kind label before the first `_`/`.`, e.g. `toolu` — never the full filename), `size_bytes` (`count`/`min`/`median`/`max`). |
| `meta_json_keys` | object | Shape of the per-subagent `meta.json` manifests: `files` (count), `parse_errors`, `keys` (key **name** → count), `key_types` (key name → {JSON-type → count}). The values behind `description`/`worktreePath` are **never** read — only their key names and value JSON-types. |
| `versions` | map | Each Claude Code `version` string → number of lines. An open, ever-growing set. |
| `baseline_diff` | null \| object | `null` for a normal contribution. Non-null only if `scan.py --baseline` was passed; then it lists `new_*`/`removed_*` taxonomy items relative to a local reference checkout. Omit it (leave null) when contributing. |

A representative `scan.json` (from a small synthetic two-session tree, abridged):

```json
{
  "summary": {
    "files_scanned": 3,
    "lines_scanned": 7,
    "parse_errors": 0,
    "session_dirs_with_subdirectories": 1
  },
  "top_level_types": {
    "user": 3,
    "assistant": 3,
    "system": 1
  },
  "content_block_types": {
    "text": 2,
    "thinking": 1,
    "tool_result": 1,
    "tool_use": 1
  },
  "session_subdirs": {
    "subagents": 1,
    "tool-results": 1
  },
  "meta_json_keys": {
    "files": 1,
    "parse_errors": 0,
    "keys": {
      "agentType": 1,
      "description": 1,
      "toolUseId": 1,
      "worktreePath": 1
    },
    "key_types": {
      "description": {
        "str": 1
      },
      "worktreePath": {
        "str": 1
      }
    }
  },
  "versions": {
    "2.1.150": 5,
    "2.1.155": 2
  },
  "baseline_diff": null
}
```

Note the `meta_json_keys` block: it records that a `description` and a `worktreePath` key
exist and hold strings — never *what* those strings are. That is the no-values discipline the
whole tier rests on.

## Scope — structural-only for v0

This tier is **structural-only**. It emits format *shape*: the key/type taxonomy, counts,
sizes, and directory names above. It deliberately emits **no analytic or value-bearing
statistics** — no retry rates, no token/turn distributions, no tool-call frequencies, no
"top commands" or "most-used MCP servers."

An **analytic-stats tier is a separate, later (v0.5) deliverable**, tracked in
[claude-code-sessions#119](https://github.com/frederick-douglas-pearce/claude-code-sessions/issues/119).
Analytic stats are under constant pressure to emit value-bearing fields that can re-identify
or leak content — especially for a single-session profile from a *named* open-source
project. The "safe by construction" property belongs to the current whitelist
(`EMITTABLE_VALUE_FIELDS = {type, version}`), **not** to "stats" generically: every
value-bearing field added there must earn the same sanitizer-grade adversarial leak review as
a sanitizer rule. `scan.py`'s safety record does not transfer to a tool that hasn't earned
it. Until #119 lands with that review, this tier stays structural-only.

## No PII-takedown obligations attach to this tier

Tier 1 carries a PII-takedown obligation because a sanitized transcript can still leak
proprietary content over time; that tier keys every contribution on the original input's
`input_sha256` **precisely so** a removal request can find and excise it.

**Tier 2 attaches no such obligation.** A structural profile is content-free *by
construction*: the `EMITTABLE_VALUE_FIELDS` whitelist and the
[SECURITY CONTRACT](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/32b2d77/tooling/format-scan/scan.py)
guarantee `scan.json` contains only key names, public taxonomy enums, value JSON-types,
counts, sizes, file extensions, and directory names. There is no prompt text, no path, and no
identifier in the artifact — so there is **nothing to take down**. This is why the tier can
ship ahead of the full-JSONL governance long-pole (license, attestation, removal runbook):
the dominant liability of the corpus simply does not arise here.

The trade-off is a **weaker verification gate**, accepted deliberately. A structural profile
**cannot be independently re-scanned** by CI, because re-derivation would need the raw input
the contributor is explicitly withholding. So Tier 2 rows are **version-attested**
(`scan_version` + `claude_code_version`), not re-scanned like Tier 1. That is a genuine
downgrade from Tier 1's independent re-scan, and it is acceptable here only *because* the
output is zero-leak regardless of trust. Consumers can tell verified rows from attested ones
by the path (`corpus/` vs. `structural/`) and the manifest. The attestation mechanics are
tracked in
[claude-code-sessions#118](https://github.com/frederick-douglas-pearce/claude-code-sessions/issues/118).
