# ADR 013: Governance — JWT Auth, RBAC, Audit Log, Input Sanitizer

**Status:** Proposed  
**Date:** 2026-09-15  

## Context

Week 7-8 focuses on governance: identity, roles, audit logging, and input sanitization. The API currently has no authentication — any caller can query any matter. Production requires:

1. **Authentication** — who is making the request
2. **Authorization** — what they're allowed to do
3. **Audit** — what happened (append-only log)
4. **Input safety** — prompt injection detection and query sanitization

## Decision

### 1. JWT Authentication

- **Library**: PyJWT (NOT python-jose — python-jose uses `cryptography` which causes SIGILL on ARM64)
- **Hashing**: bcrypt via passlib
- **Token format**: HS256 JWT with `sub` (user_id), `role`, `exp`, `iat`
- **TTL**: 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Header**: `Authorization: Bearer <token>`

### 2. Role-Based Access Control (RBAC)

Five roles with hierarchical permissions:
- `administrator` (100) — full access
- `attorney` (80) — query, upload, export
- `reviewer` (60) — read, query, export
- `paralegal` (40) — read, query
- `it_operator` (20) — read, audit

Matter-level access: users can only access matters they're members of (via `matter_memberships` table). Admins bypass matter membership checks.

### 3. Audit Log

Append-only `audit_logs` table with:
- `tenant_id`, `user_id`, `action`, `resource_type`, `resource_id`, `metadata_json`, `created_at`
- Actions: `auth.login`, `matter.create`, `document.upload`, `query.submit`, `citation.feedback`, `query.injection_detected`, etc.
- Admin-only access via `GET /audit` (paginated)

### 4. Input Sanitizer

- **Query sanitization**: control char removal, whitespace normalization, 10K char limit
- **Injection detection**: 15 patterns (ignore previous instructions, you are now, system prompt, jailbreak, developer mode, etc.)
- **Document scan**: `is_suspicious_document()` for ingestion-time checks
- Blocked queries return HTTP 400 with audit entry

### 5. Endpoint Protection

All `/matters/{id}/*` and `/documents/*` endpoints now require:
- `Depends(get_current_active_user)` — valid JWT
- `can_access_matter(current_user, matter_id, db)` — matter membership
- Query sanitization + injection detection on `/query`

Unauthenticated endpoints: `/health`, `/auth/login`, `/auth/register`

## Consequences

**Positive:**
- All endpoints now require authentication
- Matter-level isolation enforced at app level
- All queries and actions logged to audit trail
- Prompt injection attempts detected and blocked
- Role hierarchy maps to real law firm roles

**Negative:**
- Performance: each auth check adds ~5ms (token decode)
- PyJWT instead of python-jose (slightly different API)
- bcrypt 4.x required (5.x breaks passlib compatibility)

## Alternatives Considered

- **python-jose**: causes SIGILL on ARM64 (DeBERTa-v3 also affected)
- **Session tokens**: would require server-side state, more complex
- **API keys**: less granular, no per-user attribution
- **OPA/external authz**: too heavy for MVP single-tenant

## Related

- ADR 001: Single-tenant deployment
- ADR 010: Sync /ask unverified
- ADR 008: Verifier architecture

## Verification

- `test_auth.py`: 13 tests (JWT create/decode, password hashing)
- `test_rbac.py`: 16 tests (role hierarchy, permissions)
- `test_audit.py`: 8 tests (log creation, query, pagination)
- `test_sanitizer.py`: 24 tests (injection detection, sanitization)
