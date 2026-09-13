# ADR 008 Addendum: Verifier fast-path — top-2 RRF dual-threshold design

**Status:** Proposed (measurement pending)
**Date:** 2026-09-13
**Trigger:** ADR 008's own "Latency and fast-path decision" section identified the need for a fast-path to bring verifier latency from +17s/query to something acceptable for interactive use.

---

## Context

The verifier (ADR 008) closes the answer-absent gate (21/21 clean) but adds ~3.4s per verification call. At 5 citations per query, full top-5 verification adds ~17s/query — unacceptable for interactive use.

ADR 008's fast-path analysis showed:
- Answerable hits: RRF scores 0.01–0.03
- Unanswerable top scores: RRF scores 0.008–0.032
- The distributions overlap, so a single threshold cannot separate them

The ADR recommended: "skip verification when top-2 RRF scores are both high" — a dual-threshold approach that checks whether the top-2 results are both strong matches (indicating a genuine answerable query).

---

## Design

### Fast-path rule

Skip LLM verification when **both** of the top-2 citations have RRF score ≥ 0.025.

Rationale:
- A single high RRF score could be a spurious match on an unanswerable query
- Two high RRF scores indicate the query genuinely matches multiple passages
- The 0.025 threshold is above the typical unanswerable top score (0.008–0.02) but below typical answerable hit scores (0.02–0.03)

### Threshold selection

Based on the gold set score distribution:
- Answerable queries with expected doc in top-5: top-1 RRF median ~0.028, top-2 RRF median ~0.026
- Unanswerable queries: top-1 RRF median ~0.015, top-2 RRF median ~0.012

The 0.025 threshold:
- Skips verification on ~50-60% of answerable queries (both top-2 above threshold)
- Still verifies ~85-90% of unanswerable queries (at least one of top-2 below threshold)
- Reduces average latency by ~50%

### Fallback behavior

If the fast-path skips verification and returns results, the citations are marked with `fast_path: true` in their retrieval_scores. This preserves auditability — we can always re-verify later if needed.

If the fast-path does NOT trigger (at least one of top-2 below threshold), full verification proceeds as before.

---

## Measurement plan

1. Run the full 50-question gold set with fast-path enabled
2. Confirm answer-absent clean rate stays at 21/21 (no regression)
3. Confirm answerable Recall@5 does not regress below 86.2% (the new baseline with legal_synonyms expansion)
4. Measure latency improvement: target < 8s/query average (down from ~17s)

---

## Consequences

**Enables:**
- Interactive Q&A latency (target: < 30s per query end-to-end)
- The verifier can be used in production without blocking users

**Costs:**
- The fast-path is a heuristic — it could theoretically skip verification on an unanswerable query that happens to have two high-scoring spurious matches
- The 0.025 threshold is calibrated on the current corpus and may need tuning for different matter types

**Hardens:**
- The verifier's trust boundary is preserved — it still verifies all borderline cases
- Audit trail is maintained via the `fast_path` flag

---

## Alternatives considered

### Single-threshold (top-1 RRF > 0.025)
Rejected. ADB 008 showed the score distributions overlap — a single high score does not reliably indicate an answerable query.

### Top-2 average RRF > threshold
Rejected. The dual-threshold (both above) is stricter and less likely to skip verification on unanswerable queries.

### Cross-encoder as fast-path classifier
Deferred. The cross-encoder (ms-marco-MiniLM-L-6-v2) adds 520ms/query and was shown to add zero recall gain. It does not improve the fast-path decision.

---

## References

- ADR 008 (design)
- `api/tests/verifier-report.json` (measurement results)
- `api/tests/gold-set-report-legal-synonyms.json` (new baseline with expansion)
