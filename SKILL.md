# Ganymede — Hermes Agent Operating Instructions

This document tells an AI agent (Hermes) how to work in this repository. It is part of the repo's documentation, not a general prompt.

## Project identity

- **Project name:** Ganymede
- **Working category:** Private Matter Intelligence — customer-controlled AI workspace for civil-litigation teams
- **North-star sentence:** A lawyer can move from a question about the record to a reviewable, cited draft without sending matter data to a public model provider.
- **Repo slug:** `ganymede`

## Build philosophy

- **Documentation first.** No implementation code is written until the relevant specification, ADR, and benchmark design exist. The documentation phase (Weeks 1-2) produces the substance; code implements it.
- **One workflow, one deployment profile.** Do not accumulate features. The product wins through a reliable, reviewable path from record to draft.
- **Test coverage is the primary done metric.** A successful milestone is not "we added another 100 tests" — it is "we discovered and characterized a previously implicit semantic boundary."
- **Counterexamples are first-class research artifacts.** When something fails, preserve the failure case.

## Repository conventions

- ADRs live in `adr/`. Every material technical decision gets an ADR before implementation. Use `adr/000-template.md` as the template.
- Specification lives in `docs/specification/`. Version it. The benchmark, corpus rules, and non-goals are part of the spec, not separate documents.
- Discovery outputs live in `docs/discovery/`. These are Week 1-2 outputs: workflow map, economic baseline, risk baseline, buying map, interview script.
- Decisions that are not architectural go in `decisions/`.
- Weekly scorecards live in `plans/`.

## Trust constraints (non-negotiable)

1. **Export:** Every external artifact requires a deliberate human action and carries an AI-draft label.
2. **Evidence:** Answers preserve document hash, page, offsets, retrieval scores, and model/version metadata.
3. **Egress:** No telemetry or inference traffic leaves the deployment unless the customer enables it.
4. **Tenant:** No shared application database or vector index between customers.
5. **Matter:** Authorization filters retrieval before any prompt is assembled.
6. **Model:** Model output is untrusted data; it cannot grant itself tools or permissions.

Violating any of these without an ADR is a defect.

## Quality gates (pilot readiness — do not implement against these yet; they define the target)

| Gate | Minimum target | How measured |
|------|---------------|--------------|
| Parsing success | 95% of supported files | Pages and text visibly inspected |
| Retrieval recall | 80% Recall@5 | 50-question gold set |
| Citation support | 90% supported claims | Human evidence review |
| Unsupported claims | <5% material claims | Blind review of 25 outputs |
| Matter isolation | 100% attacks blocked | Cross-matter test suite |
| Recovery | Restore succeeds | Clean-machine drill |
| Latency | p95 under 30 sec | Named reference hardware |
| Audit completeness | 100% key events | Event-schema reconciliation |

These are internal launch thresholds, not market facts. They will be tightened after observing real legal reviewers.

## Failure behavior

- Partial ingestion stays visibly incomplete.
- A failed OCR job does not silently create an empty searchable document.
- Deleting a file removes it from retrieval and records a deletion event.
- If the system lacks evidence, it must say "not found in the approved matter sources." It may suggest a better query or identify missing documents, but it must not fill the gap from model memory.

## Implementation rules

- Use relational structures for entities, dates, issues, and evidence until a real pilot proves a graph engine is needed. Do not introduce Neo4j or a generalized knowledge graph for the MVP.
- Cache parsing and embeddings by content hash.
- Version prompts, models, parsers, and schemas.
- Keep matter content out of diagnostic bundles and operational analytics by default.
- Treat prompt injection inside documents, malformed files, and denial-of-service uploads as normal threat cases.
- Make source review a first-class action. The reader should never have to trust a citation merely because it looks formal.

## Do not build (MVP)

- General case-law research
- Docket scraping
- E-discovery platform
- Billing integration
- Court filing
- Email sync
- Mobile app
- Shared multi-tenant SaaS
- Model fine-tuning
- Autonomous external action
- Any claim of legal accuracy or compliance guarantee

## Implementation priority formula

40% observed task frequency and pain · 35% trust, quality, or retention impact · 25% revenue and repeatability.

## Documentation phase completion criteria

The documentation phase (Weeks 1-2) is complete when:

- One practice workflow, one buyer, one champion, one costly job are identified.
- Signed-off spec and corpus exist.
- No unresolved critical data-flow question remains.
- A design-partner letter or written pilot-review commitment is secured.

## References

- [Build Plan](https://danielkliewer.com) — 12-week MVP build plan, September 2026
- [Business Plan](https://danielkliewer.com) — full business plan, September 2026
- ABA Formal Opinion 512 (July 2024) — professional-duty grounding
- Thomson Reuters 2026 — buyer requirements: 96% confidential-data safeguards, 94% authoritative grounding, 90% explainable reasoning
