# Ganymede — Threat Model

**Status:** Draft
**Date:** September 2026
**Frozen:** Week 2 (after corpus and data-flow are defined)
**Review trigger:** Before pilot; after any material architectural change; after any security incident.

---

## Purpose

Define the threats to the deployment, the data, and the trust model — and the controls that address them. This document is a starting point; it must be completed after the data-flow diagram and access matrix are defined in Week 2.

---

## Trust boundaries (non-negotiable)

1. **Export:** Every external artifact requires a deliberate human action and carries an AI-draft label.
2. **Evidence:** Answers preserve document hash, page, offsets, retrieval scores, and model/version metadata.
3. **Egress:** No telemetry or inference traffic leaves the deployment unless the customer enables it.
4. **Tenant:** No shared application database or vector index between customers.
5. **Matter:** Authorization filters retrieval before any prompt is assembled.
6. **Model:** Model output is untrusted data; it cannot grant itself tools or permissions.

---

## Threat categories

### 1. Confidentiality breach

**What it is:** Matter data is disclosed to an unauthorized party — another tenant, another matter, an operator without a legitimate need, or an external system.

**Early signals:**
- Cross-matter retrieval returns content from a matter the user is not authorized to access.
- An operator can access matter content without a logged, justified reason.
- Data leaves the deployment via telemetry, inference, or backup without the customer's knowledge.

**Controls:**
- Database-enforced tenant and matter scope. Never rely on prompt-level instructions alone.
- Default-deny egress.
- Encrypted file volume and managed secrets.
- Operator access limited and logged.
- Diagnostic bundles redact matter content and secrets by default.

**Test:** Cross-matter attack suite. At least 10 cross-matter access attempts. 100% must be blocked.

---

### 2. Cross-matter leakage

**What it is:** Content from one matter is retrievable when the user is working in another matter, even if no explicit cross-matter request was made.

**Early signals:**
- A query in matter A returns a passage from matter B.
- The retrieval query does not filter by matter scope at the database level.

**Controls:**
- Matter scope is a database filter in every retrieval query.
- Vector and full-text indexes are scoped by matter, or the query filters by matter before results are returned.
- Authorization decision is passed to the retrieval service as scoped identifiers, not as an unconstrained user request.

**Test:** Cross-matter isolation tests. Absent evidence in the corpus must produce "not found," not content from another matter.

---

### 3. Unauthorized legal content or overclaim

**What it is:** The product or its sales materials imply legal conclusions, legal accuracy, or compliance that the system does not deliver.

**Early signals:**
- A user asks for case-law research and the system tries to answer from model memory.
- Marketing says "compliant," "secure," or "privilege-safe" without a defined control set and independent evidence.
- A buyer expects the system to practice law.

**Controls:**
- Firm-owned corpus only. No general case-law research in the first release.
- The quality rule: if evidence is absent, say "not found in the approved matter sources."
- Marketing discipline: do not lead with "AI lawyer," "perfect accuracy," or "compliance guaranteed."
- Counsel review of contracts and claims before live client data and before sales materials are finalized.

---

### 4. Unsupported or incorrect output

**What it is:** The system produces a correct-sounding answer that is not supported by the matter corpus, or misrepresents the source.

**Early signals:**
- Correct-sounding claims with no citation in the corpus.
- Citations that point to the wrong passage or page.
- The system filling gaps from model memory.

**Controls:**
- Evidence-first answer contract: every factual claim cites evidence.
- Citation object preserves document hash, page, offsets, and retrieval scores.
- Blind review of outputs against the gold set.
- Thresholds: 90% supported claims; <5% material unsupported claims.

**Test:** 50-question gold set; blind review of 25 outputs.

---

### 5. Prompt injection inside documents

**What it is:** A document in the corpus contains text that, when processed or retrieved, attempts to alter the system's behavior — to disclose other documents, to change the answer, to override instructions.

**Early signals:**
- A document contains instructions that look like system prompts.
- Retrieved passages appear to influence behavior beyond their role as evidence.

