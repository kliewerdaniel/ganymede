# Ganymede — Corpus and Gold Set Freeze Checklist

**Status:** Frozen — 2026-09-11 (frozen at Daniel's direction)
**Date:** September 2026
**Corpus:** corpus-v0.1 (Matter A) + corpus-v0.1-matter-b (Matter B)
**Gold set:** docs/specification/gold-set-draft.md (50 questions, bound to corpus-v0.1)

---

## What "frozen" means

When Daniel signs off:

1. **The corpora become immutable.** No file in corpus-v0.1 or corpus-v0.1-matter-b may be changed, replaced, or removed without a documented reason, a version bump (corpus-v0.2), and a re-check of all cross-references.
2. **The gold set becomes immutable.** No question in the gold set may be changed, replaced, or removed without a documented reason, a version bump, and re-binding to the new corpus.
3. **The benchmark becomes the definition of "works."** Every subsequent release runs against the same frozen benchmark. Improvements and regressions are attributable to the system, not to a moving target.
4. **Changes require a new corpus version.** If a corpus file is changed, the benchmark run is invalidated until the corpus is re-frozen and the gold set is re-checked against it.

---

## What Daniel is signing off on

- [ ] corpus-v0.1 (Matter A) is approved as the frozen Matter A evaluation corpus.
- [ ] corpus-v0.1-matter-b (Matter B) is approved as the frozen Matter B evaluation corpus.
- [ ] The gold set (50 questions bound to corpus-v0.1) is approved as the frozen benchmark.
- [ ] The isolation test specification (docs/specification/isolation-tests.md) is approved as the cross-matter attack battery.
- [ ] The status of the corpora and gold set changes from "Draft (candidate for freeze)" to "Frozen."

---

## What unblocks afterward

Once Daniel signs off:

1. **Benchmark-first implementation begins.** Per DEVELOPMENT.md, the benchmark is the definition of "works." Features are not done until they pass the benchmark.
2. **The quality gates become the acceptance criteria.** The eight quality gates in benchmark-design.md (parsing success, retrieval recall, citation support, unsupported claims, matter isolation, recovery, latency, audit completeness) are the internal launch thresholds.
3. **The cross-matter isolation tests become part of the regression suite.** 100% of attacks must be blocked.
4. **The pilot-readiness packet can be finalized.** The quality brief (part of the pilot-readiness packet) can reference the frozen benchmark results.

---

## Sign-off

**Daniel Kliewer:** Frozen at Daniel's direction — 2026-09-11

**Date:** September 11, 2026

---

*This checklist is the freeze gate. It is not a contract. It is the definition of what "frozen" means for the Ganymede benchmark.*
