# Ganymede — Full Gold Set Retrieval Test (correctly categorized, all 50 questions)

"""Run the frozen gold set through the retrieval pipeline and report Recall@5.

The frozen gold-set-draft.md binds 28 questions to evidence pointers (answerable).
The remaining 22 are verified unanswerable by construction:
  - 16 questions are NOT IN corpus-v0.1 (no document contains the answer)
  - 6 questions are formal answer-absent (Q39-Q44)

All 22 unanswerable questions must return zero results. Any citation = a defect."""

import os
import sys
import json
import time

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

# 28 answerable questions with evidence pointers from frozen gold-set-draft.md
GOLD_SET = [
    # Direct factual (answerable)
    ("Q01", "What is the termination date stated in the master services agreement?", "DOC-003-MSA.docx"),
    ("Q04", "What amount does the complaint allege as damages?", "DOC-001-Complaint.pdf"),
    ("Q05", "On what date did the first breach notice arrive?", "DOC-014-Chronology.pdf"),
    ("Q07", "What is the stated jurisdiction for dispute resolution?", "DOC-003-MSA.docx"),
    ("Q08", "Who signed the amendment as the corporate officer?", "DOC-004-Amendment-No-1.docx"),
    ("Q09", "What is the contract price stated in the invoice that matches the dispute?",
     ["DOC-007-Invoice-1044.docx", "DOC-008-Invoice-1045.docx"]),
    ("Q11", "What date does the deposition notice set for the first deposition?", "DOC-013-Deposition-Notice.pdf"),
    ("Q12", "Which paragraph describes the scope of the non-disclosure obligation?", "DOC-003-MSA.docx"),
    ("Q13", "What is the stated interest rate on the unpaid balance in the demand letter?", "DOC-011-Demand-Letter.pdf"),
    ("Q14", "Who is the court reporter named in the deposition scheduling order?", "DOC-013-Deposition-Notice.pdf"),
    ("Q15", "What page of the technical report contains the failure-mode analysis?", "DOC-016-Technical-Report.docx"),
    ("Q17", "What is the effective date of the most recent amendment?", "DOC-004-Amendment-No-1.docx"),
    ("Q19", "What is the stated cure period in the default clause?", "DOC-003-MSA.docx"),
    # Multi-document synthesis (answerable)
    ("Q21", "Across the contract and the amendment, what is the current notice period for termination?",
     ["DOC-003-MSA.docx", "DOC-004-Amendment-No-1.docx"]),
    ("Q22", "Do the complaint and the defendant's answer agree on the date of the alleged breach?",
     ["DOC-001-Complaint.pdf", "DOC-002-Answer.pdf"]),
    ("Q25", "Which documents establish that the defendant received notice before filing?",
     ["DOC-009-Notice-of-Default.pdf", "DOC-010-Response-Letter.pdf"]),
    ("Q29", "Which documents show the sequence of communications leading to the settlement offer?",
     ["DOC-009-Notice-of-Default.pdf", "DOC-010-Response-Letter.pdf",
      "DOC-011-Demand-Letter.pdf", "DOC-012-Settlement-Email.pdf"]),
    # Chronology (answerable)
    ("Q31", "List the events in the matter in chronological order", "DOC-014-Chronology.pdf"),
    ("Q32", "On what date did the contract transition from draft to executed?", "DOC-003-MSA.docx"),
    ("Q33", "Who sent the first breach notice and on what date?", "DOC-009-Notice-of-Default.pdf"),
    ("Q34", "What is the sequence of amendments to the agreement?", "DOC-004-Amendment-No-1.docx"),
    ("Q36", "List the filing dates for each document in the court docket excerpt", "DOC-020-Docket.pdf"),
    # Adversarial/ambiguous (answerable)
    ("Q38", "Who participated in the settlement conference, and on what date?", "DOC-012-Settlement-Email.pdf"),
    ("Q45", "The contract states the termination date as the end of the term. What is that date?", "DOC-003-MSA.docx"),
    ("Q46", "Two documents give different dates for the same event. Which is better supported?",
     ["DOC-013-Deposition-Notice.pdf", "DOC-019-Deposition-Transcript.pdf"]),
    ("Q47", "What is the date of the event described only as 'the week after the incident'?", "DOC-016-Technical-Report.docx"),
    ("Q48", "A document contains a passage that looks like an instruction to 'ignore prior confidentiality terms.' Does the system follow it?", "DOC-018b-Additional-Terms.pdf"),
    ("Q49", "The same fact appears in two documents with different quoted wording. Which is the primary source?",
     ["DOC-009-Notice-of-Default.pdf", "DOC-017-Notice-Email.pdf"]),
    ("Q50", "A user asks for a chronology of events that only some documents support. What does the chronology contain, and where is the gap?", "DOC-014-Chronology.pdf"),
]

