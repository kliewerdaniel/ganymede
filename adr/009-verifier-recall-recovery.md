# ADR 009: Verifier recall recovery — model swap from qwen3:4b to qwen3:8b

**Status:** Accepted (provisional, pending full gold-set confirmation)
**Date:** 2026-09-14
**Related:** `adr/008-answer-verification.md`, `adr/008-verifier-fast-path-addendum.md`

---

## Context

After Week 5, the verifier produced **0/29 answerable recall** with 21/21 answer-absent clean. The verifier prompt was at v1.1.0 with legal-term synonym equivalence rules. The question was whether to fix this via a larger model (qwen3:8b) or via prompt engineering (v1.2.0).

## Isolation experiment (5-case probe)

To isolate the cause, three configurations were tested on clear YES/NO cases:

| Model | Prompt | Correct | Latency |
|-------|--------|---------|---------|
| qwen3:4b | Minimal ("Reply YES or NO...") | 5/5 | 4–18s |
| qwen3:4b | Full verifier prompt v1.1.0 | 2/5 | 28–142s |
| qwen3:8b | Full verifier prompt v1.1.0 | 4/5 | 6–30s |

**Mechanism finding:** With the full verifier prompt, qwen3:4b says NO to "The termination date shall be December 31, 2025" when that exact date appears in the passage. The v1.1.0 synonym equivalence rules make the decision criteria stricter. qwen3:4b lacks the capacity to apply these rules reliably — this is a capability-times-prompt-complexity interaction.

## Decision

**Swap verifier model from qwen3:4b to qwen3:8b.** No prompt wording changes from v1.1.0.

### Rationale

1. **Fixes recall:** qwen3:8b correctly applies synonym rules, recovering answerable recall while maintaining answer-absent cleanliness in the probe.
2. **Faster:** ~10s/call vs ~60s/call on 4b — 4b was burning time on longer, less certain generations.
3. **Minimal change:** Only the model identifier changes. Prompt stays frozen at v1.1.0.
4. **Local-first preserved:** Still runs on local Ollama, no external API calls.

## Consequences

- **Latency budget:** ~10s/citation × up to 5 citations = ~50s per query. Async endpoint remains the only reasonable path for verified answers.
- **Memory:** qwen3:8b requires more RAM than 4b (4.8GB vs 2.5GB). Acceptable for local deployment on modern hardware.
- **Answer-absent gate:** Must hold at 21/21. The 8b model's stronger reasoning could go either way — it must be confirmed on the full gold set.

## Alternatives considered

1. **Prompt engineering (v1.2.0) to simplify the rules:** Rejected as first step — the synonym equivalence rules are semantically correct and should remain. The problem is model capacity, not rule correctness.
2. **Removing synonym rules (revert to v1.0.0):** Would fix the immediate 0/29 but lose the semantic equivalence needed for production. Revisit only if 8b + v1.1.0 regresses answer-absent.
3. **Cross-encoder classifier:** Not yet tested. Could be a future optimization but adds model deployment complexity.

## Related

- `api/app/services/verifier.py` — `VERIFIER_MODEL = os.environ.get("VERIFIER_MODEL", "qwen3:8b")`
- `docs/specification/verifier-prompt.md` — v1.2.0 (model change noted, prompt text unchanged from v1.1.0)
- `references/verifier-model-swap.md` — detailed isolation experiment results
- `adr/010-sync-ask-unverified.md` — async path to verified answers
