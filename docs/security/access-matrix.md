# Ganymede — Access Matrix

**Status:** Draft (completed cells)
**Date:** September 2026
**Frozen:** Week 2 (after identity model and matter boundaries are defined)
**Review trigger:** Before pilot; after any role change; after any access-control incident.

---

## Purpose

Define who can access what, under what conditions, and with what enforcement point and logging. This matrix is the operational expression of trust boundaries 4 (tenant) and 5 (matter) and must remain consistent with them.

**Rule:** Authorization is not a prompt instruction. It is a database filter. The retrieval service receives an authorization decision and scoped identifiers, not an unconstrained user request.

---

## Roles

| Role | Purpose | Default posture |
|------|---------|-----------------|
| **Administrator** | Operate the deployment: manage users, matters, backups, updates, logs. | Least privilege for matter content. Can manage the system without blanket access to matter content. |
| **Attorney** | Practice-role user with matter access. | Access only to assigned matters, with role-based controls within each matter. |
| **Paralegal** | Practice support with matter access, scoped by matter and attorney assignment. | Matter access granted per matter, typically under an attorney's matter membership. No independent export approval. |
| **Read-only reviewer** | Verification-focused user. Can inspect citations, mark feedback, review drafts. Cannot create or export artifacts independently. | Inspect and feedback only. No artifact creation, no export approval, no matter membership changes. |
| **IT operator** | Technical support with limited, logged, redacted-by-default access. | Diagnostic access that redacts matter content by default. Matter-content access only when justified, logged, and within the support process. |

Least privilege by default. A role's access is defined by matter membership and explicit permissions, not by a broad default.

---

## Access matrix

**Legend:** A = Allow (with conditions), D = Deny, A/D = Allow or Deny depending on matter membership / explicit grant. Enforcement point is the system component that enforces the decision, not the UI.

### Matters

| Resource / action | Administrator | Attorney | Paralegal | Read-only reviewer | IT operator |
|-------------------|:------------:|:--------:|:---------:|:------------------:|:-----------:|
| Create matter | A (system-level) | D | D | D | D |
| View matter list (metadata only: name, created, user count) | A | A (assigned matters only) | A (assigned matters only) | D | A (metadata, no content) |
| View matter detail (assigned users, roles, document count, status) | A | A (assigned matters only) | A (assigned matters only) | D | A (metadata, no content) |
| Assign users to matter | A | D | D | D | D |
| Remove user from matter | A | D | D | D | D |
| Delete matter | A (with deletion-event recording; removal from retrieval) | D | D | D | D |

**Enforcement point:** matter-membership table in PostgreSQL, checked at the API and retrieval layers. **Audit:** matter create / update / delete / membership change events.

### Documents

| Resource / action | Administrator | Attorney | Paralegal | Read-only reviewer | IT operator |
|-------------------|:------------:|:--------:|:---------:|:------------------:|:-----------:|
| Upload document to a matter | A (to assigned matters) | A (to assigned matters) | A (to assigned matters, if granted) | D | D |
| View document inventory (list of documents in an assigned matter) | A (assigned matters) | A (assigned matters) | A (assigned matters, if granted) | A (assigned matters, metadata only) | A (metadata, no content) |
| Download original file | A (assigned matters) | A (assigned matters) | A (assigned matters, if granted) | D | D (unless justified, logged, redacted diagnostic path) |
| View document text / extracted content | A (assigned matters) | A (assigned matters) | A (assigned matters, if granted) | A (assigned matters, within retrieval; citation context only) | D (unless justified, logged, redacted diagnostic path) |
| Re-upload / replace document | A (assigned matters) | A (assigned matters) | A (assigned matters, if granted) | D | D |
| Delete document | A (assigned matters, with deletion event) | A (assigned matters, with deletion event) | D | D | D |

**Enforcement point:** document table + matter-membership join in PostgreSQL; file volume access gated by matter scope. **Audit:** upload, parse, delete, download events.

### Prompts / questions

| Resource / action | Administrator | Attorney | Paralegal | Read-only reviewer | IT operator |
|-------------------|:------------:|:--------:|:---------:|:------------------:|:-----------:|
| Submit a question in an assigned matter | A (assigned matters) | A (assigned matters) | A (assigned matters, if granted) | A (assigned matters) | D (unless justified, logged, redacted diagnostic path) |
| View answer history in an assigned matter | A (assigned matters) | A (assigned matters) | A (assigned matters, if granted) | A (assigned matters) | D (unless justified, logged, redacted diagnostic path) |
| Submit a question outside assigned matters | D | D | D | D | D |

