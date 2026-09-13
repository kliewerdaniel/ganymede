# ADR — Post-retrieval answer verification (qwen3:4b, local Ollama)

**Status:** Proposed (measurement in progress)
**Date:** 2026-09-12
**Trigger:** ADR 007 Addendum identified post-retrieval verification as the only viable path to 100% answer-absent precision. This ADR records the design, implementation, and measurement outcome.

---

## Context

The Week 4 gate table shows:
- Recall@5: 79.3% (23/29) — 0.7 pp below 80% target
- Answer-absent precision: 0% (0/21 clean) — 100% target, gating defect
- Isolation: 8/8 blocked — PASS

Score-based abstention gates (RRF 0.003/0.005) cannot separate answerable from unanswerable queries — the score distributions overlap. The ADR 007 Addendum states: "Post-retrieval verification (LLM judge / entailment / no-answer classifier) is the only viable path."

This ADR records the chosen approach: a local LLM verifier using qwen3:4b via Ollama's `/api/generate` endpoint (local-only, no external calls). The verifier is a prompt-frozen contract stored in `docs/specification/verifier-prompt.md` version 1.0.0.

---

## Design

### Architecture

```
retrieve() → [Citation, ...] → verify_top_k() → [Citation, ...] (YES only)
                                         ↓
                                   zero results if none pass
```

For every query:
1. Retrieve top-5 citations via the existing RRF fusion pipeline.
2. For each citation, call qwen3:4b with the frozen verifier prompt + question + passage.
3. Keep only citations where the model replies `YES: <quote>`.
4. If none survive, return zero results — the API layer renders "not found in the approved matter sources."

### Prompt contract

The verifier prompt is frozen at version 1.0.0 in `docs/specification/verifier-prompt.md`. It specifies:
- Role: precision answer verifier, not summarizer or answerer.
- Output format: exactly `YES: <exact quote>` or `NO`.
- Rules: too-short passages → NO; topic mentioned but fact absent → NO; no outside knowledge; no explanation.
- Examples: 4 frozen examples (2 YES, 2 NO).

Any change to the prompt text requires a version bump and re-measurement against the frozen gold set.

### Model and endpoint

- **Model:** qwen3:4b (Ollama, local, port 11434)
- **Endpoint:** `/api/generate` (NOT `/api/chat` — qwen3:4b returns empty `content` on `/api/chat`, only `thinking` is populated)
- **Configuration:** no `options` key in payload (qwen3:4b returns empty `response` when `num_predict` is set — only the default configuration produces visible output)
- **Temperature:** 0 (default, no options)
- **Timeout:** 60s per call (shared httpx client)

### Latency characteristics (measured)

Single-call smoke test results:
- YES case (passage contains answer): ~3.3s per call
- NO case (passage does not contain answer): ~3.3s per call
- Per-query verification of 5 citations: ~16.5s (5 × 3.3s)

This is **unacceptably high for interactive use**. At 5 citations per query × 250 queries (50 questions × 5 citations), the full measurement requires ~20 minutes.

See ADR section "Latency and fast-path decision" for the mitigation plan.

---

## Measurement plan

### What we measure

1. **Unanswerable-clean rate:** 21 unanswerable questions (15 NOT_IN_CORPUS + 6 ANSWER_ABSENT). Target: 21/21 clean. Each query retrieves 5 citations, verifies all 5, and checks whether any survive.
2. **Answerable Recall@5:** 29 answerable questions. Target: must not regress below 79.3% (23/29).
3. **Verifier latency:** p50, p95, mean per query (5 citations verified).
4. **Isolation:** 8/8 blocked must hold with verifier in place (verifier sees only matter-scoped results, but verify, don't assume).

### Expected outcomes

**Best case:** Unanswerable-clean reaches 21/21, answerable Recall@5 stays at or above 79.3%, and the only cost is latency.

**Likely case:** Unanswerable-clean improves significantly but not to 100% (some unanswerable queries retrieve passages that superficially mention the topic), or answerable Recall@5 drops (the verifier incorrectly rejects valid citations).

**Failure case:** The verifier cannot separate answerable from unanswerable (both YES and NO rates are similar across the two groups). In this case, we try the cross-encoder as a verification classifier (entailment-style) before reporting failure.

---

## Latency and fast-path decision

At ~3.3s per verification call and 5 citations per query, the verifier adds ~16.5s per query. This is unacceptable for any interactive or batch use.

**Proposed fast-path:** Skip verification when the top RRF score exceeds a threshold (e.g., 0.02). The rationale: high RRF scores correlate with genuine matches, and the verifier's main value is filtering low-confidence spurious citations on unanswerable queries.

This fast-path is **not yet implemented**. It requires:
1. Measuring the RRF score distribution for answerable vs. unanswerable queries (already partially known: answerable hits range 0.01–0.03, unanswerable top scores range 0.008–0.032 — overlapping).
2. Finding a threshold that preserves recall while skipping enough verifications to bring latency down.
3. If no threshold works, the verifier is too slow for production and an alternative approach is needed (e.g., smaller/faster model, entailment-based classifier, or acceptance that answer-absent precision requires a different architecture).

---

## Alternatives considered

### Cross-encoder as verification classifier
The cross-encoder (ms-marco-MiniLM-L-6-v2) was already evaluated for ranking and found to add zero recall gain. As a verification classifier (binary entailment: does passage entail answer?), it may perform differently — verification is a precision task, ranking is a sorting task. Deferred until the LLM verifier measurement is complete.

### Smaller/faster model
qwen3:4b is the smallest model available locally. Smaller models (e.g., tinyllama) may be faster but less reliable at the verification task. Deferred until the qwen3:4b measurement is complete.

### No verification (accept 0% answer-absent)
Rejected. The pilot gate requires 100% answer-absent precision. Shipping with 0% would be a known defect.

---

## References

- ADR 007 Addendum (identifies verification as the path forward)
- `docs/specification/verifier-prompt.md` (frozen prompt, version 1.0.0)
- `api/app/services/verifier.py` (implementation)
- `api/tests/test_verifier.py` (measurement script)
- `api/tests/verifier-report.json` (measurement results, when available)
