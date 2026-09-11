# ADR 007: Retrieval fusion and reranker — RRF + local cross-encoder

**Status:** Accepted
**Date:** September 2026
**Deciders:** Daniel Kliewer (founder)
**Review trigger:** Before Week 5 (Q&A workspace) or when fusion weights are tuned.

---

## Context

The retrieval pipeline combines full-text search (FTS) and vector similarity search. The question is how to fuse the two result sets and whether to add a reranker.

---

## Decision

**Fusion:** Reciprocal Rank Fusion (RRF) with equal weights (0.5 FTS, 0.5 vector).

RRF combines two ranked lists by summing reciprocal rank scores:
```
RRF_score(d) = 0.5 / (k + rank_FTS(d)) + 0.5 / (k + rank_vector(d))
```
where k=60 (standard constant). Documents appearing in both lists get a higher combined score.

**Reranker:** Local cross-encoder via Ollama `bge-reranker-base` (or equivalent).

- The reranker takes the top-20 candidates from RRF fusion and re-scores them using cross-attention between the query and each chunk.
- This is more expensive than bi-encoder similarity but more accurate for the final ranking.
- The reranker runs locally via Ollama (no external calls).

---

## Consequences

**Enables:**
- Combines the strengths of FTS (exact keyword match) and vector (semantic similarity).
- RRF is parameter-light (only the fusion weight and k constant).
- Reranker improves precision at the top of the results.

**Costs:**
- Reranker adds latency (cross-attention is slower than bi-encoder).
- Reranker requires Ollama to be running with the reranker model pulled.
- Fusion weights are fixed; tuning requires re-running the gold set.

**Hardens:**
- The citation object includes retrieval_scores (fts_rank, vector_rank, rrf_score, reranker_score) for transparency.

---

## Alternatives considered

### Weighted linear combination of scores

Rejected. FTS and vector scores are on different scales (BM25 vs cosine similarity). RRF is rank-based and avoids scale mismatch.

### Vector-only retrieval

Rejected. FTS is superior for exact keyword matches (names, dates, legal citations). The gold set includes exact-name and date queries where FTS outperforms vector.

### FTS-only retrieval

Rejected. Vector retrieval captures semantic similarity that FTS misses (e.g., "breach of contract" vs "violation of the agreement").

### LLM-based reranker

Rejected. Too slow for interactive use, and the LLM's reasoning is not transparent. A cross-encoder is deterministic and faster.

---

## References

- ADR 001 (single-tenant deployment, local-only inference)
- ADR 005 (chunking strategy — chunks are the unit of retrieval)
- ADR 006 (embedding model — vectors are the input to vector search)
- plans/development-plan.md (Week 4 — PostgreSQL FTS + pgvector fusion, Reranker)

---

*This ADR may be superseded if fusion weights need tuning after gold-set evaluation.*
