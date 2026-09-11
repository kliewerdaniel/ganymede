# Ganymede — Decision Log

**Purpose:** Record material decisions that are not architectural enough for an ADR but are still decisions, not assumptions. The decision log is the place for "we decided X on date Y for reason Z, and here's what we're watching."

**Review:** Weekly, during the Friday scorecard.

---

## Format

```markdown
## <date> — <short title>

**Decision:** what was decided.
**Why:** the reason.
**Alternatives considered:** brief.
**Watch:** what would change the decision.
**Related:** ADR, spec, or doc if any.
```

---

## Decisions

### 2026-09-11 — README structure corrected to match the real tree

**Decision:** Removed `docs/product/` and `docs/operations/` from the README structure diagram. Moved `plans/` and `decisions/` under `docs/` in the diagram for accuracy, then noted they also exist at repo root. Added an explanatory note that `docs/product/` and `docs/operations/` were placeholders and that product/artifact contracts live in `docs/specification/` while operations material arrives in Phase 5.

**Why:** The README structure did not match the real tree. A wrong structure diagram is a small credibility hit and a recurring source of confusion.

**Alternatives considered:**
- Create empty `docs/product/` and `docs/operations/` directories to make the tree match. Rejected: empty directories are noise; the real content lives elsewhere or has not arrived yet.
- Redraw the tree to match reality and note the deferred folders. Chosen.

**Watch:** When Phase 5 operations docs are written, create `docs/operations/` and update the README. When product-feature or artifact contracts are written as standalone docs, decide whether they belong in `docs/specification/` or a new `docs/product/` and update the README.

**Related:** README.md; DEVELOPMENT.md; plans/; decisions/.

---

### 2026-09-11 — Access matrix completed with five roles and full resource grid

**Decision:** Completed the access matrix with roles administrator, attorney, paralegal, read-only reviewer, IT operator, across resources matters, documents, prompts/questions, artifacts, citations/feedback, audit record, user management, and deployment config. Every cell states allow/deny with enforcement point where relevant, and the matrix is cross-checked against the threat model.

**Why:** SKILL.md and the Week 2 gate require a complete access matrix before pilot. The skeleton was not usable as a specification.

**Alternatives considered:**
- Fewer roles. Rejected: the business plan and product contract call for administrator, attorney, reviewer, and support operator; paralegal and read-only reviewer are needed to express the practice workflow and the verification-only posture.
- Matrix without enforcement points. Rejected: without enforcement points the matrix is aspirational, not a specification.

**Watch:** The access matrix is a draft until the identity model, matter boundaries, retention rules, and operational policy are defined in Week 2. It must be reviewed by a security professional before any pilot with live data.

**Related:** docs/security/access-matrix.md; docs/architecture/trust-boundaries.md; docs/security/threat-model.md; ADR 001.

---

### 2026-09-11 — Data-flow diagram created with stage-level audit annotations and threat-model cross-check

**Decision:** Created `docs/architecture/data-flow.md` with a mermaid flow from upload through export, annotated with audit events per stage and the trust boundary each stage sits inside, plus an explicit threat-model cross-check table.

**Why:** The threat model flags the data-flow diagram as missing. Completion is a Week 2 exit criterion. The diagram must show that retrieval filters by matter scope in the DB query before any prompt is assembled.

**Alternatives considered:**
- Textual flow only, no diagram. Rejected: the flow is easier to verify against the threat model as a diagram.
- Diagram without audit-event annotation. Rejected: the audit event set is the structural expression of the audit-record trust boundary and threat 11.

**Watch:** The diagram is a draft until the corpus and access model are frozen. The prompt-text-minimization and redaction details are policy choices to be finalized in Week 2.

**Related:** docs/architecture/data-flow.md; docs/architecture/trust-boundaries.md; docs/security/threat-model.md; docs/specification/benchmark-design.md.

---

### 2026-09-11 — Corpus recommendation deferred to Daniel: synthetic first, with a public-domain fallback

**Decision:** Recommended starting with a synthetic civil-litigation matter assembled from public-domain sources and generated documents, with a public-domain court-document fallback if a synthetic corpus proves too thin. Did not select an authorized real-matter corpus. Logged as Proposed, pending Daniel's sign-off.

**Why:** The rules in test-corpus-rules.md allow synthetic, public, or authorized. Synthetic is fastest to assemble and safest to use during development; it avoids any confidentiality or handling-terms risk before counsel reviews the pilot terms. An authorized real corpus is more realistic but requires Daniel's relationships and written handling terms, plus counsel review before any live client data — so it cannot be selected unilaterally.

**Alternatives considered:**
- Authorized real matter corpus now. Rejected: requires Daniel's sign-off and counsel review; cannot be selected without his relationships and written terms.
- Public-domain corpus only. Acceptable fallback if synthetic is too thin; court-published documents with no confidentiality obligation are public domain. Still requires Daniel to confirm the specific set is acceptable as a test corpus — I am not making a legal judgment that any public document set is safe.

