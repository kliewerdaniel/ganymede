# Ganymede — Non-Goals

**Status:** Accepted, source: build plan + business plan
**Date:** September 2026
**Review trigger:** After first paid pilot, or when a prospective customer demands one of these as a condition of engagement.

---

These are not bugs to fix. They are deliberate boundaries. If a prospective customer requires one of these on day one, that is a disqualifier — not a roadmap item.

## Not in the first release

1. **General case-law research.** No licensed case-law database, no citation to authority the firm did not provide. The product works over documents the firm already owns.

2. **Docket scraping.** No automatic retrieval of court dockets, filings, or procedural status from external sources.

3. **E-discovery platform.** No large-scale document review, privilege-log workflow, deduplication across matters, or production sets. The MVP handles one matter's documents, not a discovery database.

4. **Billing integration.** No time tracking, billing codes, or practice-management financial integration.

5. **Email sync.** No ingestion of email accounts or mailboxes.

6. **Mobile application.** No native mobile app. The first release is a desktop/web workspace.

7. **Shared multi-tenant SaaS.** Each customer receives an isolated single-tenant deployment. There is no shared application database or vector index between customers.

8. **Model fine-tuning.** No fine-tuning on client matter content. The model is a local runtime with an adapter boundary; prompts and retrieval do the work, not model adaptation.

9. **Autonomous external action.** No filing, no sending, no external API calls on the model's initiative. Every external artifact requires a deliberate human action.

10. **Claim of legal accuracy or compliance guarantee.** The product does not claim to practice law, produce legally accurate conclusions, or automatically satisfy professional duties. It exposes evidence so a lawyer can evaluate their own duties.

## Not the product's job

- To find facts the firm does not have. The product works over the approved matter corpus. If the answer is not in the corpus, it says so.
- To replace the lawyer's judgment. The model proposes; the typed policy and a human decide whether content can leave the workspace.
- To make reviews unnecessary. Drafts are starting points. Review and export remain explicit human actions.
- To be comprehensive. The product is narrow by design. A broader platform is only in scope after one workflow has proven repeatable use and a buyer will pay for the expansion.

## Marketing discipline

Corresponding language discipline:
- Do not use "AI lawyer," "perfect accuracy," or "compliance guaranteed."
- Positioning: "A private matter workspace that helps your team find, organize, and draft from the record you already own."
- Do not lead with model benchmarks; model quality changes quickly and can be copied.
- Do not claim that local equals secure; prove isolation, deletion, backup, access, and audit behavior.

---

## If a customer demands one of these

| Demand | Response |
|--------|----------|
| "I need case-law research on day one." | Disqualifier for the first release. Firm-owned matter intelligence is the wedge; licensed content is a later expansion only if multiple paying customers demand it. |
| "I need it to file documents." | Not in scope. No autonomous external action. |
| "I need it to sync my email or DMS." | No connector before multiple paying customers demand the same one. |
| "I want a free trial." | No free pilot for a firm that cannot buy. The paid pilot is the qualification mechanism. |
| "Is this HIPAA/GDPR/compliant?" | That requires a defined control set and independent evidence. The verifiable claim today is "runs in a customer-controlled environment." |

---

*These non-goals are part of the product contract. They are as binding as the features.*
