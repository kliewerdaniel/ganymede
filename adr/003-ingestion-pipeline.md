# ADR 003: Ingestion pipeline — synchronous, in-process

**Status:** Accepted
**Date:** September 2026
**Deciders:** Daniel Kliewer (founder)
**Review trigger:** Before Week 4 (hybrid retrieval) or when async job queues are proposed.

---

## Context

The Week 3 ingestion pipeline must parse documents, record provenance, and store results in PostgreSQL. The question is whether to use a synchronous in-process approach or an asynchronous job queue (e.g., Celery, RQ, or a custom worker).

The requirements are:
- Ingest the full frozen corpus (36 files) reliably.
- Record provenance per page (document, page, offsets, parser version).
- Handle failures visibly (corrupt files → visible failure, not silent empty doc).
- Detect duplicates by content hash.
- Keep the pipeline simple enough for a single developer to debug and extend.

---

## Decision

Use a **synchronous, in-process ingestion pipeline** for Week 3.

The `ingest_document()` function:
1. Validates MIME type and file size.
2. Computes SHA-256 content hash.
3. Checks for duplicates (same hash in the same matter).
4. Routes the file to the appropriate parser (PyMuPDF, python-docx, Tesseract OCR, plain text).
5. Records pages with provenance (document_id, page_number, text, start_offset, end_offset, parser_version).
6. On failure, marks the document as failed with a visible error message — never silently creates an empty searchable document.

The pipeline runs in the same process as the FastAPI application. No message broker, no worker process, no job queue.

---

## Consequences

**Enables:**
- Simplicity: one code path, one process, one log stream.
- Easy debugging: trace upload → parse → provenance in one stack trace.
- Fast iteration: add a parser, run the corpus, see results immediately.
- Meets the Week 3 requirement of 36-file ingestion with provenance.

**Costs:**
- Ingestion blocks the request thread. For large files or OCR-heavy workloads, this could be slow. For Week 3 (36 small test files), this is acceptable.
- No parallelism. Files are processed one at a time. For the pilot corpus (hundreds of files), this will need to change.
- No retry mechanism. If parsing fails, the document is marked failed. Retry is a manual re-upload.

**Hardens:**
- Failure visibility: the `ingestion_status` column and `ingestion_error` column make failures queryable.
- The "never silently empty" rule: the parser validates page count > 0; 0 pages = failure.

---

## Alternatives considered

### Celery / Redis job queue

Rejected for Week 3. Celery adds infrastructure (Redis broker, worker processes, flower monitoring) that is not justified for 36 test files. Revisit in Week 4 if the pilot corpus is large enough to justify async processing.

### Thread pool / asyncio.to_thread

Rejected for Week 3. PyMuPDF and Tesseract release the GIL, so thread-based parallelism could work, but it adds complexity to provenance tracking and failure handling. Revisit if ingestion latency becomes a bottleneck.

### Separate worker process with a database-backed job table

Rejected for Week 3. The `ingestion_jobs` table is created in the schema for future use, but the worker process is deferred. The table provides a migration path: when we add a worker, it reads from `ingestion_jobs` and updates `documents.ingestion_status`.

---

## References

- ADR 001 (single-tenant deployment)
- ADR 002 (monorepo layout)
- DEVELOPMENT.md (failure behavior: "A failed OCR job does not silently create an empty searchable document")
- plans/development-plan.md (Week 3 — Ingestion with provenance)

---

*This ADR may be superseded in Week 4 if async job processing becomes necessary for retrieval or embedding workloads.*
