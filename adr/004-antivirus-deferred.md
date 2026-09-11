# ADR 004: Antivirus — deferred with documented reason

**Status:** Accepted
**Date:** September 2026
**Deciders:** Daniel Kliewer (founder)
**Review trigger:** Before pilot with live client data; before any change to the upload pipeline.

---

## Context

The Week 3 upload API needs antivirus (AV) scanning per the development plan. The options are:
1. ClamAV sidecar (Docker container, freshclam signatures, scan on upload).
2. Deferred AV with a documented reason and a migration path.

The question is whether to include ClamAV in the Week 3 build or defer it.

---

## Decision

**Defer antivirus scanning to Week 4 or later, with this documented reason:**

1. The Week 3 build ingests only the frozen synthetic corpus and synthetic adversarial fixtures. No real client data is involved. The threat model (malicious file upload) is real but the attack surface is synthetic-only in Week 3.
2. ClamAV adds operational complexity: a separate Docker container, signature updates (freshclam), and a scan timeout that can fail closed (blocking legitimate uploads) or fail open (scanning async, which defers the very protection AV provides).
3. The upload pipeline already validates MIME type, file size, and SHA-256 content hash. These are the first-line defenses. AV is a second-line defense for a threat that is not realized in Week 3's synthetic-only ingestion.

**Migration path:** Add a ClamAV sidecar to `docker-compose.yml` in Week 4, with a scan step between upload and parsing. The `ingestion_jobs` table already has a `stage` column that can track `av_scan` as a distinct stage.

---

## Consequences

**Enables:**
- Week 3 stays focused on ingestion, provenance, and failure visibility — the core Week 3 deliverables.
- No operational burden of maintaining AV signatures during the synthetic-only test phase.

**Costs:**
- Week 3 uploads are not AV-scanned. This is acceptable because the data is synthetic.
- When real client data arrives (pilot), AV must be in place before any upload.

**Hardens:**
- The `ingestion_jobs.stage` column is designed to accommodate `av_scan` as a future stage.
- The failure-behavior rule (visible failure, not silent empty doc) applies equally to AV failures.

---

## Alternatives considered

### ClamAV sidecar in Week 3

Rejected. Adds operational complexity (container, signatures, scan timeouts) for a threat that is not realized in Week 3's synthetic-only ingestion. The cost/benefit does not justify inclusion in Week 3.

### Cloud AV API (VirusTotal, etc.)

Rejected. Sends matter data to a public API, violating trust boundary 3 (Egress) and ADR 001 (single-tenant, customer-controlled). This is architecturally incompatible.

### Client-side scanning

Rejected. The client is a web browser; it cannot reliably scan files before upload. Server-side scanning is the only viable option.

---

## References

- ADR 001 (single-tenant deployment, deny-by-default egress)
- DEVELOPMENT.md (trust boundary 3: Egress)
- plans/development-plan.md (Week 3 — File upload API with MIME validation, antivirus, size limits)
- docs/security/threat-model.md (threat 8: Malicious or malformed file)

---

*This ADR documents the deferral. It does not remove the requirement. AV scanning must be implemented before any pilot with live client data.*
