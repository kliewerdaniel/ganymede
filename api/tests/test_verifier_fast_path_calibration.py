"""Fast-path threshold calibration test — no LLM calls.

Measures fast-path trigger rates using only RRF + vector similarity
(retrieval already done, no verification needed). Confirms the fast-path
never triggers on unanswerable queries. Then runs the verifier only
on a small sample of full-verification queries to get latency estimates.
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
from app.services.query_expansion import expand_query
from app.services.verifier import verify_top_k_fast_path, verify_top_k, FAST_PATH_RRF_THRESHOLD, FAST_PATH_VECTOR_THRESHOLD

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 29 answerable questions
GOLD_SET = [
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
    ("Q21", "Across the contract and the amendment, what is the current notice period for termination?",
     ["DOC-003-MSA.docx", "DOC-004-Amendment-No-1.docx"]),
    ("Q22", "Do the complaint and the defendant's answer agree on the date of the alleged breach?",
     ["DOC-001-Complaint.pdf", "DOC-002-Answer.pdf"]),
    ("Q25", "Which documents establish that the defendant received notice before filing?",
     ["DOC-009-Notice-of-Default.pdf", "DOC-010-Response-Letter.pdf"]),
    ("Q29", "Which documents show the sequence of communications leading to the settlement offer?",
     ["DOC-009-Notice-of-Default.pdf", "DOC-010-Response-Letter.pdf",
      "DOC-011-Demand-Letter.pdf", "DOC-012-Settlement-Email.pdf"]),
    ("Q31", "List the events in the matter in chronological order", "DOC-014-Chronology.pdf"),
    ("Q32", "On what date did the contract transition from draft to executed?", "DOC-003-MSA.docx"),
    ("Q33", "Who sent the first breach notice and on what date?", "DOC-009-Notice-of-Default.pdf"),
    ("Q34", "What is the sequence of amendments to the agreement?", "DOC-004-Amendment-No-1.docx"),
    ("Q36", "List the filing dates for each document in the court docket excerpt", "DOC-020-Docket.pdf"),
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

# 16 NOT_IN_CORPUS questions
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

# 6 formal ANSWER_ABSENT questions
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
        print("Fast-Path Threshold Calibration Test")
        print(f"RRF threshold: {FAST_PATH_RRF_THRESHOLD}, Vector threshold: {FAST_PATH_VECTOR_THRESHOLD}")
        print("=" * 70)

        doc_lookup = {}
        for doc in db.query(Document).filter(Document.matter_id == matter_a.id).all():
            doc_lookup[doc.sha256] = doc.original_filename

        # --- Phase 1: Fast-path trigger rates (no LLM calls) ---
        print("\n[1] Fast-path trigger rates (no LLM calls)...")
        answerable_fast = 0
        answerable_full = 0
        unanswerable_fast = 0
        unanswerable_full = 0

        answerable_results = []
        unanswerable_results = []

        for q_id, question, expected_docs in GOLD_SET:
            expanded_q = expand_query(question)
            citations = retrieve(db, str(matter_a.id), expanded_q, top_k=5)

            top_1_rrf = 0.0
            top_2_rrf = 0.0
            top_1_vec = 0.0
            fast = False
            if len(citations) >= 2:
                top_1_rrf = citations[0].retrieval_scores.get("rrf_score", 0) or 0
                top_2_rrf = citations[1].retrieval_scores.get("rrf_score", 0) or 0
                top_1_vec = citations[0].retrieval_scores.get("vector_similarity", 0) or 0
                fast = top_1_rrf >= FAST_PATH_RRF_THRESHOLD and top_2_rrf >= 0.031 and top_1_vec >= FAST_PATH_VECTOR_THRESHOLD

            answerable_results.append({"q_id": q_id, "fast": fast, "top_1_rrf": top_1_rrf, "top_2_rrf": top_2_rrf, "top_1_vec": top_1_vec})
            if fast:
                answerable_fast += 1
            else:
                answerable_full += 1

        for q_id, question in NOT_IN_CORPUS + ANSWER_ABSENT:
            expanded_q = expand_query(question)
            citations = retrieve(db, str(matter_a.id), expanded_q, top_k=5)

            top_1_rrf = 0.0
            top_2_rrf = 0.0
            top_1_vec = 0.0
            fast = False
            if len(citations) >= 2:
                top_1_rrf = citations[0].retrieval_scores.get("rrf_score", 0) or 0
                top_2_rrf = citations[1].retrieval_scores.get("rrf_score", 0) or 0
                top_1_vec = citations[0].retrieval_scores.get("vector_similarity", 0) or 0
                fast = top_1_rrf >= FAST_PATH_RRF_THRESHOLD and top_2_rrf >= 0.031 and top_1_vec >= FAST_PATH_VECTOR_THRESHOLD

            group = "NOT_IN_CORPUS" if q_id in [x[0] for x in NOT_IN_CORPUS] else "ANSWER_ABSENT"
            unanswerable_results.append({"q_id": q_id, "group": group, "fast": fast, "top_1_rrf": top_1_rrf, "top_2_rrf": top_2_rrf, "top_1_vec": top_1_vec})
            if fast:
                unanswerable_fast += 1
            else:
                unanswerable_full += 1

        total_answerable = len(GOLD_SET)
        total_unanswerable = len(NOT_IN_CORPUS) + len(ANSWER_ABSENT)
        print(f"  Answerable: fast-path={answerable_fast}/{total_answerable} ({answerable_fast/total_answerable*100:.1f}%), full-verify={answerable_full}/{total_answerable} ({answerable_full/total_answerable*100:.1f}%)")
        print(f"  Unanswerable: fast-path={unanswerable_fast}/{total_unanswerable} ({unanswerable_fast/total_unanswerable*100:.1f}%), full-verify={unanswerable_full}/{total_unanswerable} ({unanswerable_full/total_unanswerable*100:.1f}%)")

        if unanswerable_fast > 0:
            print(f"  ⚠ WARNING: Fast-path triggers on {unanswerable_fast} unanswerable queries!")
            for r in unanswerable_results:
                if r["fast"]:
                    print(f"    {r['q_id']} ({r['group']}): rrf1={r['top_1_rrf']:.4f} rrf2={r['top_2_rrf']:.4f} vec={r['top_1_vec']:.3f}")

        # --- Phase 2: Measure latency on full-verification queries only ---
        print("\n[2] Latency measurement on full-verification queries (2-sample)...")
        # Pick 2 queries that require full verification (keep sample small for CI)
        full_verify_queries = []
        for r in answerable_results + unanswerable_results:
            if not r["fast"]:
                q_id = r["q_id"]
                # Get the question text
                for q in GOLD_SET + [(q[0], q[1], None) for q in NOT_IN_CORPUS] + [(q[0], q[1], None) for q in ANSWER_ABSENT]:
                    if q[0] == q_id:
                        full_verify_queries.append((q[0], q[1]))
                        break
            if len(full_verify_queries) >= 2:
                break

        latencies = []
        for q_id, question in full_verify_queries:
            expanded_q = expand_query(question)
            citations = retrieve(db, str(matter_a.id), expanded_q, top_k=5)
            t0 = time.time()
            verified = verify_top_k(question, citations, top_k_verify=len(citations))
            latency = time.time() - t0
            latencies.append(latency)
            print(f"    {q_id}: {latency:.2f}s ({len(citations)} citations → {len(verified)} verified)")

        # --- Phase 3: Latency estimates ---
        print("\n[3] Latency estimates...")
        p50 = 0.0
        mean_lat = 0.0
        estimated_avg = 0.0
        if latencies:
            p50 = sorted(latencies)[len(latencies) // 2]
            mean_lat = sum(latencies) / len(latencies)
            print(f"  Measured p50: {p50:.2f}s, mean: {mean_lat:.2f}s (on {len(latencies)} full-verification queries)")

            # Estimated average latency with fast-path
            # Fast-path queries: ~0s (no verification)
            # Full-verification queries: ~mean_lat
            # Overall = (fast_count * 0 + full_count * mean_lat) / total
            total_queries = total_answerable + total_unanswerable
            fast_count = answerable_fast + unanswerable_fast
            full_count = answerable_full + unanswerable_full
            estimated_avg = (full_count * mean_lat) / total_queries if total_queries > 0 else 0
            print(f"  Estimated average latency: {estimated_avg:.2f}s/query")
            print(f"  Baseline (no fast-path): {mean_lat:.2f}s/query")
            print(f"  Improvement: {(1 - estimated_avg/mean_lat)*100:.1f}%" if mean_lat > 0 else "  Improvement: N/A")

        # --- Phase 4: Gate verification on a small sample ---
        print("\n[4] Gate verification (fast-path doesn't reopen answer-absent, 5-sample)...")
        # Run 5 unanswerable queries that require full verification
        leaks = 0
        sample_unanswerable = [(r["q_id"], r["group"]) for r in unanswerable_results if not r["fast"]][:5]
        for q_id, group in sample_unanswerable:
            # Get question text
            question = None
            for q in NOT_IN_CORPUS + ANSWER_ABSENT:
                if q[0] == q_id:
                    question = q[1]
                    break
            if not question:
                continue
            expanded_q = expand_query(question)
            citations = retrieve(db, str(matter_a.id), expanded_q, top_k=5)
            verified = verify_top_k_fast_path(question, citations, top_k_verify=len(citations))
            if len(verified) > 0:
                leaks += 1
                print(f"  ⚠ {q_id} ({group}): leaked {len(verified)} citations")
            else:
                print(f"  ✓ {q_id} ({group}): clean")

        if leaks == 0:
            print("  Sample confirms fast-path doesn't leak on unanswerable queries.")
        else:
            print(f"  ⚠ {leaks}/5 unanswerable queries leaked — thresholds need adjustment!")

        # --- Save report ---
        report = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "rrf_threshold": FAST_PATH_RRF_THRESHOLD,
            "vector_threshold": FAST_PATH_VECTOR_THRESHOLD,
            "answerable_fast": answerable_fast,
            "answerable_full": answerable_full,
            "total_answerable": total_answerable,
            "unanswerable_fast": unanswerable_fast,
            "unanswerable_full": unanswerable_full,
            "total_unanswerable": total_unanswerable,
            "unanswerable_fast_path_leaks": unanswerable_fast,
            "latency_sample_size": len(latencies),
            "latency_p50_s": p50 if latencies else None,
            "latency_mean_s": mean_lat if latencies else None,
            "estimated_avg_latency_s": estimated_avg,
            "baseline_latency_s": mean_lat if latencies else None,
        }

        report_dir = os.path.join(os.path.dirname(__file__), "..", "tests")
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, "verifier-fast-path-calibration.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved to: {report_path}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
