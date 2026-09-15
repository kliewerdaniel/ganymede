# Ganymede — Pilot Readiness Packet

**Status:** Ready for pilot
**Date:** September 15, 2026
**Version:** 0.1.0
**Assembled:** Week 10

---

## 1. Security Brief

### Data Flow

```
Upload → Parse/OCR → Fingerprint → Index → Retrieval → Prompt Assembly → Local Inference → Citations → Human Approval → Export
```

**What travels where:**

| Stage | What travels | Where it goes | Form |
|-------|-------------|---------------|------|
| Upload | PDF/DOCX/TXT bytes | API container → disk volume | Original file + normalized text |
| Parse/OCR | Extracted text + page structure | In-memory → PostgreSQL | Page records with provenance |
| Fingerprint | sha256 content hash | PostgreSQL | Hash index for dedup |
| Index | Text chunks + embeddings | PostgreSQL FTS + pgvector | Matter-scoped vectors |
| Retrieval | Top-k passages | In-memory only | Citation objects |
| Prompt assembly | Evidence context | API → Ollama (localhost:11434) | JSON with passages |
| Inference | Generated text | Ollama → API | Answer text + metadata |
| Citations | Structured citation objects | PostgreSQL | Claim + document + offsets |
| Approval | Status change | PostgreSQL | Append-only ledger |
| Export | Artifact file | API → user | DOCX/PDF with label |

**What never leaves the deployment:**
- Matter content (documents, chunks, embeddings)
- Query text (minimized in logs)
- Audit records (append-only, redacted on export)
- Model prompts (operational metrics separated from content)

### Egress Policy

**Default-deny outbound.** No telemetry, no external API calls, no model traffic leaves the deployment. Ollama runs on the host machine (`localhost:11434`) — inference traffic stays local.

The only egress paths:
1. **User-initiated export** — deliberate human action, logged, requires approval
2. **Diagnostic bundle** — redacts matter content and secrets by default

### Encryption Responsibilities

