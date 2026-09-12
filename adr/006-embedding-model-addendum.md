# ADR 006 Addendum: Embedding model head-to-head — nomic-embed-text retained

**Status:** Supplemental to ADR 006 (Accepted)
**Date:** 2026-09-12
**Trigger:** ADR 006's own revisit trigger fired — Recall@5 below 80% target on the full 28-question gold set.

---

## Context

ADR 006 selected Ollama `nomic-embed-text` (768-dim) as the default embedding model and specified a review trigger: "Before Week 5 (Q&A workspace) or when embedding quality is evaluated against the gold set." That trigger has fired.

---

## Head-to-head measurement

| Model | Recall@5 (28 Q) | Found | Avg latency/query | Dim | Runtime |
|-------|-----------------|-------|-------------------|-----|---------|
| nomic-embed-text (Ollama) | **64.3%** | 18/28 | 86 ms | 768 | Ollama API |
| bge-m3 (sentence-transformers) | 42.9% | 12/28 | 2636 ms | 1024 | Local HF |

**Delta: −21.4 pp Recall@5** for bge-m3 vs nomic-embed-text.

---

## Per-question breakdown

bge-m3 underperforms nomic-embed-text on 10 of 28 questions: Q01, Q04, Q17, Q29, Q32, Q45, Q05, Q09, Q11, Q13. Both models miss on the remaining 8 structural misses (Q05, Q09, Q11, Q13, Q14, Q25, Q33, Q36, Q46, Q49).

The key finding: bge-m3 is not just slower (2636 ms vs 86 ms avg), it is also less accurate on this domain. The larger dimensionality (1024 vs 768) does not translate to better discrimination on legal text.

---

## Decision

**Retain nomic-embed-text as the default embedding model.**

bge-m3 is both slower and less accurate on the frozen gold set. The 21.4 pp Recall@5 gap and 30× latency penalty are decisive.

---

## Consequences

**Enables:**
- Continued use of Ollama as the single inference runtime (ADR 001).
- No new model download or dependency on Hugging Face Hub at runtime.
- 768-dim vectors remain compatible with existing pgvector index.

**Costs:**
- Recall@5 remains below the 80% target (64.3% on full 28-question set).
- The embedding model is not the primary bottleneck — fusion and answer-absent precision are larger gaps.

**Hardens:**
- ADR 006's review trigger is satisfied; the decision is re-affirmed with data.
- Future embedding model changes require a head-to-head on the frozen gold set.

---

## Alternatives considered

### bge-m3 (BAAI)
Rejected. Despite larger context window (8192 tokens) and local inference, the 21.4 pp Recall@5 drop on legal text is decisive.

### Fine-tuned legal embedding model
Deferred. Would require labeled legal data and training infrastructure. Revisit only if retrieval quality blocks pilot conversion after fusion/reranker improvements are exhausted.

---

## References

- ADR 006 (original decision)
- `api/tests/adr-006-head-to-head.json` (raw results)
- `api/tests/test_adr006_head_to_head.py` (measurement script)

---

*This addendum does not supersede ADR 006; it records the triggered review outcome.*
