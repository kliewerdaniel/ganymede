# Ganymede — Week 4 Gold Set Retrieval Test

"""Run the frozen gold set through the retrieval pipeline and report Recall@5."""

import os
import sys
import json
import time
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.models import Base, Tenant, Matter, Document, Page, Chunk, ChunkEmbedding
from app.services.chunker import chunk_all_pages
from app.services.embedding import embed_all_chunks
from app.services.retrieval import retrieve

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Gold set questions (answerable only — Q01-Q38 minus answer-absent ones)
# Each entry: (question_id, question_text, expected_document_filename)
GOLD_SET = [
    # Direct factual questions (answerable)
    ("Q01", "What is the termination date stated in the master services agreement?", "DOC-003-MSA.docx"),
    ("Q04", "What amount does the complaint allege as damages?", "DOC-001-Complaint.pdf"),
    ("Q05", "On what date did the first breach notice arrive?", "DOC-014-Chronology.pdf"),
    ("Q07", "What is the stated jurisdiction for dispute resolution?", "DOC-003-MSA.docx"),
    ("Q08", "Who signed the amendment as the corporate officer?", "DOC-004-Amendment-No-1.docx"),
    ("Q09", "What is the contract price stated in the invoice that matches the dispute?", ["DOC-007-Invoice-1044.docx", "DOC-008-Invoice-1045.docx"]),
    ("Q11", "What date does the deposition notice set for the first deposition?", "DOC-013-Deposition-Notice.pdf"),
    ("Q12", "Which paragraph describes the scope of the non-disclosure obligation?", "DOC-003-MSA.docx"),
    ("Q13", "What is the stated interest rate on the unpaid balance in the demand letter?", "DOC-011-Demand-Letter.pdf"),
    ("Q14", "Who is the court reporter named in the deposition scheduling order?", "DOC-013-Deposition-Notice.pdf"),
    ("Q15", "What page of the technical report contains the failure-mode analysis?", "DOC-016-Technical-Report.docx"),
    ("Q17", "What is the effective date of the most recent amendment?", "DOC-004-Amendment-No-1.docx"),
    ("Q19", "What is the stated cure period in the default clause?", "DOC-003-MSA.docx"),
    # Multi-document synthesis (answerable)
    ("Q21", "Across the contract and the amendment, what is the current notice period for termination?", ["DOC-003-MSA.docx", "DOC-004-Amendment-No-1.docx"]),
    ("Q25", "Which documents establish that the defendant received notice before filing?", ["DOC-009-Notice-of-Default.pdf", "DOC-010-Response-Letter.pdf"]),
    ("Q29", "Which documents show the sequence of communications leading to the settlement offer?", ["DOC-009-Notice-of-Default.pdf", "DOC-010-Response-Letter.pdf", "DOC-011-Demand-Letter.pdf", "DOC-012-Settlement-Email.pdf"]),
    # Chronology (answerable)
    ("Q31", "List the events in the matter in chronological order", "DOC-014-Chronology.pdf"),
    ("Q32", "On what date did the contract transition from draft to executed?", "DOC-003-MSA.docx"),
    ("Q33", "Who sent the first breach notice and on what date?", "DOC-009-Notice-of-Default.pdf"),
    ("Q34", "What is the sequence of amendments to the agreement?", "DOC-004-Amendment-No-1.docx"),
    ("Q36", "List the filing dates for each document in the court docket excerpt", "DOC-020-Docket.pdf"),
    # Adversarial/ambiguous (answerable)
    ("Q45", "The contract states the termination date as the end of the term. What is that date?", "DOC-003-MSA.docx"),
    ("Q46", "Two documents give different dates for the same event. Which is better supported?", ["DOC-013-Deposition-Notice.pdf", "DOC-019-Deposition-Transcript.pdf"]),
    ("Q49", "The same fact appears in two documents with different quoted wording. Which is the primary source?", ["DOC-009-Notice-of-Default.pdf", "DOC-017-Notice-Email.pdf"]),
]

# Answer-absent questions (should return nothing)
ANSWER_ABSENT = [
    ("Q39", "What did the CEO say in the internal meeting on March 14?"),
    ("Q40", "Which external case law supports the defendant's motion?"),
    ("Q41", "What is the opposing party's current settlement demand?"),
    ("Q42", "Who will be called as the second expert witness?"),
    ("Q43", "What is the plaintiff's attorney's hourly rate?"),
    ("Q44", "Which document is missing from the file that would establish the date of delivery?"),
]


