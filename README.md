# Ganymede

**Private Matter Intelligence** — a single-tenant, customer-controlled AI workspace for civil-litigation teams.

A lawyer can move from a question about the record to a reviewable, cited draft without sending matter data to a public model provider.

---

## What this is

Ganymede lets a litigation team do three jobs over documents they already own:

1. **Find the fact** — ask a question, get an answer with document name, page, quoted passage, and visible uncertainty.
2. **Build the record** — extract a reviewable chronology and issue/evidence table from the matter corpus.
3. **Start the work product** — produce an internal memo or deposition-prep draft grounded only in approved matter sources, with human review before export.

It is **not** a legal chatbot, a case-law research tool, an e-discovery platform, or an autonomous filing agent. See [Product Contract](docs/specification/product-contract.md) and [Non-Goals](docs/specification/non-goals.md).

---

## Trust model (summary)

- **Private by architecture.** Matter data stays inside a customer-controlled single-tenant deployment. No outbound inference traffic by default.
- **Grounded by default.** Every factual answer links to the exact source passage. If evidence is absent, the system says so.
- **Human-owned.** Drafts carry an AI-assisted label. Export requires a deliberate human action and preserves approval lineage in an append-only audit record.

Full trust boundaries are in [Trust Boundaries](docs/architecture/trust-boundaries.md).

---

## Repository structure

```
ganymede/
├── README.md                  # this file
├── SKILL.md                   # Hermes agent operating instructions for this repo
├── DEVELOPMENT.md             # engineering conventions and build rules
├── adr/                       # Architecture Decision Records
│   ├── 000-template.md
│   ├── 001-single-tenant-deployment.md
│   ├── 002-monorepo-layout.md
│   ├── 003-ingestion-pipeline.md
│   ├── 004-antivirus-deferred.md (+ addendum)
│   ├── 005-chunking-strategy.md
│   ├── 006-embedding-model.md (+ addendum)
│   ├── 007-retrieval-fusion-reranker.md (+ addendum)
│   ├── 008-answer-verification.md (+ fast-path addendum)
│   ├── 009-verifier-recall-recovery.md
│   ├── 010-sync-ask-unverified.md
│   └── 011-cross-encoder-verification.md (revoked)
├── api/                       # FastAPI backend (Python 3.11)
│   ├── app/
│   │   ├── api/               # REST endpoints
│   │   ├── core/              # config, CORS, database
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # ingestion, retrieval, verifier, etc.
│   │   └── main.py            # FastAPI app factory
│   ├── tests/                 # gold-set evals, integration tests
│   ├── Dockerfile
│   ├── requirements.txt
│   └── alembic.ini
├── web/                       # Static frontend (dark-themed SPA)
│   └── index.html
├── docs/
│   ├── discovery/             # Phase 1 (Weeks 1-2) discovery outputs
│   ├── specification/         # versioned product spec, benchmark, corpus rules
│   ├── architecture/          # stack, data flow, trust boundaries
│   ├── commercial/            # pricing, proposal, sales narrative, pilot scorecard
│   ├── sales/                 # discovery script, one-pager, prospect tracking
│   ├── security/              # threat model, access matrix, incident path
│   └── pilot/                 # pilot agreement, readiness packet
├── plans/                     # implementation plans and weekly scorecards
├── decisions/                 # decision log
├── docker-compose.yml         # API + PostgreSQL + pgvector + host Ollama
├── testdata/
│   ├── corpus-v0.1/           # synthetic test corpus, Matter A (23 docs + manifest + facts ledger)
│   └── corpus-v0.1-matter-b/  # synthetic test corpus, Matter B (12 docs + manifest + facts ledger)
└── corpus-v0.1/               # legacy build scripts
```

---

## Architecture

### Stack

| Layer | Choice | Notes |
|-------|--------|-------|
| Web | Vanilla JS SPA (`web/index.html`) | Dark-themed, matter selector, citation cards, source inspector |
| API | FastAPI / Python 3.11 | Typed AI and document pipeline |
| Data | PostgreSQL + pgvector | One operable store for MVP; FTS + vectors |
| Parsing | PyMuPDF, python-docx, Tesseract OCR | Page-aware provenance |
| Inference | Ollama (local) | LLM verifier + embeddings; adapter boundary kept for vLLM swap |
| Delivery | Docker Compose | Single-tenant deployment |

