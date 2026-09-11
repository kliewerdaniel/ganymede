# Ganymede — Trust Boundaries

**Status:** Accepted
**Date:** September 2026
**Source:** Build plan + business plan
**Review trigger:** Any proposed change to a boundary requires an ADR.

---

These are the five non-negotiable trust boundaries. They are not aspirational. They are the definition of the product's trust model. Violating one without an ADR is a defect.

---

## 1. EXPORT — Every external artifact requires a deliberate human action

- Exports carry an AI-assisted draft label.
- Export requires approval. Approval binds to the exact artifact version, source set, user, time, and policy decision.
- Editing after approval invalidates it.
- The label is retained in the exported artifact. The firm controls whether it is retained in downstream work product.

**Why:** Drafts are never represented as final legal advice. Review and export remain explicit human actions.

---

## 2. EVIDENCE — Answers preserve the source

Every factual answer links to the exact source passage. The citation object preserves:

- Document hash (sha256).
- Page.
- Start and end offsets.
- Quoted text.
- Parser version.
- Retrieval scores.
- Model and version metadata.
- Access scope.

If the system lacks evidence, it says "not found in the approved matter sources." It may suggest a better query or identify missing documents, but it must not fill the gap from model memory.

**Why:** Grounded by default. Every claim cites evidence. No source, no factual claim.

---

## 3. EGRESS — No telemetry or inference traffic leaves unless the customer enables it

- The deployment is customer-controlled.
- Default-deny outbound network policy.
- No telemetry or inference traffic leaves the deployment unless the customer enables it.
- Diagnostic bundles redact matter content and secrets by default.

**Why:** Matter data stays inside a customer-controlled single-tenant environment and is not sent to public model APIs.

---

## 4. TENANT — No shared application database or vector index between customers

- Each customer receives an isolated stack: application, database, file volume, model runtime, and audit domain.
- There is no shared application database or vector index between customers.
- A customer's data does not coexist with another customer's data in a shared store.

**Why:** Single-tenant is the trust story. Shared state would make the story illegible.

---

## 5. MATTER — Authorization filters retrieval before any prompt is assembled

- Authorization is not a prompt instruction. It is a database filter.
- The retrieval service receives an authorization decision and scoped identifiers, not an unconstrained user request.
- Matter scope is enforced in the retrieval query, before results are returned.
- Cross-matter retrieval is prohibited.

**Why:** If access control lives only in the prompt, it can be bypassed by prompt injection or retrieval misconfiguration. The boundary must be below the prompt layer.

---

## Model boundary (related, not one of the five)

- Model output is untrusted data.
- The model cannot grant itself tools or permissions.
- The model proposes; the typed policy and a human decide whether content can leave the workspace.

**Why:** Authority Non-Equivalence Principle. No model response, confidence score, or requested action is authorization.

---

## What these boundaries rule out

- Multi-tenant SaaS with shared indexes.
- Sending matter content to a public model API.
- Retrieval that does not filter by matter scope at the database level.
- Exports that are not reviewed and marked.
- Telemetry or logging that includes matter content by default.
- Any feature that would require weakening one of these boundaries.

---

*These boundaries are part of the product contract. They are as binding as the features.*
