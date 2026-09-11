# Ganymede — Roadmap

**Status:** Draft
**Date:** September 2026
**Source:** 12-week MVP build plan
**Review trigger:** Weekly; formal review at each phase boundary.

---

## 12-week build to a paid design-partner pilot

Commercial work runs in parallel from Day 1. The build has two tracks: product evidence and buyer evidence. A technically successful MVP without a signed pilot is an unfinished experiment.

---

## Phase 1 — Weeks 1-2: Discover and specify

**Goal:** Prevent a generic chatbot before code hardens.

### Week 1 — Choose the matter and recruit the buyer

**Build:** Repository, ADR template, product analytics event description, 30-account prospect list, interview script, one-page pilot schema, clickable low-fidelity workflow.

**Sell:** Request 8 meetings.

**Exit:** One practice workflow, one buyer, one champion, one costly job. Three interviewees independently describe the same "before" baseline.

### Week 2 — Freeze scope, threats, and the evaluation corpus

**Build:** Data contract, threat model, access matrix, ingestion schema, gold-set harness.

**Validate:** 50 benchmark questions; 10 cross-matter attacks; 10 unsupported-answer tests.

**Sell:** Secure one design-partner letter or a written pilot-review commitment.

**Exit:** Signed-off spec and corpus; no unresolved critical data-flow question.

### Required discovery outputs

- **Workflow map:** trigger, inputs, actors, work, review, output.
- **Economic baseline:** people, hours, frequency, delay, write-offs.
- **Risk baseline:** where confidential data currently travels.
- **Buying map:** sponsor, approver, IT/security reviewer, end user, and budget owner.

### Questions worth asking

- Show me the last chronology or internal memo you built.
- Where did you lose time?
- What would make you distrust an answer immediately?
- Which data can never leave your control?
- Who approves a new tool and what evidence do they require?

### Do not proceed if

- The only interest is "AI is exciting."
- No one will supply a safe corpus or review outputs.
- The desired use case requires licensed legal content.
- The buyer expects autonomous legal advice or guaranteed accuracy.
- Every prospect demands a different first integration.

---

## Phase 2 — Weeks 3-4: Build the evidence engine

**Goal:** Ingestion and citations are the product core.

### Week 3 — Make every page attributable

**Build:** Matter creation, file upload, MIME validation, antivirus scanning, content hashing, duplicate detection, parser/OCR routing, page segmentation, ingestion status. Preserve the original file and a normalized representation.

**Test:** Upload API, parse queue, OCR path. Digital PDFs, scans, DOCX, TXT, tables, rotated pages, corrupt files, duplicates.

**Observe:** Per-file status, parser version, duration, page count, error reason.

**Exit:** 95% supported-file success on the frozen corpus; failures recover safely.

### Week 4 — Return evidence before prose

**Build:** Hybrid retrieval with metadata filters, PostgreSQL full-text search, local embeddings, and reranking. Apply customer and matter scope in the database query — never by prompt instruction. Render retrieved passages first, then generate an answer constrained to those passages.

**Build:** Chunker, embedding jobs, FTS/vector fusion, reranker, citation object schema.

**Test:** Recall@5, exact-name search, dates, negation, answer-absent, cross-matter isolation.

**Exit:** 80% Recall@5 and zero unauthorized passages across the attack suite.

### Key design decision

Do not introduce Neo4j or a generalized knowledge graph yet. Store entities, dates, and relationships in ordinary tables sufficient for chronology and issue views. Add a graph engine only if the pilot demonstrates a query that relational structures cannot serve cleanly.

### Performance discipline

Batch embeddings. Cache by content hash. Keep model interfaces swappable. Measure every stage separately so slow retrieval is not mistaken for slow inference.

---

## Phase 3 — Weeks 5-6: Turn evidence into reviewable work

**Goal:** The interface should make verification faster.

### Week 5 — Ship matter Q&A with citation inspection

**Build:** Matter home, document inventory, question workspace, answer history, split-view source inspector. Clicking a citation opens the exact page and highlights the relevant passage. Users can mark a citation as supporting, weak, wrong, or inaccessible.

**Guard:** Prompt injection filtering, quoted-source boundaries, no hidden tool invocation.

**Research:** Five usability sessions using the same task and corpus.

**Exit:** Users can verify a key claim in under 20 seconds without training.

