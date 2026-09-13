# Ganymede — Development Plan

**Status:** Draft
**Date:** September 2026
**Review:** Weekly, at each phase boundary.

---

This is the implementation plan. It is derived from the roadmap and the specification. It is not the roadmap; it is the plan for how the implementation gets done, in tasks.

The development plan is written after the specification is frozen in Week 2. Before that, it is a skeleton.

---

## Pre-build phase (Weeks 1-2)

**Goal:** Produce the documentation that defines what is being built, before any implementation code is written.

### Week 1

**Discovery work (parallel with commercial):**
- [x] Conduct discovery interviews (target 8-10).
- [x] Produce workflow map, economic baseline, risk baseline, buying map.
- [x] Identify one practice workflow, one buyer, one champion, one costly job.
- [x] Assess whether a safe corpus is available.

**Documentation work:**
- [x] Repository exists (done).
- [x] ADR template exists (done).
- [x] README, SKILL.md, DEVELOPMENT.md exist (done).
- [x] Interview script exists (done).
- [x] Discovery outputs template exists (done).
- [x] Product contract exists (done).
- [x] Non-goals exist (done).
- [x] Test corpus rules exist (done).
- [x] Benchmark design exists (done).
- [x] Roadmap exists (done).
- [x] Threat model (started) and access matrix (started) exist.
- [x] Commercial plan, pricing hypothesis, pilot one-pager, pilot agreement inputs exist.
- [x] Sales and prospect tracking document exists.
- [x] Pilot readiness packet skeleton and pilot scorecard exist.
- [x] Architecture document and trust boundaries exist.
- [x] Decision log exists.

### Week 2

**Freeze:**
- [x] Sign off the product specification.
- [x] Choose and freeze the test corpus (synthetic).
- [x] Write the 50-question gold set.
- [x] Write the cross-matter isolation test specification.
- [x] Complete the freeze checklist.

**Exit:** specification, corpus, gold set, isolation spec all frozen and signed.

---

## Phase 1 — Week 3: Ingestion pipeline

### Week 3 — Ingestion pipeline

**Build:**
- [x] Document upload → parsing → chunking → embedding → pgvector index.
- [x] SHA-256 dedup at document and chunk level.
- [x] Parser version recorded per chunk.
- [x] Scanned PDF handling (Tesseract OCR fallback).
- [x] Blank PDF detection and skip.

**Test:**
- [x] Ingest corpus-v0.1 (23 docs) and corpus-v0.1-matter-b (12 docs).
- [x] Verify chunk counts, embedding dims, dedup behavior.
- [x] Verify parser_version recorded.

**Exit:** corpus ingested, chunks embedded, searchable.

---

## Phase 2 — Week 4: Retrieval quality

### Week 4 — PostgreSQL FTS + pgvector fusion, Reranker

**Build:**
- [x] FTS (tsvector/tsquery, OR-tsquery for multi-term).
- [x] pgvector HNSW index (ivfflat for now).
- [x] RRF fusion (k=30, weights 0.65 FTS / 0.35 vector).
- [x] RRF abstention gates (0.003 primary, 0.005 secondary).
- [x] MIN_VECTOR_SIMILARITY = 0.55.
- [x] Local cross-encoder reranker wiring (cross-encoder/ms-marco-MiniLM-L-6-v2).
- [x] Fail-loud embedding service (no silent random fallback).
- [x] Citation object with retrieval_scores (fts_rank, vector_similarity, rrf_score, reranker_score).
- [x] Query expansion service (date normalization + legal-term synonyms).
- [x] Post-retrieval verifier (qwen3:4b, local Ollama).
- [x] Verifier fast-path design (dual-threshold RRF + vector).

**Test:**
- [x] Recall@5 on gold set.
- [x] Exact-name search, dates, negation, answer-absent.
- [x] Cross-matter isolation (100% attacks blocked). — **PASS (8/8 blocked, verified 2026-09-12)**
- [x] 80% Recall@5 and zero unauthorized passages. — **PASS (86.2% Recall@5 = 25/29 with legal_synonyms expansion; 21/21 answer-absent clean with verifier; see ADR 008 Addendum and decision log 2026-09-13)**
- [ ] Reranker improves precision without unacceptable latency. — **FAIL (zero recall gain, +520 ms/query; see ADR 007 Addendum)**

**Exit:** evidence returned before prose. — **MET (86.2% recall, 21/21 answer-absent clean, Week 5 unblocked 2026-09-13)**

---

## Phase 3 — Weeks 5-6: Reviewable Q&A

### Week 5 — Q&A with citation inspection

