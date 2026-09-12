## 2026-09-12 — Week 4 retrieval remediation measurement complete; pipeline not ready for Week 5

**Decision:** Week 4 retrieval remediation is complete. The "up" tuning (RRF k=30, weights 0.65/0.35, abstention gates 0.003/0.005, MIN_VECTOR_SIMILARITY=0.55, fail-loud embeddings) improved Recall@5 from 58.3% (24-question subset) to 65.5% (29-question full set), but the pipeline remains below the 80% target and answer-absent precision is 0%. The pipeline is NOT ready for Week 5.

**Measurement results (all on frozen gold set, 29 answerable + 22 unanswerable = 51 total):**

1. **Recall@5 on full 29-question answerable set:** 65.5% (19/29). Target: 80%. Status: FAIL.
   - 10 persistent misses: Q05, Q09, Q11, Q13, Q14, Q25, Q33, Q36, Q46, Q49.
   - Q14 (court reporter in deposition notice) was a false negative caused by the SHA-256 mismatch in the corrigendum: retrieval finds DOC-013 (SHA `ced31546...`, the regenerated PDF) but the test expected SHA `d915c545...` (the MANIFEST value). Fixing the test to use the on-disk SHA recovers Q14. The remaining 9 misses are structural: FTS/vector fusion fails to surface the correct document for specific question types (dates, invoice amounts, deposition details).

2. **Answer-absent precision (22 unanswerable questions):** 0/22 (0%). Target: 22/22 (100%). Status: FAIL.
   - 16 NOT_IN_CORPUS questions: all return 5 citations.
   - 6 formal ANSWER_ABSENT (Q39-Q44): all return 5 citations.
   - RRF abstention gates (0.003/0.005) did NOT close the leak. Top results for unanswerable queries have RRF scores of 0.008–0.032 — above the gates. Raising the gates would block legitimate results. The answer-absent problem is unsolved by the current retrieval pipeline.

3. **Isolation battery:** 8/8 attacks blocked. Target: 8/8 (100%). Status: PASS.
   - Matter A-scoped user cannot reach Matter B content across all 8 attack vectors.

4. **ADR-006 head-to-head (nomic-embed-text vs bge-m3):** nomic-embed-text 64.3% vs bge-m3 42.9% Recall@5 on the 28-question set. **Decision: retain nomic-embed-text.** bge-m3 loses 21.4 pp recall and is 30× slower per query (86 ms vs 2636 ms).

5. **ADR-007 reranker evaluation:** cross-encoder/ms-marco-MiniLM-L-6-v2 adds 578% latency (+520 ms/query, 90→610 ms) for zero recall gain on the 10 hard misses. **Decision: keep reranker wiring, disable by default** (`RECRANKER_MODEL_PATH=""`), re-enable only if a legal-domain cross-encoder demonstrates recall gain.

6. **ClamAV:** `clamdscan` binary present in API container but `clamd` daemon not running (no sidecar, ARM64 incompatibility). `antivirus.py` service exists but scans fail with "Could not connect to clamd". Second deferral logged — same as Week 3.

7. **Corrigendum:** 4 documents replaced during frozen window (DOC-009, DOC-011, DOC-013, DOC-020). SHA-256 mismatches documented in `testdata/corpus-v0.1/CORRIGENDUM.md`. All affected gold question pointers re-verified against on-disk files — content matches expectations. Process violation recorded; no substantive impact on retrieval quality after re-ingestion.

**Next steps before Week 5:**
- Fix the 10 structural misses via query expansion / hybrid query rewriting (date normalization, legal-term synonyms, entity expansion).
- Solve answer-absent precision via post-retrieval verification (LLM judge / entailment check / explicit no-answer classifier).
- Decide on ClamAV: run daemon in API container, or accept deferral with documented risk.

**Related:** `testdata/corpus-v0.1/CORRIGENDUM.md`; `adr/006-embedding-model-addendum.md`; `adr/007-retrieval-fusion-reranker-addendum.md`; `plans/development-plan.md` (Week 4 boxes updated).

---

## 2026-09-12 — Corpus process break: four PDFs regenerated during frozen window, corrigendum written

**Decision:** Four documents in the frozen corpus v0.1 were regenerated outside the freeze process (DOC-009, DOC-011, DOC-013, DOC-020). The on-disk SHA-256 hashes no longer match the frozen MANIFEST.md. This is a process violation.

**Why:** The PDFs were likely regenerated via `reportlab` to fix "blank" rendering issues, but no version bump, manifest re-signing, or gold-set re-binding occurred.

**Impact:** Procedural only. All affected gold question pointers re-resolved against on-disk files — content matches expectations. Retrieval test results are valid against the current on-disk corpus.

**Rule (going forward):** A frozen corpus is immutable. If a file must be replaced: (1) bump corpus version (v0.1 → v0.2), (2) recompute SHA-256 for all affected files in new MANIFEST.md, (3) re-bind every gold question pointer touching those documents, (4) re-run full retrieval + isolation battery, (5) log in `decisions/log.md`.

**Related:** `testdata/corpus-v0.1/CORRIGENDUM.md`; `testdata/corpus-v0.1/MANIFEST.md`; `decisions/log.md` (this entry).

---

## 2026-09-12 — Database cleaned: 691 duplicate documents removed, corrigendum alignment applied

**Decision:** Database had 691 duplicate document records (is_duplicate=true) from repeated test runs, plus 4 corrigendum document records with old MANIFEST SHA-256 values. All duplicates removed; corrigendum documents aligned to on-disk SHA-256 (one record per document, matching the current file on disk).

**Why:** Duplicate records pollute retrieval results (the old SHA-256 records for DOC-009, DOC-011, DOC-013, DOC-020 were being returned instead of the on-disk versions). The test for Q14 was failing because the expected SHA came from the MANIFEST, not the on-disk file.

**What changed:** Raw SQL deletion (ORM cascade disabled on foreign keys). 691 duplicate documents + dependent chunks/pages/embeddings/ingestion_jobs removed. 4 old-SHA corrigendum records removed. Final state: 44 unique documents, all SHA-256 values match on-disk files.

**Related:** `testdata/corpus-v0.1/CORRIGENDUM.md`; `api/tests/test_retrieval_gold_set_full.py` (now uses is_duplicate=False filter for expected_shas).

---

## vs. ADRs

- **ADR:** material technical decision with context, consequences, and alternatives. Written before implementation.
- **Decision log:** narrower, operational, or provisional decisions. Still written down, still dated, still watched.

If a decision log entry grows into something that affects the architecture, it becomes an ADR.

---

*Tail of log trimmed — see file for earlier entries.*
