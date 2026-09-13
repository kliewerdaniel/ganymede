"""Targeted query expansion for 6 structural misses — Week 4 gate closure.

Design: NOT the over-expanded "combined" variant (already tested and rejected).
Instead, a context-aware expansion that:
1. Applies date normalization ONLY when the question references a date.
2. Applies legal-term synonyms ONLY for terms actually present in the question.
3. Uses tighter, more precise synonym mappings than the rejected "combined" variant.
4. Does NOT stack expansions that produce verbose, score-diluting queries.

Measured against the frozen gold set. Does not modify the corpus.
"""

import os
import sys
import json
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.models import Matter, Document
from app.services.retrieval import retrieve

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# The 6 structural misses
MISSES = [
    ("Q05", "On what date did the first breach notice arrive?", "DOC-014-Chronology.pdf"),
    ("Q09", "What is the contract price stated in the invoice that matches the dispute?",
     ["DOC-007-Invoice-1044.docx", "DOC-008-Invoice-1045.docx"]),
    ("Q25", "Which documents establish that the defendant received notice before filing?",
     ["DOC-009-Notice-of-Default.pdf", "DOC-010-Response-Letter.pdf"]),
    ("Q33", "Who sent the first breach notice and on what date?", "DOC-009-Notice-of-Default.pdf"),
    ("Q46", "Two documents give different dates for the same event. Which is better supported?",
     ["DOC-013-Deposition-Notice.pdf", "DOC-019-Deposition-Transcript.pdf"]),
    ("Q49", "The same fact appears in two documents with different quoted wording. Which is the primary source?",
     ["DOC-009-Notice-of-Default.pdf", "DOC-017-Notice-Email.pdf"]),
]

# Keyword detectors for context-aware expansion
DATE_KEYWORDS = {"date", "when", "what date", "on what date", "timeline", "chronolog"}
LEGAL_TERM_MAPPINGS = {
    "breach": ["default", "breach"],
    "notice": ["notice", "demand", "notification"],
    "invoice": ["invoice", "billing", "statement"],
    "filing": ["filing", "docket", "court filing"],
    "contract price": ["amount", "total", "balance", "sum"],
    "received notice": ["served with notice", "notice was sent", "received demand"],
    "deposition": ["deposition", "testimony", "examination"],
    "document": ["document", "record", "paper"],
    "settlement": ["settlement", "resolution", "accord"],
    "damages": ["damages", "compensation", "award"],
    "termination": ["termination", "end", "expiration"],
    "amendment": ["amendment", "modification", "revision"],
    "complaint": ["complaint", "petition", "suit"],
    "answer": ["answer", "response", "reply"],
    "default": ["default", "breach", "failure to perform"],
    "cure period": ["cure period", "grace period", "remediation period"],
    "jurisdiction": ["jurisdiction", "venue", "forum"],
    "indemnitor": ["indemnitor", "indemnifier", "guarantor"],
    "warranty": ["warranty", "guarantee", "assurance"],
    "confidentiality": ["confidentiality", "non-disclosure", "nda"],
    "non-compete": ["non-compete", "non-competition", "restraint of trade"],
    "exhibit": ["exhibit", "attachment", "appendix"],
    "expert": ["expert", "specialist", "consultant"],
    "witness": ["witness", "testifier", "deponent"],
}


def _is_date_question(question: str) -> bool:
    """Check if the question is asking about a date or temporal ordering."""
    q = question.lower()
    return any(kw in q for kw in DATE_KEYWORDS)


def _detect_legal_terms(question: str) -> list:
    """Detect which legal terms from the mapping are present in the question."""
    q = question.lower()
    found = []
    for term in LEGAL_TERM_MAPPINGS:
        if term in q:
            found.append(term)
    return found


def targeted_expand(question: str) -> str:
    """Apply targeted query expansion based on question content.

    Rules:
    1. If the question references a date, add DATE marker (but don't duplicate).
    2. For each detected legal term, append its synonyms (but don't replace the original).
    3. Do NOT stack all expansions — only apply what's relevant.
    4. Keep the query concise — the RRF fusion benefits from precision, not verbosity.
    """
    q = question.lower()
    expansions = []

    # Date normalization: only for date questions
    if _is_date_question(question):
        # Add DATE marker if not already present
        if "date" in q and "date date" not in q:
            expansions.append("DATE")

    # Legal term expansion: only for terms actually present
    detected_terms = _detect_legal_terms(question)
    for term in detected_terms:
        synonyms = LEGAL_TERM_MAPPINGS[term]
        # Add synonyms that aren't already in the question
        for syn in synonyms:
            if syn not in q:
                expansions.append(syn)

    if not expansions:
        return question

    # Build expanded query: original + expansions, deduplicated
    expanded = question + " " + " ".join(expansions)
    return expanded


