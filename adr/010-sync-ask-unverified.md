# ADR 010: Sync /ask endpoint is unverified by design

**Status:** Accepted
**Date:** 2026-09-14
**Supersedes:** None (new decision)

---

## Context

The synchronous `POST /api/v1/matters/{id}/ask` endpoint originally called the LLM verifier sequentially for up to 5 citations. With qwen3:4b, each verification call took 28–142s, making the endpoint timeout-prone even with a 180s server-side timeout. With qwen3:8b, each call takes 6–30s, so 5 citations can still stack to 50s+.

The async endpoint (`POST /ask-async` + `GET /ask/{id}/status`) was built in Week 5 to handle this: it returns immediately with raw citations, then verifies in the background. The frontend SPA already uses the async endpoint exclusively.

The sync endpoint's verifier calls were both slow and unreliable — a poor contract for a synchronous HTTP response.

## Decision

**Make `POST /api/v1/matters/{id}/ask` return raw citations WITHOUT verifier calls.** It becomes a fast, unverified retrieval endpoint. The response includes `"verified": false` so callers know the citations have not been checked.

**`POST /ask-async` remains the only path to verified answers.** It returns a `query_id` immediately, runs retrieval + verification in a background thread, and the client polls `GET /ask/{id}/status` for results.

### Rationale

1. **Latency contract:** A synchronous HTTP endpoint should return in <2s. Verification (even at ~10s/call × 5 citations = 50s) violates this. The async endpoint is the correct pattern for slow verification.

2. **Fail-closed clarity:** The sync endpoint no longer claims to verify. The old behavior (returning "Not found" when the verifier rejected everything) was misleading — it looked like a verified negative, not a verifier failure.

3. **Debugging value:** The sync endpoint is still useful for testing retrieval without waiting for verification. It is documented as debug-only.

4. **No frontend changes needed:** The SPA already uses `/ask-async`. The sync endpoint is for API consumers who want raw retrieval only.

## Consequences

- **Sync /ask:** Returns in <1s, no verification, `"verified": false` in response.
- **Async /ask-async:** Returns `query_id` immediately, verified results via polling.
- **API docs:** Must clearly state that only the async path produces verified answers.
- **Verifier coverage:** The verifier still runs on every async query. No loss of answer-absent protection.

## Alternatives considered

1. **Make /ask verifier-capable with a 120s timeout budget:** Rejected — 120s is too long for a synchronous HTTP response, and the async endpoint already solves this properly.

2. **Remove /ask entirely:** Rejected — the endpoint is useful for debugging retrieval without verification overhead.

3. **Make /ask use the fast-path only:** Rejected — the fast-path was calibrated to never trigger on this corpus (see ADR 008 addendum), so it would behave identically to the unverified endpoint anyway.

## Related

- `adr/008-verifier-fast-path-addendum.md` — fast-path calibration (no safe threshold)
- `api/app/api/__init__.py` — route implementation
- `api/app/services/async_verification.py` — background verification service
