# Decision Log — 2026-09-13

---

## 2026-09-14 — Week 6 closeout: Docker/Ollama connectivity fix

**Decision:** The Docker build was never a registry/network issue. The root cause was Ollama reachability from inside the container: `localhost:11434` resolves to the container itself, not the host running Ollama.

**Fix (committed as `274e0d0`):**
- `docker-compose.yml`: Added `OLLAMA_ENDPOINTS=host.docker.internal:11434,localhost:11434`, `OLLAMA_URL=http://host.docker.internal:11434`, `extra_hosts: host.docker.internal:host-gateway`, and `./docs:/docs` mount
- `api/Dockerfile`: Pinned `python:3.11-slim@sha256:9534e5a8e315485d4061ed659af0fd78a284c015f9b73661b41d6bab25604534`
- `api/app/services/verifier.py`: `OLLAMA_URL` reads from env (default `http://host.docker.internal:11434`), timeout 60s→180s via `OLLAMA_TIMEOUT_SECONDS`

**Verified:** Clean restart, all endpoints return expected responses. Sync `/ask` returns in <1s with `"verified": false`.

---

## 2026-09-14 — Week 6 closeout: Verifier recall root cause identified

**Decision:** The verifier prompt v1.1.0 is the problem, not model size in isolation. The synonym equivalence rules make the decision criteria stricter, and qwen3:4b lacks the capacity to apply them reliably.

**Isolation experiment (5-case probe):**

| Model | Prompt | Correct | Latency |
|-------|--------|---------|---------|
| qwen3:4b | Minimal ("Reply YES or NO...") | 5/5 | 4–18s |
| qwen3:4b | Full verifier prompt v1.1.0 | 2/5 | 28–142s |
| qwen3:8b | Full verifier prompt v1.1.0 | 4/5 | 6–30s |

**Key finding:** With the full prompt, qwen3:4b says NO to "The termination date shall be December 31, 2025" when that exact date appears in the passage. qwen3:8b gets it right. This is a capability-times-prompt-complexity interaction.

**Decision: Adopt qwen3:8b for verification.** Provisional pending full gold-set confirmation.

**Related:** `adr/009-verifier-recall-recovery.md`, `docs/specification/verifier-prompt.md` (v1.2.0)

---

## 2026-09-14 — Week 6 closeout: Sync /ask endpoint is unverified by design

**Decision:** The synchronous `POST /api/v1/matters/{id}/ask` endpoint no longer calls the verifier. It returns raw citations with `"verified": false`. The async endpoint (`POST /ask-async` + `GET /ask/{id}/status`) is the only path to verified answers.

**Rationale:** Verification adds ~10-60s per citation. A synchronous HTTP endpoint should return in <2s. The async endpoint is the correct pattern for slow verification. The old behavior (returning "Not found" when the verifier rejected everything) was misleading — it looked like a verified negative, not a verifier failure.

**Committed as `493e217`.** ADR: `adr/010-sync-ask-unverified.md`.

---

## Verifier fast-path measurement complete — no safe threshold found

**Decision:** The verifier fast-path (ADR 008 Addendum) was tested against the full 50-question gold set with query expansion enabled. The score distributions for answerable and unanswerable queries overlap so significantly that **no threshold can skip LLM verification without reopening the answer-absent gate**.

### Measurement results

| Vector threshold | Answerable fast-path | Unanswerable fast-path (LEAKS) | Latency improvement |
|------------------|----------------------|-------------------------------|---------------------|
| ≥ 0.65           | 16/29 (55%)          | **3/21 (14%)**                | 38%                 |
| ≥ 0.68           | 12/29 (41%)          | **2/21 (10%)**                | 28%                 |
| ≥ 0.70           | 7/29 (24%)           | **1/21 (5%)**                 | 16%                 |
| ≥ 0.72           | 3/29 (10%)           | **0/21 (0%) ✓ SAFE**          | 6%                  |

**Key finding:** Even with vector similarity ≥ 0.72 (extremely strict), only 3/29 answerable queries get the fast-path — a mere 6% latency improvement. The answer-absent gate (21/21 clean) is the binding constraint.

### Why this happens

Query expansion boosts RRF scores for unanswerable queries by adding legal synonyms. The expanded keywords match documents even when the semantic intent doesn't. The vector similarity (which measures semantic similarity) was expected to separate them, but the distributions still overlap:
- Answerable top-1 vector: 0.48–0.78
- Unanswerable top-1 vector: 0.52–0.71