### Retrieval pipeline

1. **Query expansion** — legal-term synonym expansion (e.g., `breach` → `default breach`)
2. **Hybrid fusion** — FTS (PostgreSQL) + vector (pgvector) via RRF (k=30, weights 0.65/0.35)
3. **LLM verification** — `qwen3:8b` via Ollama binary YES/NO: "Does this passage contain the answer?"

### Verifier (ADR 009, accepted)

- **Architecture**: LLM-as-verifier via Ollama (host.docker.internal:11434 from container)
- **Model**: `qwen3:8b` (production default; `VERIFIER_MODEL` env var to override)
- **Prompt**: Binary YES/NO answer-containment detection
- **Score**: Binary decision (YES → 0.85, NO → 0.15); threshold via `VERIFIER_THRESHOLD` (default 0.5)
- **Latency**: ~12s per citation, 5 citations per question

**Why LLM?** Cross-encoder and NLI approaches were tested and revoked — they measure topical relevance, not answer containment. Only LLM generation can classify "does this passage actually answer this question?"

### Sync vs async `/ask`

| Endpoint | Verified | Latency | Use case |
|----------|----------|---------|----------|
| `POST /api/v1/matters/{id}/ask` | No (returns raw citations) | <1s | Fast review, UI preview |
| `POST /api/v1/matters/{id}/ask-async` | Yes (LLM verification) | ~60s (5 citations × 12s) | Verified answers for export |

Per ADR 010, sync `/ask` is intentionally unverified. `/ask-async` is the only path to verified answers.

---

## Roadmap

| Phase | Weeks | Focus | Status |
|-------|-------|-------|--------|
| Discover and specify | 1-2 | Workflow map, economic baseline, risk baseline, buyer map, corpus rules, 50-question benchmark, threat model | **Complete** |
| Build the evidence engine | 3-4 | Matter creation, ingestion with page-level provenance, hybrid retrieval with citation objects | **Complete** |
| Turn evidence into reviewable work | 5-6 | Matter Q&A with citation inspection, chronology, issue table, internal memo draft | **Complete** |
| Make governance visible | 7-8 | Identity, roles, matter scope, session controls, audit ledger, approval binding | **In progress** |
| Package, attack, recover | 9-10 | Docker Compose release, red-team, benchmark, restore drill, pilot-readiness packet | Planned |
| Pilot and decide | 11-12 | One paid design-partner pilot, closeout, go/narrow/stop decision | Planned |

Full roadmap detail: [Product Roadmap](docs/specification/roadmap.md). Weekly scorecard: [Weekly Scorecard](plans/weekly-scorecard.md).

---

## Status

**Week 7 complete.** Implemented and running:

- **Retrieval pipeline** — hybrid FTS + vector fusion (RRF), query expansion with legal-term synonyms, pgvector storage
- **Verifier** — LLM-as-verifier (qwen3:8b via Ollama) checks whether retrieved passages actually answer the question; strict mode (fail-closed)
- **Q&A workspace** — dark-themed SPA with matter selector, document inventory, citation cards, source inspector, async polling
- **Async verification** — submit-then-poll pattern: returns query_id immediately, verifies in background
- **Docker Compose** — API + PostgreSQL + pgvector, local Ollama for embeddings and verification
- **Frozen corpus v0.1** — 23 documents, 50-question gold set (29 answerable, 21 answer-absent)
- **Frozen corpus v0.1 Matter B** — 12 documents, employment/retaliation matter for cross-matter isolation testing

### Key metrics (Week 7, post verifier sweep)

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Recall@5 (expansion ON) | **86.2%** (25/29) | ≥80% | **PASS** |
| Verifier recall | **75.9%** (22/29) | ≥80% | Marginal — 3 leaks (Q23, Q30, Q35) |
| Answer-absent clean | **18/21** (85.7%) | 100% | Marginal — 3 leaks |
| Isolation | 8/8 blocked | 100% | **PASS** |
| Verifier latency | ~12s/citation | <30s | **PASS** |

### Verifier model comparison (Week 7 gold-set sweep)