def main():
    db = SessionLocal()
    try:
        matter_a = db.query(Matter).filter(Matter.name.like("%Matter A%")).first()
        if not matter_a:
            print("ERROR: Matter A not found.")
            return

        print("=" * 70)
        print("Targeted Query Expansion — 6 Structural Misses")
        print("=" * 70)

        doc_lookup = {}
        for doc in db.query(Document).filter(Document.matter_id == matter_a.id).all():
            doc_lookup[doc.sha256] = doc.original_filename

        results = []
        total_start = time.time()

        for q_id, question, expected_doc in MISSES:
            if isinstance(expected_doc, str):
                expected_doc = [expected_doc]

            expected_shas = set()
            for doc_name in expected_doc:
                doc = db.query(Document).filter(
                    Document.original_filename == doc_name,
                    Document.matter_id == matter_a.id,
                    Document.is_duplicate == False,
                ).first()
                if doc:
                    expected_shas.add(doc.sha256)

            # Original query
            t0 = time.time()
            citations_orig = retrieve(db, str(matter_a.id), question, top_k=5)
            elapsed_orig = (time.time() - t0) * 1000
            found_orig = any(c.sha256 in expected_shas for c in citations_orig[:5])
            top_orig = doc_lookup.get(citations_orig[0].sha256, "NONE") if citations_orig else "NONE"

            # Targeted expansion
            expanded_q = targeted_expand(question)
            t0 = time.time()
            citations_exp = retrieve(db, str(matter_a.id), expanded_q, top_k=5)
            elapsed_exp = (time.time() - t0) * 1000
            found_exp = any(c.sha256 in expected_shas for c in citations_exp[:5])
            top_exp = doc_lookup.get(citations_exp[0].sha256, "NONE") if citations_exp else "NONE"

            row = {
                "q_id": q_id,
                "question": question,
                "expected": expected_doc,
                "original": {
                    "found": found_orig,
                    "top_doc": top_orig,
                    "elapsed_ms": elapsed_orig,
                    "query": question,
                },
                "targeted": {
                    "found": found_exp,
                    "top_doc": top_exp,
                    "elapsed_ms": elapsed_exp,
                    "query": expanded_q,
                },
            }
            results.append(row)

            status_orig = "✓" if found_orig else "✗"
            status_exp = "✓" if found_exp else "✗"
            print(f"  {q_id}: original={status_orig} targeted={status_exp}")
            print(f"    Original:  {question[:70]}")
            print(f"    Targeted:  {expanded_q[:70]}")
            print(f"    Top orig:  {top_orig}  Top targeted: {top_exp}")
            print()

        total_time = time.time() - total_start

        # Summary
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)

        orig_hits = sum(1 for r in results if r["original"]["found"])
        exp_hits = sum(1 for r in results if r["targeted"]["found"])
        print(f"  Original:  {orig_hits}/6 hits")
        print(f"  Targeted:  {exp_hits}/6 hits")
        print(f"  Delta:     {exp_hits - orig_hits:+d}")

        # Show which questions were recovered
        recovered = [r["q_id"] for r in results if r["targeted"]["found"] and not r["original"]["found"]]
        lost = [r["q_id"] for r in results if not r["targeted"]["found"] and r["original"]["found"]]
        if recovered:
            print(f"  Recovered: {', '.join(recovered)}")
        if lost:
            print(f"  Lost:      {', '.join(lost)}")

        print(f"\nTotal time: {total_time:.1f}s")

        # Save report
        report = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "variant": "targeted_date_legal",
            "n_misses_tested": len(MISSES),
            "original_hits": orig_hits,
            "targeted_hits": exp_hits,
            "delta": exp_hits - orig_hits,
            "recovered": recovered,
            "lost": lost,
            "per_question": results,
            "total_time_s": total_time,
        }

        report_dir = os.path.join(os.path.dirname(__file__), "..", "tests")
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, "expansion-targeted-report.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved to: {report_path}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
