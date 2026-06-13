# Removal & leak-response runbook

How CCDC responds to a **leak report** (PII or a secret found in the corpus) or a **removal
request** (a contributor taking down their own data). This is an operational runbook: it is written
to be executed **step by step by someone who is not the original maintainer**, under time pressure,
without having to make the hard calls in the moment. The calls are made here, in advance.

It is the mechanics behind the service levels committed in [GOVERNANCE.md](GOVERNANCE.md#removal--leak-response).
The public intake form is [`.github/ISSUE_TEMPLATE/leak_or_removal.yml`](.github/ISSUE_TEMPLATE/leak_or_removal.yml).

> **Who can run this.** A *tombstone* (the default, §6A) needs **repo write access**. A *history
> rewrite* (the exception, §6B) needs **repo admin** plus contacting GitHub Support. Either way you
> do not need the original maintainer present — that is the point.

---

## 0. Golden rules (read before touching anything)

1. **Never reproduce the secret/PII in a public place.** Not in an issue, PR title, commit message,
   CI log, or this repo's history. Refer to it by `input_sha256` / `scan_id` and *kind* only.
2. **A live credential is the reporter's emergency first.** Removing it from CCDC does not rotate it.
   If the report names a live credential, tell the affected party to **rotate it now**; CCDC cannot.
3. **Removal is prospective and incomplete.** Deleting from the published branch does **not** erase
   data from clones, forks you don't control, or third-party caches/mirrors. Say so honestly; never
   promise erasure you cannot deliver (§9).
4. **Default to the reversible-cost path.** Tombstone first (§6A). Reserve history rewrite (§6B) for
   the narrow case where the data's mere presence *in git history* is itself live harm.

## 1. Intake — where reports arrive

- **Public:** the [leak / removal issue template](.github/ISSUE_TEMPLATE/leak_or_removal.yml)
  (labeled `security`). It instructs reporters not to paste the secret and to point by path /
  `input_sha256` / `scan_id`.
- **Private:** for cases that cannot be described safely in a public issue, a private channel is
  needed so a reporter never has to expose a live secret to open it.
  > 🔧 **Setup gap (maintainer action):** designate a private intake address (e.g. a dedicated
  > security email or GitHub private vulnerability reporting) and link it from the issue template and
  > [GOVERNANCE.md](GOVERNANCE.md#removal--leak-response). Until that exists, the documented fallback
  > is: open a public issue describing only the *location and kind*, withholding all specifics, and
  > the maintainer follows up over a private channel.

A complete report carries: **(a)** the `input_sha256` (Tier 1) or `scan_id` (Tier 2) and/or file
path, **(b)** the *kind* of data (which credential type, or what category of PII), and **(c)** the
reporter's relationship to the data. It must **not** carry the secret/PII itself.

## 2. Verify the requester (removal requests only)

A **leak report** can come from anyone — no identity check; a planted secret is a problem whoever
finds it. A **removal request for contributed data** must come from the contributor who submitted it.
Use a lightweight proof, BigCode-style — the requester demonstrates control of the contributor
identity tied to the contribution (the GitHub account that opened the original contribution PR, or
the contact on record for that `contributor_id`). The `input_sha256` is the handle that ties the
request to a specific contribution.

## 3. Triage & classify (acknowledge within the SLA)

**Acknowledge within 3 business days** (GOVERNANCE SLA). Classify the report — this picks the method
and the clock:

| Class | Example | Method | Target |
|-------|---------|--------|--------|
| **Live credential** | An un-rotated API key / token still valid | Urgent: tell reporter to rotate **now**, then **§6A immediately**, escalate to **§6B** | Ahead of all else; best-effort same week |
| **Dead secret** | An expired/rotated key, still sensitive | §6A tombstone; §6B only if presence-in-history is itself harmful | Remove ≤7 calendar days |
| **PII / proprietary content** | Names, emails, internal identifiers, confidential prose | §6A tombstone; §6B for serious cases | Remove ≤7 calendar days |
| **Contributor removal request** | "Take down my data" (after §2 check) | §6A tombstone | Remove ≤7 calendar days |

When in doubt, treat it as the more severe class. Clock starts at acknowledgment.

## 4. Locate the contribution from the hash

Map the reported hash to its files and its manifest row:

```bash
# Tier 1: the path is content-addressed on input_sha256
ls corpus/*/<input_sha256>/                 # the contribution directory
# Tier 2: content-addressed on scan_id
ls structural/*/<scan_id>/

# Find the manifest index row (exactly one line matches the hash)
grep -n '<input_sha256_or_scan_id>' manifest.jsonl
```

You now have: the contribution directory (files to remove) and the one `manifest.jsonl` line that
indexes it. Both go in the tombstone.

## 5. Decision: tombstone vs. history rewrite

**This is the standing decision, made here so no one improvises it under pressure:**

> **Tombstone (§6A) is the default and is sufficient for almost every case. History rewrite (§6B) is
> the exception, used only when a *live* secret or serious PII is present and its continued existence
> in git history — reachable by commit SHA even after deletion from the branch — is itself an active
> harm that rotation cannot neutralize.**

Rationale: removing from the published branch is fast, low-risk, reversible-in-process, and needs
only write access — it is the part CCDC fully controls. A history rewrite force-rewrites every
commit, breaks every existing clone and open PR, *still* cannot reach forks and caches (§9), and
requires GitHub Support to purge cached views — so it buys little for a dead secret or ordinary
removal request while costing a lot. Reserve it for true emergencies.

## 6A. Tombstone procedure (default)

Removes the contribution from the published branch and records the removal in an auditable ledger,
without retaining the data. The locked manifest schema indexes only *live* contributions
(`additionalProperties: false`, no status field — see [SCHEMA.md](SCHEMA.md)), so removal **deletes**
the row rather than flagging it; the [`removals.jsonl`](removals.jsonl) ledger (§7) preserves the
audit trail.

```bash
git switch main && git pull
git switch -c removal/<short-reason>-<short-hash>

# 1. Delete the contribution directory (files + sidecar)
git rm -r corpus/<contributor_id>/<input_sha256>/        # or structural/<cid>/<scan_id>/

# 2. Delete its manifest index row (the single matching line)
grep -v '<input_sha256_or_scan_id>' manifest.jsonl > manifest.jsonl.tmp && \
  mv manifest.jsonl.tmp manifest.jsonl

# 3. Append a removals-ledger record (see §7 for the fields; no secret/PII in it)
#    Edit removals.jsonl and add one line.

git add -A
git commit -m "chore(removal): tombstone <tier> contribution <short-hash> (<reason class>)"
git push -u origin HEAD
```

Open a PR using the [security template](.github/PULL_REQUEST_TEMPLATE.md); its **Security review**
section states the reason *class* (not the specifics). Merge it — a removal PR does **not** wait on
the normal contribution gate; it is a maintainer action. After merge, confirm the files are gone from
the published branch and the manifest row is absent.

> A tombstone leaves the data in git **history** (reachable only by an explicit old commit SHA, not
> from the branch). For a dead secret, an ordinary removal request, or most PII that is acceptable.
> If it is **not** acceptable (live credential / serious PII), continue to §6B.

## 6B. History-rewrite escalation (exception)

Only after §6A, only for the live-credential / serious-PII case, and only with **repo admin**. This
rewrites history and is disruptive — every clone and open PR must be re-based or re-cloned.

```bash
# Use git-filter-repo (https://github.com/newren/git-filter-repo); work on a FRESH clone.
git clone --mirror https://github.com/frederick-douglas-pearce/claude-code-data-collective.git
cd claude-code-data-collective.git
git filter-repo --invert-paths --path corpus/<contributor_id>/<input_sha256>/
git push --force
```

Then — the part git cannot do alone:

1. **Contact GitHub Support** to purge cached views reachable by old commit SHA and to drop stale PR
   refs. GitHub does this only for risks not mitigable by rotation, and publishes no SLA — open the
   request immediately and reference the security context (no secret in the message).
2. **Rotate** any live credential (the reporter/affected party does this; confirm it happened).
3. **Force-expire** open PRs/branches that reintroduce the data.
4. Record the rewrite in [`removals.jsonl`](removals.jsonl) with `method: "history-rewrite"`.

Even after all of this, forks and prior clones remain out of reach (§9).

## 7. The removals ledger (`removals.jsonl`)

Append-only, one JSON object per removal, parallel to `manifest.jsonl`. It is the tombstone's durable
record — it documents *that* a contribution existed and was removed, **without** retaining the data or
the leaked content. Carry no secret/PII bytes in any field.

| Field | Value |
|-------|-------|
| `removed_at` | UTC `YYYY-MM-DDThh:mm:ssZ` of the removal merge |
| `tier` | `"full"` or `"structural"` |
| `contributor_id` | from the removed contribution's path |
| `input_sha256` *or* `scan_id` | the content-address handle of what was removed |
| `reason_class` | `"live-credential"` \| `"dead-secret"` \| `"pii"` \| `"contributor-request"` \| `"other"` |
| `method` | `"tombstone"` or `"history-rewrite"` |
| `reported_via` | `"public-issue"` \| `"private"` \| `"internal-rescan"` |
| `notes` | short, non-sensitive (e.g. "expired key, contributor confirmed"); **never** the secret/PII |

> A formal JSON Schema for `removals.jsonl` (mirroring `schema/manifest-row.schema.json`) is a small
> follow-up; the field set above is the contract in the meantime.

## 8. Communicate & close

- **Acknowledge** the reporter within the SLA; tell them the class and that it is being actioned.
- **Notify the contributor** if the removal was triggered by someone else (a leak report), unless
  doing so would expose the reporter.
- **Close** the intake issue once the removal merges. Keep the public issue free of specifics.
- If the removed data underpinned a published claim or the corpus count, note the change (an erratum /
  changelog entry) so the corpus stays honestly described.

## 9. The honest limits (state these to every reporter)

- **Forks and prior clones cannot be retracted.** Anyone who cloned or forked before removal still has
  the data; CCDC has no mechanism to reach them.
- **Caches persist.** Even after a history rewrite, cached views by commit SHA persist until GitHub
  Support purges them.
- **A live secret must be rotated** — removal from CCDC is not rotation and is not a substitute for it.
- Removal makes the data **no longer distributed by CCDC going forward**; it does not unpublish the
  past. This is the same reality The Stack, C4, and GitHub's own guidance state plainly.

## 10. Sanitizer re-scan hits are disclosure events

When the pinned sanitizer is upgraded, the corpus is re-scanned against the new pattern set
([#24](https://github.com/frederick-douglas-pearce/claude-code-data-collective/issues/24)). A hit on
already-merged data is a **disclosure event** and enters this runbook at §3 (classify) — it must not
be surfaced in a public CI log. "Sanitizer improved → re-sanitize → re-release" is a normal,
first-class event (the Re-LAION precedent), not an emergency; the affected contributor can re-sanitize
from their retained original and re-contribute.

---

## Quick incident checklist

```
[ ] Do NOT reproduce the secret/PII anywhere public
[ ] Live credential? → tell affected party to ROTATE NOW
[ ] Acknowledge reporter (≤ 3 business days)
[ ] Removal request? → verify requester controls the contributor identity (§2)
[ ] Classify: live-credential / dead-secret / pii / contributor-request (§3)
[ ] Locate: hash → corpus|structural/<cid>/<hash>/ + manifest.jsonl row (§4)
[ ] Tombstone (§6A): git rm dir, drop manifest row, append removals.jsonl, PR+merge
[ ] Live/serious? → history rewrite (§6B): filter-repo, force-push, GitHub Support, rotate
[ ] Communicate + close; erratum if it changes a published count/claim (§8)
[ ] State the honest limits to the reporter (§9)
```

## See also

- [GOVERNANCE.md](GOVERNANCE.md) — the curation model and the SLA this runbook implements.
- [`.github/ISSUE_TEMPLATE/leak_or_removal.yml`](.github/ISSUE_TEMPLATE/leak_or_removal.yml) — intake form.
- [LAYOUT.md](LAYOUT.md) · [SCHEMA.md](SCHEMA.md) — content-addressed paths and the locked manifest schema.
- [`docs/research-governance-norms.md`](docs/research-governance-norms.md) §2 — the comparable-dataset
  takedown norms (The Stack opt-out, Re-LAION, GitHub history guidance) behind these mechanics.
