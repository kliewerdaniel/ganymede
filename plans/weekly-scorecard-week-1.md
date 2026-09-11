# Ganymede — Week 1 Scorecard

**Status:** Initialized
**Week of:** Week 1 (starting September 11, 2026)
**Review:** Friday of Week 1.

---

The weekly scorecard is the founder's operating rhythm. It answers six questions every week and records the evidence. It is not a status update for an audience; it is the decision instrument for the founder.

---

## Week of: Week 1 (starting September 11, 2026)

**Founder time split this week:** product + quality / customer work / operations.
**Cash position:** —.

---

## 1. Demand — Did a qualified buyer move closer to payment?

**Question:** Did a qualified buyer move closer to payment this week?

**Evidence:**

| Prospect | Stage | Evidence | Next step |
|----------|-------|----------|-----------|
| Kemp Smith LLP | qualified contact | outreach draft ready | send draft; book call if reply |
| Wright & Greenhill, P.C. | qualified contact | outreach draft ready | send draft; book call if reply |
| Ratliff Law Firm PLLC | qualified contact | outreach draft ready | send draft; book call if reply |
| Thompson Coe (Austin office) | qualified contact | outreach draft ready | send draft; book call if reply |
| Dunham LLP | qualified contact | outreach draft ready | send draft; book call if reply |
| Shaw Cowart Attorneys at Law LLP | qualified contact | outreach draft ready | send draft; book call if reply |
| Gottfried Alexander Law Firm | qualified contact | outreach draft ready | send draft; book call if reply |
| Sheehan Law, PLLC | qualified contact | outreach draft ready | send draft; book call if reply |

**Stage definitions:**
- Qualified contact (10/week target): partner, operations leader, or legal technologist in target profile.
- Live conversation (3/week target): workflow-first call, no generic pitch.
- Commitment advance (1/week target): corpus review, technical meeting, proposal, or signature.

**Buyer evidence ladder:**
- Weak: "Interesting," newsletter signup, social reaction, feature suggestion.
- Useful: introduces IT, offers a corpus, schedules reviewers, shares current cost.
- Strong: reviews terms, names budget, signs pilot, or pays.

**This week's movement:** outreach drafts prepared for top 8; no emails sent yet. Movement to "live conversation" requires sending the drafts and getting replies.

---

## 2. Usage — Did a user complete the target job?

**Question:** Did a user complete the target job this week?

**Evidence:** task event and observation notes.

**If no users yet:** not applicable; the question is whether the prototype or demo enabled a task-based conversation.

**This week's observation:** no users yet; preparation phase. The "usage" question this week is whether the documentation and prospect research are positioned to support a task-based conversation when a prospect replies.

---

## 3. Quality — Did benchmark performance improve or hold?

**Question:** Did benchmark performance improve or hold this week?

**Evidence:** versioned evaluation report or note that no benchmark run occurred.

**If no benchmark yet:** note the nearest milestone (corpus frozen, gold set written, first benchmark run scheduled).

**This week's result:** gold-set draft written (`docs/specification/gold-set-draft.md`, status Draft, 50 questions, pending corpus freeze). No benchmark run yet; nearest milestone is corpus selection and freeze.

---

## 4. Trust — Can every output be reviewed and explained?

**Question:** Can every output be reviewed and explained this week?

**Evidence:** citations, lineage, approvals, audit — or note that this is prospective.

**This week's note:** prospective. Trust boundaries are documented (`docs/architecture/trust-boundaries.md`, accepted). Access matrix completed (`docs/security/access-matrix.md`), data-flow diagram created (`docs/architecture/data-flow.md`) with per-stage audit annotations and threat-model cross-check. No running system yet.

---

## 5. Reliability — Can a clean deployment install and recover?

**Question:** Can a clean deployment install and recover this week?

**Evidence:** automated test and restore log — or note that this is prospective.

**This week's note:** prospective. Deployment model is set by ADR 001 (single-tenant, customer-controlled, Docker Compose). Operations docs are Phase 5 (Weeks 9-10). No running system yet.

---

## 6. Focus — What did we decline to build?

**Question:** What did we decline to build this week?

**Evidence:** decision log entries and deferred backlog.

**This week's declines:**
- No implementation code. Documentation phase is still in effect.
- No `docs/product/` or `docs/operations/` directories created. README corrected to match the real tree; product/artifact contracts live in `docs/specification/`; operations material arrives in Phase 5.
- No corpus chosen. Corpus recommendation logged as Proposed, pending Daniel's sign-off.
- No emails sent. Outreach drafts prepared; Daniel sends them.
- No legal conclusion that any public document set is a safe test corpus. Recommendation only.

---

## Risk review (weekly)

Name one owner per risk. Record likelihood, impact, and next test.

**Open risks:**

| Risk | Owner | Likelihood | Impact | Next test |
|------|-------|-----------|--------|-----------|
| No design partner | Daniel | — | — | 8 outreach emails sent; replies tracked |
| Unreliable citations | — | — | — | gold set drafted; corpus freeze next |
| Cross-matter leakage | — | — | — | access matrix + data-flow completed; retrieval scope test in benchmark |
| Installation burden | — | — | — | ADR 001 sets deployment model; operations docs Phase 5 |
| Support overload | — | — | — | one workflow, one deployment profile; paid scope |
| Unauthorized legal content | — | — | — | non-goals + quality rule documented; counsel review before live data |
| Model dependency | — | — | — | adapter boundary in ADR 001; benchmark versioned |
| Competitor compression | — | — | — | differentiate on evidence + workflow; monitor |
| False compliance claims | — | — | — | marketing discipline in non-goals; counsel review before claims |

**New risks this week:** none added. Corpus choice risk is tracked under "No design partner" until a corpus is selected; an unworkable corpus choice would slow the benchmark and the pilot.

**Escalations this week:** none. Any suspected confidentiality breach, cross-matter disclosure, credential exposure, corrupted audit record, or unrecoverable data loss would pause the pilot. Preserve evidence, notify the designated customer contact under the agreed process, and resume only after review.

---

## Commercial work this week

**Outreach:** 8 drafts prepared; 0 sent. Top 8 prospects staged at qualified-contact stage.
**Conversations:** 0.
**Commitment advances:** 0.
**Technical piece (if any):** —.

**Outreach targets (top 8):**
1. Kemp Smith LLP
2. Wright & Greenhill, P.C.
3. Ratliff Law Firm PLLC
4. Thompson Coe (Austin office)
5. Dunham LLP
6. Shaw Cowart Attorneys at Law LLP
7. Gottfried Alexander Law Firm
8. Sheehan Law, PLLC

---

## Product work this week

**What was built:** nothing (documentation phase).
**What was specified:** access matrix completed; data-flow diagram created; gold-set draft written; README structure corrected; corpus recommendation logged.
**What was tested:** nothing (no running system).
**What was deferred:** corpus selection, implementation code, operations docs, prospect outreach sending.

---

## Operating note

Founder time budget: 60% product + quality, 25% customer work, 15% operations. If the split drifts materially for two weeks in a row, note why and what corrects it.

---

*This scorecard is the weekly operating record. It is not optional. A week without a scorecard is a week without evidence.*