**Enforcement point:** retrieval query filters by matter scope from the authorization decision before any prompt is assembled. **Audit:** retrieval events (with matter scope, user, timestamp, retrieval scores; prompt text minimized or excluded by default).

### Artifacts (chronology, issue table, memo)

| Resource / action | Administrator | Attorney | Paralegal | Read-only reviewer | IT operator |
|-------------------|:------------:|:--------:|:---------:|:------------------:|:-----------:|
| Create artifact in an assigned matter | A (assigned matters) | A (assigned matters) | A (assigned matters, if granted) | D | D |
| Edit artifact (pre-approval) | A (assigned matters) | A (assigned matters) | A (assigned matters, if granted) | D | D |
| Approve artifact for export | A (assigned matters) | A (assigned matters) | D | A (reviewer role: approve or reject per artifact review workflow) | D |
| Reject artifact / request edit | D | A (assigned matters) | D | A (reviewer role) | D |
| Export artifact (post-approval) | A (assigned matters, post-approval) | A (assigned matters, post-approval) | D | D (reviewer does not export; approval is separate from export action) | D |
| View artifact version history | A (assigned matters) | A (assigned matters) | A (assigned matters, if granted) | A (assigned matters) | D (unless justified, logged, redacted diagnostic path) |
| Edit artifact after approval | A (assigned matters; invalidates approval) | A (assigned matters; invalidates approval) | D | D | D |

**Enforcement point:** artifact table + approval-binding record. Export action requires an approved artifact version and emits an export event. **Audit:** create, edit, approve, reject, export, version-change events; approval binds to exact artifact version, source set, user, time, policy decision.

### Citations / feedback

| Resource / action | Administrator | Attorney | Paralegal | Read-only reviewer | IT operator |
|-------------------|:------------:|:--------:|:---------:|:------------------:|:-----------:|
| Inspect citation in context (open exact page, highlight passage) | A (assigned matters) | A (assigned matters) | A (assigned matters, if granted) | A (assigned matters) | D (unless justified, logged, redacted diagnostic path) |
| Mark citation as supporting / weak / wrong / inaccessible | A (assigned matters) | A (assigned matters) | A (assigned matters, if granted) | A (assigned matters) | D |

**Enforcement point:** citation-feedback table scoped by matter membership. **Audit:** citation-feedback events.

### Audit record

| Resource / action | Administrator | Attorney | Paralegal | Read-only reviewer | IT operator |
|-------------------|:------------:|:--------:|:---------:|:------------------:|:-----------:|
| View audit record (operational view) | A | D | D | D | A (operational view; redacted of matter content by default) |
| Export audit record | A (with redaction policy applied) | D | D | D | A (with redaction policy applied; no matter content or secrets by default) |

**Enforcement point:** audit ledger is append-only; export applies redaction policy. **Audit:** audit-export events.

### User management

| Resource / action | Administrator | Attorney | Paralegal | Read-only reviewer | IT operator |
|-------------------|:------------:|:--------:|:---------:|:------------------:|:-----------:|
| Create user | A | D | D | D | D |
| Disable / revoke user | A | D | D | D | D |
| Change user role | A | D | D | D | D |
| View user list (metadata: name, role, status, matter memberships) | A | A (own profile + matter membership context) | A (own profile + matter membership context) | A (own profile only) | A (metadata; no secrets) |
| Reset / manage credentials | A | D | D | D | D (within operational policy; logged) |

**Enforcement point:** user table and session store. Revoked users lose access immediately; sessions time out. **Audit:** user create / update / disable / role-change / credential events.

### Deployment config / operational settings

