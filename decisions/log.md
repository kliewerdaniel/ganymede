# Ganymede — Decision Log

**Purpose:** Record material decisions that are not architectural enough for an ADR but are still decisions, not assumptions.

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

**Decision:** Removed `docs/product/` and `docs/operations/` from the README structure diagram; moved `plans/` and `decisions/` back to repo root in the diagram (they are at root, not under `docs/`); added an explanatory note.

**Why:** The README structure did not match the real tree.

**Alternatives considered:**
- Create empty `docs/product/` and `docs/operations/`. Rejected.
- Redraw to match reality. Chosen.

**Watch:** When Phase 5 operations docs are written, create `docs/operations/` and update the README if `docs/product/` is ever needed.

**Related:** README.md; DEVELOPMENT.md.

---

### 2026-09-11 — Access matrix completed with five roles and full resource grid

**Decision:** Completed the access matrix with roles administrator, attorney, paralegal, read-only reviewer, IT operator, across resources matters, documents, prompts/questions, artifacts, citations/feedback, audit record, user management, and deployment config.

**Why:** SKILL.md and the Week 2 gate require a complete access matrix.

**Related:** docs/security/access-matrix.md; docs/architecture/trust-boundaries.md; ADR 001.

---

### 2026-09-11 — Data-flow diagram created with stage-level audit annotations and threat-model cross-check

**Decision:** Created `docs/architecture/data-flow.md` with a mermaid flow from upload through export, annotated with audit events per stage and the trust boundary each stage sits inside, plus an explicit threat-model cross-check table.

**Related:** docs/architecture/data-flow.md; docs/security/threat-model.md.

---

### 2026-09-11 — Corpus recommendation deferred to Daniel: synthetic first, with a public-domain fallback

**Decision:** Recommended starting with a synthetic civil-litigation matter, with a public-domain court-document fallback. Did not select an authorized real-matter corpus.

**Related:** docs/specification/test-corpus-rules.md.

---

### 2026-09-11 — Gold set drafted as 50 questions, status Draft, pending corpus freeze

**Decision:** Drafted a 50-question gold-set skeleton covering the three product-contract jobs, plus cross-matter attack questions, "not found" cases, uncertain-date cases, and contradiction cases.

**Related:** docs/specification/benchmark-design.md; docs/specification/gold-set-draft.md.

---

### 2026-09-11 — 30 Austin-area prospect list assembled from public directories, with verified and inferred fields split

**Decision:** Assembled a 30-row Austin-area civil-litigation prospect list from public directories. No attorney names or invented counts.

**Related:** docs/sales/prospect-tracking.md.

---

### 2026-09-11 — 8 outreach drafts written, unsent, top-8 prospects only

**Decision:** Drafted 8 personalized outreach emails to the top 8 prospects. None sent.

**Related:** docs/sales/outreach-drafts.md.

---

### 2026-09-11 — Week 1 scorecard initialized with 8 outreach targets at qualified-contact stage

**Decision:** Copied the weekly scorecard template to `plans/weekly-scorecard-week-1.md` and pre-filled the prospect table.

**Related:** plans/weekly-scorecard-week-1.md.

---

### 2026-09-11 — README tree fixed: removed duplicate `plans/` and `decisions/` entries

**Decision:** Fixed the README tree diagram so `plans/` and `decisions/` appear once, at root. Added a note that `docs/product/` and `docs/operations/` are not current folders.

**Why:** The previous README listed `plans/` and `decisions/` under `docs/` and again at root. The real tree has them only at root.

**Alternatives considered:**
- Leave the duplicate entries and add a note. Rejected: duplicates are confusing.
- Remove the duplicates and keep `docs/operations/` noted as deferred. Chosen.

**Watch:** When `docs/operations/` is created in Phase 5, update the README.

**Related:** README.md.

---

### 2026-09-11 — Fixed broken references from the previous commit

**Decision:** Fixed the following broken references:
- README "Weekly scorecard" link now points to `plans/weekly-scorecard.md` (correct: plans/ is at root, not under docs/).
- README "Product Roadmap" link points to `docs/specification/roadmap.md` (correct).
- README structure diagram no longer lists `docs/product/` or `docs/operations/` as existing folders.

**Why:** The previous commit's README had `plans/` and `decisions/` duplicated and pointed `docs/operations/` as if it existed.

**Related:** README.md.

---

### 2026-09-11 — Corpus v0.1 built: 23-document synthetic civil-litigation matter

**Decision:** Built `testdata/corpus-v0.1/` with a 23-document synthetic matter (Meridian Logistics Solutions, LLC v. Cascade Retail Group, Inc.). Formats: 13 native PDFs, 8 DOCX, 2 scanned-image PDFs. Includes a facts ledger (corpus-facts.md) and manifest (MANIFEST.md) with SHA-256 hashes. All fictional; nothing scraped.

