# ADR 006: Embedding model — Ollama nomic-embed-text (local-only)

**Status:** Accepted
**Date:** September 2026
**Deciders:** Daniel Kliewer (founder)
**Review trigger:** Before Week 5 (Q&A workspace) or when embedding quality is evaluated against the gold set.

---

## Context

The retrieval pipeline needs an embedding model to convert text chunks into dense vectors for similarity search. The model must be:
- Local-only (no external API calls, per ADR 001 egress rules).
- Recorded with name + version in every embedding (for reproducibility).
- Compatible with pgvector (fixed-dimension vectors).

---

## Decision

Use **Ollama nomic-embed-text** as the default embedding model.

- **Model:** nomic-embed-text (Nomic AI's text embedding model).
- **Dimension:** 768 (fits in pgvector).
- **Context window:** 8192 tokens (more than enough for 512-character chunks).
- **Runtime:** Ollama (local, no external calls).
- **Version recorded:** model name + Ollama model tag (e.g., "nomic-embed-text:latest").

---

## Consequences

**Enables:**
- Local-only inference (no external API calls, no telemetry).
- 768-dimensional vectors (storage-efficient, fast similarity search).
- Ollama is already the planned inference runtime (ADR 001).

**Costs:**
- nomic-embed-text is a general-purpose model, not fine-tuned for legal text. Retrieval quality on legal terminology may be lower than a domain-specific model.
- Ollama must be running and the model must be pulled before embedding jobs can run.
- Embedding generation is CPU/GPU-bound; large corpora will take time.

**Hardens:**
- The `chunk_embeddings` table records model name + version with every embedding.
- Embeddings are cached by content hash (never re-embed unchanged content).

---

## Alternatives considered

### bge-m3 (BAAI General Embedding)

Rejected for Week 4. bge-m3 is a stronger multilingual model (1024 dimensions), but it requires a separate runtime (sentence-transformers / HuggingFace). Ollama is the planned runtime, and nomic-embed-text is available via Ollama. Revisit if retrieval quality on the gold set is below the 80% Recall@5 target.

### MiniLM-class via sentence-transformers

Rejected. sentence-transformers is a separate runtime from Ollama. Keeping all inference in Ollama simplifies the stack. Revisit if a smaller, faster model is needed for the pilot.

### OpenAI text-embedding-3-small

Rejected. External API call violates ADR 001 egress rules. Not acceptable for a single-tenant, customer-controlled deployment.

---

## References

- ADR 001 (single-tenant deployment, local-only inference)
- ADR 003 (ingestion pipeline — embeddings are the next stage after chunking)
- plans/development-plan.md (Week 4 — Embedding jobs)

---

*This ADR may be superseded if a domain-specific embedding model becomes necessary for retrieval quality.*
