"""Verify the verifier v1.1.0 prompt with synonym equivalence.

Test on the 6 structural misses (Q05, Q09, Q25, Q33, Q46, Q49) to confirm
the synonym-aware verifier accepts expanded retrieval results.
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
from app.services.verifier import verify_top_k, VERIFIER_PROMPT_VERSION

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# The 6 structural misses (Q05, Q09, Q25, Q33, Q46, Q49)
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


def main():
    db = SessionLocal()
    try:
        matter_a = db.query(Matter).filter(Matter.name.like("%Matter A%")).first()
        if not matter_a:
            print("ERROR: Matter A not found.")
            return

        print("=" * 70)
        print(f"Verifier v{VERIFIER_PROMPT_VERSION} — Synonym-Aware Verification Test")
        print("=" * 70)

        doc_lookup = {}
        for doc in db.query(Document).filter(Document.matter_id == matter_a.id).all():
            doc_lookup[doc.sha256] = doc.original_filename

        results = []
        for q_id, question, expected_docs in MISSES:
            if isinstance(expected_docs, str):
                expected_docs = [expected_docs]

            expected_shas = set()
            for doc_name in expected_docs:
                doc = db.query(Document).filter(
                    Document.original_filename == doc_name,
                    Document.matter_id == matter_a.id,
                    Document.is_duplicate == False,
                ).first()
                if doc:
                    expected_shas.add(doc.sha256)

            # Retrieve (with expansion built-in)
            raw_citations = retrieve(db, str(matter_a.id), question, top_k=5)

            # Verify
            t0 = time.time()
            if len(raw_citations) > 0:
                verified = verify_top_k(question, raw_citations, top_k_verify=len(raw_citations))
            else:
                verified = []
            latency = time.time() - t0

            # Check if any verified citation matches expected
            found = False
            for c in verified:
                if c.sha256 in expected_shas:
                    found = True
                    break

            # Show per-citation verifier decisions
            print(f"\n{q_id}: {question[:60]}")
            print(f"  Expected: {expected_docs}")
            print(f"  Raw={len(raw_citations)} Verified={len(verified)} Latency={latency:.2f}s Found={'✓' if found else '✗'}")

            for i, c in enumerate(raw_citations[:5]):
                fn = doc_lookup.get(c.sha256, "?")
                decision = c.retrieval_scores.get("verifier_decision", "?")
                quote = c.retrieval_scores.get("verifier_quote", "")
                is_match = "✓" if c.sha256 in expected_shas else " "
                print(f"    {i+1}. [{decision}] {is_match} {fn}")
                if quote:
                    print(f"       Quote: {quote[:80]}...")

            results.append({
                "q_id": q_id,
                "found": found,
                "n_raw": len(raw_citations),
                "n_verified": len(verified),
                "latency_s": latency,
            })

        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)

        hits = sum(1 for r in results if r["found"])
        print(f"Recovered: {hits}/6 ({hits/6*100:.1f}%)")
        print(f"Verifier prompt version: {VERIFIER_PROMPT_VERSION}")
        print(f"Average latency: {sum(r['latency_s'] for r in results)/len(results):.2f}s")

    finally:
        db.close()


if __name__ == "__main__":
    main()
