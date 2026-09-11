# ADR 005: Chunking strategy — sliding window with provenance

**Status:** Accepted
**Date:** September 2026
**Deciders:** Daniel Kliewer (founder)
**Review trigger:** Before Week 5 (Q&A workspace) or when chunking parameters are tuned.

---

## Context

The retrieval pipeline needs to split document pages into chunks that can be embedded and searched. The chunking strategy determines:
- How much context each chunk carries (affects retrieval quality).
- How provenance is preserved (affects citation accuracy).
- How many chunks are generated (affects storage and retrieval speed).

---

## Decision

Use a **sliding-window chunker** with these parameters:
- **Chunk size:** 512 characters (not tokens — character count is deterministic and parser-agnostic).
- **Overlap:** 128 characters (25% overlap to avoid splitting facts across chunk boundaries).
- **Provenance per chunk:** document_id, sha256, page_number, start_offset, end_offset, parser_version.

Each chunk records its exact character offsets relative to the page text. When a chunk is retrieved, the citation points to the exact span in the original document.

---

## Consequences

**Enables:**
- Deterministic, reproducible chunking (no tokenizer dependency).
- Full provenance: every chunk traces back to document + page + offsets.
- Overlap reduces the chance of a fact being split across chunks.

**Costs:**
- Character-based chunking is less semantically precise than token-based. For legal documents (prose-heavy), this is acceptable.
- Overlap increases the number of chunks by ~33%, increasing storage and embedding cost.
- Chunks do not respect paragraph or sentence boundaries — a chunk may start mid-sentence.

**Hardens:**
- The citation object schema (frozen in Week 4) includes start_offset and end_offset, which are directly populated from the chunk record.
- Chunk content hash is used to cache embeddings (never re-embed unchanged content).

---

## Alternatives considered

### Token-based chunking (tiktoken / HuggingFace tokenizer)

Rejected for Week 4. Adds a tokenizer dependency and makes chunk boundaries dependent on the tokenizer version. Character-based chunking is deterministic and version-independent. Revisit if token-aligned chunks prove necessary for retrieval quality.

### Paragraph-based chunking

Rejected. Paragraphs in legal documents vary wildly in length (10 characters to 2000+). Short paragraphs would under-utilize the embedding model's context window; long paragraphs would exceed it. A fixed-size window is more predictable.

### Sentence-based chunking

Rejected. Sentence boundary detection (spaCy / NLTK) adds a dependency and can fail on legal text (e.g., "Mr.", "§ 14.3", "U.S.C."). Character-based chunking avoids this.

---

## References

- ADR 001 (single-tenant deployment)
- ADR 003 (ingestion pipeline — pages are the input to chunking)
- DEVELOPMENT.md (citation object schema)
- plans/development-plan.md (Week 4 — Chunker)

---

*This ADR may be superseded if token-based chunking becomes necessary for retrieval quality in Week 5 or later.*