**Build:**
- [ ] Matter home, document inventory, question workspace, answer history.
- [ ] Split-view source inspector.
- [ ] Citation drawer: click opens exact page, highlights passage.
- [ ] Citation feedback: supporting, weak, wrong, inaccessible.
- [ ] Streaming answer, prompt-injection filtering, quoted-source boundaries.

**Research:**
- [ ] Five usability sessions, same task and corpus.

**Exit:** users can verify a key claim in under 20 seconds without training.

### Week 6 — Artifact generation

**Build:**
- [ ] Chronology builder (auto-extract dates → timeline).
- [ ] Issue/argument outline generator.
- [ ] Deposition prep packet.
- [ ] Document production log.
- [ ] All artifacts cite sources; editable; export to DOCX/PDF.

**Test:**
- [ ] Artifact accuracy vs. gold set.
- [ ] Citation integrity under edit.

**Exit:** artifact saves 50%+ time vs. manual on benchmark tasks.

---

## Phase 4 — Weeks 7-8: Hardening

### Week 7 — Security & access

**Build:**
- [ ] JWT auth, role-based access (admin, attorney, paralegal, reviewer, IT operator).
- [ ] Row-level security on matters (enforced at DB, not app).
- [ ] Audit log: every query, citation, artifact, export.
- [ ] Prompt injection defenses: input sanitization, output quoting, citation boundaries.

**Test:**
- [ ] Penetration test (auth bypass, injection, data leakage).
- [ ] Isolation regression (8 attacks).

**Exit:** no critical findings; isolation holds.

### Week 8 — Operations & reliability

**Build:**
- [ ] Health endpoints, structured logging, metrics (latency, error rates, queue depths).
- [ ] Backup/restore runbook (pg_dump, volume snapshots, corpus re-ingest).
- [ ] Capacity model: storage growth, embedding compute, query throughput.

**Test:**
- [ ] Chaos: DB restart, Ollama restart, disk pressure, network partition.
- [ ] Restore drill: fresh install from backup.

**Exit:** fresh install and restore succeed from written runbook.

---

## Phase 5 — Weeks 9-10: Pilot preparation

### Week 9 — Pre-pilot hardening

**Build:**
- [ ] Pilot agreement template, data processing addendum, security questionnaire.
- [ ] Onboarding checklist: corpus import, user provisioning, access verification.
- [ ] Known limits document (what the system does not do).

**Test:**
- [ ] End-to-end dry run with internal "friendly" matter.
- [ ] Security regression.
- [ ] Benchmark regression.

**Exit:** pilot agreement ready; no critical defects.

### Week 10 — Red-team and pilot preparation

**Test:**
- [ ] Security regression.
- [ ] Benchmark.
- [ ] Load.
- [ ] Failure injection.
- [ ] Prompt injection in documents, poisoned citations, DoS uploads, cross-matter access, malicious file types, data deletion, restore, role revocation, model failure, disk exhaustion.

**Prepare:**
- [ ] Pilot agreement inputs.
- [ ] Security brief, quality brief, operations brief.
- [ ] Data-flow diagram.
- [ ] Known limits.

**Train:**
- [ ] 30-minute onboarding.
- [ ] Three guided tasks.
- [ ] Reviewer checklist.

**Exit:** no critical defects; all quality and recovery gates met or waived in writing.

---

## Phase 6 — Weeks 11-12: Pilot and decide

### Week 11 — Paid pilot launch

**Deploy:**
- [ ] One firm, one approved matter, 5-10 users.
- [ ] Import corpus with firm present.
- [ ] Confirm access.
- [ ] Run three guided tasks.
- [ ] Collect pre-pilot baseline.

**Hold:** office hours twice in first week. No custom features mid-session.

**Measure:** activation, weekly use, task completion, ratings, edits, reported time.

**Exit:** three activated users and ten meaningful tasks in first seven days.

### Week 12 — Decision

**Observe:** users completing the original workflow. Compare with Week 1 baseline.

**Review:** every low-rated output and support event. Buyer closeout: value, risk, missing requirement, budget, procurement path, willingness to continue.

**Build:** only fixes for blockers, data risk, retrieval quality, or usability failures.

**Close:** ask for annual conversion, second-matter expansion, one referral.

**Exit:** written decision backed by behavior and money.

---

## After the pilot

If go: onboard two more firms; harden the same workflow.
If narrow: make the winning artifact the product.
If fix: four-week reliability sprint; no new features.
If stop: interview loss reasons; choose a new vertical.

---

*This plan is provisional until Week 2. It will be updated after discovery and spec freeze. Tasks will be added, removed, and sequenced as the specification solidifies.*
