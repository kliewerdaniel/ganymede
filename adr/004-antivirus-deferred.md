# ADR 004: Antivirus — implemented with ClamAV sidecar

**Status:** Accepted
**Date:** September 2026
**Deciders:** Daniel Kliewer (founder)
**Review trigger:** Before pilot with live client data; before any change to the upload pipeline.

---

## Context

The Week 3 upload API deferred antivirus scanning (see original ADR 004). Week 4 implements it.

---

## Decision

**Implement antivirus scanning via a ClamAV sidecar in Docker Compose.**

- Add `clamav/clamav:latest` as a service in `docker-compose.yml`.
- Scan on upload: after the file is received but before parsing, scan with `clamdscan`.
- If the scan detects a virus, reject the upload and return an error.
- If the scan times out or the scanner is unavailable, fail closed (reject the upload).

---

## Consequences

**Enables:**
- Virus scanning before parsing (no malicious file enters the ingestion pipeline).
- Fail-closed behavior: scanner unavailable = upload rejected.

**Costs:**
- ClamAV container adds memory and startup time.
- Signature updates (freshclam) run automatically on container start.
- Scan timeout (60s) adds latency to large file uploads.

**Hardens:**
- The `ingestion_jobs.stage` column tracks `av_scan` as a distinct stage.
- The failure-behavior rule (visible failure, not silent empty doc) applies to AV failures.

---

## Alternatives considered

### Cloud AV API (VirusTotal, etc.)

Rejected. Sends matter data to a public API, violating trust boundary 3 (Egress) and ADR 001 (single-tenant, customer-controlled). This is architecturally incompatible.

### Client-side scanning

Rejected. The client is a web browser; it cannot reliably scan files before upload. Server-side scanning is the only viable option.

---

## References

- ADR 001 (single-tenant deployment, deny-by-default egress)
- ADR 003 (ingestion pipeline — AV scan added as a stage)
- DEVELOPMENT.md (trust boundary 3: Egress)
- plans/development-plan.md (Week 4 — Antivirus)

---

*This ADR documents the implementation. The original ADR 004 deferred it; this follows through.*
