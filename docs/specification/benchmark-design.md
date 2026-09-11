# Ganymede — Benchmark Design

**Status:** Draft
**Date:** September 2026
**Frozen:** Week 2 (after corpus is chosen)
**Purpose:** Define "works" before writing features. Every subsequent release runs against the same questions, citations, access-control attacks, and operational checks.

---

## The benchmark is part of the product

Freeze a synthetic or properly authorized test matter in Week 2. Every subsequent release runs against the same benchmark. Improvements and regressions are attributable to the system, not to a moving target.

See [Test Corpus Rules](test-corpus-rules.md) for the corpus requirements.

---

## Gold-set anatomy

The gold set has 50 questions, structured as follows:

| Type | Count | Description |
|------|-------|-------------|
| Direct factual questions | 20 | Single fact, single document or small set. "Where does the record discuss the termination date?" |
| Multi-document synthesis | 10 | Fact that requires connecting two or more documents. |
| Chronology questions | 8 | Date, sequence, actor, event ordering. |
| Answer-absent questions | 6 | Questions the corpus cannot answer. The system must say "not found," not fill the gap. |
| Adversarial or ambiguous | 6 | Edge cases, ambiguity, contradiction, uncertainty. |

Each gold-set item records:
- The question.
- The acceptable answer (what a reviewer would accept as correct).
- The exact supporting passages (document, page, offsets).
- Forbidden sources (if any).
- Reviewer notes.

---

## Quality gates for pilot readiness

These are internal launch thresholds, not market facts. They will be tightened after observing real legal reviewers.

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

Latency must always be reported with the model, corpus size, and reference hardware.

---

## Benchmark categories

### Parsing tests

- Digital PDFs
- Scanned PDFs (with OCR)
- DOCX
- TXT
- Tables
- Rotated pages
- Corrupt or malformed files
- Duplicate detection
- Failure recovery (a failed OCR job does not silently create an empty searchable document)

### Retrieval tests

- Recall@5 on the gold set
- Exact-name search
- Date search
- Negation (questions that depend on a fact being absent)
- Answer-absent (system must say "not found")
- Cross-matter isolation (no passage from matter A appears in answers about matter B)

### Citation tests

- Every claim cites evidence.
- Citation object preserves document hash, page, offsets, retrieval scores, model/version metadata.
- Unsupported material claims below threshold.
- Blind review of 25 outputs.

### Security tests

- IDOR (insecure direct object reference)
- Guessed document IDs
- Stale sessions
- Revoked users
- Export permission
- Prompt injection inside documents
- Poisoned citations
- Denial-of-service uploads
- Malicious file types
- Data deletion attacks
- Restore integrity
- Role revocation
- Model failure behavior
- Disk exhaustion

### Operational tests

- Fresh install succeeds.
- Restore succeeds from backup.
- Health checks report correctly.
- Backup/restore is tested on a clean machine.
- Diagnostic bundle redacts matter content and secrets by default.

---

## Release evidence (generated every build)

Every build produces three artifacts:

1. **Model card** — model, quantization, prompt version, known limitations.
2. **Benchmark report** — retrieval, citation, absence, latency, and security results.
3. **Release manifest** — image digests, migrations, dependencies, and signed release checksum.

---

## Quality rule in the benchmark

If the system lacks evidence, it must say "not found in the approved matter sources." It may suggest a better query or identify missing documents, but it must not fill the gap from model memory.

---

## Benchmark-first discipline

- The benchmark is the definition of "works." Features are not done until they pass the benchmark.
- Benchmark regressions are not hidden. If a release regresses, it is not shipped until the regression is explained or fixed.
- The gold set is frozen after Week 2. Additions are documented; the frozen set is always run.

---

*This document is provisional until the corpus is chosen and the gold set is written. It will be updated in Week 2.*
