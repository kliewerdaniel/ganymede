# Ganymede — Access Matrix

**Status:** Draft
**Date:** September 2026
**Frozen:** Week 2 (after identities, roles, and matter boundaries are defined)

---

## Purpose

Define who can access what, under what conditions, and with what logging. This document is incomplete until the identity model, matter boundaries, retention rules, and operator access are defined in Week 2.

---

## Roles (planned)

| Role | Purpose | Default privileges |
|------|---------|-------------------|
| Administrator | Operate the deployment, manage users and matters, access operational logs | Manage users, matters, backups, updates, logs. Does not automatically have matter-content access for review. |
| Attorney | Practice-role user with matter access | Access assigned matters, ask questions, inspect citations, edit and approve artifacts, export with approval. |
| Reviewer | Review-role user focused on verification | Inspect citations, mark supporting/weak/wrong/inaccessible, review drafts, approve or reject exports. |
| Support operator | Technical support with limited, logged access | Diagnostic access that redacts matter content by default. Matter-content access only when justified, logged, and within the support process. |

Least privilege by default. A role's access is defined by matter membership and explicit permissions, not by a broad default.

---

## Matter boundary

- Each matter is a separate scope.
- Authorization filters retrieval before any prompt is assembled.
- A user's access to a matter is explicit: the user is a member of that matter, with a role.
- Cross-matter retrieval is prohibited. A query in matter A must not return passages from matter B.

---

## Document access

- Within a matter, document access is governed by matter membership and role.
- Upload, parse, index, retrieve, edit, approve, and export are separate actions with separate controls.
- Export requires approval. Approval binds to the exact artifact version, source set, user, time, and policy decision.

---

## Operator access

- Operators do not have blanket access to matter content.
- Diagnostic bundles redact matter content and secrets by default.
- Any matter-content access by an operator for support is logged and justified under the support process.
- Critical confidentiality, authorization, or data-loss events pause use and follow the contractual incident path.

---

## Session and authentication

- Sessions time out and can be revoked.
- Revoked users lose access immediately.
- Stale sessions do not retain access.

---

## Deletion

- Deleting a file removes it from retrieval and records a deletion event.
- Retention and deletion behavior is documented and enforceable.

---

## Audit

- Uploads, parses, retrievals, generations, edits, approvals, exports, access changes, and deletions are recorded.
- The audit ledger is append-only.
- Audit events preserve the lineage needed to reconstruct each artifact.

---

## Missing

This matrix is a template. It must be completed with:
- The actual roles and their privileges.
- The actual matter boundary enforcement mechanism.
- The actual operator access policy.
- The actual retention and deletion rules.
- The actual logging and audit schema.

These are Week 2 outputs.

---

*This document is a starting point for the Week 2 access matrix. It must be reviewed by a security professional before any pilot with live data.*
