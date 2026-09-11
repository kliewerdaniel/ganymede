# Ganymede — Product Contract

**Status:** Draft (to be signed off in Week 2)
**Date:** September 2026
**Source:** 12-week MVP build plan + full business plan
**Review trigger:** After discovery interviews; before implementation begins.

---

## One narrow product, one buyer, one proof

Build a customer-controlled workspace that lets a civil-litigation team ask questions of one matter, assemble a chronology, and draft an internal memo — with source-exact citations, matter-level permissions, and an audit trail.

**Scope:** one matter per pilot. 5-10 pilot users. 30 pilot days.

Contain risk and make setup, quality review, and value measurement tractable. Enough users to expose workflow differences without creating enterprise rollout overhead. A short paid engagement with explicit exit criteria, not an indefinite free beta.

---

## The product promise

**Private by architecture.** Matter data stays inside a customer-controlled single-tenant environment and is not sent to public model APIs.

**Grounded by default.** Every factual answer links to the exact source passage.

**Human-owned.** Drafts are never represented as final legal advice; review and export remain explicit human actions.

---

## Three jobs the user hires it for

### 1. Find the fact

"Where does the record discuss the termination date?"

Return an answer, document name, page, and quoted passage.

### 2. Build the record

Extract a reviewable chronology and issue/evidence table from the matter corpus.

### 3. Start the work product

Produce an internal memo or deposition-prep draft grounded only in approved matter sources.

---

## The smallest complete workflow

1. Create a matter and assign users.
2. Upload PDF, DOCX, TXT, and scanned PDF files.
3. Parse, OCR, fingerprint, index, and record provenance.
4. Ask a question or request a structured artifact.
5. Inspect cited passages in context.
6. Edit, approve, and export a marked draft.
7. Review the immutable activity record.

---

## MVP feature contract

| Ship | Definition | Acceptance |
|------|------------|------------|
| Matter workspace | Users, files, prompts, artifacts | No cross-matter retrieval |
| Ingestion | PDF, scanned PDF, DOCX, TXT | Page-level provenance retained |
| Grounded Q&A | Hybrid retrieval + reranking | Every claim cites evidence |
| Chronology | Date, event, actor, source | Editable; uncertain dates flagged |
| Issue table | Issue, supporting/contrary evidence | No evidence means "not found" |
| Draft memo | Template-bound internal draft | Human review before export |
| Audit record | Inputs, retrieval, model, output | Append-only and exportable |

---

## Initial customer profile

10-50 attorney U.S. civil-litigation firm. No internal machine-learning platform team. A managing partner or operations lead willing to sponsor a bounded pilot. A technical contact who can approve a customer-controlled deployment. The firm can provide a synthetic, public, or expressly authorized pilot corpus.

## Why this wedge fits now

Legal AI spending and investment establish that the category is real. ABA guidance requires fact-specific assessment of confidentiality risks before client information enters a generative AI tool. Document-heavy matters and recurring chronology or memo work are common. Legal professionals place high value on confidential-data safeguards, authoritative grounding, and explainability. Small firms face the same duties without Big Law's procurement leverage.

---

## Positioning sentence

"A private matter workspace that helps your team find, organize, and draft from the record you already own."

**Avoid:** "AI lawyer," "perfect accuracy," "compliance guaranteed."

---

## Explicit non-goals

See [Non-Goals](non-goals.md). In summary: no general case-law research, docket scraping, e-discovery platform, billing integration, court filing, email sync, mobile app, shared multi-tenant SaaS, model fine-tuning, autonomous external action, or claim of legal accuracy. Each would add risk before the core value is proven.

---

## Quality rule

If the system lacks evidence, it must say "not found in the approved matter sources." It may suggest a better query or identify missing documents, but it must not fill the gap from model memory.

---

## North-star sentence

A lawyer can move from a question about the record to a reviewable, cited draft without sending matter data to a public model provider.

---

## Product rule

No feature without an observed task. No connector before multiple paying customers demand the same one. No model-driven external action in the initial product.

---

*This is a product and engineering contract. It does not establish legal compliance, security certification, or professional-responsibility advice. Those require review by qualified counsel and security professionals against the actual deployment and contracts.*