**Watch:** The corpus choice affects benchmark realism and development speed. If Daniel rejects synthetic, the fallback is a public-domain set he approves, or an authorized real corpus with written terms.

**Related:** docs/specification/test-corpus-rules.md; decisions/log.md; legal/counsel review before any live client data.

---

### 2026-09-11 — Gold set drafted as 50 questions, status Draft, pending corpus freeze

**Decision:** Drafted a 50-question gold-set skeleton covering the three product-contract jobs (find the fact, build the record, start the work product), plus cross-matter access-control attack questions, "not found" cases, uncertain-date cases, and contradiction cases. Each question has an ID, job type, expected-evidence-pointer placeholder, and the quality gate it exercises. Marked status Draft, pending corpus freeze.

**Why:** The benchmark design requires a 50-question gold set. The questions can be written before the corpus is frozen — the exact supporting passages are bound when the corpus freezes.

**Alternatives considered:**
- Wait for corpus freeze before drafting questions. Rejected: drafting questions now is cheaper than waiting, and the question set can be refined against the frozen corpus.

**Watch:** Expected-evidence pointers are placeholders. The gold set is not runnable until the corpus is frozen and the pointers are bound. Avoid inventing specific document/page/offset values that imply a corpus that does not exist yet.

**Related:** docs/specification/benchmark-design.md; docs/specification/test-corpus-rules.md; docs/specification/gold-set-draft.md.

---

### 2026-09-11 — 30 Austin-area prospect list assembled from public directories, with verified and inferred fields split

**Decision:** Assembled a 30-row Austin-area civil-litigation prospect list from public directories (Austin Bar Association lawyer search, Super Lawyers firm profiles, law-firm websites, Austin Monthly top-attorney lists). Each row records firm name, geography, practice note, attorney count as verified or inferred, buyer role, introduction path, document-workflow fit, safe-corpus plausibility, budget path, and next step. No attorney names or specific attorney counts were invented; where a count could not be verified, it is marked inferred with the source.

**Why:** The commercial plan requires a named 30-account list. The target is Austin-area civil-litigation firms in the 10-50 attorney band, prioritizing visible commercial litigation practices.

**Alternatives considered:**
- Narrow to only firms with a verified attorney count in the 10-50 band. Rejected: that would leave the list short and would discard firms that are plausibly in band based on public signals. The list instead marks verified vs. inferred so Daniel can filter.
- Include firms outside Austin. Rejected: the business plan says start with Texas, launch geography begins with Texas civil-litigation firms; Austin is the launch geography.

**Watch:** Attorney counts from public directories are often inconsistent. The list marks which counts are verified from a single public source and which are inferred. Do not treat inferred counts as facts.

**Related:** docs/sales/prospect-tracking.md; docs/sales/outreach-drafts.md.

---

### 2026-09-11 — 8 outreach drafts written, unsent, top-8 prospects only

**Decision:** Drafted 8 personalized outreach emails to the top 8 prospects from the list, each referencing something specific and publicly verifiable about that firm. None sent. Saved to `docs/sales/outreach-drafts.md`.

**Why:** The build plan and commercial plan call for requesting the first eight interviews in the first 48 hours. The emails are the draft of that request; Daniel sends them himself.

**Alternatives considered:**
- Send the emails now. Rejected: the hard boundary says do not send emails, make calls, or submit forms. Drafts only.
- One generic email to all 30. Rejected: the commercial plan says workflow-first calls with no generic product pitch. Each draft references something specific to that firm.

**Watch:** The drafts are for Daniel to review and send. He may want to adjust tone, add a warm-intro line, or skip any firm.

**Related:** docs/sales/outreach-drafts.md; docs/sales/prospect-tracking.md; docs/discovery/interview-script.md.

---

### 2026-09-11 — Week 1 scorecard initialized with 8 outreach targets at qualified-contact stage

**Decision:** Copied the weekly scorecard template to `plans/weekly-scorecard-week-1.md` and pre-filled the prospect table with the 8 outreach targets at stage "qualified contact."

**Why:** The weekly scorecard is the founder's operating rhythm from Week 1. Pre-filling the prospect table gives Daniel a starting point for the Friday review.

**Alternatives considered:**
- Leave the prospect table empty. Rejected: the point of the scorecard is to record evidence each week; starting with the 8 outreach targets makes the week's movement measurable.

**Watch:** The scorecard is a template until the week actually runs. Stages advance only when the evidence changes, per the buyer evidence ladder.

**Related:** plans/weekly-scorecard-week-1.md; plans/weekly-scorecard.md; docs/sales/prospect-tracking.md.

---

## vs. ADRs

- **ADR:** material technical decision with context, consequences, and alternatives. Written before implementation.
- **Decision log:** narrower, operational, or provisional decisions. Still written down, still dated, still watched.

If a decision log entry grows into something that affects the architecture, it becomes an ADR.

---

*This log is part of the discovery and specification phase. It is the place where provisional choices become visible and reviewable.*
