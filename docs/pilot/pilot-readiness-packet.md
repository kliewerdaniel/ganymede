# Ganymede — Pilot Readiness Packet

**Status:** Draft
**Date:** September 2026
**Assembled:** Week 10 (before pilot launch)

---

This packet is assembled in Week 10, before the pilot launches. It is the collection of briefs the buyer, IT/security reviewer, and operators need to understand what they are piloting and what the controls are.

---

## Security brief

**Contents:**
- Data flow: what travels where, in what form, under what terms. What never leaves the deployment by default.
- Egress policy: default-deny outbound network. No telemetry or inference traffic leaves unless the customer enables it.
- Encryption responsibilities: TLS, encrypted file volume, managed secrets.
- Operator access: who can access matter content, under what conditions, with what logging.
- Retention and deletion: how long data is kept, who can delete, what happens at pilot end.
- Incident contact and process: who is notified and under what process for a suspected confidentiality breach, cross-matter disclosure, credential exposure, corrupted audit record, or unrecoverable data loss.

**Rule:** "Runs in a customer-controlled environment" is the verifiable architecture statement. Do not claim "secure," "privilege-safe," or "compliant" without a defined control set and independent evidence.

---

## Quality brief

**Contents:**
- Benchmark method: the frozen corpus, the 50-question gold set, the categories, and how results are measured.
- Model and version: the model, quantization, prompt version, and known limitations.
- Citation results: retrieval recall, citation support rate, unsupported-claim rate, matter isolation results.
- Known limitations: what the system does not do, and where it is weakest.
- Required human review: which artifacts require review before use, and what the review is for.

**Rule:** These are internal launch thresholds, not market facts. They will be tightened after observing real legal reviewers.

---

## Operations brief

**Contents:**
- Installation: the Docker Compose release, the reference hardware, the model installation, and the administrator bootstrap.
- Backups: daily encrypted backup, tested restore.
- Restore: the restore procedure, tested on a clean machine.
- Updates: the update procedure, rollback, and signed release manifest.
- Logs: what is logged, what is redacted by default, and what is available to operators.
- Support path: business-hours support, severity model, response target, diagnostic bundle that redacts matter content and secrets by default.
- Recovery objective: what restore covers and what the recovery time objective is.

---

## Minimum controls (must be in place before pilot)

- TLS.
- Secure cookies.
- Encrypted volume.
- Managed secrets; no credentials in logs.
- Default-deny egress.
- Daily encrypted backup and tested restore.
- Administrator access logging.
- Documented update policy.
- Database-enforced tenant and matter scope.
- Append-only audit events and artifact versions.
- Role-based access and session controls.
- Antivirus, MIME, and size validation on upload.
- Prompt-injection and cross-matter tests in the benchmark.

---

## Legal and professional-duty note

Before ingesting real client data, qualified counsel must establish confidentiality, data-processing, incident, retention/deletion, liability, and permitted-use terms. ABA Formal Opinion 512 identifies the professional duties a lawyer must consider when using generative AI — competence, confidentiality, communication, supervision, candor, meritorious claims, and reasonable fees. The product should surface information that helps a lawyer evaluate those duties; it should not claim to automatically satisfy them.

---

## Incident rule

Any suspected confidentiality breach, cross-matter disclosure, credential exposure, corrupted audit history, or unrecoverable data loss pauses the affected deployment. Preserve evidence, follow the agreed notification path, remediate, and obtain explicit approval before resuming.

---

*This packet is assembled in Week 10. It is not a security certification or legal advice. It is the honest, testable description of what the pilot includes and what it does not.*
