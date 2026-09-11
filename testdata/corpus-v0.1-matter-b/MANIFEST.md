# Ganymede — Synthetic Test Corpus v0.1 Matter B
**Status:** Draft (candidate for freeze)
**Version:** v0.1-matter-b
**Matter:** Acme Healthcare Solutions, Inc. v. Dr. Sarah J. Whitfield (Cause No. D-2026-00187, Travis County District Court)
**Provenance:** Synthetic, generated for evaluation. No real client, party, firm, attorney, judge, court reporter, or document. All names, entities, addresses, dates, and amounts are fictional.
**Label:** Every file in this corpus is labeled SYNTHETIC.

## Document count
12 evidence documents: DOC-B001 through DOC-B012. Plus 2 metadata files (this MANIFEST.md and corpus-facts.md).

## Document manifest

| Doc ID | Filename | Format | SHA-256 | Label |
|--------|----------|--------|---------|-------|
| DOC-B001 | DOC-B001-Complaint.pdf | PDF (native) | 2fa0ece64dc466820378e65ad549dd1e18ca2f6054174d93ccd4b7debdb845b6 | SYNTHETIC |
| DOC-B002 | DOC-B002-Employment-Agreement.pdf | PDF (native) | 97a6a566f5bca24c9aceefb44c6373a7fe654c7962a3f016e5078cb83bd1fbdc | SYNTHETIC |
| DOC-B003 | DOC-B003-Non-Compete-Covenant.pdf | PDF (native) | a0d436d9405891fc594ff24ef1f26358fb36f9e511fbd5299cc29043966888e8 | SYNTHETIC |
| DOC-B004 | DOC-B004-Resignation-Letter.pdf | PDF (native) | c7f42d0e257ffb4dbde2801976f94a1524e7dea9ded8a276703b7895cae4e8db | SYNTHETIC |
| DOC-B005 | DOC-B005-Mercy-Hill-Offer.pdf | PDF (native) | 876f90c733d35dfb9ad361e42da305cb774f205aeb62a12686c4b8627a912b20 | SYNTHETIC |
| DOC-B006 | DOC-B006-Cease-and-Desist.pdf | PDF (native) | c3d2a366a798b217e4345b53b7b9ea2025c973d429090198a6ba34828e63053f | SYNTHETIC |
| DOC-B007 | DOC-B007-Answer.pdf | PDF (native) | e39176509275d3100b0ff1ae57e81978c5fb45eb305e1f9b4c93a9b50cd81a3d | SYNTHETIC |
| DOC-B008 | DOC-B008-Motion-to-Dismiss.pdf | PDF (native) | a1d5760fa1225055d8b3ba3ee3d7e465cd3a07efe6a30a8423c9274a2740743f | SYNTHETIC |
| DOC-B009 | DOC-B009-Affidavit.pdf | PDF (native) | 74ac115c9f4e51cb9e1ba31cb8ffd2e38a752ff70184828baf86b0601b6a5b30 | SYNTHETIC |
| DOC-B010 | DOC-B010-TRO.pdf | PDF (native) | 40bdf56b6a2e4fdf46746e4707ab55a33ecf914359a472fa73c13036fcca14fa | SYNTHETIC |
| DOC-B011 | DOC-B011-Discovery-Requests.pdf | PDF (native) | d7021daffac088077c13738e1aa5fa63b7aacc9d582bed459f888fbf1cde2450 | SYNTHETIC |
| DOC-B012 | DOC-B012-Mediation-Statement.pdf | PDF (native) | af5ec4e3a4d1cdacade9dfffa9fbe2a414d1a9f91df221d0316510bb1d1739fe | SYNTHETIC |

## Format coverage
- PDF (native, text-based): DOC-B001 through DOC-B012 (12 files)

## Cross-matter isolation
This corpus is Matter B. Combined with corpus-v0.1 (Matter A), Rule 4 (two-matter minimum) is satisfied.

## Entity overlap check
- Matter A: Meridian Logistics Solutions, LLC v. Cascade Retail Group, Inc.
- Matter B: Acme Healthcare Solutions, Inc. v. Dr. Sarah J. Whitfield
- No overlapping parties, counsel, courts, or document IDs.

## Test corpus rules compliance summary
- Rule 1 (safe by default): PASS — synthetic, labeled SYNTHETIC.
- Rule 2 (frozen): CONDITIONAL — candidate; frozen on approval by Daniel.
- Rule 3 (sufficient for benchmark): PASS for cross-matter tests.
- Rule 4 (two-matter minimum): PASS when combined with corpus-v0.1.
- Rule 5 (document the corpus): PASS — this manifest + corpus-facts.md.
- Rule 6 (evaluation corpus, not ad-hoc): PASS.
- Rule 7 (re-evaluate if compromised): noted.
