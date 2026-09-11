# Ganymede

**Private Matter Intelligence** — a single-tenant, customer-controlled AI workspace for civil-litigation teams.

A lawyer can move from a question about the record to a reviewable, cited draft without sending matter data to a public model provider.

---

## What this is

Ganymede lets a litigation team do three jobs over documents they already own:

1. **Find the fact** — ask a question, get an answer with document name, page, quoted passage, and visible uncertainty.
2. **Build the record** — extract a reviewable chronology and issue/evidence table from the matter corpus.
3. **Start the work product** — produce an internal memo or deposition-prep draft grounded only in approved matter sources, with human review before export.

It is **not** a legal chatbot, a case-law research tool, an e-discovery platform, or an autonomous filing agent. See [Product Contract](docs/specification/product-contract.md) and [Non-Goals](docs/specification/non-goals.md).

---

## Trust model (summary)

- **Private by architecture.** Matter data stays inside a customer-controlled single-tenant deployment. No outbound inference traffic by default.
- **Grounded by default.** Every factual answer links to the exact source passage. If evidence is absent, the system says so.
- **Human-owned.** Drafts carry an AI-assisted label. Export requires a deliberate human action and preserves approval lineage in an append-only audit record.

Full trust boundaries are in [Trust Boundaries](docs/architecture/trust-boundaries.md).

---

## Repository structure

```
ganymede/
├── README.md                  # this file
├── SKILL.md                   # Hermes agent operating instructions for this repo
├── DEVELOPMENT.md             # engineering conventions and build rules
├── adr/                       # Architecture Decision Records
│   ├── 000-template.md
│   └── 001-single-tenant-deployment.md
├── docs/
│   ├── discovery/             # Phase 1 (Weeks 1-2) discovery outputs
│   ├── specification/         # versioned product spec, benchmark, corpus rules
│   ├── architecture/          # stack, data flow, trust boundaries
│   ├── commercial/            # pricing, proposal, sales narrative, pilot scorecard
│   ├── sales/                 # discovery script, one-pager, prospect tracking
│   ├── security/              # threat model, access matrix, incident path
│   └── pilot/                 # pilot agreement, readiness packet
├── plans/                     # implementation plans and weekly scorecards
├── decisions/                 # decision log
└── testdata/
    └── corpus-v0.1/           # synthetic test corpus (23 docs + manifest + facts ledger)
```

`docs/product/` was a placeholder in an earlier draft. Product-feature and artifact contracts live in `docs/specification/`. `docs/operations/` is deferred to Phase 5 (Weeks 9-10) and does not exist yet.

---

## Roadmap

A 12-week build to a paid design-partner pilot. Commercial work runs in parallel from Day 1.

| Phase | Weeks | Focus |
|-------|-------|-------|
| Discover and specify | 1-2 | Workflow map, economic baseline, risk baseline, buyer map, corpus rules, 50-question benchmark, threat model |
| Build the evidence engine | 3-4 | Matter creation, ingestion with page-level provenance, hybrid retrieval with citation objects |
| Turn evidence into reviewable work | 5-6 | Matter Q&A with citation inspection, chronology, issue table, internal memo draft |
| Make governance visible | 7-8 | Identity, roles, matter scope, session controls, audit ledger, approval binding |
| Package, attack, recover | 9-10 | Docker Compose release, red-team, benchmark, restore drill, pilot-readiness packet |
| Pilot and decide | 11-12 | One paid design-partner pilot, closeout, go/narrow/stop decision |

Full roadmap detail: [Product Roadmap](docs/specification/roadmap.md). Weekly scorecard: [Weekly Scorecard](plans/weekly-scorecard.md).

---

## Commercial summary

- **Pilot:** $4,500 / 30 days — one matter, up to 10 named users, onboarding, three guided tasks, final scorecard.
- **Initial annual contract (hypothesis):** $24,000 platform + $150/user/month for additional users. Implementation $7,500 once. Managed dedicated hosting $12,000/year (infra billed separately).
- **Week 12 test:** one firm has paid, at least three users returned, citation quality met the launch threshold, and the buyer can name a realistic annual budget.
- **Target:** first paid design partner in Week 11.

See [Commercial Plan](docs/commercial/plan.md) and [Pricing Hypothesis](docs/commercial/pricing-hypothesis.md).

---

## Immediate next actions (Day 1-2)

Per the build plan, the first 48 hours create momentum on both tracks:

**Product/repo:**
1. This repository exists.
2. One-page product contract written.
3. ADR template in place.
4. Repository analytics event description defined.
5. Approved test-corpus rules documented.
6. 50-question benchmark schema drafted.
7. Data-flow and threat model started.
8. Clickable low-fidelity workflow described.

**Commercial:**
1. 30-account prospect list started.
2. Interview script drafted.
3. One-page pilot schema drafted.
4. Paid-pilot one-pager drafted.
5. First eight interviews requested.

---

## Status

Pre-build. Documentation phase. No implementation code yet.

---

*This is a product, engineering, and go-to-market plan. It does not establish legal compliance, security certification, or professional-responsibility advice. Those require review by qualified counsel and security professionals against the actual deployment and contracts.*