The overlap is fundamental to this corpus and retrieval architecture.

### Conclusion

The fast-path design in `verifier.py` is kept for future use (thresholds are configurable), but **the verifier is not fast enough for interactive use on this corpus**. The answer-absent gate takes priority over latency.

**Alternatives for production latency:**
1. Async verification (return results immediately, verify in background, update UI)
2. Smaller/faster model (tinyllama, phi-minimodal)
3. Cross-encoder verification classifier (not yet tested)
4. Accept ~17s/query latency for Week 5 (the verifier is correct, just slow)

**Related:** `adr/008-verifier-fast-path-addendum.md`, `api/tests/verifier-fast-path-calibration.json`

---

## 2026-09-13 — Verifier v1.1.0 with synonym equivalence: still 0/29 recall

**Decision:** Updated verifier prompt to v1.1.0 with legal-term synonym equivalence (breach↔default, notice↔demand, etc.). The verifier still drops answerable recall to 0/29.

**Why:** qwen3:4b is too small to reliably perform the verification task. Even with explicit synonym rules in the prompt, the model fails to connect question terms to passage terms. The answer-absent gate holds at 21/21, but the cost is rejecting all answerable citations.

**Production decision:** Use the verifier in strict mode. The system says "not found" rather than risk a false citation. This is the fail-closed tradeoff SKILL.md requires.

**Path forward for production:**
1. Use a larger model (qwen3:8b or better) for verification
2. Implement async verification (return raw results, verify in background, update UI)
3. Accept ~17s/query latency with the current strict verifier

**Related:** `docs/specification/verifier-prompt.md` (v1.1.0), `api/tests/full-pipeline-report.json`

---

## Recall@5 measurement with legal_synonyms expansion: 86.2% (PASS)

**Decision:** Query expansion using legal-term synonyms (inline replacement) improves Recall@5 from 79.3% to **86.2%** (25/29), exceeding the 80% target by 6.2 pp.

### Measurement setup
- Frozen gold set: 29 answerable + 21 unanswerable
- Query expansion: legal-term synonyms (breach→default breach, notice→notice demand, etc.)
- No corpus modifications
- Same RRF configuration (k=30, weights 0.65/0.35)

### Results

| Question | Baseline (no expansion) | With legal_synonyms | Notes |
|----------|------------------------|---------------------|-------|
| Q05      | MISS                   | MISS                | DOC-014-Chronology.pdf not retrieved — OCR'd page, low vector similarity |
| Q09      | MISS                   | MISS                | DOC-007/008 invoices ranked below MSA |
| Q25      | MISS                   | MISS                | DOC-010-Response-Letter.pdf has 0 chars (OCR failure) |
| Q46      | MISS                   | **HIT**             | Now retrieves DOC-013-Deposition-Notice.pdf |
| Q49      | MISS                   | MISS                | Source attribution — requires synthesis |

**Recovered:** Q46 (deposition date comparison)
**Still missing:** Q05, Q09, Q25, Q49 (4 structural misses remaining)

### The 4 remaining misses

1. **Q05 (date question):** DOC-014-Chronology.pdf is OCR'd text — the vector similarity is lower than native PDFs. The date normalization variant from the original benchmark recovered this one, but at the cost of also adding "DATE" keyword noise that hurt other questions.

2. **Q09 (invoice amount):** The invoices (DOC-007/008) are 512-char chunks that don't contain the exact phrase "contract price stated in the invoice." The MSA (DOC-003) ranks higher because it contains more matching keywords.

3. **Q25 (multi-document synthesis):** DOC-010-Response-Letter.pdf has **0 characters** of text (OCR failure on a PDF with no extractable text). This is a corpus defect, not a retrieval defect. The question is unanswerable from the corpus.

4. **Q49 (source attribution):** Requires comparing quoted wording across two documents — a synthesis task beyond the fusion model's reach.

### Decision

**Accept 86.2% as the final recall number.** The 4 remaining misses are:
- 1 corpus defect (Q25 — empty OCR page)
- 2 semantic gaps that would require a rewriter, not query expansion (Q09, Q49)
- 1 date-specific retrieval gap (Q05)

All 21 unanswerable queries correctly return 5 raw citations (the verifier handles the filtering). The recall gate (≥80%) is **PASS**.

**Related:** `api/tests/gold-set-report-legal-synonyms.json`