**Controls:**
- Quoted-source boundaries: retrieved passages are evidence, not instructions.
- Prompt-injection filtering.
- No hidden tool invocation.
- The model output is untrusted data and cannot grant itself tools or permissions.

**Test:** Prompt-injection test cases embedded in corpus documents.

---

### 6. Poisoned citations

**What it is:** A document or retrieval result causes the system to cite the wrong source, or to cite a source that does not support the claim.

**Early signals:**
- Citations that point to passages that do not contain the quoted text.
- Retrieval scores that over-weight a misleading passage.

**Controls:**
- Citation object preserves the actual quoted text and offsets.
- Human feedback channel: supporting / weak / wrong / inaccessible.
- Review low-rated outputs.

**Test:** Poisoned-citation test cases.

---

### 7. Denial-of-service and resource exhaustion

**What it is:** Large or malformed uploads, repeated expensive queries, or disk exhaustion degrade or disable the deployment.

**Early signals:**
- A large file upload consumes disproportionate resources.
- Repeated queries degrade response time or cause failures.
- Disk fills up.

**Controls:**
- Size and MIME validation on upload.
- Antivirus scanning.
- Resource limits on uploads and queries.
- Backup and capacity planning.

**Test:** DoS upload and disk-exhaustion test cases.

---

### 8. Malicious or malformed file

**What it is:** An uploaded file is malformed, malicious, or in an unsupported format, and the parser misbehaves.

**Early signals:**
- A corrupt PDF causes a parser crash or incorrect extraction.
- A file in an unsupported format is accepted and produces empty or incorrect results.

**Controls:**
- MIME validation.
- Antivirus scanning.
- Size limits.
- Parser failure returns a visible error, not an empty searchable document.
- Partial ingestion stays visibly incomplete.

**Test:** Corrupt files, unsupported formats, malformed PDFs.

---

### 9. Access control bypass

**What it is:** A user accesses a matter, document, or artifact they are not authorized to see, through IDOR, guessed IDs, stale sessions, or revoked-user access.

**Early signals:**
- A user can access another matter's documents by guessing an ID.
- A revoked user's session remains active.
- An export is available without approval.

**Controls:**
- Role-based access and matter membership enforced at the database and API level.
- Session timeout and revocation.
- Export requires approval and carries an AI-draft label.
- Denials fail closed.

**Test:** IDOR, guessed document IDs, stale sessions, revoked users, export permission.

---

### 10. Data loss or unrecoverable state

**What it is:** Matter data is lost or corrupted, or the deployment cannot be restored from backup.

**Early signals:**
- A deletion removes matter data without a record.
- A backup cannot be restored.
- An update corrupts the database or file volume.

**Controls:**
- Deletion records a deletion event and removes the file from retrieval.
- Daily encrypted backup.
- Tested restore on a clean machine.
- Documented update and rollback procedure.

**Test:** Restore drill. Clean-machine install and restore.

---

### 11. Audit record compromise

**What it is:** The audit trail is altered, deleted, or becomes inconsistent with the artifacts it describes.

**Early signals:**
- An audit event is missing or out of order.
- An exported artifact cannot be reconstructed from its audit lineage.
- An approval references an artifact version that no longer exists.

**Controls:**
- Append-only audit ledger.
- Hash-chain of audit events.
- Approval binds to the exact artifact version, source set, user, time, and policy decision.
- Editing after approval invalidates it.

**Test:** Audit completeness: 100% of key events reconciled against the event schema.

---

## Escalation rule

Any suspected confidentiality breach, cross-matter disclosure, credential exposure, corrupted audit record, or unrecoverable data loss pauses the affected deployment. Preserve evidence, notify the designated customer contact under the agreed process, and resume only after review.

---

## Missing: data-flow diagram and access matrix

This threat model is incomplete until:
- The data-flow diagram is defined (what travels where, in what form, under what terms).
- The access matrix is defined (who can access what, under what conditions, with what logging).
- The corpus and its handling terms are defined.

These are Week 2 outputs. The threat model will be updated after they exist.

---

*This document is a starting point for the Week 2 threat model. It must be reviewed by a security professional before any pilot with live data.*