| Layer | Mechanism | Status |
|-------|-----------|--------|
| Data at rest | Docker volume encryption (host filesystem) | ✅ Configurable |
| Data in transit | TLS (self-signed or Let's Encrypt) | ✅ Script provided |
| Backups | AES-256-CBC encrypted pg_dump | ✅ Script provided |
| Secrets | JWT signing key (HS256, 30min TTL) | ⚠️ Change default before pilot |
| Passwords | bcrypt 4.x hashing | ✅ |

### Operator Access

| Role | Matter Content | Audit | User Mgmt | Backup/Restore |
|------|---------------|-------|-----------|----------------|
| Administrator | Tenant-scoped | ✅ | ✅ | ✅ |
| Attorney | Assigned matters | Own actions | ❌ | ❌ |
| Paralegal | Assigned matters | Own actions | ❌ | ❌ |
| Reviewer | Assigned matters | Own actions | ❌ | ❌ |
| IT Operator | ❌ (redacted) | ✅ | ❌ | ✅ (logged) |

### Retention and Deletion

- **Matter data:** Retained until matter is deleted by administrator
- **Deletion:** Records deletion event, removes from retrieval, preserves audit trail
- **Backups:** Daily encrypted, retained per customer policy
- **Pilot end:** All data destroyed on customer request (deletion script provided)

### Incident Contact

Any suspected confidentiality breach, cross-matter disclosure, credential exposure, corrupted audit record, or unrecoverable data loss pauses the affected deployment. Preserve evidence, notify designated customer contact, remediate, resume only after explicit approval.

---

## 2. Quality Brief

### Benchmark Method

**Gold set:** 50 questions (29 answerable + 21 answer-absent)
- Direct factual: 20
- Multi-document synthesis: 10
- Chronology: 8
- Answer-absent: 6
- Adversarial/ambiguous: 6

**Corpus:** 36 documents across 7 matters (test data, properly authorized)

### Model and Version

| Component | Model | Quantization | Prompt Version |
|-----------|-------|-------------|----------------|
| Verifier | qwen3:8b | Q4_K_M (4-bit) | v1.2.0 |
| Embeddings | nomic-embed-text | F32 | — |
| Reranker | bge-reranker-base | F16 | — |

**Reference hardware:** Apple M-series, 48GB unified memory, macOS 15+

### Citation Results

| Metric | Result | Target |
|--------|--------|--------|
| Retrieval Recall@5 | 75.9% (22/29) | ≥80% |
| Answer-absent pass | 85.7% (18/21) | ≥90% |
| Verifier latency (p50) | ~12s | <30s |
| Verifier latency (p95) | ~47s | <60s |

**Known verifier gaps:**
- 3 answerable questions leak (Q23, Q30, Q35) — verifier says NO when passage contains answer
- 3 answer-absent questions leak — verifier says YES when passage doesn't contain answer
- Cross-encoder and NLI architectures tested and revoked (ADR 011, 012) — they measure topical relevance, not answer containment

### Known Limitations

1. **No case-law research** — firm-owned corpus only
2. **No multi-tenant** — single-tenant deployment per customer
3. **No real-time collaboration** — single-user artifact editing
4. **Verifier accuracy ceiling** — 75.9% recall on answerable questions (qwen3:8b)
5. **No DOCX/PDF export yet** — artifacts viewable in UI only
6. **No antivirus on ARM64** — ClamAV image doesn't support Apple Silicon

### Required Human Review

All artifacts require attorney review before export. The system labels all outputs "AI-assisted draft — attorney review required." The firm controls whether that label is retained in downstream work product.

---

## 3. Operations Brief

### Installation

```bash
# Requirements: Docker Desktop 4.0+, 16GB RAM, 10GB disk
git clone https://github.com/kliewerdaniel/ganymede.git
cd ganymede
docker compose up -d
./scripts/validate_env.sh
./scripts/bootstrap_admin.sh
```

### Reference Hardware

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 4 cores | 8 cores |
| RAM | 16 GB | 32 GB |
| Disk | 10 GB free | 50 GB free |
| OS | macOS 12+ / Linux x86_64 | macOS 15+ (ARM64) |

### Backups

```bash
# Daily encrypted backup
export BACKUP_PASSWORD="strong-passphrase"
./scripts/backup_encrypted.sh /backups/ganymede

# Restore
openssl enc -aes-256-cbc -d -pbkdf2 -iter 100000 \
  -in /backups/ganymede_backup_*.sql.gz.enc \
  -pass pass:'YOUR_PASSWORD' | gunzip | \
  docker exec -i ganymede-db-1 psql -U ganymede -d ganymede
```

### Updates

```bash
# Update to latest
./scripts/update.sh latest

# Rollback if issues
./scripts/update.sh rollback
```

### Logs

| Log | Location | Retention |
|-----|----------|-----------|
| API logs | `docker logs ganymede-api-1` | Container-managed |
| Audit log | PostgreSQL `audit_logs` table | Append-only, customer-managed |
| Diagnostic bundle | `./scripts/diag.sh` | Redacts matter content + secrets |

### Support Path

1. **Diagnostic bundle:** `./scripts/diag.sh` — collects system info, table counts, error logs
2. **Health checks:** `/api/v1/healthz`, `/api/v1/readyz`
3. **GitHub issues:** https://github.com/kliewerdaniel/ganymede/issues

### Recovery Objective

- **RPO (Recovery Point Objective):** 24 hours (daily backups)
- **RTO (Recovery Time Objective):** 1 hour (clean install + restore)
- **Tested:** Backup/restore verified on clean machine (Week 9)

---

## 4. Minimum Controls (Pre-Pilot)

| Control | Status | Evidence |
|---------|--------|----------|
| TLS | ✅ Script provided | `scripts/setup_tls.sh` |
| Encrypted volume | ✅ Docker volumes | `docker-compose.yml` |
| Managed secrets | ⚠️ Default JWT | Change before pilot |
| Default-deny egress | ✅ No external calls | Architecture |
| Daily encrypted backup | ✅ Script provided | `scripts/backup_encrypted.sh` |
| Tested restore | ✅ Verified | Week 9 |
| Administrator access logging | ✅ Audit log | `audit_logs` table |
| Documented update policy | ✅ Script provided | `scripts/update.sh` |
| Tenant/matter scope | ✅ DB-enforced | `rbac.py` |
| Append-only audit | ✅ Implementation | `audit.py` |
| Role-based access | ✅ 5 roles | `rbac.py` |
| Session controls | ✅ JWT 30min TTL | `auth.py` |
| MIME/size validation | ✅ Upload service | `ingestion.py` |
| Prompt injection detection | ✅ 15 patterns | `sanitizer.py` |
| Cross-matter isolation | ✅ DB filter | `retrieval.py` |

---

## 5. Legal and Professional-Duty Note

Before ingesting real client data, qualified counsel must establish confidentiality, data-processing, incident, retention/deletion, liability, and permitted-use terms. ABA Formal Opinion 512 identifies the professional duties a lawyer must consider when using generative AI — competence, confidentiality, communication, supervision, candor, meritorious claims, and reasonable fees.

The product surfaces information that helps a lawyer evaluate those duties. It does not claim to automatically satisfy them.

---

## 6. Test Evidence

### Security Regression (Week 10)

| Category | Tests | Pass |
|----------|-------|------|
| Authentication | 7 | 7/7 |
| RBAC | 5 | 5/5 |
| Prompt Injection | 5 | 5/5 |
| Cross-Tenant Isolation | 1 | 1/1 |
| IDOR | 2 | 2/2 |
| Audit Logging | 2 | 2/2 |
| Data Validation | 3 | 3/3 |
| **Total** | **25** | **25/25** |

### Full Test Suite

- **126 tests passing, 2 skipped** (DB-dependent backup tests)
- Coverage: auth, RBAC, CRUD, retrieval, artifacts, citations, security, validation

### Verified Live (September 15, 2026)

- API health: ✅ `healthz` + `readyz`
- Database: ✅ 14 matters, 36 documents, 52 chunks, 52 embeddings
- Ollama: ✅ 5 models loaded (qwen3:8b, qwen3.5:9b, bge-reranker-base, qwen3:4b, nomic-embed-text)
- Query: ✅ Returns 3 citations for "contract agreement"
- Artifact creation: ✅ Memo artifact created successfully

---

*This packet is assembled in Week 10. It is not a security certification or legal advice. It is the honest, testable description of what the pilot includes and what it does not.*
