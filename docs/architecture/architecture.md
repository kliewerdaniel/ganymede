# Ganymede — Architecture

**Status:** Draft
**Date:** September 2026
**Frozen:** Week 2 (after spec and corpus are defined)

---

## Single-tenant stack

Each customer receives an isolated application, database, file volume, model runtime, and audit domain. Authorization scopes retrieval before a prompt is assembled. No model output can grant itself access or permission.

**The trust story is legible because the deployment is one stack, not a distributed system with shared state.**

---

## Layers (planned)

### Interface

- Next.js matter workspace.
- Matter home, document inventory, question workspace, answer history, split-view source inspector.
- Citation drawer. Clicking a citation opens the exact page and highlights the relevant passage.
- Chronology, issue table, memo builder, version history, export (DOCX/PDF).

### Application

- FastAPI with typed request and response schemas.
- Matter creation, file upload, MIME validation, antivirus scanning, content hashing, duplicate detection.
- Parse queue, OCR path, page segmentation, ingestion status.
- Hybrid retrieval: metadata filters, PostgreSQL full-text search, local embeddings, reranking.
- Structured artifact builders: chronology, issue table, memo.
- Audit event recording, artifact versioning, approval binding.
- Authorization decision and scoped identifiers passed to retrieval — not an unconstrained user request.

### Policy gate

- Identity, role, matter membership, session controls.
- Authorization decision filters retrieval before prompt assembly.
- Denials fail closed.
- Export requires approval; approval binds to exact artifact version, source set, user, time, and policy decision.
- Model output is untrusted data; it cannot grant itself tools or permissions.

### Inference

- Local model runtime, initially Ollama, with an adapter boundary for vLLM or another local runtime.
- Prompts, models, parsers, and schemas are versioned.
- Model output is evidence-constrained: render retrieved passages first, then generate an answer constrained to those passages.

---

## Data plane (planned)

### Raw files

- Encrypted file volume.
- Original files preserved alongside normalized representation.

### Parser / OCR

- PyMuPDF for PDF text and structure.
- python-docx for DOCX.
- Plain text for TXT.
- OCRmyPDF / Tesseract for scanned PDFs.
- Page segmentation: every extracted span points back to the original document and page.
- Content hashing and duplicate detection.
- Failed OCR does not silently create an empty searchable document. Partial ingestion stays visibly incomplete.

### Hybrid index

- PostgreSQL full-text search.
- pgvector for embeddings.
- Metadata filters: matter scope, document type, page, date, parser version.
- Reranker on top of FTS/vector fusion.

### Evidence

- Citation objects: matter_id, document_id, sha256, page, start_offset, end_offset, quoted_text, parser_version, retrieval_scores, access_scope.
- Passage and provenance preserved.
- Audit ledger: append-only, hash-chained, exportable.

---

## Data flow (planned, to be diagrammed in Week 2)

1. Files are uploaded to an encrypted volume. MIME, size, and antivirus checks run first.
2. Parser/OCR routing extracts pages and text. Checksums and provenance are recorded.
3. Pages are indexed: full-text and embeddings, scoped by matter.
4. A user asks a question within a matter. The authorization decision and matter scope are passed to retrieval.
5. Retrieval returns passages with document name, page, offsets, and scores.
6. The answer is generated constrained to those passages. Every claim cites evidence.
7. The user inspects passages in context. They can mark citations as supporting, weak, wrong, or inaccessible.
8. Structured artifacts (chronology, issue table, memo) are assembled from reviewed facts and citations.
9. Export requires approval. The exported artifact carries an AI-draft label, a generated timestamp, and a source list.
10. Every action is recorded in the append-only audit ledger.

---

## Design rules

- Use relational structures for entities, dates, issues, and evidence until a real pilot proves a graph engine is needed. Do not introduce Neo4j or a generalized knowledge graph for the MVP.
- Cache parsing and embeddings by content hash.
- Version prompts, models, parsers, and schemas.
- Keep matter content out of diagnostic bundles and operational analytics by default.
- Treat prompt injection inside documents, malformed files, and denial-of-service uploads as normal threat cases.
- Measure every stage separately so slow retrieval is not mistaken for slow inference.

---

## Deployment (planned)

- Docker Compose for a customer-controlled Linux server or private VPC.
- Reverse proxy, TLS, encrypted volume, managed secrets.
- Default-deny outbound network policy.
- Daily encrypted backup. Tested restore on a clean machine.
- Signed release manifest.
- Automated environment validation, migrations, model installation, TLS configuration, administrator bootstrap, backups, updates, and rollback.
- Diagnostic bundle that redacts matter content and secrets by default.

---

## Reuse from the portfolio (concepts, not repos)

- **Knowledge Compiler:** ingestion, provenance, versioned artifacts.
- **MCBot01:** document processing, retrieval, citation UI patterns.
- **Sovereign Agent Fleet:** proposal/authorization split, identity, ledger.
- **Sovereign Agent Stack:** deployment profile and sovereignty audit.
- **SpecGen/workflow:** specification, validation, repeatable release process.

Reuse concepts and tested modules, not entire repositories. Consolidate into one product codebase with one schema, one permission model, and one test suite.

---

*This document is a draft. It will be updated and diagrammed in Week 2 after the spec and corpus are frozen.*
