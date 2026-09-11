# Ganymede — Data Flow

**Status:** Draft
**Date:** September 2026
**Frozen:** Week 2 (after corpus and access model are defined)
**Review trigger:** Before pilot; after any material architectural change; after any security incident.

---

## Purpose

Describe what travels where, in what form, under what terms — from file upload to exported artifact. Annotate every stage with the audit events it emits and the trust boundary it sits inside. Cross-check against the threat model: every threat category must be visible in the flow or explicitly marked out of scope for the MVP.

---

## High-level flow

```
Upload → Parse / OCR → Fingerprint → Index → Retrieval
                                              ↓
                                   Prompt assembly → Local inference → Citation objects
                                                              ↓
                                                    Human approval → Export
```

Every stage emits audit events. Every stage that touches matter content sits inside the tenant and matter boundaries. Retrieval filters by matter scope at the database query, before any prompt is assembled.

---

## Mermaid diagram

```mermaid
flowchart TD
    U[Upload<br/>PDF / DOCX / TXT / scanned PDF] --> P
    P[Parse / OCR<br/>PyMuPDF · docx · Tesseract<br/>page segmentation] --> F
    F[Fingerprint<br/>sha256 · page offsets · parser version] --> I
    I[Index<br/>PostgreSQL FTS + pgvector<br/>metadata filters · matter scope] --> R
    R[Retrieval<br/>DB query filtered by matter scope<br/>FTS + vector fusion + rerank] --> PA
    PA[Prompt assembly<br/>retrieved passages as evidence only<br/>no matter content in prompt text by default] --> LI
    LI[Local inference<br/>Ollama (adapter boundary for vLLM)<br/>answer constrained to passages] --> C
    C[Citation objects<br/>document hash · page · offsets · quoted text<br/>parser version · retrieval scores · model/version · access scope] --> HA
    HA[Human approval<br/>review citations · mark feedback<br/>approve / reject / edit] --> E
    E[Export<br/>AI-assisted draft label · timestamp · source list<br/>approval binds artifact version + source set + user + time + policy decision]

    U -.-> AE1[Audit: file upload · MIME check · size check · AV scan]
    P -.-> AE2[Audit: parse start · parse complete · page count · parser version · OCR status · failure]
    F -.-> AE3[Audit: content hash · fingerprint · duplicate detection]
    I -.-> AE4[Audit: index event · matter scope · embedding job · content hash cache]
    R -.-> AE5[Audit: retrieval event · matter scope · user · timestamp · retrieval scores<br/>prompt text minimized / excluded by default]
    PA -.-> AE6[Audit: prompt-assembly event · evidence set · matter scope]
    LI -.-> AE7[Audit: generation event · model · model version · prompt version<br/>model output treated as untrusted data]
    C -.-> AE8[Audit: citation object created · document hash · page · offsets · quoted text]
    HA -.-> AE9[Audit: citation feedback · artifact edit · approval · rejection · approval invalidation on edit]
    E -.-> AE10[Audit: export event · artifact version · source set · approver · timestamp · policy decision]

    classDef boundary fill:#f5f5f5,stroke:#333,stroke-width:1px;
    class U,P,F,I,R,PA,LI,C,HA,E boundary;
```

---

## Stage-by-stage detail

### Stage 0 — Upload

**What enters:** PDF, DOCX, TXT, scanned PDF. Encrypted file volume at rest.

**Checks before any parsing:**
- MIME validation.
- Size limits.
- Antivirus scan.

**Failure behavior:** A failed upload does not create a partially ingested document. A corrupt or malformed file is rejected at the upload stage or fails visibly during parsing — never silently produces an empty searchable document.

**Audit events:** file upload, MIME check, size check, antivirus result.

**Trust boundaries:** Egress (no data leaves the deployment), Matter (file is scoped to a matter on upload), Model (no model involved yet).

**Threat-model coverage:** threat 7 (DoS/resource exhaustion), threat 8 (malicious/malformed file).

---

### Stage 1 — Parse / OCR

**What happens:** PyMuPDF for PDF text and structure; python-docx for DOCX; plain text for TXT; OCRmyPDF / Tesseract for scanned PDFs. Page segmentation: every extracted span points back to the original document and page.

**Output:** page-level text and structure, with provenance.

**Failure behavior:** A failed OCR job does not silently create an empty searchable document. Partial ingestion stays visibly incomplete. Parser version is recorded per document.

**Audit events:** parse start, parse complete, page count, parser version, OCR status, failure reason.

**Trust boundaries:** Evidence (page-level provenance), Egress (no data leaves).

**Threat-model coverage:** threat 8 (malformed file — parser failure behavior), threat 4 (unsupported output — provenance supports citation verification).

---

### Stage 2 — Fingerprint

**What happens:** Content hashing (sha256) and duplicate detection. The original file and a normalized representation are preserved.

**Output:** content hash, duplicate flag, parser version, page offsets.

