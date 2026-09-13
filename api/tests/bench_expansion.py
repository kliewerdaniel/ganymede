"""Week 4 gate closure: query expansion benchmark for 6 structural misses.

Tests query expansion variants on the 6 persistent misses:
Q05, Q09, Q25, Q33, Q46, Q49

Variants:
1. Original question (baseline)
2. Date-normalized (dates expanded to "DATE" + original)
3. Legal-term synonyms (breach→default, notice→demand, etc.)
4. Both combined

Measures per-question whether the expected document enters top-5.
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

# Query expansion variants
EXPANSIONS = {
    "original": None,  # no expansion
    "date_normalized": lambda q: q.replace("date", "DATE date").replace("when", "DATE when"),
    "legal_synonyms": lambda q: (
        q.replace("breach", "default breach")
         .replace("notice", "notice demand")
         .replace("invoice", "invoice contract price")
         .replace("filing", "filing court docket")
         .replace("deposition", "deposition transcript")
         .replace("document", "document filing")
    ),
    "combined": lambda q: (
        q.replace("date", "DATE date").replace("when", "DATE when")
         .replace("breach", "default breach")
         .replace("notice", "notice demand")
         .replace("invoice", "invoice contract price")
         .replace("filing", "filing court docket")
         .replace("deposition", "deposition transcript")
         .replace("document", "document filing")
    ),
}


def main():
    db = SessionLocal()
    try:
        matter_a = db.query(Matter).filter(Matter.name.like("%Matter A%")).first()
        if not matter_a:
            print("ERROR: Matter A not found.")
            return

        print("=" * 70)
        print("Query Expansion Benchmark — 6 Structural Misses")
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

            row = {"q_id": q_id, "question": question, "expected": expected_doc, "variants": {}}

            for variant_name, expand_fn in EXPANSIONS.items():
                if expand_fn:
                    expanded_q = expand_fn(question)
                else:
                    expanded_q = question

                t0 = time.time()
                citations = retrieve(db, str(matter_a.id), expanded_q, top_k=5)
                elapsed = (time.time() - t0) * 1000

                found = any(c.sha256 in expected_shas for c in citations[:5])
                top_doc = doc_lookup.get(citations[0].sha256, "NONE") if citations else "NONE"

                row["variants"][variant_name] = {
                    "found": found,
                    "top_doc": top_doc,
                    "top_sha": citations[0].sha256 if citations else None,
                    "elapsed_ms": elapsed,
                    "n_citations": len(citations),
                    "query_used": expanded_q[:80],
                }

                status = "✓ HIT" if found else "✗ miss"
                print(f"  {q_id} [{variant_name:15s}]: {status} "
                      f"(top={top_doc}, {elapsed:.0f}ms)")

            results.append(row)
            print()

        total_time = time.time() - total_start

        # Summary
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)

        for variant_name in EXPANSIONS:
            hits = sum(1 for r in results if r["variants"][variant_name]["found"])
            print(f"  {variant_name:15s}: {hits}/6 hits ({(hits/6*100):.1f}%)")

        print(f"\nTotal time: {total_time:.1f}s")
        print(f"Baseline (original): {sum(1 for r in results if r['variants']['original']['found'])}/6")

        # Save report
        report = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "n_misses_tested": len(MISSES),
            "variants": list(EXPANSIONS.keys()),
            "per_question": results,
            "total_time_s": total_time,
        }

        report_dir = os.path.join(os.path.dirname(__file__), "..", "tests")
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, "expansion-report.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved to: {report_path}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
