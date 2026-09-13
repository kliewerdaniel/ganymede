# ADR 004 Addendum: ClamAV antivirus — second deferral, no owner

**Status:** Supplemental to ADR 004 (Deferred)
**Date:** 2026-09-12
**Trigger:** ADR 004 deferred antivirus to Week 4. Week 4 is now ending. A decision is required: implement or log deferral with owner + date.

---

## Context

ADR 004 (deferred) specified ClamAV antivirus scanning for uploaded documents. The implementation status at end of Week 4:

- `api/app/services/antivirus.py` exists — ClamAV scan wrapper using `clamdscan`.
- `clamdscan` binary is installed in the API container (Dockerfile installs `clamav-daemon`).
- `clamd` daemon is NOT running — the container has no supervisor to start it, and the ARM64 architecture is incompatible with the ClamAV daemon in the current Docker image.
- Scanning fails with "Could not connect to clamd" — same as Week 3.

The `antivirus.py` service is wired but non-functional. No scan results are ever produced.

---

## Measurement

| Component | Status |
|-----------|--------|
| `clamdscan` binary | Installed in API container |
| `clamd` daemon | Not running (no supervisor, ARM64 incompatibility) |
| `antivirus.py` service | Exists, non-functional |
| Scan results | Never produced |
| Docker sidecar (ARM64) | Incompatible — ADR 004 originally considered and rejected |

**Time spent this Week 4:** ~30 minutes investigating. No productive implementation achieved.

---

## Decision

**Defer ClamAV again. This time with an owner and a date.**

| Field | Value |
|-------|-------|
| **Decision** | Defer ClamAV antivirus scanning |
| **Owner** | Daniel Kliewer |
| **Target date** | End of Week 7 (security & access phase) |
| **Trigger for earlier action** | Pilot agreement requires a security questionnaire that asks about malware scanning; if the answer is "not implemented," the pilot cannot proceed |
| **Workaround** | Document the gap in the known-limits document; recommend client-side antivirus as compensating control for pilot firms |

---

## Consequences

**Enables:**
- Week 4 can close without blocking on ARM64 ClamAV incompatibility.
- Clear accountability: Daniel owns the fix, Week 7 is the deadline.

**Costs:**
- Uploaded documents are not virus-scanned for the duration of the deferral.
- Pilot firms must be informed (known-limits document) and advised to use client-side scanning.
- If the security questionnaire requires malware scanning and the gap is not closed by Week 7, the pilot is blocked.

**Hardens:**
- "Deferred" with no owner and no date is not a decision — this ADR records the owner (Daniel) and the date (end of Week 7).
- The incompatibility is architectural (ARM64 Docker image), not a code issue — fixing it requires either a different Docker base image, a different antivirus solution, or a sidecar on a different architecture.

---

## Alternatives considered

### Run clamd in the API container via supervisord
Rejected. Adds operational complexity to the API container. The ARM64 incompatibility may prevent clamd from running at all — unverified.

### Use a different antivirus (e.g., `clamav` via Python bindings, or a cloud service)
Deferred. Requires evaluation of alternatives against the single-tenant, air-gapped deployment model (ADR 001). Cloud services violate the deployment model. Python bindings require a running clamd instance.

### Accept the gap and do not scan
Rejected. Malware scanning is a reasonable security expectation for a document ingestion pipeline. The gap is documented and owned, but it is not accepted as permanent.

---

## References

- ADR 004 (original deferral)
- `api/app/services/antivirus.py` (non-functional implementation)
- `Dockerfile` (clamav-daemon installed, clamd not started)
- `plans/development-plan.md` (Week 7 security phase — target for implementation)
