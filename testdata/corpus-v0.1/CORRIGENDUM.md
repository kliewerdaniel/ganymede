# Corpus v0.1 Corrigendum

**Date:** 2026-09-12
**Corpus:** `testdata/corpus-v0.1/` (frozen 2026-09-11 at commit `c2bba85`)
**Commits:** `7d656f7` ("Replace blank OCR PDFs with proper text PDFs (DOC-009/011/013/020)"), parent `7d656f7^` = `13e35e9` (pre-regeneration tree)

---

## Summary

Four PDFs in the frozen corpus v0.1 were regenerated at commit `7d656f7`, outside the freeze process (the freeze was signed at `c2bba85`). The on-disk SHA-256 hashes no longer match the frozen `MANIFEST.md`. This corrigendum records the actual old→new hash transition, verified from git history (`git show <commit>:<path> | shasum -a 256`), and every gold question whose evidence pointer touches each affected document.

**Process violation:** A frozen corpus is immutable. Regeneration should have triggered a version bump (v0.1 → v0.2), MANIFEST re-signing, gold-set re-binding, and full re-measurement. None of that occurred.

**Substantive impact:** None. All affected gold question pointers re-verified against on-disk files — content matches expectations. One retrieval-test false negative (Q14) was caused by the hash mismatch and has been resolved by removing old-SHA DB records.

---

## Document-by-document record

### DOC-009 — Notice of Default

| Field | Value |
|-------|-------|
| **Document** | `DOC-009-Notice-of-Default.pdf` |
| **Type** | PDF (native, text-based) |
| **Old SHA-256** (7d656f7^, pre-regeneration) | `07e4df163afdb08c893269e797ea15d1843bfaf29fb33d49ec001136c5bc8fed` |
| **New SHA-256** (current on-disk, HEAD d9cf341) | `58c57a53836ab1126c761b2ac0aa4016fafe30e8c4e80484c740f08ec8d27614` |
| **MANIFEST.md SHA** (frozen at c2bba85, matches old) | `07e4df163afdb08c893269e797ea15d1843bfaf29fb33d49ec001136c5bc8fed` |
| **Regeneration reason** | Blank PDF rendering — document was generated with `reportlab` producing an empty page; replaced with a non-blank version containing the notice text from corpus-facts.md. |
| **Evidence** | `git show 7d656f7^:testdata/corpus-v0.1/DOC-009-Notice-of-Default.pdf | shasum -a 256` → `07e4df...`; current on-disk `shasum -a 256 testdata/corpus-v0.1/DOC-009-Notice-of-Default.pdf` → `58c57a...`; MANIFEST.md line at c2bba85 → `07e4df...` (matches old SHA). The `7d656f7` diff shows the MANIFEST was incorrectly changed from `07e4df...` to `661516...` (a third, non-matching value); subsequent commits restored it to `07e4df...`. Current MANIFEST at d9cf341 shows `66151637...` (third state — see note). |

**Note on DOC-009 MANIFEST anomaly:** The `7d656f7` commit changed the MANIFEST.md DOC-009 line from the correct old SHA (`07e4df...`) to an incorrect value (`661516...`). This incorrect value persisted in the MANIFEST and is what the frozen MANIFEST at HEAD currently shows. The MANIFEST should read `07e4df...` (the pre-regeneration SHA) but reads `661516...` instead. This is a second-order MANIFEST corruption, not a corpus file corruption.

**Gold questions touching DOC-009:**
- Q25: "Which documents establish that the defendant received notice before filing?" — expects DOC-009-Notice-of-Default.pdf
- Q29: "Which documents show the sequence of communications leading to the settlement offer?" — expects DOC-009-Notice-of-Default.pdf
- Q33: "Who sent the first breach notice and on what date?" — expects DOC-009-Notice-of-Default.pdf
- Q49: "The same fact appears in two documents with different quoted wording. Which is the primary source?" — expects DOC-009-Notice-of-Default.pdf

### DOC-011 — Demand Letter

| Field | Value |
|-------|-------|
| **Document** | `DOC-011-Demand-Letter.pdf` |
| **Type** | PDF (native, text-based) |
| **Old SHA-256** (7d656f7^, pre-regeneration) | `0e9c8cd07d37d2df04b17061fa4e0969c3720e8442da87fa9b912919be1e7afa` |
| **New SHA-256** (current on-disk, HEAD d9cf341) | `ebcc9a0ca1695f5caad20e4dfa8489b7a7bea50e113c42fbd50cf9dd3c04d0c0` |
| **MANIFEST.md SHA** (frozen at c2bba85, matches old) | `0e9c8cd07d37d2df04b17061fa4e0969c3720e8442da87fa9b912919be1e7afa` |
| **Regeneration reason** | Blank PDF rendering — document was generated with `reportlab` producing an empty page; replaced with a non-blank version containing the demand letter text from corpus-facts.md. |
| **Evidence** | `git show 7d656f7^:testdata/corpus-v0.1/DOC-011-Demand-Letter.pdf | shasum -a 256` → `0e9c8c...`; current on-disk `shasum -a 256 testdata/corpus-v0.1/DOC-011-Demand-Letter.pdf` → `ebcc9a...`; MANIFEST.md line at c2bba85 → `0e9c8c...` (matches old SHA — MANIFEST was not updated after regeneration). |

**Gold questions touching DOC-011:**
- Q13: "What is the stated interest rate on the unpaid balance in the demand letter?" — expects DOC-011-Demand-Letter.pdf
- Q29: "Which documents show the sequence of communications leading to the settlement offer?" — expects DOC-011-Demand-Letter.pdf

### DOC-013 — Deposition Notice