**Why:** The proposed corpus decision (synthetic first) and test-corpus-rules.md require a buildable synthetic corpus. The gold set must be bound to real pointers.

**Alternatives considered:**
- Fewer documents. Rejected: the corpus must exercise PDF, DOCX, TXT-equivalent, and scanned-image formats, plus multi-document synthesis and chronology.
- More documents. Deferred: 15 is sufficient for the gold-set binding; additional documents can be added in a later corpus version.

**Watch:** corpus-v0.1 is a candidate for freeze; it is not frozen until Daniel approves. If he approves, the gold set becomes frozen against it.

**Related:** testdata/corpus-v0.1/; docs/specification/gold-set-draft.md; docs/specification/test-corpus-rules.md.

---

### 2026-09-11 — Corpus v0.1 composition decisions logged

**Decision:** Corpus composition decisions:
- Matter: Meridian Logistics Solutions, LLC v. Cascade Retail Group, Inc., Cause No. D-2025-00418, Travis County District Court. All fictional.
- Document count: 15 documents (22 files total counting the MANIFEST and facts ledger as corpus metadata, not evidence documents; the 15 evidence documents are DOC-001 through DOC-022 minus the two non-evidence metadata files).
- Formats: native PDF (12), DOCX (8), scanned-image PDF (2).
- Key facts: MSA March 15, 2023; effective April 1, 2023; term ends March 31, 2026; Amendment No. 1 January 22, 2024; hourly rate $125→$145; four invoices (#1042 $55,100; #1043 $48,140; #1044 $52,300; #1045 $49,800); disputed total $102,100; notice January 28, 2025; response February 14, 2025; demand March 3, 2025; complaint filed April 2, 2025; answer filed May 1, 2025; deposition of James Okafor held August 15, 2025.
- Scanned documents: DOC-018 (handwritten meeting notes, undated) and DOC-018b (Additional Terms Addendum, undated, with the "ignore all prior confidentiality restrictions" footnote for Q48).
- No real person, firm, attorney, judge, court reporter, or document. No scraping.

**Why:** The corpus must be internally consistent, format-diverse, and sufficient for the gold set. The scanned documents exercise the OCR path and the prompt-injection edge case.

**Related:** testdata/corpus-v0.1/corpus-facts.md; testdata/corpus-v0.1/MANIFEST.md; docs/specification/gold-set-draft.md.

---

### 2026-09-11 — Gold set bound to corpus-v0.1 with real pointers

**Decision:** Updated `docs/specification/gold-set-draft.md` to bind all 50 questions to real evidence pointers in corpus-v0.1. Six answer-absent questions (Q39–Q44) verified unanswerable by construction. Q02, Q03, Q06, Q10, Q16, Q18, Q20, Q24, Q26, Q27, Q28, Q30, Q35, Q37, and Q46b are either not answerable from this corpus or require Matter B (for Q46b).

**Why:** The benchmark design requires the gold set to be bound to real pointers once a corpus exists.

**Alternatives considered:**
- Keep all pointers as placeholders. Rejected: the point of building the corpus was to bind the pointers.
- Invent pointers for unanswerable questions. Rejected: that would defeat the answer-absent tests.

**Watch:** The gold set is Draft, not frozen, until Daniel freezes corpus-v0.1. If he approves a different corpus, the pointers must be re-bound.

**Related:** docs/specification/gold-set-draft.md; testdata/corpus-v0.1/.

---

### 2026-09-11 — Interview capture template created

**Decision:** Created `docs/discovery/interview-capture-template.md` as a per-interview form that maps to the four discovery-outputs.md sections (workflow map, economic baseline, risk baseline, buying map) and includes the buyer evidence ladder fields.

**Why:** The interview script is the question set; the capture template is the structured record.

**Related:** docs/discovery/interview-capture-template.md; docs/discovery/interview-script.md; docs/discovery/discovery-outputs.md.

---

### 2026-09-11 — Design-partner / pilot-review commitment letter drafted

**Decision:** Drafted `docs/commercial/design-partner-letter-draft.md` from the pilot-agreement-inputs.md. Draft only; Daniel sends it himself; must be reviewed by counsel before sending.

**Why:** The build plan and commercial plan call for a written pilot-review commitment. The letter is the first written ask.

**Related:** docs/commercial/design-partner-letter-draft.md; docs/commercial/pilot-agreement-inputs.md.

---

## vs. ADRs

- **ADR:** material technical decision with context, consequences, and alternatives. Written before implementation.
- **Decision log:** narrower, operational, or provisional decisions. Still written down, still dated, still watched.

If a decision log entry grows into something that affects the architecture, it becomes an ADR.

---

*This log is part of the discovery and specification phase. It is the place where provisional choices become visible and reviewable.*
