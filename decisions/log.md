## 2026-09-12 — Week 4 retrieval remediation measurement complete; pipeline 1 question short of target, answer-absent unresolved

**Decision:** Week 4 retrieval remediation is complete. The "up" tuning (RRF k=30, weights 0.65/0.35, abstention gates 0.003/0.005, MIN_VECTOR_SIMILARITY=0.55, fail-loud embeddings) improved Recall@5 from 58.3% (24-question subset, dirty DB) to 79.3% (29-question full set, clean DB), which is 0.7 pp below the 80% target. Answer-absent precision is 0%. The pipeline is NOT ready for Week 5 — answer-absent is the gating defect.

**Measurement results (all on frozen gold set, 29 answerable + 21 unanswerable = 50 total):**

1. **Recall@5 on full 29-question answerable set:** 79.3% (23/29). Target: 80%. Status: FAIL (1 question short).
   - 6 persistent misses: Q05, Q09, Q25, Q33, Q46, Q49.
   - Q14 (court reporter in deposition notice) was a false negative caused by the SHA-256 mismatch in the corrigendum: retrieval finds DOC-013 (SHA `ced31546...`, the regenerated PDF) but the test expected SHA `d915c545...` (the MANIFEST value). Fixing the DB (removing old-SHA record) recovers Q14, confirming the retrieval was correct — the test was comparing against the wrong SHA.
   - The remaining 6 misses are structural: FTS/vector fusion fails to surface the correct document for specific question types (dates, invoice amounts, multi-document synthesis).

2. **Answer-absent precision (21 unanswerable questions):** 0/21 (0%). Target: 21/21 (100%). Status: FAIL.
   - 15 NOT_IN_CORPUS questions: all return 5 citations.
   - 6 formal ANSWER_ABSENT (Q39-Q44): all return 5 citations.
   - RRF abstention gates (0.003/0.005) did NOT close the leak. Top results for unanswerable queries have RRF scores of 0.008–0.032 — above the gates. Raising the gates would block legitimate results. The answer-absent problem is unsolved by the current retrieval pipeline.

3. **Isolation battery:** 8/8 attacks blocked. Target: 8/8 (100%). Status: PASS.
   - Matter A-scoped user cannot reach Matter B content across all 8 attack vectors.

4. **ADR-006 head-to-head (nomic-embed-text vs bge-m3):** nomic-embed-text 64.3% vs bge-m3 42.9% Recall@5 on the 28-question set. **Decision: retain nomic-embed-text.** bge-m3 loses 21.4 pp recall and is 30× slower per query (86 ms vs 2636 ms).

5. **ADR-007 reranker evaluation:** cross-encoder/ms-marco-MiniLM-L-6-v2 adds 578% latency (+520 ms/query, 90→610 ms) for zero recall gain on the 6 hard misses. **Decision: keep reranker wiring, disable by default** (`RECRANKER_MODEL_PATH=""`), re-enable only if a legal-domain cross-encoder demonstrates recall gain.

6. **ClamAV:** `clamdscan` binary present in API container but `clamd` daemon not running (no sidecar, ARM64 incompatibility). `antivirus.py` service exists but scans fail with "Could not connect to clamd". Second deferral logged — same as Week 3.

7. **Corrigendum:** 4 documents replaced during frozen window (DOC-009, DOC-011, DOC-013, DOC-020). SHA-256 mismatches documented in `testdata/corpus-v0.1/CORRIGENDUM.md`. All affected gold question pointers re-verified against on-disk files — content matches expectations. Process violation recorded; no substantive impact on retrieval quality after DB cleanup.

8. **Database cleanup:** 691 duplicate documents removed via raw SQL (ORM cascade disabled on FKs). 4 old-SHA corrigendum records removed. Final state: 44 unique documents, all SHA-256 values match on-disk files. The `is_duplicate=False` filter added to test's `expected_shas` lookup as defense-in-depth.

**Next steps before Week 5:**
- Close the 0.7 pp Recall@5 gap via query expansion / hybrid query rewriting (date normalization, legal-term synonyms, entity expansion). Target: 1 more hit from the 6 structural misses.
- Solve answer-absent precision via post-retrieval verification (LLM judge / entailment check / explicit no-answer classifier). This is the gating defect.
- Decide on ClamAV: run daemon in API container, or accept deferral with documented risk.