### Week 6 — Add two structured artifacts and one guarded draft

**Build:** Chronology, issue table, memo builder, version history, DOCX/PDF export.

**Review:** Row-level source links, editable fields, "uncertain" and "contradicted" states.

**Validate:** Two attorneys or legal reviewers score 25 representative outputs.

**Exit:** 90% of material claims supported; reviewer can correct outputs before export.

### Artifact contracts

| Artifact | Required fields | Never infer silently |
|----------|----------------|----------------------|
| Chronology | Date, event, actor, source | Unknown dates or ordering |
| Issue table | Issue, support, contrary, gap | Legal conclusion from silence |
| Internal memo | Question, record, analysis, limits | Authority outside corpus |

### Interface principle

Make source review a first-class action. The reader should never have to trust a citation merely because it looks formal.

### Drafting principle

Exports carry "AI-assisted draft — attorney review required," a generated timestamp, and a source list. The firm controls whether that label is retained in downstream work product.

### Scope discipline

Do not build free-form agent orchestration in these weeks. The product wins through a reliable, reviewable path from record to draft.

---

## Phase 4 — Weeks 7-8: Make governance visible

**Goal:** Authorization is a workflow, not a disclaimer.

### Week 7 — Enforce identity, role, and matter scope

**Build:** Organization users, roles, matter membership, session controls, administrative access review.

**Roles:** Administrator, attorney, reviewer, support operator. Least privilege by default.

**Test:** IDOR, guessed document IDs, stale sessions, revoked users, export permission.

**Exit:** All cross-matter and privilege-escalation tests fail safely.

### Week 8 — Bind approval to the exact artifact

**Build:** Append-only ledger, artifact versions, approval binding, audit viewer/export.

**Privacy:** Minimize prompt text in logs; separate operational metrics from matter content.

**Review:** Walk the evidence chain with a managing partner and technical reviewer.

**Exit:** Every exported artifact reconstructs its source and approval lineage.

### The chain

Knowledge (approved matter sources) → Cognition (local model proposes) → Policy (deterministic decision) → Human (reviews and approves) → Evidence (ledger preserves lineage).

### Align to professional duties

Adapt the Authority Non-Equivalence Principle: no model response, confidence score, or requested action is authorization. The model proposes content; the typed policy and a human decide whether it can leave the workspace. The product should surface the facts needed for a lawyer to evaluate their professional duties, not promise automatic compliance.

---

## Phase 5 — Weeks 9-10: Package, attack, and recover

**Goal:** The pilot starts only after a clean-machine drill.

### Week 9 — Turn the codebase into an installable product

**Build:** Docker Compose release for a customer-controlled Linux server or private VPC. Automate environment validation, migrations, local model installation, TLS configuration, administrator bootstrap, backups, updates, and rollback.

**Reference:** Document exact hardware, model, corpus, throughput, storage growth.

**Support:** Diagnostic bundle that redacts matter content and secrets by default.

**Exit:** Fresh install and restore succeed from written runbook; no undocumented steps.

### Week 10 — Red-team the product and prepare the pilot

**Test:** Security regression, benchmark, load, failure injection, dependency scan.

**Prepare:** Pilot agreement inputs, security brief, data-flow diagram, known limits.

**Train:** 30-minute onboarding, three guided tasks, reviewer checklist.

**Exit:** No critical defects; all quality and recovery gates met or waived in writing.

### Pilot-readiness packet

- **Security brief:** data flow, egress policy, encryption responsibilities, operator access, retention, deletion, incident contact.
- **Quality brief:** benchmark method, model/version, citation results, known limitations, required human review.
- **Operations brief:** installation, backups, restore, updates, logs, support path, recovery objective.

### Do not overclaim security

"Runs in a customer-controlled environment" is verifiable. "Secure," "privilege-safe," or "compliant" requires a defined control set and independent evidence. Before pilots, have qualified counsel review contracts and have a security professional review the threat model and deployment.

### Minimum controls

TLS, secure cookies, encrypted volume, managed secrets, default-deny egress, daily encrypted backup, tested restore, administrator access logging, and a documented update policy.

---

## Phase 6 — Weeks 11-12: Pilot and decide

**Goal:** Charge for a bounded outcome, then watch behavior.

### Week 11 — Launch one paid design-partner pilot

