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
- [ ] Conduct discovery interviews (target 8-10).
- [ ] Produce workflow map, economic baseline, risk baseline, buying map.
- [ ] Identify one practice workflow, one buyer, one champion, one costly job.
- [ ] Assess whether a safe corpus is available.

**Documentation work:**
- [ ] Repository exists (done).
- [ ] ADR template exists (done).
- [ ] README, SKILL.md, DEVELOPMENT.md exist (done).
- [ ] Interview script exists (done).
- [ ] Discovery outputs template exists (done).
- [ ] Product contract exists (done).
- [ ] Non-goals exist (done).
- [ ] Test corpus rules exist (done).
- [ ] Benchmark design exists (done).
- [ ] Roadmap exists (done).
- [ ] Threat model (started) and access matrix (started) exist.
- [ ] Commercial plan, pricing hypothesis, pilot one-pager, pilot agreement inputs exist.
- [ ] Sales and prospect tracking document exists.
- [ ] Pilot readiness packet skeleton and pilot scorecard exist.
- [ ] Architecture document and trust boundaries exist.
- [ ] Decision log exists.

### Week 2

**Freeze:**
- [x] Sign off the product specification.
- [x] Choose and freeze the test corpus (synthetic).
- [x] Write the 50-question gold set.
- [x] Write 10 cross-matter attack tests.
- [ ] Write 10 unsupported-answer tests.
- [ ] Complete the data contract, threat model, and access matrix.
- [ ] Secure a design-partner letter or written pilot-review commitment.

**Exit criteria:**
- [ ] One practice workflow, one buyer, one champion, one costly job identified.
- [ ] Signed-off spec and corpus exist.
- [ ] No unresolved critical data-flow question.
- [ ] Design-partner letter or written pilot-review commitment secured.

---

## Phase 2 — Weeks 3-4: Evidence engine

### Week 3 — Ingestion with provenance

**Build:**
- [x] Matter creation and user assignment.
- [x] File upload API with MIME validation, antivirus, size limits.
- [x] Content hashing and duplicate detection.
- [x] Parser/OCR routing: PyMuPDF, DOCX, TXT, OCRmyPDF/Tesseract.
- [x] Page segmentation and provenance recording.
- [x] Ingestion status and failure visibility.

**Test:**
- [x] Digital PDFs, scans, DOCX, TXT.
- [x] Tables, rotated pages.
- [x] Corrupt files, duplicates.
- [x] 95% supported-file success on frozen corpus.

**Exit:** failures recover safely; provenance is preserved.

### Week 4 — Hybrid retrieval with citations

**Build:**
- [ ] Chunker.
- [ ] Embedding jobs (batched, cached by content hash).
- [ ] PostgreSQL FTS + pgvector fusion.
- [ ] Reranker.
- [ ] Citation object schema (frozen).
- [ ] Matter scope enforced in retrieval query, not by prompt.

**Test:**
- [ ] Recall@5 on gold set.
- [ ] Exact-name search, dates, negation, answer-absent.
- [ ] Cross-matter isolation (100% attacks blocked).
- [ ] 80% Recall@5 and zero unauthorized passages.

**Exit:** evidence returned before prose.

---

## Phase 3 — Weeks 5-6: Reviewable work

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

### Week 6 — Chronology, issue table, memo

**Build:**
- [ ] Chronology: date, event, actor, source; editable; uncertain dates flagged.
- [ ] Issue table: issue, support, contrary, gap; no evidence means "not found."
- [ ] Memo builder: template-bound, assembles only reviewed facts and citations.
- [ ] Version history.
- [ ] Export (DOCX/PDF) with AI-assisted draft label, timestamp, source list.

**Validate:**
- [ ] Two attorneys or legal reviewers score 25 representative outputs.
- [ ] 90% of material claims supported; reviewer can correct before export.

**Exit:** reviewable path from record to draft.

---

## Phase 4 — Weeks 7-8: Governance

### Week 7 — Identity, roles, matter scope

**Build:**
- [ ] Organization users, roles, matter membership.
- [ ] Session timeout and revocation.
- [ ] Administrator access review.
- [ ] Authorization decision passed to retrieval as scoped identifiers.

**Roles:** administrator, attorney, reviewer, support operator. Least privilege by default.

**Test:**
- [ ] IDOR, guessed document IDs, stale sessions, revoked users, export permission.

**Exit:** all cross-matter and privilege-escalation tests fail safely.

### Week 8 — Audit and approval binding

**Build:**
- [ ] Append-only ledger, hash-chained.
- [ ] Artifact versions.
- [ ] Approval binding to exact artifact version, source set, user, time, policy decision.
- [ ] Audit viewer and export.
- [ ] Minimize prompt text in logs; separate operational metrics from matter content.

**Review:**
- [ ] Walk the evidence chain with a managing partner and technical reviewer.

**Exit:** every exported artifact reconstructs its source and approval lineage.

---

## Phase 5 — Weeks 9-10: Package, attack, recover

### Week 9 — Installable product

**Build:**
- [ ] Docker Compose release.
- [ ] Environment validation, migrations, local model installation, TLS configuration.
- [ ] Administrator bootstrap, backups, updates, rollback.
- [ ] Health checks.
- [ ] Signed release manifest.
- [ ] Diagnostic bundle that redacts matter content and secrets by default.

**Reference:**
- [ ] Document exact hardware, model, corpus, throughput, storage growth.

**Exit:** fresh install and restore succeed from written runbook.

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