**Audit events:** content hash, fingerprint, duplicate detection.

**Trust boundaries:** Evidence (document hash in every citation object), Egress.

**Threat-model coverage:** threat 4 (citation integrity), threat 10 (data loss — fingerprint supports integrity checking).

---

### Stage 3 — Index

**What happens:** PostgreSQL full-text search + pgvector embeddings. Metadata filters: matter scope, document type, page, date, parser version. Embeddings batched and cached by content hash.

**Output:** searchable index scoped by matter.

**Matter scope:** The index is scoped by matter, or the query filters by matter before results are returned. Either way, the retrieval query cannot return passages from a matter the user is not authorized to access.

**Audit events:** index event, matter scope, embedding job, content-hash cache hit/miss.

**Trust boundaries:** Tenant (no shared index between customers), Matter (scope enforced in index/retrieval), Egress, Model (index is data, not model output).

**Threat-model coverage:** threat 2 (cross-matter leakage), threat 7 (resource exhaustion — batch embeddings, cache by content hash).

---

### Stage 4 — Retrieval

**What happens:** Hybrid retrieval — PostgreSQL FTS + pgvector fusion, plus reranking. Authorization decision and matter scope are passed to the retrieval service as scoped identifiers. The retrieval query filters by matter scope at the database level before any prompt is assembled.

**Output:** retrieved passages with document name, page, offsets, and retrieval scores.

**Critical rule:** Retrieved passages are evidence, not instructions. They are rendered first; the answer is generated constrained to those passages.

**Audit events:** retrieval event, matter scope, user, timestamp, retrieval scores. Prompt text minimized or excluded by default.

**Trust boundaries:** Matter (authorization filters retrieval before any prompt is assembled), Evidence (passages + scores preserved), Export (no export yet), Model (model output is untrusted).

**Threat-model coverage:** threat 1 (confidentiality breach — matter scope in retrieval), threat 2 (cross-matter leakage), threat 5 (prompt injection — passages are evidence, not instructions), threat 9 (access control bypass — scope enforced in the query).

---

### Stage 5 — Prompt assembly

**What happens:** Retrieved passages are assembled into the evidence context for the prompt. The prompt is assembled from the scoped retrieval results, not from an unconstrained user request. Prompt text is minimized in logs.

**Output:** evidence-constrained prompt.

**Audit events:** prompt-assembly event, evidence set, matter scope.

**Trust boundaries:** Evidence, Matter, Egress (prompt text minimized in logs; matter content not in operational logs by default).

**Threat-model coverage:** threat 5 (prompt injection — quoted-source boundaries), threat 4 (unsupported output — answer constrained to passages).

---

### Stage 6 — Local inference

**What happens:** The local model runtime (Ollama initially; adapter boundary for vLLM or another runtime) generates an answer constrained to the retrieved passages. Model, quantization, and prompt version are recorded.

**Output:** generated answer text, with model/version metadata.

**Critical rule:** Model output is untrusted data. It cannot grant itself tools or permissions. The model proposes; the typed policy and a human decide whether content can leave the workspace.

**Audit events:** generation event, model, model version, prompt version.

**Trust boundaries:** Model (output untrusted; cannot grant tools/permissions), Evidence (answer must cite evidence), Egress (no inference traffic leaves unless customer enables it).

**Threat-model coverage:** threat 3 (unauthorized legal content/overclaim — model output is not authority), threat 4 (unsupported output), threat 5 (prompt injection — model output cannot override system), threat 6 (poisoned citations — model cannot invent a citation; it must ground in the evidence set).

---

### Stage 7 — Citation objects

**What happens:** Every factual claim is tied to a citation object preserving: matter_id, document_id, sha256, page, start_offset, end_offset, quoted_text, parser_version, retrieval_scores, model/version metadata, access_scope.

**Output:** answer with claim + citation IDs + quoted passages + uncertainty + missing-information note.

**Critical rule:** If the system lacks evidence, it says "not found in the approved matter sources." It may suggest a better query or identify missing documents, but it must not fill the gap from model memory.

**Audit events:** citation object created, document hash, page, offsets, quoted text.

