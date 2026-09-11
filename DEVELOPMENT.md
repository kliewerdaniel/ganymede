# Ganymede — Development Conventions

## Language and stack (planned, not yet implemented)

| Layer | Planned choice | Notes |
|-------|---------------|-------|
| Web | Next.js / React / TypeScript | Founder leverage and fast review UX |
| API | FastAPI / Python | Typed AI and document pipeline |
| Data | PostgreSQL + pgvector | One operable store for MVP; FTS + vectors |
| Parsing | PyMuPDF, python-docx, OCRmyPDF/Tesseract | Page-aware provenance |
| Inference | Ollama initially | Adapter boundary kept for vLLM or other local runtime |
| Delivery | Docker Compose | Apprepable for first isolated installs |

These are placeholders pending Week 2 specification freeze. They may change.

## Architectural rules

- Authorization filters retrieval **in the database query**, never by prompt instruction.
- Every extracted span must point back to the original document and page.
- Model output is untrusted data. It cannot grant itself tools or permissions.
- No feature without an observed task. No connector before multiple paying customers demand it. No model-driven external action in the initial product.

## ADR discipline

Every material technical decision gets an ADR in `adr/` before implementation. The ADR must state:
- Title and status (Proposed / Accepted / Deprecated / Superseded)
- Context: what is being decided and why now
- Decision: what we are doing
- Consequences: what this enables and what it costs
- Alternatives considered: brief

## Benchmark-first

The benchmark is part of the product. A frozen synthetic or authorized test matter is established in Week 2. Every subsequent release runs against the same questions, citations, access-control attacks, and operational checks.

See [Benchmark Design](docs/specification/benchmark-design.md).

## Citation object (planned schema)

```json
{
  "matter_id": "...",
  "document_id": "...",
  "sha256": "...",
  "page": 1,
  "start_offset": 0,
  "end_offset": 0,
  "quoted_text": "...",
  "parser_version": "...",
  "retrieval_scores": {},
  "access_scope": "..."
}
```

This schema is provisional. It will be frozen in the specification.

## Failure behavior (must hold in implementation)

- Partial ingestion stays visibly incomplete.
- A failed OCR job does not silently create an empty searchable document.
- Deleting a file removes it from retrieval and records a deletion event.
- If the system lacks evidence, it says "not found in the approved matter sources."

## Test categories (planned)

- Parsing tests: supported file types, corrupt files, duplicates, rotated pages, tables
- Retrieval tests: Recall@5, exact-name search, dates, negation, answer-absent, cross-matter isolation
- Citation tests: every claim cites evidence; unsupported claims below threshold
- Security tests: IDOR, guessed document IDs, stale sessions, revoked users, export permission, prompt injection in documents, poisoned citations
- Operational tests: fresh install, restore, backup, update, rollback

## Definition of done (feature level)

A feature is done when it has: typed contract, tests, permission checks, failure state, observable events, and user-facing limits.

## Definition of done (release level)

A release is done when: benchmark passes, image signed, migration tested, backup restored, runbook updated.

## Source of truth

The specification docs in `docs/specification/` are the source of truth for what is being built. The build plan and business plan are context, not the spec. When they conflict, the spec wins after it has been signed off.
