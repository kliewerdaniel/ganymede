# Ganymede — Week 7-8 Governance Build Plan

**Date:** 2026-09-15
**Goal:** Authorization is a workflow, not a disclaimer.

---

## Phase 0: Fix broken tests (immediate)

- [ ] Add back `VERIFIER_PROMPT_VERSION`, `verify_batch_latency`, `FAST_PATH_RRF_THRESHOLD`, `FAST_PATH_VECTOR_THRESHOLD` to `verifier.py` as compat stubs
- [ ] Fix `test_adversarial.py` fixture issue
- [ ] Verify all tests collect and pass

## Phase 1: JWT authentication

- [ ] Add `python-jose` and `passlib[bcrypt]` to requirements.txt
- [ ] Create `api/app/core/auth.py` with:
  - `create_access_token(secret, user_id, role, exp_minutes)`
  - `verify_access_token(token) -> {user_id, role, exp}`
  - `get_current_user(token) -> User` dependency
  - `require_role(user, allowed_roles)` guard
- [ ] Update `api/app/models/__init__.py`:
  - Add `password_hash` column to User
  - Add `password_hash` field to UserCreate schema
- [ ] Add `POST /api/v1/auth/login` endpoint (email + password → JWT)
- [ ] Add `POST /api/v1/auth/register` endpoint (dev only)
- [ ] Update `docker-compose.yml` with `JWT_SECRET_KEY` env var

## Phase 2: Role-based access control (RBAC)

- [ ] Define roles: `admin`, `attorney`, `reviewer`, `paralegal`, `operator`
- [ ] Create `api/app/core/rbac.py`:
  - Role hierarchy and permissions matrix
  - `can_access_matter(user, matter_id)` — checks MatterMembership
  - `can_query_matter(user, matter_id)`
  - `can_export_artifact(user, matter_id)`
  - `can_manage_users(user, tenant_id)` — admin only
- [ ] Add middleware: every matter-scoped endpoint checks membership
- [ ] Update all `/matters/{matter_id}/*` endpoints to require auth + membership

## Phase 3: Row-level security (DB-level)

- [ ] Add PostgreSQL RLS policies:
  - Users can only see documents in matters they're members of
  - Users can only see chunks from accessible matters
  - Admins can see all
- [ [ ] Enable RLS on documents, pages, chunks, chunk_embeddings tables
- [ ] Set app role per request (SET LOCAL app.current_user_id)
- [ ] Add `api/app/core/rls.py` to set session context

## Phase 4: Audit log

- [ ] Create `audit_logs` table:
  - id, tenant_id, user_id, action, resource_type, resource_id, timestamp, metadata JSONB
- [ ] Actions: `query.submit`, `citation.view`, `citation.feedback`, `artifact.export`, `document.upload`, `auth.login`, `auth.logout`
- [ ] Create `api/app/core/audit.py`:
  - `log_action(db, user_id, action, resource_type, resource_id, metadata)`
- [ ] Instrument key endpoints to emit audit events
- [ ] Add `GET /api/v1/audit` endpoint (admin-only, paginated)

## Phase 5: Prompt injection defenses

- [ ] Create `api/app/core/sanitizer.py`:
  - `sanitize_query(text)` — strip control chars, limit length, detect injection patterns
  - `sanitize_passage(text)` — ensure quoted boundaries
- [ ] Add injection patterns detection:
  - "ignore previous instructions"
  - "system prompt"
  - "you are now"
  - Hidden instructions in document text
- [ ] Instrument ingestion to flag suspicious patterns in document text
- [ ] Add `/api/v1/admin/scan-injection` endpoint (admin, re-scans all documents)

## Phase 6: Governance tests

- [ ] `test_auth.py`: JWT creation, verification, expiration, tampering
- [ ] `test_rbac.py`: role hierarchy, permission checks, membership enforcement
- [ ] `test_rls.py`: RLS policies prevent cross-matter access at DB level
- [ ] `test_audit.py`: audit events emitted for key actions, pagination
- [ ] `test_sanitizer.py`: injection detection, boundary preservation

---

## Files to create/modify

### New files
- `api/app/core/auth.py`
- `api/app/core/rbac.py`
- `api/app/core/rls.py`
- `api/app/core/audit.py`
- `api/app/core/sanitizer.py`
- `api/app/models/audit_log.py`
- `api/tests/test_auth.py`
- `api/tests/test_rbac.py`
- `api/tests/test_rls.py`
- `api/tests/test_audit.py`
- `api/tests/test_sanitizer.py`
- `adr/013-governance-auth-rbac.md`

### Modified files
- `api/app/models/__init__.py` — add password_hash, AuditLog model
- `api/app/schemas/__init__.py` — add LoginRequest, TokenResponse, AuditResponse
- `api/app/api/__init__.py` — add auth endpoints, secure matter endpoints
- `api/app/core/config.py` — add JWT_SECRET_KEY setting
- `api/app/services/verifier.py` — add back compat constants
- `api/requirements.txt` — add jose, passlib
- `api/Dockerfile` — add bcrypt build deps
- `docker-compose.yml` — add JWT_SECRET_KEY
- `api/tests/test_verifier.py` — fix imports
- `api/tests/test_verifier_fast_path.py` — fix imports
- `api/tests/test_verifier_fast_path_calibration.py` — fix imports
- `api/tests/test_verifier_v110.py` — fix imports
- `api/tests/test_adversarial.py` — fix fixture
- `decisions/log.md` — add Week 7-8 closeout

---

## Acceptance criteria

1. All endpoints under `/matters/{id}/*` require valid JWT + matter membership
2. Users cannot access matters they're not members of (enforced at DB level)
3. Every query, citation view, and export emits an audit event
4. Prompt injection patterns in queries are detected and rejected
5. All governance tests pass
6. Gold-set retrieval quality does not regress (86.2% recall, 8/8 isolation)
