# Contributing to CCDC

This is the end-to-end walkthrough for contributing Claude Code session data to the
**Claude Code Data Collective**. It is meant to be runnable start to finish: sanitize (or
scan) your sessions locally, place the files per the locked layout, affirm the attestation,
open a pull request, and pass the CI gate.

Read the [README](README.md) first for *what* CCDC is and the two-tier model, and
[GOVERNANCE.md](GOVERNANCE.md) for the curation model and your rights. This page is the
*how*.

> **Status — v0.** The documented path, the contributor attestation, and the independent CI
> re-scan gate are all live. The corpus formally opens for external contributions with the
> seed corpus and launch (see [README](README.md#contributing)); until then this guide is the
> authoritative path and is exercised by the maintainer's own seed contributions.

## The two tiers, in one line

| Tier | You contribute | Lives under | Preferred? |
|---|---|---|---|
| **Tier 1 — full sanitized session** | a `ccs-sanitize`d `session.jsonl` + its `.scrubbed` sidecar | [`corpus/`](corpus/) | **Yes — full sessions are the preferred contribution.** |
| **Tier 2 — structural profile** | a content-free `scan.py --json` `scan.json` | [`structural/`](structural/) | The zero-leak, low-friction on-ramp. |

Only Tier 1 can develop or validate a parser — the primary downstream use. Tier 2
complements it; it does not substitute for it. The full cross-tier comparison and the
"full preferred" stance live in the [README](README.md#two-contribution-tiers). Pick the
tier you can share; if you can share full sessions, **please do**.

## Before you start

You need:

1. **A GitHub account** — a pull request *is* the curation queue.
2. **A clone of this repo** (fork it, then clone your fork) — this is where your contribution
   files land and where you run the local checks.
3. **The upstream tools** from
   [`claude-code-sessions`](https://github.com/frederick-douglas-pearce/claude-code-sessions),
   which produce every contribution:
   - [`ccs-sanitize`](https://github.com/frederick-douglas-pearce/claude-code-sessions/tree/main/tooling/sanitizer)
     for Tier 1 — see its README for install (`uv pip install -e ".[dev]"`).
   - [`scan.py`](https://github.com/frederick-douglas-pearce/claude-code-sessions/blob/main/tooling/format-scan/scan.py)
     for Tier 2 — runs with stock Python 3.
4. **Your retained originals.** You affirm you keep your pre-sanitization input. For **Tier 1**
   that pins a discrete original so the contribution can be re-sanitized if the sanitizer's
   rules improve; for **Tier 2** there is no discrete original, so the affirmation is primarily
   that the profile came from **real, authentic session data** plus best-effort retention
   ([ATTESTATION.md §C](ATTESTATION.md#c-you-retain-the-original)). Don't delete your raw
   sessions after contributing.

**Ground rules, non-negotiable** (full security posture in [CLAUDE.md](CLAUDE.md) and
[GOVERNANCE.md](GOVERNANCE.md#the-review-gate)):

- **No raw session JSONL is ever committed.** Only `ccs-sanitize` output (Tier 1) or
  `scan.py --json` output (Tier 2). Your raw transcripts in `~/.claude/projects/` stay on
  your machine.
- **No secrets** in any committed file or in commit history.
- **You read your own sanitized transcript before submitting.** The gate re-runs the
  sanitizer's residual secret scan, but it does **not** catch arbitrary PII (names, emails,
  internal identifiers) or novel-format secrets — that residual risk is allocated to you by
  [ATTESTATION.md §B4](ATTESTATION.md#b4-third-party-content-and-pii).

## Your `contributor_id`

Your `contributor_id` is your **GitHub username, lowercased**. It is the first path segment
of every contribution and the `contributor_id` field of every `contribution.json`; CI binds
the two together (they must match) and the manifest indexes contributions under it.

It must match the locked format `^[a-z0-9][a-z0-9-]{0,38}$` — every GitHub username already
does once lowercased, so for `Ada-Lovelace` your id is `ada-lovelace`. Use it verbatim
everywhere below (the examples write it as `$ID`).

## What you affirm

Every contribution carries the [contributor attestation](ATTESTATION.md) — the human
backstop for what the gate structurally cannot catch (arbitrary PII, employer-owned content,
novel secrets). You make it through three retained acts, all of which the steps below produce:

1. **Your `contribution.json`** — the machine-readable affirmation
   (`license: "CCDC-1.0"`, `right_to_contribute: true`, `original_retained: true`).
2. **A signed-off commit** — `git commit -s`, tying the affirmation to your git identity.
3. **The attestation block** in the [pull-request template](.github/PULL_REQUEST_TEMPLATE.md).

Read [ATTESTATION.md](ATTESTATION.md) in full before you set those booleans — in particular
[§B3 employer/confidentiality](ATTESTATION.md#b3-employer--confidentiality) and
[§B7 public-and-permanent](ATTESTATION.md#b7-public-and-permanent-acknowledgment). They are a
gate condition, not a formality.

---

## Tier 1 — contribute a full sanitized session

### 1. Sanitize the raw session

From your `claude-code-sessions` checkout (with `ccs-sanitize` installed), run the sanitizer
over one raw session file. **Never** open the raw file by hand or commit it — only the
sanitizer's output leaves your machine.

```bash
ccs-sanitize ~/.claude/projects/<project-dir>/<session-uuid>.jsonl -o session.jsonl
```

This writes two files: `session.jsonl` (the sanitized transcript) and
`session.jsonl.scrubbed` (the audit **sidecar**). Both are required; CI rejects a
`session.jsonl` that arrives without its sidecar.

> **Read it.** Open the resulting `session.jsonl` and skim it for residual PII or secrets the
> scanner cannot know about (internal hostnames, project codenames, a colleague's name). If
> you find any, extend your *local* scrub config and re-run — never edit `session.jsonl` by
> hand (that breaks the re-scan) and never touch the CI config
> ([ATTESTATION.md §B5](ATTESTATION.md#b5-org-specific-scrubbing-is-your-responsibility)).

### 2. Find your `input_sha256`

The directory is keyed on the SHA-256 of the *original* input — the sidecar records it. It's
a YAML file:

```bash
grep input_sha256 session.jsonl.scrubbed
# input_sha256: 9f2c4e1a7b3d…   ← the 64-hex value is your <input_sha256>
```

That hash is the **only handle for retroactive PII removal**, which is why it keys the
directory ([LAYOUT.md](LAYOUT.md#tier-1--corpus)).

### 3. Place the files

In your clone of **this** repo:

```bash
ID=<your-github-username-lowercased>
SHA=<input_sha256 from the sidecar>
mkdir -p corpus/$ID/$SHA
mv session.jsonl session.jsonl.scrubbed corpus/$ID/$SHA/
```

The canonical filename is always `session.jsonl` — the original UUID filename is not used in
the path (the sidecar records it if needed).

### 4. Write `contribution.json`

Create `corpus/$ID/$SHA/contribution.json`. It is **thin** — identity, license, attestation,
nothing more — and identical in shape for both tiers
([SCHEMA.md](SCHEMA.md#contributionjson)):

```json
{
  "schema_version": "1",
  "contributor_id": "your-github-username-lowercased",
  "license": "CCDC-1.0",
  "attestation": {
    "right_to_contribute": true,
    "original_retained": true
  }
}
```

Those exact four keys, no more (the schema forbids extras). `contributor_id` must equal your
`$ID` path segment. You declare **no** hashes, versions, tiers, or dates — anything CI can
derive or you could get wrong is not yours to assert ([SCHEMA.md](SCHEMA.md#design-thin-declaration-ci-derived-provenance)).

### 5. Adding more than one session

Repeat steps 1–4 for each session — one `corpus/$ID/<input_sha256>/` directory per session,
each with its own `contribution.json`. A single PR can carry several sessions; the seed
corpus targets multiple sessions per contributor.

### 6. Validate locally, then open the PR

→ continue at [Validate and open your PR](#validate-and-open-your-pr).

---

## Tier 2 — contribute a structural profile

A structural profile records the *shape* of your sessions — which keys, block types, and
versions appear, and how often — and **never** their content. It is safe by construction, so
it carries no PII-takedown obligation ([structural/README.md](structural/README.md)).

### 1. Produce `scan.json`

From your `claude-code-sessions` checkout, scan your projects root:

```bash
python3 tooling/format-scan/scan.py --json > scan.json
```

`scan.py` defaults to `~/.claude/projects/` and emits with sorted keys, so the output is
deterministic. **Do not** pass `--baseline` for a contribution — it adds local-checkout noise
([structural/README.md](structural/README.md#producing-your-scanjson)). Commit `scan.json`
**byte-for-byte** as emitted; do not reformat it (the path is content-addressed on its bytes).

### 2. Compute your `scan_id`

The directory is the SHA-256 of the `scan.json` bytes:

```bash
sha256sum scan.json
# 3a5e7f9d2b4c…  scan.json   ← the 64-hex digest is your <scan_id>
```

### 3. Place the files

```bash
ID=<your-github-username-lowercased>
SCAN_ID=<sha256 of scan.json>
mkdir -p structural/$ID/$SCAN_ID
mv scan.json structural/$ID/$SCAN_ID/
```

### 4. Write `contribution.json`

Identical to Tier 1 — create `structural/$ID/$SCAN_ID/contribution.json` with the same four
keys shown [above](#4-write-contributionjson). The tier is decided by the path
(`structural/`), never by a field, so the file is the same for both tiers. One clause means
something tier-specific here: `original_retained` has **no discrete original** to pin for a
structural profile, so for Tier 2 it primarily affirms the profile came from **real, authentic
session data** — the basis for this never-re-scanned tier's trust — plus best-effort retention
([ATTESTATION.md §C2](ATTESTATION.md#c2-tier-2--you-retain-authentic-source-sessions-best-effort),
[structural/README.md](structural/README.md#what-original_retained-means-for-tier-2)).

### 5. Validate locally, then open the PR

→ continue below.

---

## Validate and open your PR

### Run the gate locally

The same validator CI runs is in this repo. Check your contribution before you push:

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r ci/requirements.txt

# validate one or more contribution directories directly:
python3 ci/validate_contribution.py corpus/$ID/$SHA/
python3 ci/validate_contribution.py structural/$ID/$SCAN_ID/
```

A green run means your layout, `contribution.json`, sidecar/​content-address, and (Tier 1)
the independent secret re-scan all pass. (See [ci/README.md](ci/README.md) for what each tier
check does.)

### Commit, signed off

```bash
git checkout -b add-sessions-$ID
git add corpus/$ID/ structural/$ID/   # whichever you added
git commit -s -m "feat(corpus): add sanitized session(s) for $ID"
```

The `-s` is required — it adds the `Signed-off-by` trailer that ties your attestation to your
git identity ([ATTESTATION.md](ATTESTATION.md#how-you-make-this-attestation)). Use
`feat(corpus):` for Tier 1 and `feat(structural):` for Tier 2
([commit conventions](CLAUDE.md#commit-conventions)).

### Open the pull request

Push your branch and open a PR against `main`. Fill in **every section** of the
[PR template](.github/PULL_REQUEST_TEMPLATE.md) — especially the **Contributor attestation**
and **Security review** blocks, which cannot be skipped for a contribution PR. Tier 1
contributions are squash-merged like any other change.

## What happens next

1. **The CI gate runs** ([`.github/workflows/contribution-gate.yml`](.github/workflows/contribution-gate.yml)).
   For Tier 1 it **re-derives the secret scan from your `session.jsonl` and never trusts your
   sidecar**; for Tier 2 it confirms the profile is content-addressed and version-attested. It
   routes by path, so the right job runs by construction. The gate is the load-bearing trust
   mechanism — see [ci/README.md](ci/README.md).
2. **A maintainer reviews** the diff for the residual risks the gate cannot catch (PII,
   employer content, right-to-share), per the [review gate](GOVERNANCE.md#the-review-gate).
3. **On merge**, your contribution is indexed in the CI-generated
   [`manifest.jsonl`](manifest.jsonl) — one row, derived from your artifacts and the merge
   commit. You never hand-write a manifest row; it is generated, not contributor-asserted
   ([SCHEMA.md](SCHEMA.md#manifestjsonl-row)). *(Row generation is the one remaining piece of
   automation landing after this guide; until it ships, the maintainer adds rows at merge.)*

Once merged, the contribution is **public and effectively permanent** — removal is
prospective and cannot retract forks or mirrors
([ATTESTATION.md §B7](ATTESTATION.md#b7-public-and-permanent-acknowledgment)). Contribute only
data you are willing to have permanently public.

## Updating or removing a contribution

- **Re-sanitize on a sanitizer bump.** When the pinned sanitizer version is raised, re-run
  `ccs-sanitize` over your retained original and open a new PR
  ([GOVERNANCE.md](GOVERNANCE.md#sanitizer-versioning--coverage-updates)).
- **Removal / leak reports.** To remove your own data, or to report a leak in someone's
  contribution, follow the [removal path](GOVERNANCE.md#removal--leak-response) — open a
  [removal/leak issue](.github/ISSUE_TEMPLATE/leak_or_removal.yml). The mechanics and service
  levels are in [REMOVAL.md](REMOVAL.md).

## See also

- [README.md](README.md) — what CCDC is, the two-tier model, the license.
- [LAYOUT.md](LAYOUT.md) — the locked per-contribution paths and trust mechanics.
- [SCHEMA.md](SCHEMA.md) — the `contribution.json` and `manifest.jsonl` field schemas.
- [ATTESTATION.md](ATTESTATION.md) — what you affirm, in full.
- [GOVERNANCE.md](GOVERNANCE.md) — curation model, review gate, removal SLA.
- [ci/README.md](ci/README.md) — how the contribution gate works.
- [structural/README.md](structural/README.md) — the Tier 2 artifact format and policy.
</content>
</invoke>