| Model | Params | Recall | Answer-absent | Latency | Status |
|-------|--------|--------|---------------|---------|--------|
| **qwen3:8b** | 8B | **75.9%** | **85.7%** | **12s** | **Production** |
| qwen3:14b | 14B | 86.2% | 76.2% | 24.5s | Higher recall, more leaks |
| qwen3.5:9b | 9B | 65.5% | 85.7% | 6.6s | Too strict |
| ornith-1.5:35b | 35B MoE (3B active) | 58.6% | 81.0% | 4.4s | 3B active insufficient |
| muse-glimmer:30b-mlx | 30B dense | 0.0% | 100% | 18s | Always says NO |

**Key finding**: MoE models with few active parameters (ornith 3B active) and newer-generation models (qwen3.5:9b) over-strict the task. qwen3:8b is the best balance of recall, specificity, and latency.

### ADR status

| ADR | Title | Status |
|-----|-------|--------|
| 001 | Single-tenant deployment | Accepted |
| 002 | Monorepo layout | Accepted |
| 003 | Ingestion pipeline | Accepted |
| 004 | Antivirus (deferred to Phase 5) | Accepted |
| 005 | Chunking strategy | Accepted |
| 006 | Embedding model (nomic-embed-text) | Accepted |
| 007 | Retrieval fusion + reranker (RRF) | Accepted |
| 008 | Answer verification (LLM-as-verifier) | Accepted |
| 009 | Verifier recall recovery | Accepted |
| 010 | Sync /ask unverified | Accepted |
| 011 | Cross-encoder verification | **Revoked** |
| 012 | NLI verification | **Revoked** |

---

## Running locally

```bash
# Build and start
docker compose up -d

# Ingest corpus
docker exec ganymede-api-1 python3 /app/init_db.py
docker exec ganymede-api-1 python3 /app/tests/reingest_corpus.py

# Run gold-set evaluation
docker exec ganymede-api-1 python3 /app/tests/test_retrieval_gold_set.py
docker exec -e VERIFIER_MODEL=qwen3:8b ganymede-api-1 python3 /app/tests/eval_llm_verifier.py

# Frontend
open http://localhost:8080
```

**Requirements**: Docker Desktop, Ollama running on host (default `localhost:11434`), 8GB+ RAM recommended.

---

## Immediate next actions

1. **Week 8**: Governance — identity, roles, matter scope, session controls, audit ledger
2. **Week 9-10**: Docker release hardening, red-team attack suite, restore drill
3. **Week 11**: First paid design-partner pilot

---

## Commercial summary

- **Pilot:** $4,500 / 30 days — one matter, up to 10 named users, onboarding, three guided tasks, final scorecard.
- **Initial annual contract (hypothesis):** $24,000 platform + $150/user/month for additional users. Implementation $7,500 once. Managed dedicated hosting $12,000/year (infra billed separately).
- **Week 12 test:** one firm has paid, at least three users returned, citation quality met the launch threshold, and the buyer can name a realistic annual budget.
- **Target:** first paid design partner in Week 11.

See [Commercial Plan](docs/commercial/plan.md) and [Pricing Hypothesis](docs/commercial/pricing-hypothesis.md).

---

## Test suite

```bash
# All tests
docker exec ganymede-api-1 python3 -m pytest /app/tests/ -v

# Specific suites
docker exec ganymede-api-1 python3 -m pytest /app/tests/test_retrieval_gold_set.py -v
docker exec ganymede-api-1 python3 -m pytest /app/tests/test_isolation.py -v
docker exec ganymede-api-1 python3 -m pytest /app/tests/test_adversarial.py -v
docker exec ganymede-api-1 python3 -m pytest /app/tests/test_provenance.py -v
docker exec ganymede-api-1 python3 -m pytest /app/tests/test_verifier.py -v
```

**Test categories**: parsing, retrieval (Recall@5, isolation, answer-absent), citation provenance, adversarial (IDOR, prompt injection), verifier calibration, async verification.

---

*This is a product, engineering, and go-to-market plan. It does not establish legal compliance, security certification, or professional-responsibility advice. Those require review by qualified counsel and security professionals against the actual deployment and contracts.*