**Trust boundaries:** Evidence (this is the boundary's structural expression), Export (citations are the review chain for any export).

**Threat-model coverage:** threat 4 (unsupported output), threat 6 (poisoned citations — actual quoted text and offsets preserved).

---

### Stage 8 — Human approval

**What happens:** The user inspects citations in context (opens the exact page, highlights the passage), marks citation feedback (supporting / weak / wrong / inaccessible), reviews the draft artifact, and approves or rejects it. Editing after approval invalidates the approval.

**Output:** approved artifact version, with source set, approver, timestamp, and policy decision recorded.

**Audit events:** citation feedback, artifact edit, approval, rejection, approval invalidation on edit.

**Trust boundaries:** Export (approval is the gate), Evidence (human verification of citations), Model (model proposes; human decides).

**Threat-model coverage:** threat 4 (unsupported output — human review), threat 6 (poisoned citations — human feedback), threat 9 (access control bypass — approval is a controlled action), threat 11 (audit record compromise — approval binding).

---

### Stage 9 — Export

**What happens:** The approved artifact is exported (DOCX/PDF) with an AI-assisted draft label, a generated timestamp, and a source list. The firm controls whether the label is retained in downstream work product. Export requires approval; the exported artifact reconstructs its source and approval lineage.

**Output:** exported artifact with label, timestamp, source list, approval lineage.

**Audit events:** export event, artifact version, source set, approver, timestamp, policy decision.

**Trust boundaries:** Export (this is the boundary's structural expression), Evidence (source list + lineage), Egress (export is a deliberate human action, not telemetry).

**Threat-model coverage:** threat 1 (confidentiality breach — export is controlled), threat 3 (unauthorized legal content — export carries AI-draft label; no claim of legal accuracy), threat 11 (audit record compromise — exported artifact reconstructs lineage).

---

## Audit event summary

| Stage | Representative audit events |
|-------|-----------------------------|
| Upload | file upload, MIME check, size check, AV scan |
| Parse/OCR | parse start, parse complete, page count, parser version, OCR status, failure |
| Fingerprint | content hash, fingerprint, duplicate detection |
| Index | index event, matter scope, embedding job, content-hash cache |
| Retrieval | retrieval event, matter scope, user, timestamp, retrieval scores (prompt text minimized/excluded) |
| Prompt assembly | prompt-assembly event, evidence set, matter scope |
| Local inference | generation event, model, model version, prompt version |
| Citation objects | citation object created, document hash, page, offsets, quoted text |
| Human approval | citation feedback, artifact edit, approval, rejection, approval invalidation on edit |
| Export | export event, artifact version, source set, approver, timestamp, policy decision |

Operational metrics are separated from matter content. Diagnostic bundles redact matter content and secrets by default.

---

## Threat-model cross-check (explicit)

| Threat model category | Where addressed in this flow | If not fully addressed here |
|------------------------|------------------------------|-----------------------------|
| 1. Confidentiality breach | Upload (encrypted volume), Index (tenant scope), Retrieval (matter scope in query), Export (controlled), IT operator access (redacted, logged) | Full operator-access policy is in the access matrix, to be finalized in Week 2. |
| 2. Cross-matter leakage | Index (matter scope), Retrieval (matter scope as DB filter) | Matter scope enforcement mechanism is in the access matrix. |
| 3. Unauthorized legal content / overclaim | Non-goals, quality rule, marketing discipline, counsel review | Not a flow-control issue; handled by product contract, non-goals, and the quality rule. |
| 4. Unsupported or incorrect output | Retrieval (passages as evidence), Prompt assembly (evidence-constrained), Local inference (answer constrained to passages), Citation objects (evidence preserved), Human approval (review) | Gold-set benchmark and blind review are the measurement; defined in benchmark-design.md. |
| 5. Prompt injection inside documents | Retrieval (passages as evidence), Prompt assembly (quoted-source boundaries), Local inference (model output untrusted), Model boundary | Prompt-injection filtering details are implementation; the boundary is defined here and in trust-boundaries.md. |
| 6. Poisoned citations | Citation objects (actual quoted text + offsets), Human approval (feedback channel) | Human feedback UI and review workflow are implementation; the boundary is defined here. |
| 7. Denial-of-service / resource exhaustion | Upload (size/MIME/AV limits), Index (batch embeddings, cache by content hash) | Resource-limit implementation is in the operations docs (Phase 5). |
| 8. Malicious or malformed file | Upload (MIME/AV/size), Parse/OCR (failure returns visible error, not empty document; partial ingestion visibly incomplete) | Parser robustness is implementation; the failure behavior is defined here. |
| 9. Access control bypass | Retrieval (matter scope in DB query), Artifacts (export requires approval), User management (session timeout/revocation, role enforcement), denials fail closed | Full matrix is in access-matrix.md. |
| 10. Data loss / unrecoverable state | Fingerprint (integrity), Export (lineage), Backup/restore (operational; Phase 5) | Backup/restore mechanics are in the operations docs (Phase 5). |
| 11. Audit record compromise | Every stage emits audit events; audit ledger append-only + hash-chain; approval binding; edit-after-approval invalidates | Audit schema is implementation; the event set is defined here. |

---

## Out of scope for the MVP (explicitly)

- Multi-tenant cross-customer flows (there is no cross-customer store; trust boundary 4).
- External action flows (filing, sending, external API calls on the model's initiative) — not present in the MVP; trust boundary 1 and non-goals.
- Case-law research flows (not in the product; non-goals).
- Any flow that sends matter content to a public model API (trust boundary 3; ADR 001).

---

*This document is a draft. It will be updated and diagram-checked in Week 2 after the corpus and access model are frozen.*