**Related:** `testdata/corpus-v0.1/CORRIGENDUM.md`; `adr/006-embedding-model-addendum.md`; `adr/007-retrieval-fusion-reranker-addendum.md`; `plans/development-plan.md` (Week 4 boxes updated).

---

## 2026-09-12 — Corpus process break: four PDFs regenerated during frozen window, corrigendum written

**Decision:** Four documents in the frozen corpus v0.1 were regenerated outside the freeze process (DOC-009, DOC-011, DOC-013, DOC-020). The on-disk SHA-256 hashes no longer match the frozen MANIFEST.md. This is a process violation.

**Why:** The PDFs were likely regenerated via `reportlab` to fix "blank" rendering issues, but no version bump, manifest re-signing, or gold-set re-binding occurred.

**Impact:** Procedural only. All affected gold question pointers re-resolved against on-disk files — content matches expectations. Retrieval test results are valid against the current on-disk corpus. One false negative (Q14) in the retrieval test was caused by this mismatch; resolved by removing old-SHA DB records.

**Rule (going forward):** A frozen corpus is immutable. If a file must be replaced: (1) bump corpus version (v0.1 → v0.2), (2) recompute SHA-256 for all affected files in new MANIFEST.md, (3) re-bind every gold question pointer touching those documents, (4) re-run full retrieval + isolation battery, (5) log in `decisions/log.md`.

**Related:** `testdata/corpus-v0.1/CORRIGENDUM.md`; `testdata/corpus-v0.1/MANIFEST.md`; `decisions/log.md` (this entry).

---

## 2026-09-12 — Database cleaned: 691 duplicate documents removed, corrigendum alignment applied

**Decision:** Database had 691 duplicate document records (is_duplicate=true) from repeated test runs, plus 4 corrigendum document records with old MANIFEST SHA-256 values (two `is_duplicate=False` records per corrigendum document — one with MANIFEST SHA, one with on-disk SHA). All duplicates removed; old-SHA corrigendum records removed. Final state: 44 unique documents, one record per document, all SHA-256 values match on-disk files.

**Why:** Duplicate records pollute retrieval results. The old-SHA records for DOC-009, DOC-011, DOC-013, DOC-020 were being returned as `expected_shas` by the test's `first()` query, while the retrieval pipeline returned chunks inheriting the on-disk SHA from the other record. This caused a false negative on Q14.

**What changed:** Raw SQL deletion (ORM cascade disabled on foreign keys — ingestion_jobs, pages, chunks, chunk_embeddings deleted in reverse dependency order before documents). 691 duplicate documents + 4 old-SHA corrigendum records removed. `is_duplicate=False` filter added to test's `expected_shas` lookup as defense-in-depth.

**Related:** `testdata/corpus-v0.1/CORRIGENDUM.md`; `api/tests/test_retrieval_gold_set_full.py` (now uses is_duplicate=False filter for expected_shas).

---

## 2026-09-12 — DB schema tech debt: FK cascade deletes disabled, raw SQL used for cleanup

**Decision:** Log a schema tech debt. The SQLAlchemy models do not configure cascade deletes on foreign key relationships (no `cascade="all, delete-orphan"` on `Document→pages`, `Document→chunks`, `Chunk→chunk_embeddings`, `Document→ingestion_jobs`). When cleaning 691 duplicate documents + 4 corrigendum old-SHA records on 2026-09-12, ORM-level deletion failed with `NotNullViolation` (ingestion_jobs.document_id) and `ForeignKeyViolation` (pages.document_id). The cleanup was performed via raw SQL in reverse-dependency order: `chunk_embeddings → chunks → pages → ingestion_jobs → documents`.

**Impact:** Test DB only. The cleanup worked but required manual SQL ordering knowledge. If a future cleanup needs to remove documents, the same FK issue will recur.

**Fix (deferred):** Add `cascade="all, delete-orphan"` to the `Document.pages`, `Document.chunks`, and related relationships in `api/app/models/`. This is a test-environment issue but the schema should be correct regardless.

**Related:** `decisions/log.md` (DB cleanup entry above); `api/app/models/` (relationship definitions).

- **ADR:** material technical decision with context, consequences, and alternatives. Written before implementation.
- **Decision log:** narrower, operational, or provisional decisions. Still written down, still dated, still watched.

If a decision log entry grows into something that affects the architecture, it becomes an ADR.

---

*Tail of log trimmed — see file for earlier entries.*