| Resource / action | Administrator | Attorney | Paralegal | Read-only reviewer | IT operator |
|-------------------|:------------:|:--------:|:---------:|:------------------:|:-----------:|
| View health checks / system status | A | A (read-only) | A (read-only) | A (read-only) | A |
| Configure backup | A | D | D | D | A (within operational policy; logged) |
| Trigger backup | A | D | D | D | A (within operational policy; logged) |
| Run restore | A | D | D | D | A (within operational policy; logged; requires administrator authorization) |
| Apply update / rollback | A | D | D | D | D (planned change via administrator action; IT operator may execute under administrator authorization, logged) |
| View logs (operational, redacted) | A | D | D | D | A (operational, redacted of matter content and secrets by default) |
| Access matter content for support | D (no blanket access) | D | D | D | A only when justified, logged, and within the support process; diagnostic bundles redact matter content by default |

**Enforcement point:** deployment configuration store; backup/restore/update actions gated by role and logged. **Audit:** backup, restore, update, rollback, log-access events.

---

## Enforcement summary

- **Tenant boundary (trust boundary 4):** There is no shared application database or vector index between customers. This matrix applies within one customer's isolated deployment. Cross-customer access is not represented because there is no cross-customer store.
- **Matter boundary (trust boundary 5):** Every retrieval query filters by matter scope from the authorization decision. A user's access to a matter is explicit: the user is a member of that matter, with a role. Cross-matter retrieval is prohibited at the database query level, not by prompt instruction.
- **Export boundary (trust boundary 1):** Export requires approval. Approval binds to the exact artifact version, source set, user, time, and policy decision. Editing after approval invalidates it.
- **Evidence boundary (trust boundary 2):** Citation objects preserve document hash, page, offsets, retrieval scores, model/version metadata, and access scope. If evidence is absent, the answer says "not found in the approved matter sources."
- **Egress boundary (trust boundary 3):** No telemetry or inference traffic leaves the deployment unless the customer enables it. Diagnostic bundles redact matter content and secrets by default.
- **Model boundary:** Model output is untrusted data. It cannot grant itself tools or permissions.

---

## Access matrix vs. threat model cross-check

Every threat category in `docs/security/threat-model.md` is addressed by this matrix or by the data-flow controls in `docs/architecture/data-flow.md`:

1. **Confidentiality breach** — tenant isolation, matter scope in retrieval, operator access limited and logged, diagnostic redaction. (Matrix: documents, audit, deployment config; data-flow: encrypted volume, default-deny egress.)
2. **Cross-matter leakage** — matter scope is a database filter in every retrieval query. (Matrix: matters, prompts/questions; data-flow: retrieval stage.)
3. **Unauthorized legal content or overclaim** — firm-owned corpus only; quality rule; marketing discipline; counsel review. (Not an access-control issue per se; addressed by product contract, non-goals, and the quality rule.)
4. **Unsupported or incorrect output** — evidence-first answer contract; citation object; blind review; thresholds. (Matrix: citations/feedback; data-flow: retrieval → prompt assembly → inference → citation objects.)
5. **Prompt injection inside documents** — quoted-source boundaries; prompt-injection filtering; no hidden tool invocation; model output untrusted. (Data-flow: prompt assembly → inference; model boundary.)
6. **Poisoned citations** — citation object preserves actual quoted text and offsets; human feedback channel; review low-rated outputs. (Matrix: citations/feedback; data-flow: citation-object stage.)
7. **Denial-of-service and resource exhaustion** — size and MIME validation; antivirus; resource limits; backup and capacity planning. (Data-flow: upload → parse/OCR stage; deployment config.)
8. **Malicious or malformed file** — MIME validation; antivirus; size limits; parser failure returns visible error, not empty searchable document; partial ingestion stays visibly incomplete. (Data-flow: upload → parse/OCR stage.)
9. **Access control bypass** — role-based access and matter membership enforced at database and API level; session timeout and revocation; export requires approval; denials fail closed. (Matrix: matters, documents, prompts, artifacts, user management; data-flow: retrieval.)
10. **Data loss or unrecoverable state** — deletion records a deletion event and removes file from retrieval; daily encrypted backup; tested restore; documented update and rollback. (Matrix: matters, documents, deployment config; data-flow: fingerprint/index, backup/restore.)
11. **Audit record compromise** — append-only audit ledger; hash-chain; approval binding; editing after approval invalidates it. (Matrix: artifacts, audit record; data-flow: every stage emits audit events.)

---

*This matrix is a working draft. It will be updated after the identity model, matter boundaries, retention rules, and operational policy are defined in Week 2. It must be reviewed by a security professional before any pilot with live data.*