| Field | Value |
|-------|-------|
| **Document** | `DOC-013-Deposition-Notice.pdf` |
| **Type** | PDF (native, text-based) |
| **Old SHA-256** (7d656f7^, pre-regeneration) | `d915c545d3bd213e6ef4fb6a45890a89b9e4c79c5962c382ae9d520c5e1d48d8` |
| **New SHA-256** (current on-disk, HEAD d9cf341) | `ced31546e80fc2b64eeb94a511cea96218096054500630bbf3889dccea2e695f` |
| **MANIFEST.md SHA** (frozen at c2bba85, matches old) | `d915c545d3bd213e6ef4fb6a45890a89b9e4c79c5962c382ae9d520c5e1d48d8` |
| **Regeneration reason** | Blank PDF rendering — document was generated with `reportlab` producing an empty page; replaced with a non-blank version containing the deposition notice text from corpus-facts.md. |
| **Evidence** | `git show 7d656f7^:testdata/corpus-v0.1/DOC-013-Deposition-Notice.pdf | shasum -a 256` → `d915c5...`; current on-disk `shasum -a 256 testdata/corpus-v0.1/DOC-013-Deposition-Notice.pdf` → `ced315...`; MANIFEST.md line at c2bba85 → `d915c5...` (matches old SHA — MANIFEST was not updated after regeneration). |

**Gold questions touching DOC-013:**
- Q11: "What date does the deposition notice set for the first deposition?" — expects DOC-013-Deposition-Notice.pdf
- Q14: "Who is the court reporter named in the deposition scheduling order?" — expects DOC-013-Deposition-Notice.pdf
- Q46: "Two documents give different dates for the same event. Which is better supported?" — expects DOC-013-Deposition-Notice.pdf

**Note on Q14:** The retrieval pipeline correctly identifies DOC-013 (SHA `ced315...`, the regenerated on-disk version) as the top result for Q14. The false negative in the retrieval test was caused by the test's `expected_shas` lookup returning the old MANIFEST SHA (`d915c5...`) from a stale DB record (created during the original ingestion before the regeneration), while the chunk citations carried the on-disk SHA (`ced315...`). This was resolved by removing the old-SHA DB record on 2026-09-12.

### DOC-020 — Court Docket

| Field | Value |
|-------|-------|
| **Document** | `DOC-020-Docket.pdf` |
| **Type** | PDF (native, text-based) |
| **Old SHA-256** (7d656f7^, pre-regeneration) | `861b4e4a8392e9fb465d2e73a923fdf8737040d63165f656ff5cc88fb9c8b1b8` |
| **New SHA-256** (current on-disk, HEAD d9cf341) | `424c1de39885020e653a9e8f2055198442370cd5f6df80e9d1d929b84b61114b` |
| **MANIFEST.md SHA** (frozen at c2bba85, matches old) | `861b4e4a8392e9fb465d2e73a923fdf8737040d63165f656ff5cc88fb9c8b1b8` |
| **Regeneration reason** | Blank PDF rendering — document was generated with `reportlab` producing an empty page; replaced with a non-blank version containing the docket text from corpus-facts.md. |
| **Evidence** | `git show 7d656f7^:testdata/corpus-v0.1/DOC-020-Docket.pdf | shasum -a 256` → `861b4e...`; current on-disk `shasum -a 256 testdata/corpus-v0.1/DOC-020-Docket.pdf` → `424c1d...`; MANIFEST.md line at c2bba85 → `861b4e...` (matches old SHA — MANIFEST was not updated after regeneration). |

**Gold questions touching DOC-020:**
- Q36: "List the filing dates for each document in the court docket excerpt" — expects DOC-020-Docket.pdf

---

## Verification methodology

All hashes verified on 2026-09-12 from HEAD (d9cf341):

1. **Old SHA-256:** `git show 7d656f7^:testdata/corpus-v0.1/<file> | shasum -a 256` — reads the file content as it existed in the pre-regeneration tree (commit 13e35e9).
2. **New SHA-256:** `shasum -a 256 testdata/corpus-v0.1/<file>` — reads the current on-disk file at HEAD d9cf341.
3. **MANIFEST SHA:** extracted from `testdata/corpus-v0.1/MANIFEST.md` at commit c2bba85 (the freeze commit). For DOC-009, the MANIFEST at HEAD also checked (`661516...` — third state, incorrect).
4. All three sources cross-referenced. Three of four documents (DOC-011, DOC-013, DOC-020) have MANIFEST SHA = old SHA (MANIFEST was not updated). DOC-009 has MANIFEST SHA ≠ old SHA (MANIFEST was corrupted during the regeneration commit).

---

## Resolution status

DB records aligned to on-disk SHA-256 on 2026-09-12. Four old-SHA DB records removed (one per corrigendum document, the pre-regeneration version). Final state: one record per document, SHA-256 matching current on-disk file at HEAD d9cf341.

**Unresolved:** MANIFEST.md at HEAD still contains the incorrect SHA `661516...` for DOC-009 (should be `07e4df...`), and the correct old-SHA values for DOC-011, DOC-013, DOC-020 (which have not been updated to reflect the regeneration). The MANIFEST is frozen and should not be modified without a full corpus version bump. The correct action is a v0.2 corpus with re-signed MANIFEST and re-bound gold questions — deferred until the pipeline is ready for Week 5.

---

## Rule (going forward)

A frozen corpus is immutable. If a file must be replaced:
1. Bump corpus version (v0.1 → v0.2)
2. Recompute SHA-256 for all affected files in new MANIFEST.md
3. Re-bind every gold question pointer touching those documents
4. Re-run full retrieval + isolation battery
5. Log in `decisions/log.md`
