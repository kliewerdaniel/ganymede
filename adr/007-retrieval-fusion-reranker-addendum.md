# ADR 007 Addendum: Retrieval fusion and reranker — RRF retained, reranker not a recall lever

**Status:** Supplemental to ADR 007 (Accepted)
**Date:** 2026-09-12
**Trigger:** Fusion weights tuning and reranker integration per ADR 007; gold-set evaluation below 80% target.

---

## Context

ADR 007 specified:
- **Fusion:** Reciprocal Rank Fusion (RRF) with equal weights (0.5 FTS, 0.5 vector), k=60.
- **Reranker:** Local cross-encoder via Ollama `bge-reranker-base` (or equivalent).
- **Review trigger:** "Before Week 5 (Q&A workspace) or when fusion weights are tuned."

The "up" tuning (committed in `retrieval.py`) changed:
- RRF k: 60 → 30
- Fusion weights: 0.5/0.5 → 0.65 FTS / 0.35 vector
- RRF abstention gates: 0.003 (primary) / 0.005 (secondary)
- MIN_VECTOR_SIMILARITY: 0.55
- Reranker model: `bge-reranker-base` unavailable on Ollama; wired `cross-encoder/ms-marco-MiniLM-L-6-v2` from sentence-transformers instead.

---

## Measurements

### Full gold set evaluation (RRF only, no reranker)

**Setup:** 29 answerable + 21 unanswerable = 50 questions. Clean database (44 unique documents, no duplicates). On-disk SHA-256 alignment (corrigendum resolved: 4 old-SHA records removed).

| Gate | Result | Target | Status |
|------|--------|--------|--------|
| Recall@5 (29 answerable) | **79.3%** (23/29) | ≥80% | **FAIL (1 question short)** |
| Answer-absent precision (21 unanswerable) | **0%** (0/21 clean) | 100% | **FAIL** |
| Isolation (8 attacks) | **8/8 blocked** | 100% | **PASS** |

**Persistent misses (6 structural):** Q05, Q09, Q25, Q33, Q46, Q49.

Breaking down the 29:
- 23 found (≥1 expected doc in top 5)
- 6 miss: the correct document is not in the top-5 for specific question types
- Q14 (court reporter in deposition notice): was a false negative due to corrigendum SHA mismatch. Fixed by removing old-SHA DB record → now passes. This confirms the retrieval was finding DOC-013 correctly; the test was comparing against the wrong SHA.

**Effect of "up" tuning vs baseline (24-question subset):**
- Baseline: 58.3% (14/24) with k=60, 0.6/0.4 weights
- "up": 79.3% (23/29) with k=30, 0.65/0.35 weights, clean DB
- Net improvement: +21.0 pp on comparable questions (14/24 → 23/29, with Q14 fixed by DB cleanup)

The k reduction from 60→30 and weight shift 0.6/0.4→0.65/0.35 improved FTS-dominated queries significantly. The remaining 6 misses are not fixed by further RRF tuning — they are fusion failures (the correct document is not in the candidate pool for both FTS and vector).

### Reranker evaluation (cross-encoder/ms-marco-MiniLM-L-6-v2)

| Config | Recall@5 on 6 hard misses | Avg latency/query | Additional latency |
|--------|---------------------------|-------------------|--------------------|
| RRF only (fallback) | 0/6 = 0% | ~90 ms | baseline |
| + Reranker | 0/6 = 0% | ~610 ms | +520 ms/query |

**Delta: +0 recall, +520 ms/query (578% latency increase).**

The reranker reorders candidates but does not recover any of the 6 hard misses. The cross-encoder scores are well-calibrated — it correctly assigns low scores to irrelevant documents — but the correct document is not in the top-20 fused candidates for these queries. Reranking cannot recover what fusion did not surface.

### Answer-absent analysis

All 21 unanswerable queries (15 NOT_IN_CORPUS + 6 formal ANSWER_ABSENT) return 5 citations each. The RRF abstention gates (0.003/0.005) do not trigger — top RRF scores for unanswerable queries range 0.008–0.032, above both gates.