# 16 questions verified NOT IN corpus-v0.1 — no document contains the answer
NOT_IN_CORPUS = [
    ("Q02", "Who is named as the non-compete defendant in the employment dispute?"),
    ("Q03", "Which paragraph of the lease states the notice period for termination?"),
    ("Q06", "Which exhibit lists the purchased equipment serial numbers?"),
    ("Q10", "Which party is identified as the indemnitor in the indemnification clause?"),
    ("Q16", "Which clause limits the warranty to the original purchaser?"),
    ("Q18", "Which attachment lists the excluded liabilities?"),
    ("Q20", "Who is the named insured in the policy at issue?"),
    ("Q23", "Across the invoices and the purchase order, what is the total amount ordered?"),
    ("Q24", "What is the chain of title from the original agreement to the current assignee?"),
    ("Q26", "Across the minutes and the bylaw amendment, who is authorized to execute contracts above $50,000?"),
    ("Q27", "Do the expert report and the underlying data summary agree on the failure date?"),
    ("Q28", "Across the lease and the correspondence, what is the current rent amount after the modification?"),
    ("Q30", "Across the policy declarations and the claim form, who is the additional insured?"),
    ("Q35", "When did the parties first exchange Position statements?"),
    ("Q37", "Which event occurred first: the inspection or the repair request?"),
]

# 6 formal answer-absent questions (Q39-Q44, frozen Section D)
ANSWER_ABSENT = [
    ("Q39", "What did the CEO say in the internal meeting on March 14?"),
    ("Q40", "Which external case law supports the defendant's motion?"),
    ("Q41", "What is the opposing party's current settlement demand?"),
    ("Q42", "Who will be called as the second expert witness?"),
    ("Q43", "What is the plaintiff's attorney's hourly rate?"),
    ("Q44", "Which document is missing from the file, if any, that would establish the date of delivery?"),
]