**Deploy:** One firm, one approved matter, 5-10 users. Import the corpus with the firm present, confirm access, run the three guided tasks, collect a pre-pilot baseline.

**Hold:** Short office hours twice during the first week. Do not build custom features mid-session.

**Offer:** 30 days, one matter, up to 10 users, fixed onboarding and review scope. $4,500 paid pilot, credited toward an annual agreement if converted.

**Measure:** Activation, weekly use, task completion, ratings, edits, reported time.

**Exit:** Three activated users and ten meaningful tasks in the first seven days.

### Week 12 — Convert evidence into a go, narrow, or stop decision

**Observe:** Users completing the original workflow. Compare time and quality with the Week 1 baseline.

**Review:** Every low-rated output and support event. Conduct a buyer closeout: value, risk, missing requirement, budget, procurement path, and willingness to continue.

**Build:** Only fixes for blockers, data risk, retrieval quality, or usability failures.

**Close:** Ask for annual conversion, second-matter expansion, and one referral.

**Exit:** A written decision backed by behavior and money, not compliments.

### Decision matrix

| Outcome | Evidence | Next move |
|---------|----------|-----------|
| Go | Repeated use + quality pass + paid continuation | Onboard two more firms; harden the same workflow |
| Narrow | One artifact wins; broader workspace does not | Make that artifact the product |
| Fix | Demand exists; retrieval or deployment misses | Four-week reliability sprint; no new features |
| Stop | No recurring use or budget after valid trial | Interview loss reasons; choose a new vertical |

### Pricing is a test, not a truth

The $4,500 pilot is an initial hypothesis designed to filter for a real buyer and pay for high-touch onboarding. Test the reaction in Week 1. If buyers reject it, identify whether the objection is price, trust, procurement, or insufficient value before discounting.

---

## After a successful pilot: the next 90 days

| Area | Work |
|------|------|
| Reliability | Improve difficult PDFs, evaluation coverage, incremental indexing, backup automation, upgrade safety |
| Workflow | Deepen the winning artifact, add firm templates, batch review, cited comparison across versions |
| Security | Independent penetration test, formal control matrix, security questionnaire library, incident exercise |

---

## Commercial cadence (parallel track, Day 1)

| Weeks | Customer motion | Evidence to collect |
|-------|----------------|---------------------|
| 1-2 | 8-10 discovery interviews | Workflow, baseline, buyer, risk |
| 3-4 | Two prototype reviews | Citation trust and corpus fit |
| 5-6 | Five task-based usability tests | Verification speed and artifact value |
| 7-8 | Buyer + IT/security walkthrough | Approval blockers and evidence needs |
| 9-10 | Pilot proposal and diligence | Price reaction and contracting path |
| 11-12 | Paid pilot and conversion ask | Use, quality, savings, continuation |

---

## Weekly founder scorecard

| Dimension | Question answered every Friday | Evidence |
|-----------|-------------------------------|----------|
| Demand | Did a qualified buyer move closer to payment? | Meeting, commitment, proposal, signature |
| Usage | Did a user complete the target job? | Task event and observation notes |
| Quality | Did benchmark performance improve or hold? | Versioned evaluation report |
| Trust | Can every output be reviewed and explained? | Citations, lineage, approvals, audit |
| Reliability | Can a clean deployment install and recover? | Automated test and restore log |
| Focus | What did we decline to build? | Decision log and deferred backlog |

---

## Definition of done at each layer

| Layer | Release | Pilot |
|-------|---------|-------|
| Feature | Typed contract, tests, permission checks, failure state, observable events, and user-facing limits | — |
| Release | Benchmark passes, image signed, migration tested, backup restored, runbook updated | — |
| Pilot | — | Agreement signed, corpus authorized, users trained, baseline recorded, closeout scheduled |

---

## North-star sentence

A lawyer can move from a question about the record to a reviewable, cited draft without sending matter data to a public model provider.

---

## Assumptions to validate

- Civil litigation is the right first wedge.
- Firms will accept single-tenant deployment.
- A 30-day, $4,500 pilot is both purchasable and qualifying.
- Firm-owned matter content is sufficient.
- Buyers will trade some speed for verifiability.

---

## Founder time budget

60% product + quality · 25% customer work · 15% operations.

---

*This roadmap is provisional until Week 2. It will be updated after discovery and spec freeze.*
