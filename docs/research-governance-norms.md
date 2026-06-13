# Research — data-governance norms for CCDC

**Status:** Reference / due-diligence scan. **Date:** 2026-06-13. **Audience:** maintainer + future
contributors who want the evidentiary basis behind CCDC's governance, attestation, and removal
decisions.

> This is a **point-in-time literature/landscape scan**, not a living spec. It records what
> comparable public datasets and the surrounding literature do, so CCDC's choices are grounded in
> prior art rather than invented from scratch. The authoritative *decisions* live in
> [GOVERNANCE.md](../GOVERNANCE.md), the [LICENSE](../LICENSE), the removal runbook (#6), and the
> contributor attestation (#9); this doc is the *why behind* them. Where this scan flagged a gap,
> it is noted inline and tracked to an issue. Conducted with web research + an architecture review;
> sources are primary where possible.

---

## Why this exists

The maintainer is new to AI/data governance and asked for due diligence before opening the corpus.
Two questions drove it: (1) the general AI-data-governance landscape (documentation, PII/takedown,
consent, licensing, sustainability), and (2) a specific technical concern — the sanitizer is
configured around the maintainer's own data, so how do config updates for new contributors flow in,
and does that affect the CI re-scan gate's ability to validate? The technical concern is answered in
its own section below ([Sanitizer versioning & the gate's coverage boundary](#sanitizer-versioning--the-gates-coverage-boundary)).

---

## 1. Dataset documentation norms

The field has four nested reference standards:

- **Datasheets for Datasets** (Gebru et al., [arXiv:1803.09010](https://arxiv.org/abs/1803.09010),
  CACM Dec 2021) — a 7-section prose *questionnaire* (~50 questions): Motivation, Composition,
  Collection, Preprocessing/cleaning, Uses, Distribution, Maintenance.
- **Data Statements for NLP** (Bender & Friedman, [TACL 2018, Q18-1041](https://aclanthology.org/Q18-1041/))
  — lettered fields A–I; crucially distinguishes a **long form** from a **short form (60–100 words)**.
  The short form is the realistic minimum.
- **Hugging Face Dataset Cards** ([docs](https://huggingface.co/docs/hub/datasets-cards)) — one
  `README.md` = YAML front-matter (`license`, `language`, `pretty_name`, `task_categories`,
  `size_categories`) + a markdown body modeled on Datasheets + Data Statements. Unfillable sections
  get the literal `[More Information Needed]`.
- **Croissant** (MLCommons, 2024, [announce](https://mlcommons.org/2024/03/croissant_metadata_announce/)
  · [repo](https://github.com/mlcommons/croissant)) — JSON-LD on schema.org standardizing the
  *description*; HF auto-generates it from the card.

**Applicable to CCDC:** the realistic target is **one repo-level datasheet + the existing manifest**
— not per-session data statements, not the 50-question form. Load-bearing sections: Motivation (lift
from PRD), Composition (the two tiers, counts, sensitive-content handling), Collection (donated,
**self-selected non-probability sample** — state this generalizability caveat explicitly),
Preprocessing (the differentiator — link `ccs-sanitize` / `scan.py`, note retained raw inputs), Uses,
Distribution + Maintenance (license + removal path). **Gap:** CCDC documents the *parts* (`SCHEMA.md`,
`structural/README.md`) but nothing yet documents the *corpus as a citable research object*, and the
self-selected-sample limitation is unstated. This is assembly of existing content, not new research.
Mirroring schema.org field names in the manifest now makes a future Croissant export free.

## 2. PII and takedown in public corpora

Real projects converge on three hard truths: removal is **prospective**, takedown is **not erasure**,
and the credible response to a serious finding is **pull the live artifact immediately, then
re-release a fixed, version-renamed dataset**.

- **The Stack / BigCode** — "[Am I in The Stack](https://huggingface.co/spaces/bigcode/in-the-stack)"
  is a *lookup* tool; opt-out is a GitHub issue in
  [`bigcode-project/opt-out-v2`](https://github.com/bigcode-project/opt-out-v2), verified by **issue
  authorship**. Removal is **prospective only** (next version); the license binds downstream users to
  update to the latest version. PII handling evolved regex → trained model across versions, shipping
  v1 with an openly-acknowledged work-in-progress PII pipeline.
- **LAION** — Dec 19 2023, Stanford found CSAM links; LAION took down all of LAION-5B **same day**,
  then released cleaned **[Re-LAION-5B](https://laion.ai/blog/relaion-5b/)** ~8 months later. Model:
  immediate tombstone, deliberate fixed re-release.
- **C4 / Common Crawl** — opt-out is **crawl-time only** (CCBot honors robots.txt, prospective); the
  static C4 snapshot has **no removal path at all**. The cautionary baseline.
- **Hugging Face** — a "Report" affordance opening a public discussion; DMCA via `dmca@huggingface.co`;
  discretionary takedown ([moderation docs](https://huggingface.co/docs/hub/moderation)).
- **Git-history vs tombstone** — [GitHub's own guidance](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
  is blunt: deleting from HEAD is *not* deletion. Data persists in cached views by SHA, in PR refs,
  and in **forks/clones you cannot reach**. True deletion needs `git filter-repo` **plus contacting
  GitHub Support**, which they do only for risks not mitigable by credential rotation. No published SLA.

**Applicable to CCDC:** CCDC has The Stack's shape, C4's frozen-snapshot problem, and GitHub's
history trap. Adopt an explicit **"fast tombstone, slow rewrite"** model in the removal runbook (#6):
(a) immediately remove from HEAD via PR (the part we control); (b) reserve `git filter-repo` + GitHub
Support escalation as a separate, slower step for confirmed secrets/PII — **pre-write that procedure,
don't improvise under pressure**. Tell contributors the truth: removal is prospective and forks/clones
cannot be retracted. The modest SLA already in GOVERNANCE.md (ack ≤3 business days, tombstone ≤7
calendar days) beats HF's only public number (90 days). Copy BigCode's lightweight identity check
(prove control of the contributor identity). Treat **"sanitizer improved → re-sanitize → re-release"**
as a normal, first-class event (the Re-LAION precedent), not an emergency. Provide a **private** report
channel so a reporter never pastes a live secret into a public issue.

## 3. Contributor consent / right-to-share attestation

The **DCO** is the right *shape* — but the stock DCO is **provenance-only** and does not cover data
rights, third-party content, employer confidentiality, or the Anthropic basis.

- **[DCO 1.1](https://developercertificate.org)** certifies right-to-submit via a `Signed-off-by` git
  trailer; enforced by the [DCO bot](https://github.com/apps/dco). Used by Linux kernel, CNCF, OpenSSF.
- **DCO vs CLA** — DCO certifies *provenance*; a CLA *grants* rights and enables relicensing. Apache's
  CCLA is the canonical instrument for **employer-owned** contributions.
  [Kemitchell's warning](https://writing.kemitchell.com/2021/07/02/DCO-Not-CLA): a DCO has value only
  if you **retain and link the signed assertion** per contribution — a checkbox with no audit trail
  "achieves next to nothing."
- **The Anthropic basis** ([Commercial Terms](https://www.anthropic.com/legal/commercial-terms)):
  customer "retains all rights to its Inputs" and "owns its Outputs," with Anthropic assigning its
  rights in Outputs "**(if any)**" and "**subject to compliance**." A transcript = contributor's
  Inputs + Claude's Outputs, so there's a clean rights basis for the Claude-interaction layer — **but**
  it is tier-dependent (Commercial vs consumer), does not cleanse **third-party material captured
  inside** the session, and does not waive **employer ownership**.

**Applicable to CCDC:** build a DCO-shaped, signed, **retained** attestation (#9) certifying: (1)
ownership / right to share; (2) the Anthropic Inputs/Outputs basis — framed as *the contributor*
affirming their rights, not CCDC leaning on Anthropic's "if any" grant; (3) **employer / confidentiality**
(the clause the DCO most lacks); (4) **third-party content / PII** (the human backstop the scanner
structurally cannot provide — see §3b); (5) public-and-permanent acknowledgment; (6) sanitization
affirmation (committed file is sanitizer output, no raw JSONL); (7) removal-path acknowledgment. Fold
the signed assertion into the **manifest / PR record**, not a bare checkbox.

## 3b. Secret-scanning as a trust gate — confirmed limitations

The accepted understanding is unambiguous: **pattern/entropy scanners only catch credential types
they have a signature for, and they do not target arbitrary PII.**

- Regex detectors are scoped to a curated catalog —
  [GitHub](https://docs.github.com/en/code-security/secret-scanning/introduction/about-secret-scanning)
  detects "known secret types"; custom formats need user-defined patterns.
  [GitGuardian](https://blog.gitguardian.com/secrets-in-source-code-episode-3-3-building-reliable-secrets-detection/)
  states plainly that pattern-based detection misses custom tokens and internal API keys. TruffleHog
  matches a fixed catalog; its "verification" raises *precision*, not *coverage*.
- Entropy detection trades false positives against false negatives; structured/low-entropy secrets
  evade thresholds ([Yelp detect-secrets](https://github.com/Yelp/detect-secrets)).
- **PII gap:** every source scopes these tools to **credentials, not names/emails/bespoke identifiers**.

**Applicable to CCDC:** this squarely supports CCDC's stance — the independent re-scan is a
**load-bearing-but-bounded** backstop, not a guarantee. It cannot catch novel-format secrets or any
PII, so **diff-level human review remains a required complement**, and the attestation's
third-party/PII clause (§3) is where that residual risk is formally allocated. See
[Sanitizer versioning & the gate's coverage boundary](#sanitizer-versioning--the-gates-coverage-boundary).

## 4. Licensing norms for use-restricted AI-training data

CCDC's custom no-train-competing-AI license sits in the RAIL/OpenRAIL lineage. Three realities:

- **[RAIL/OpenRAIL](https://huggingface.co/blog/open_rail)** attach behavioral-use restrictions;
  adoption reached ~24% of *licensed* HF models by Jan 2024 but is fragmenting
  ([arXiv:2402.05979](https://arxiv.org/pdf/2402.05979)).
- **Not "open source"** — any field-of-use / no-train restriction fails
  [OSD Clause 6](https://opensource.org/osd), so OSI approval is impossible (same reason Llama is "not
  open source").
- **"No training competing models"** is a **contract** restriction, not a copyright one that runs with
  copies ([arXiv:2310.16787](https://arxiv.org/pdf/2310.16787)).
- **Pass-through is the weak point.** RAIL *text* says restrictions propagate, but the *enforcement
  structure does not* ([Kate Downing](https://katedowninglaw.com/2023/07/13/ai-licensing-cant-balance-open-with-responsible/)):
  no requirement that licensees enforce downstream, no termination for upstream on downstream breach,
  no standing against indirect recipients. On re-host/mirror, you realistically enforce only against a
  **direct counterparty who accepted terms**, plus **platform takedown**.

**Applicable to CCDC:** do not architect governance assuming the clause auto-propagates to mirrors —
it almost certainly does not. The live levers are (a) the direct downloader who accepted terms and (b)
takedown-on-report — which makes the leak/removal template *the* practical enforcement mechanism, more
than the clause. Size expectations to **"deterrent + standing against direct bad actors + takedown
basis,"** not airtight viral control. In copy, call the corpus **"use-restricted" / "source-available,"
not "open source."**

## 5. Governance / sustainability for single-maintainer sensitive datasets

CCDC is the textbook profile these norms target: **bus factor of 1, ~3 contributors, sensitive
provenance, v0.** A 2016 study found 46% of popular GitHub projects have bus factor exactly 1.

- **Sustainability cautionary tales:** **xz-utils** ([CVE-2024-3094](https://www.cisa.gov/news-events/news/lessons-xz-utils-achieving-more-sustainable-open-source-ecosystem))
  is the direct analogue — a solo, burned-out maintainer of a trust-bearing artifact was socially
  engineered into merging a backdoor; CISA frames sustainability as *supply-chain security*. Plus
  core-js and left-pad.
- **PII-liability cautionary tales:** MS-Celeb-1M (pulled 2019, copies persisted), Duke MTMC / Brainwash
  (consent failures), MIT Tiny Images (withdrawn *permanently* 2020). Lesson
  ([MIT Tech Review](https://www.technologyreview.com/2021/08/13/1031836/ai-ethics-responsible-data-stewardship/)):
  **"deleting unethical datasets isn't good enough"** — prevention at ingest beats post-hoc removal.
- **"Enough" governance:** CNCF's
  [`GOVERNANCE-maintainer.md`](https://github.com/cncf/project-template/blob/main/GOVERNANCE.md) (sized
  for "small, very unified projects"), the Datasheets **Maintenance block**, and
  [FAIR](https://www.go-fair.org/fair-principles/)'s "metadata remain accessible even when data are
  not" (design for clean removal).

**Applicable to CCDC:** CCDC is already strong on the highest-leverage lesson — **prevention at
ingest** (sanitize + independent re-scan, never trust the sidecar, no raw JSONL). Gaps, in priority:

1. **Bus factor of 1 is the top risk, and it is a *security* risk (xz), not just continuity.** Name a
   **backup maintainer** with admin rights and document **succession** (repo / org / domain /
   credentials). Until there is a second trusted human, every governance doc has a single point of
   failure.
2. **The leak/removal runbook (#6) is table-stakes and currently half-built** — the issue template
   exists, the incident-response process behind it does not.
3. **Add a Datasheet-style maintenance block** (host, contact, erratum, update/removal comms, retention).
4. **Promote the ingest discipline from CLAUDE.md into a public data-handling policy + the attestation**
   — the consent-at-ingest failures are the harm class sanitization alone doesn't catch.

---

## Sanitizer versioning & the gate's coverage boundary

This answers the maintainer's specific technical concern and is the most consequential finding for
how contributions are actually validated. It is grounded in the current implementation
([`ci/validate_contribution.py`](../ci/validate_contribution.py),
[`ci/requirements.txt`](../ci/requirements.txt) — which pins the upstream sanitizer to an immutable
commit) and an architecture review.

**The gate's guarantee boundary.** The CI re-scan re-runs the sanitizer's *own* residual scan over the
submitted file. It therefore catches only **patterns the scanner already knows**. A novel secret
format or any PII the scanner has no signature for passes **both** the contributor's local sanitize
**and** the CI re-scan — the same blind spot in both. So the gate's real guarantee is: *defense against
a tampered, hand-edited, or wrong-config'd file for known patterns* — **not** prevention of
unknown-pattern leaks. This is inherent to pattern scanning (§3b), is accepted, and must be **disclosed**,
with the catch-nets named in the same breath: required maintainer diff review (pre-merge) and the
leak/removal path (post-merge).

**The load-bearing asymmetry: local-scrub-strengthens vs. CI-config-weakens.** A contributor extending
their *local* scrub config to catch more is strictly safe — it removes more before publication. A
contributor influencing the *CI* scanner config could *weaken* the gate to pass their own leak. These
are not symmetric, which dictates every answer below.

**Therefore — how sanitizer config updates flow (and the answer to "must updates be in the PR?"):**

- **No — sanitizer config is never bundled into a contribution PR.** Validation config must never be
  contributor-controlled; that is the whole reason tier and scan are routed by things a contributor
  cannot set. Bundling config would let a contributor weaken the residual scanner to pass their own
  data. This is structural, not a judgment call.
- **Rule improvements flow upstream.** A new pattern is added in `claude-code-sessions` (scrub rule +
  matching residual-scan rule + test), reviewed there, and released as a new commit/version. CCDC then
  **bumps the pinned commit** in `ci/requirements.txt` in a *separate, maintainer-reviewed* PR
  ("adopt sanitizer pattern set vX"). The affected contributor **re-sanitizes from their retained
  original** and resubmits — exactly what the "retain originals" expectation is for.

**Coverage-gap lifecycle (who owns each step):**
1. Contributor sanitizes locally; CI catches known-pattern tampering, or silently passes a novel
   pattern. *(contributor)*
2. **Required maintainer diff review** — scan the diff for what the gate structurally cannot catch
   (novel-format secrets, names/emails, org identifiers). In v0 this is a **required pre-merge
   backstop, not optional.** *(maintainer)*
3. Post-merge, the leak/removal path is the catch-net. *(anyone)*
4. Gap closed upstream → pin bumped → contributor re-sanitizes. *(maintainer + contributor)*

**Retroactive coverage (recommended into v0).** When the pin is bumped to catch a new pattern,
already-merged contributions were validated under the *old* scanner. A **corpus-wide re-scan against
the new pinned scanner on every bump** is cheap (it reuses the existing `validate_full` scan), needs no
contributor involvement, and is *detection-only* — which puts it on the in-scope side of PRD §10's line
(the deferred item is *nudging contributors to re-sanitize*, not detection). It is the one place a
now-known pattern can be caught mechanically in old data. Its hits are **disclosure events** — route
them through the private removal path, not a public CI log.

**Org-specific patterns too narrow for the shared scanner** (internal hostnames, project codenames):
reject the binary. Don't refuse such data (unenforceable) and don't pretend the gate covers it. It is
the **contributor's pre-submission responsibility** under the attestation + maintainer review + leak
path; encourage extending their *local* scrub (safe), forbid CI-config control (the threat). The
attestation (#9) should carry an explicit clause to this effect.

---

## Decisions this scan prompts (surfaced to the maintainer)

| # | Finding | Suggested action | Tracks to |
|---|---------|------------------|-----------|
| 1 | Gate catches known-pattern tampering, not unknown-pattern leaks | Disclose the boundary in GOVERNANCE.md; make maintainer diff review a *required* pre-merge backstop | GOVERNANCE.md (this PR) |
| 2 | Sanitizer config must never be contributor-controlled; updates flow upstream → pin bump → re-sanitize | Add a "sanitizer versioning" section to GOVERNANCE.md | GOVERNANCE.md (this PR) |
| 3 | Corpus-wide re-scan on every pin bump is cheap, detection-only, high-value | Add as a CI job; treat hits as disclosure events | New issue (CI) |
| 4 | Bus factor of 1 is the top *security* risk; no backup maintainer / succession | Name a backup maintainer + document succession before opening | **maintainer decision** |
| 5 | Stock DCO is insufficient | Attestation must add employer/confidentiality, third-party/PII, Anthropic-basis, sanitization clauses; retain signed in manifest | #9 |
| 6 | Removal is half-built; "fast tombstone, slow rewrite" + private channel needed | Pre-write `git filter-repo` procedure; add private report channel | #6 |
| 7 | No corpus-level datasheet; self-selected-sample limitation unstated | Add `docs/datasheet-ccdc.md` (mostly assembly) | New issue (docs) |
| 8 | License clause won't auto-propagate to mirrors | Call corpus "use-restricted," not "open source"; lean on takedown-on-report | copy review |

---

## Sources

Primary sources are linked inline above. Two sources (exposing.ai; CISA, which 403'd automated fetch)
were corroborated via reputable secondary reporting (MIT Tech Review, 404 Media, The Register),
cross-checked across at least two each. All other claims were verified against the cited primaries.