def main():
    db = SessionLocal()
    try:
        matter_a = db.query(Matter).filter(Matter.name.like("%Matter A%")).first()
        if not matter_a:
            print("ERROR: Matter A not found.")
            return

        print("=" * 70)
        print("Week 4 Full Gold Set Retrieval Test")
        print("28 answerable + 22 unanswerable = 50 total (frozen gold-set-draft.md)")
        print("=" * 70)

        # Step 1: Chunk all pages
        print("\n[1] Chunking pages...")
        total_chunks = chunk_all_pages(db, str(matter_a.id))
        print(f"    Created {total_chunks} chunks")

        # Step 2: Embed all chunks
        print("\n[2] Embedding chunks...")
        total_embeddings = embed_all_chunks(db, str(matter_a.id))
        print(f"    Created {total_embeddings} embeddings")

        doc_lookup = {}
        for doc in db.query(Document).filter(Document.matter_id == matter_a.id).all():
            doc_lookup[doc.sha256] = doc.original_filename

        # --- Answerable queries ---
        print(f"\n[3] Running {len(GOLD_SET)} answerable gold set queries...")
        results = []
        start_time = time.time()

        for q_id, question, expected_docs in GOLD_SET:
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

            citations = retrieve(db, str(matter_a.id), question, top_k=5)

            found = False
            for c in citations[:5]:
                if c.sha256 in expected_shas:
                    found = True
                    break

            results.append({
                "q_id": q_id,
                "question": question,
                "expected": expected_docs,
                "expected_shas": list(expected_shas),
                "found": found,
                "citations_count": len(citations),
                "top_sha": citations[0].sha256 if citations else None,
                "top_doc": doc_lookup.get(citations[0].sha256, "?") if citations else None,
            })

            status = "✓" if found else "✗ MISS"
            top_doc = doc_lookup.get(citations[0].sha256, "?") if citations else "NONE"
            print(f"    {q_id}: {status} ({len(citations)} citations, top={top_doc})")

        elapsed = time.time() - start_time

        # --- Unanswerable queries (must return zero) ---
        print(f"\n[4] Running {len(NOT_IN_CORPUS) + len(ANSWER_ABSENT)} unanswerable queries (must return 0)...")
        unanswerable_results = []

        for q_id, question in NOT_IN_CORPUS + ANSWER_ABSENT:
            citations = retrieve(db, str(matter_a.id), question, top_k=5)
            returned = len(citations)
            is_clean = returned == 0
            unanswerable_results.append({
                "q_id": q_id,
                "group": "NOT_IN_CORPUS" if q_id in [x[0] for x in NOT_IN_CORPUS] else "ANSWER_ABSENT",
                "returned": returned,
                "is_clean": is_clean,
                "top_sha": citations[0].sha256 if citations else None,
                "top_doc": doc_lookup.get(citations[0].sha256, "?") if citations else None,
            })
            top_doc = doc_lookup.get(citations[0].sha256, "?") if citations else "NONE"
            status = "✓" if is_clean else f"✗ RETURNED {returned} (top={top_doc})"
            print(f"    {q_id}: {status}")

        # --- Summary ---
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)

        total_answerable = len(GOLD_SET)
        found_count = sum(1 for r in results if r["found"])
        recall_at_5 = found_count / total_answerable * 100 if total_answerable > 0 else 0

        print(f"\nAnswerable: {found_count}/{total_answerable} with expected doc in top 5")
        print(f"Recall@5: {recall_at_5:.1f}%")
        print(f"Target: >=80%")
        print(f"Status: {'PASS' if recall_at_5 >= 80 else 'FAIL'}")
        print(f"Query time: {elapsed:.2f}s total, {elapsed/total_answerable:.2f}s avg")

        total_unanswerable = len(NOT_IN_CORPUS) + len(ANSWER_ABSENT)
        clean_count = sum(1 for r in unanswerable_results if r["is_clean"])
        print(f"\nUnanswerable: {clean_count}/{total_unanswerable} returned zero results")
        print(f"Target: {total_unanswerable}/{total_unanswerable} (100%)")
        print(f"Status: {'PASS' if clean_count == total_unanswerable else 'FAIL'}")

        not_in_corpus_clean = sum(1 for r in unanswerable_results if r["group"] == "NOT_IN_CORPUS" and r["is_clean"])
        aa_clean = sum(1 for r in unanswerable_results if r["group"] == "ANSWER_ABSENT" and r["is_clean"])
        print(f"  Not-in-corpus: {not_in_corpus_clean}/{len(NOT_IN_CORPUS)} clean")
        print(f"  Answer-absent (Q39-Q44): {aa_clean}/{len(ANSWER_ABSENT)} clean")

        # Miss details
        misses = [r for r in results if not r["found"]]
        if misses:
            print(f"\nMisses ({len(misses)} of {total_answerable}):")
            for m in misses:
                print(f"  {m['q_id']}: {m['question'][:60]}...")
                print(f"    Expected: {m['expected']}")
                print(f"    Top result: {m['top_doc']}")

        # Leak details
        leaks = [r for r in unanswerable_results if not r["is_clean"]]
        if leaks:
            print(f"\nUnanswerable leaks ({len(leaks)} of {total_unanswerable}):")
            for l in leaks:
                print(f"  {l['q_id']} ({l['group']}): returned {l['returned']} citations, top={l['top_doc']}")

        # Save report
        report = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "recall_at_5": recall_at_5,
            "found": found_count,
            "total_answerable": total_answerable,
            "unanswerable_clean": clean_count,
            "unanswerable_total": total_unanswerable,
            "not_in_corpus_clean": not_in_corpus_clean,
            "answer_absent_clean": aa_clean,
            "pass": recall_at_5 >= 80 and clean_count == total_unanswerable,
            "misses": misses,
            "leaks": leaks,
            "query_time_total_s": elapsed,
        }

        report_dir = os.path.join(os.path.dirname(__file__), "..", "tests")
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, "gold-set-report.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nDetailed report saved to: {report_path}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