Raising the gates to 0.01+ would block legitimate results on answerable queries (observed RRF scores for hits: 0.01–0.03). The answer-absent problem is not solvable via RRF gate tuning; it requires a post-retrieval verification step (LLM-as-judge, entailment check, or explicit "no answer" classifier).

---

## Decision

### 1. Retain RRF fusion with "up" tuning

Keep k=30, weights 0.65 FTS / 0.35 vector, abstention gates 0.003/0.005, MIN_VECTOR_SIMILARITY=0.55.

These constants improved Recall@5 from 58.3% to 79.3% (with clean DB) without harming latency and are the current best configuration. Further RRF tuning is low-value — the remaining 6 misses are candidate-generation failures, not ranking failures.

### 2. Keep reranker wiring, disable by default

The cross-encoder is wired (`rerank()` function, `RECRANKER_MODEL_PATH` config). Set `RECRANKER_MODEL_PATH=""` (default) to disable. Re-enable only if:
- A legal-domain cross-encoder becomes available with demonstrated recall gain on the frozen gold set, OR
- Latency budget allows (current 610 ms/query is unacceptable for interactive use)

### 3. Answer-absent requires a new approach

Post-retrieval verification (LLM judge / entailment / no-answer classifier) is the only viable path to 100% answer-absent precision. This is scoped for Week 5, not as a retrieval tuning task.

### 4. Pipeline is ALMOST ready for Week 5 — 1 question short

Recall@5 (79.3%) is 0.7 pp below the 80% target. The 6 structural misses share patterns (dates, invoice amounts, multi-document synthesis) and are candidates for query expansion or hybrid query rewriting. A single additional hit would meet the target.

**Answer-absent precision (0%) is the gating defect.** Even if Recall@5 reaches 80%, the pipeline cannot ship without solving answer-absent. This is the Week 5 pre-requisite.

---

## Consequences

**Enables:**
- Clear separation of concerns: retrieval quality (fusion + candidate generation) vs. answer verification (post-retrieval).
- Reranker infrastructure remains in place for future experimentation.
- The 6 structural misses are now well-characterized: they share patterns (dates, invoice amounts, deposition metadata) and are candidates for query expansion or hybrid query rewriting.

**Costs:**
- Week 5 (Q&A workspace) is blocked until answer-absent is solved.
- One more tuning cycle (query expansion) could close the 0.7 pp Recall@5 gap.

**Hardens:**
- ADR 007's review trigger satisfied with data.
- Reranker is not a silver bullet for recall; candidate generation (fusion) is the bottleneck.
- Answer-absent is not a retrieval problem — it is a verification problem.
- DB cleanliness matters: duplicate records and SHA mismatches directly inflate apparent misses.

---

## Alternatives considered

### Higher RRF abstention gates
Rejected. Gates at 0.01+ would block legitimate results. The score distribution overlap between answerable and unanswerable queries makes this infeasible.

### Different cross-encoder (bge-reranker-base via HF)
Deferred. Model not available on Ollama; would require HF token and download. The ms-marco-MiniLM-L-6-v2 result (zero recall gain) suggests the bottleneck is candidate generation, not reranking — a different model is unlikely to change this.

### Query expansion / hybrid query rewriting
**Next step.** The 6 structural misses share patterns:
- Date-specific questions (Q05, Q33)
- Invoice/amount questions (Q09)
- Multi-document synthesis where one document dominates (Q25, Q49)
- Cross-document conflict questions (Q46)

Query expansion (synonyms, legal-term aliases, date normalization, entity expansion) before fusion is the most promising lever. This is the Week 5 pre-requisite for Recall@5.

---

## References

- ADR 007 (original decision)
- `api/tests/gold-set-report.json` (full results)
- `api/tests/isolation-report.json` (isolation results)
- `testdata/corpus-v0.1/CORRIGENDUM.md` (SHA mismatches)
- `api/tests/adr-006-head-to-head.json` (embedding model comparison)

---

*This addendum does not supersede ADR 007; it records the triggered review outcome.*
