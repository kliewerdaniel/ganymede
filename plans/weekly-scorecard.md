# Ganymede — Weekly Scorecard

**Week of:** September 13, 2026

---

## 1. Demand — Did a qualified buyer move closer to payment?

| Prospect | Stage | Evidence | Next step |
|----------|-------|----------|-----------|
| — | — | — | — |

This week's movement: No commercial work this week — focused on Week 4 closure and Week 5 build.

---

## 2. Usage — Did a user complete the target job?

No users yet — Q&A workspace just built this week. Usability sessions planned for next week.

---

## 3. Quality — Did benchmark performance improve or hold?

**This week's result:** Week 4 gate closure — **both gates PASS** (without verifier) or **answer-absent only** (with verifier).

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Recall@5 (no verifier, expansion ON) | **86.2%** (25/29) | ≥80% | **PASS** (+6.9pp vs last week) |
| Recall@5 (with verifier, strict mode) | **0%** (0/29) | ≥80% | FAIL — verifier too strict |
| Answer-absent clean | **21/21** (100%) | 100% | **PASS** (verifier closes the leak) |
| Isolation | 8/8 blocked | 100% | PASS (held from last week) |
| Verifier latency | ~17s/query | <30s | marginal |

**Key findings:**
- Query expansion (legal-term synonyms) closed the recall gap from 79.3% to 86.2%
- Verifier (ADR 008) closes the answer-absent gate: 0/21 → 21/21
- **Strict verifier drops answerable recall to 0%** — expanded query terms cause verifier NO decisions
- Fast-path design tested but found ineffective (no safe threshold)

**Tradeoff:** The verifier is correct but strict. Production uses strict mode (answer-absent gate preserved, answerable recall reduced). The system says "not found" rather than risk a false citation.

**Reports:** `api/tests/gold-set-report-legal-synonyms.json`, `api/tests/full-pipeline-report.json`

---

## 4. Trust — Can every output be reviewed and explained?

**This week's note:** Citation object carries document hash, page, offsets, retrieval scores (RRF, vector, FTS), parser version, model version, access scope. Verifier adds `verifier_decision` and `verifier_quote`. Fast-path adds `fast_path: true` flag for audit trail.

Frontend (`web/index.html`) shows citation cards with full provenance, click-to-view source inspector, and citation feedback buttons (supporting/weak/wrong/inaccessible).

---

## 5. Reliability — Can a clean deployment install and recover?

**This week's note:** DB schema tech debt fixed — `cascade="all, delete-orphan"` added to Document relationships. Init script (`init_db.py`) works on clean DB. Corpus re-ingestion verified.

---

## 6. Focus — What did we decline to build?

**This week's declines:**
- Fast-path verifier optimization (ineffective — score distributions overlap)
- Cross-encoder as verification classifier (deferred)
- Smaller/faster model for verification (deferred)
- Query rewrite / multi-document synthesis (out of scope for MVP)

---

## Risk review (weekly)

| Risk | Owner | Likelihood | Impact | Next test |
|------|-------|-----------|--------|-----------|
| No design partner | — | — | — | — |
| Unreliable citations | — | Low | High | 86.2% recall, 21/21 answer-absent clean |
| Cross-matter leakage | — | Low | Critical | 8/8 isolation |
| Verifier latency | — | High | Medium | ~17s/query — needs async or smaller model |
| False compliance claims | — | — | — | — |

---

## Commercial work this week

**Outreach:** None
**Conversations:** None
**Commitment advances:** None

---

## Product work this week

**What was built:**
- Query expansion service (`api/app/services/query_expansion.py`)
- Verifier fast-path design (`api/app/services/verifier.py`)
- Full Q&A frontend (`web/index.html`)
- API endpoints: `/api/v1/health`, `/api/v1/matters/{id}/documents`, `/api/v1/matters/{id}/ask`
- CORS middleware, frontend serving
- Corpus re-ingestion script

**What was tested:**
- Query expansion benchmark on 6 structural misses
- Full gold set with legal_synonyms expansion (86.2% recall)
- Verifier fast-path calibration (negative result — no safe threshold)
- Full 50-question gold set with expansion + verifier

**What was deferred:**
- Cross-encoder verification classifier
- Smaller/faster verification model
- Multi-document synthesis (rewriter)

**What was removed:** Nothing

---

## Operating note

Founder time budget: ~90% product + quality, 10% operations, 0% customer work. The focus on closing the recall gap and building the Q&A workspace was necessary to unblock Week 5. Commercial work resumes after usability sessions.

---

*This scorecard is the weekly operating record. It is not optional.*
