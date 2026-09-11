# Ganymede — Approved Test Corpus Rules

**Status:** Proposed
**Date:** September 2026
**Frozen:** Week 2 (after discovery)

---

## Purpose

A frozen test corpus lets every subsequent release run against the same questions, citations, access-control attacks, and operational checks. The corpus must be safe to use during development and evaluation — never live client data without written permission and handling terms.

## Rule 1 — Safe by default

Development and evaluation corpora must be one of:

- **Synthetic:** generated or assembled specifically for evaluation, with no real client or party identity.
- **Public domain:** publicly available legal documents that carry no confidentiality obligation.
- **Expressly authorized:** a real matter corpus where the client or firm has given written permission with explicit handling terms, including what may be stored, who may access it, and when it must be deleted.

**Never** use client documents for development without written permission and handling terms.

## Rule 2 — Frozen

Once the evaluation corpus is frozen in Week 2, it does not change without a documented reason and a note in the benchmark log. The point is that improvements (or regressions) in later releases are attributable to the system, not to a moving target.

## Rule 3 — Sufficient for the benchmark

The frozen corpus must be sufficient to evaluate:

- Parsing success across supported file types (PDF, scanned PDF, DOCX, TXT).
- Retrieval recall on the 50-question gold set.
- Citation support and unsupported-claim rate.
- Cross-matter isolation (requires at least two distinct matter corpora).
- Answer-absent questions (requires at least some questions the corpus cannot answer).
- Operational checks: fresh install, restore, backup.

## Rule 4 — Two-matter minimum for isolation tests

To run cross-matter access tests, you need at least two matter corpora that are distinct enough that retrieving from one should not surface content from the other. The evaluation corpus must include this.

## Rule 5 — Document the corpus

For each matter corpus in the evaluation set, record:

- Source and provenance (synthetic / public / authorized — and the authorization terms if applicable).
- Document types and approximate counts.
- Approximate page count.
- Known characteristics that affect parsing (scans, rotated pages, tables, handwriting, poor-quality scans).
- Anything that makes a question answerable or unanswerable.
- Retention and deletion terms, if applicable.

## Rule 6 — Separation of development and evaluation

The evaluation corpus is not the same as the ad-hoc files used to prototype parsers or retrieval. Ad-hoc files are fine for exploration. The evaluation corpus is the frozen benchmark target.

## Rule 7 — Re-evaluate if the corpus is compromised

If a corpus file is changed, replaced, or removed outside the documented process, the benchmark run is invalidated until the corpus is re-frozen and the gold set is re-checked against it.

---

## Decision pending

We have not yet chosen the specific corpus. This document defines the rules it must satisfy. The choice is made in Week 2, after discovery.

**Options under consideration:**

- A synthetic civil-litigation matter assembled from public-domain sources and generated documents.
- An expressly authorized real matter corpus, with written handling terms.
- A public-domain matter corpus (e.g., court-published documents with no confidentiality obligation).

The choice affects the benchmark's realism and the speed of development. Synthetic corpora are fastest to assemble and safest to use; authorized real corpora are more realistic but require paperwork and handling discipline.

---

*This document is part of the specification. It will be updated when the corpus is chosen and frozen.*
