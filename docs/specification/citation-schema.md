# Ganymede — Frozen Citation Object Schema

**Status:** Frozen — 2026-09-11
**Purpose:** The citation object is the contract between retrieval and the Week 5 Q&A workspace. Every citation returned by the query endpoint conforms to this schema.

---

## Schema

```json
{
  "matter_id": "uuid",
  "document_id": "uuid",
  "sha256": "string (64-char hex)",
  "page": "integer (1-based page number)",
  "start_offset": "integer (character offset within page text)",
  "end_offset": "integer (character offset within page text)",
  "quoted_text": "string (exact text span from the document)",
  "parser_version": "string (e.g., '1.26.5', 'ocr-tesseract-5.5.3')",
  "retrieval_scores": {
    "fts_rank": "float or null",
    "vector_similarity": "float or null",
    "rrf_score": "float",
    "reranker_score": "float or null"
  },
  "access_scope": "string (always 'matter' for Week 4)",
  "model_version": "string (e.g., 'nomic-embed-text:latest')"
}
```

## Provenance chain

```
matter_id → document_id → sha256 (content hash)
                              ↓
                   page + start_offset + end_offset
                              ↓
                        quoted_text (verified against original)
```

## Frozen fields

Once a citation is returned, the following fields are immutable:
- `matter_id`, `document_id`, `sha256` — these identify the source document
- `page`, `start_offset`, `end_offset` — these identify the exact span
- `quoted_text` — this is the exact text from the document
- `parser_version` — this records which parser produced the text

The `retrieval_scores` may vary across retrieval runs (different queries produce different scores), but the provenance fields are stable.

## Matter scope enforcement

Every citation's `matter_id` matches the matter_id in the query. This is enforced at the database query level — the retrieval query filters by `matter_id` before any search is performed. A citation from another matter is impossible by construction (and is tested by the 8 isolation attacks).

## Why this schema

The citation object is designed so that a reviewer can verify any claim in under 20 seconds:
1. Identify the document (sha256 confirms it hasn't been tampered with).
2. Go to the exact page and offsets.
3. Confirm the quoted_text matches the original.
4. Inspect the retrieval scores to understand why this passage was surfaced.
