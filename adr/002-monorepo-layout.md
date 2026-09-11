# ADR 002: Monorepo layout — api/ + web/ + docker-compose

**Status:** Accepted
**Date:** September 2026
**Deciders:** Daniel Kliewer (founder)
**Review trigger:** Before any material change to the repository structure or deployment topology.

---

## Context

Ganymede is a single-tenant, customer-controlled deployment (ADR 001). The stack is FastAPI (Python) for the API and document pipeline, Next.js (TypeScript) for the web UI, and PostgreSQL + pgvector for data and search. The repository must organize these components so that:

- The API and web layers can be developed, tested, and versioned together.
- The Docker Compose release packages them as one deployable unit.
- A developer can run the full stack locally with one command.

The question is how to lay out the repository to support this.

---

## Decision

The repository uses a monorepo layout:

```
ganymede/
├── api/                    # FastAPI application, ingestion pipeline, migrations
│   ├── app/
│   │   ├── main.py         # FastAPI app factory
│   │   ├── core/           # config, database, security
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── api/            # route handlers
│   │   ├── services/       # business logic (ingestion, parsing, etc.)
│   │   └── db/             # migrations (Alembic)
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── web/                    # Next.js application (minimal in Week 3)
├── docker-compose.yml      # app + PostgreSQL with pgvector
├── adr/
├── docs/
├── plans/
├── decisions/
└── testdata/
```

- `api/` owns the backend: FastAPI app, SQLAlchemy models, Alembic migrations, ingestion pipeline, parsing/OCR services, and API routes.
- `web/` owns the frontend: Next.js app (minimal in Week 3; full UI in Week 5).
- `docker-compose.yml` ties them together with PostgreSQL + pgvector.
- Test fixtures that are NOT part of the frozen corpus go in `testdata/fixtures/`.

---

## Consequences

**Enables:**
- One command (`docker-compose up`) runs the full stack.
- The API and web layers share one version history.
- Alembic migrations live next to the code they version.
- Clear separation: the API has no dependency on the web framework, and the web app talks to the API over HTTP.

**Costs:**
- A monorepo couples deployment versions. A change to the API and a change to the web UI land in the same commit. This is acceptable for a small team and a single deployable unit.
- Build times grow as both layers grow. This is acceptable for the MVP scale.

---

## Alternatives considered

### Polyrepo (separate api/ and web/ repositories)

Rejected. A single-tenant deployment that ships as one Docker Compose unit benefits from one version history. Separate repos add release-coordination overhead for no gain at this scale.

### Monorepo with a shared `packages/` directory for common types

Rejected for Week 3. The API and web UI share types over the HTTP boundary (Pydantic schemas on the API side, generated or hand-written types on the web side). A shared package is premature until the API contract stabilizes.

---

## References

- ADR 001 (single-tenant deployment)
- DEVELOPMENT.md (planned stack)
- plans/development-plan.md (Phase 2, Weeks 3-4)

---

*This ADR establishes the repository layout. It does not define the internal structure of api/ or web/; those are implementation details that will be built in Week 3.*
