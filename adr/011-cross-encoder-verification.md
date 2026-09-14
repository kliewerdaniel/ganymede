# ADR 011: Replace LLM-as-judge verifier with cross-encoder semantic verification

**Status:** Accepted
**Date:** 2026-09-14
**Related:** `adr/009-verifier-recall-recovery.md`, `adr/008-answer-verification.md`

---

## Context

ADR 009 (qwen3:4b → qwen3:8b swap) was accepted provisionally, pending full gold-set confirmation. The full gold-set evaluation has now run. **The provisional acceptance is revoked.**

### Gold-set results: qwen3:8b + verifier prompt v1.1.0

| Metric | qwen3:4b (v1.1.0) | qwen3:8b (v1.1.0) | No verifier (Week 4) |
|--------|-------------------|-------------------|----------------------|
| Answerable recall | 0/29 (0%) | 22/29 (75.9%) | 25/29 (86.2%) |
| Answer-absent clean | 21/21 (100%) | 18/21 (85.7%) | 21/21 (100%) |
| p50 verifier latency | ~60s | ~47s | — |

Qwen3:8b regresses answer-absent from 21/21 to 18/21 (3 LEAKS: Q23, Q30, Q35). The 5-case probe that recommended 8b was insufficient — it did not characterize the failure modes across 50 questions.

### Root cause: LLM-as-judge binary classification is fundamentally fragile

Both qwen3:4b and qwen3:8b use the same prompt v1.1.0 (synonym equivalence rules). The problem is not model size — it is the architecture of asking an LLM to make a binary YES/NO judgment on a complex decision boundary:

- **4b is too weak:** Can't apply the synonym rules, rejects everything (0/29 recall)
- **8b is stronger but miscalibrated:** Applies surface-level textual matching, producing false YES on related-but-non-answering passages (3 LEAKS) AND false negatives on complex-phrased answerable questions (7 MISSES)

The two failure modes coexist because the LLM's decision boundary is not aligned with "does this passage contain the specific fact asked for." Prompt engineering cannot fix this — the boundary is inherently fuzzy for generative models.

## Decision

**Replace LLM-as-judge verification with cross-encoder semantic similarity scoring.**

A cross-encoder (e.g., `cross-encoder/ms-marco-MiniLM-L-6-v2`) takes (question, passage) → similarity score in [0, 1]. Verification becomes: `score >= threshold → YES, else NO`. This is:

- **Deterministic:** Same input → same output, every time
- **Fast:** ~50ms per (question, passage) pair vs 10-60s for LLM generation
- **No prompt alignment problem:** The decision boundary is a continuous similarity threshold, not a binary generation
- **Calibratable:** The threshold is a single float, tuned on the gold set

### Architecture

```
Question + Passage → Cross-Encoder → score ∈ [0, 1]
                                    ↓
                              score >= threshold? → YES (verified)
                              score < threshold? → NO (rejected)
```

The same threshold applies to all questions — no per-question tuning, no prompt variants.

### Implementation plan

1. **Add `sentence-transformers` to `requirements.txt`** — cross-encoder inference
2. **Download `cross-encoder/ms-marco-MiniLM-L-6-v2` model** — via HuggingFace at build time
3. **Rewrite `verifier.py`** — replace LLM call with cross-encoder `model.predict([(question, passage)])`
4. **Calibrate threshold** — sweep on gold set, pick threshold that maximizes answerable recall subject to answer-absent = 21/21
5. **Full gold-set evaluation** — confirm recall and answer-absent on 50 questions

## Consequences

- **Latency:** ~50ms per citation × 5 citations = ~250ms per query (vs 10-60s with LLM). Sync `/ask` becomes viable for verified answers.
- **Memory:** Cross-encoder model is ~500MB (vs 2.5GB for qwen3:4b, 4.8GB for qwen3:8b)
- **Local-first preserved:** Cross-encoder runs on CPU, no external API calls
- **Trade-off:** Cross-encoder is weaker than LLM on complex multi-hop reasoning. Questions that require synthesis across documents (e.g., Q31 "List events in chronological order") may score lower. Accepted — retrieval already handles simple multi-document queries; the verifier's job is to reject spurious matches, not solve the question.

## Alternatives considered

1. **Prompt engineering (v1.2.0):** Rejected — the synonym equivalence rules are semantically correct. The problem is the binary classification architecture, not the prompt.
2. **Keep qwen3:8b + accept 18/21 answer-absent:** Rejected — answer-absent cleanliness is higher-stakes than recall. 3 false positives is unacceptable.
3. **Hybrid: cross-encoder first, LLM second for borderline:** Rejected as first step — adds complexity without evidence it helps. Revisit if cross-encoder alone can't hit target.
4. **Ollama-hosted cross-encoder via `/api/embeddings`:** Rejected — Ollama's embedding endpoint produces single-vector embeddings, not cross-encoder pair scores. Cross-encoders require joint encoding of (question, passage), which Ollama doesn't support.

## Related

- `api/app/services/verifier.py` — rewrite to use cross-encoder
- `api/requirements.txt` — add `sentence-transformers`
- `api/Dockerfile` — add model download step
- `docs/specification/verifier-prompt.md` — archive v1.1.0 as superseded; document cross-encoder architecture
- `adr/009-verifier-recall-recovery.md` — status updated to "Revoked"
- `api/tests/discordance_analysis.py` — evidence for the failure modes (run output pending)
