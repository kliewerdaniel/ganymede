# Ganymede — Synthetic Test Corpus v0.1 Matter B
**Status:** Draft (candidate for freeze)
**Version:** v0.1-matter-b
**Matter:** Accme Healthcare Solutions, Inc. v. Dr. Sarah J. Whitfield (Cause No. D-2026-00187, Travis County District Court)
**Provenance:** Synthetic, generated for evaluation. No real client, party, firm, attorney, judge, court reporter, or document. All names, entities, addresses, dates, and amounts are fictional.
**Label:** Every file in this corpus is labeled SYNTHETIC.

## Document count
12 evidence documents: DOC-B001 through DOC-B012. Plus 2 metadata files (this MANIFEST.md and corpus-facts.md).

## Document manifest

| Doc ID | Filename | Format | SHA-256 | Label |
|--------|----------|--------|---------|-------|
| DOC-B001 | DOC-B001-Complaint.pdf | PDF (native) | 789beb039cfee7aa37d4ae1322fca8dd20c5b8ee6943d031a46b3b21be25111d | SYNTHETIC |
| DOC-B002 | DOC-B002-Employment-Agreement.pdf | PDF (native) | d5e47bf140cf7c43951934f3d2564fcc4a36ad76c4385bad5f7234d150c41ccc | SYNTHETIC |
| DOC-B003 | DOC-B003-Non-Compete-Covenant.pdf | PDF (native) | 4111c3155e5df6496bd6ce4cd7ccd8a2aa80031194c1fadc0a6139ca3956c4cb | SYNTHETIC |
| DOC-B004 | DOC-B004-Resignation-Letter.pdf | PDF (native) | 88cba3d3ee5288aa01cc7403a20d8f8684eccb812d1a7ef8567550b16e38ce7e | SYNTHETIC |
| DOC-B005 | DOC-B005-Mercy-Hill-Offer.pdf | PDF (native) | 8cbfb418519c8fa532770ec001adc700bf2425523a234288c58a12c959f0612f | SYNTHETIC |
| DOC-B006 | DOC-B006-Cease-and-Desist.pdf | PDF (native) | dda6a904f2745c74295c1b0af6784c4bb7d402ad31e91e0948a58164d92ffbc8 | SYNTHETIC |
| DOC-B007 | DOC-B007-Answer.pdf | PDF (native) | e39176509275d3100b0ff1ae57e81978c5fb45eb305e1f9b4c93a9b50cd81a3d | SYNTHETIC |
| DOC-B008 | DOC-B008-Motion-to-Dismiss.pdf | PDF (native) | a1d5760fa1225055d8b3ba3ee3d7e465cd3a07efe6a30a8423c9274a2740743f | SYNTHETIC |
| DOC-B009 | DOC-B009-Affidavit.pdf | PDF (native) | 10b697e008007127b97da5a28dfe067f53cf36310c705b780209fc7ba6ae81e3 | SYNTHETIC |
| DOC-B010 | DOC-B010-TRO.pdf | PDF (native) | 40bdf56b6a2e4fdf46746e4707ab55a33ecf914359a472fa73c13036fcca14fa | SYNTHETIC |
| DOC-B011 | DOC-B011-Discovery-Requests.pdf | PDF (native) | d682c6a7703c71973731fc53e0280b01f901667f3202a42b425f67d3adadb5cd | SYNTHETIC |
| DOC-B012 | DOC-B012-Mediation-Statement.pdf | PDF (native) | 468323ec7c5e7f7a666b93efb6addccda7dc8b2be9efda9aa040e24d4f02ac70 | SYNTHETIC |

## Format coverage
- PDF (native, text-based): DOC-B001 through DOC-B012 (12 files)

## Cross-matter isolation
This corpus is Matter B. Combined with corpus-v0.1 (Matter A), Rule 4 (two-matter minimum) is satisfied.

## Entity overlap check
- Matter A: Meridian Logistics Solutions, LLC v. Cascade Retail Group, Inc.
- Matter B: Accme Healthcare Solutions, Inc. v. Dr. Sarah J. Whitfield
- No overlapping parties, counsel, courts, or document IDs.

## Test corpus rules compliance summary
- Rule 1 (safe by default): PASS — synthetic, labeled SYNTHETIC.
- Rule 2 (frozen): CONDITIONAL — candidate; frozen on approval by Daniel.
- Rule 3 (sufficient for benchmark): PASS for cross-matter tests.
- Rule 4 (two-matter minimum): PASS when combined with corpus-v0.1.
- Rule 5 (document the corpus): PASS — this manifest + corpus-facts.md.
- Rule 6 (evaluation corpus, not ad-hoc): PASS.
- Rule 7 (re-evaluate if compromised): noted.