def check_recall_at_k(citations, expected_docs, top_k=5):
    """Check if any expected document appears in top_k citations."""
    if not citations:
        return False
    top_citations = citations[:top_k]
    for c in top_citations:
        for expected in expected_docs:
            if expected in str(c.get("document_id", "")):
                return True
    return False


def main():
    db = SessionLocal()
    try:
        # Get Matter A
        matter_a = db.query(Matter).filter(Matter.name.like("%Matter A%")).first()
        if not matter_a:
            print("ERROR: Matter A not found. Run test_ingest_corpus.py first.")
            return

        print("=" * 70)
        print("Week 4 Gold Set Retrieval Test")
        print("=" * 70)

        # Step 1: Chunk all pages
        print("\n[1] Chunking pages...")
        total_chunks = chunk_all_pages(db, str(matter_a.id))
        print(f"    Created {total_chunks} chunks")

        # Step 2: Embed all chunks
        print("\n[2] Embedding chunks...")
        total_embeddings = embed_all_chunks(db, str(matter_a.id))
        print(f"    Created {total_embeddings} embeddings")

        # Step 3: Run gold set queries
        print("\n[3] Running gold set queries...")
        results = []
        start_time = time.time()

        for q_id, question, expected_docs in GOLD_SET:
            if isinstance(expected_docs, str):
                expected_docs = [expected_docs]

            # Get document IDs for expected docs
            expected_ids = []
            for doc_name in expected_docs:
                doc = db.query(Document).filter(
                    Document.original_filename == doc_name,
                    Document.matter_id == matter_a.id,
                ).first()
                if doc:
                    expected_ids.append(str(doc.id))

            # Run retrieval
            citations = retrieve(db, str(matter_a.id), question, top_k=5)

            # Check recall
            found = False
            for c in citations[:5]:
                if c.document_id in expected_ids:
                    found = True
                    break

            results.append({
                "q_id": q_id,
                "question": question,
                "expected": expected_docs,
                "found": found,
                "citations_count": len(citations),
            })

            status = "✓" if found else "✗ MISS"
            print(f"    {q_id}: {status} ({len(citations)} citations)")

        elapsed = time.time() - start_time

        # Step 4: Answer-absent queries
        print("\n[4] Running answer-absent queries...")
        absent_results = []
        for q_id, question in ANSWER_ABSENT:
            citations = retrieve(db, str(matter_a.id), question, top_k=5)
            # Should return nothing above threshold
            returned = len(citations)
            is_clean = returned == 0
            absent_results.append({
                "q_id": q_id,
                "returned": returned,
                "is_clean": is_clean,
            })
            status = "✓" if is_clean else f"✗ RETURNED {returned}"
            print(f"    {q_id}: {status}")

        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)

        total_questions = len(GOLD_SET)
        found_count = sum(1 for r in results if r["found"])
        recall_at_5 = found_count / total_questions * 100 if total_questions > 0 else 0

        print(f"\nGold set: {found_count}/{total_questions} questions with expected doc in top 5")
        print(f"Recall@5: {recall_at_5:.1f}%")
        print(f"Target: ≥80%")
        print(f"Status: {'✓ PASS' if recall_at_5 >= 80 else '✗ FAIL'}")
        print(f"Query time: {elapsed:.2f}s total, {elapsed/total_questions:.2f}s avg")

        # Miss details
        misses = [r for r in results if not r["found"]]
        if misses:
            print(f"\nMisses ({len(misses)}):")
            for m in misses:
                print(f"  {m['q_id']}: {m['question'][:60]}...")
                print(f"    Expected: {m['expected']}")

        # Answer-absent summary
        clean_count = sum(1 for r in absent_results if r["is_clean"])
        print(f"\nAnswer-absent: {clean_count}/{len(ANSWER_ABSENT)} returned zero results")
        print(f"Target: 6/6 (100%)")
        print(f"Status: {'✓ PASS' if clean_count == 6 else '✗ FAIL'}")

        # Save detailed results
        report = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "recall_at_5": recall_at_5,
            "found": found_count,
            "total": total_questions,
            "pass": recall_at_5 >= 80,
            "misses": misses,
            "answer_absent": {
                "clean": clean_count,
                "total": len(ANSWER_ABSENT),
                "pass": clean_count == 6,
            },
            "query_time_total_s": elapsed,
        }

        report_path = os.path.join(os.path.dirname(__file__), "..", "tests", "gold-set-report.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nDetailed report saved to: {report_path}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
