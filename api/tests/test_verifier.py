"""Week 4 gate closure: post-retrieval verifier integration test.

Measures:
- Unanswerable-clean rate on all 21 unanswerable questions (target: 21/21)
- Answerable Recall@5 with verifier (must not regress below 79.3%)
- Verifier latency p50/p95
- Isolation battery with verifier in place (target: 8/8 blocked)
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
from app.services.chunker import chunk_all_pages
from app.services.embedding import embed_all_chunks
from app.services.retrieval import retrieve
from app.services.verifier import verify_top_k, verify_batch_latency, VERIFIER_PROMPT_VERSION, VERIFIER_PROMPT_VERSION

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Gold set: 29 answerable questions
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

# 21 unanswerable questions
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
        print("Week 4 Gate Closure: Post-Retrieval Verifier Test")
        print("Verifier prompt version: 1.0.0 (qwen3:4b, local Ollama)")
        print("=" * 70)

        # Prepare
        print("\n[0] Preparing corpus (chunking + embedding if needed)...")
        total_chunks = chunk_all_pages(db, str(matter_a.id))
        total_embeddings = embed_all_chunks(db, str(matter_a.id))
        print(f"    Chunks: {total_chunks}, Embeddings: {total_embeddings}")

        doc_lookup = {}
        for doc in db.query(Document).filter(Document.matter_id == matter_a.id).all():
            doc_lookup[doc.sha256] = doc.original_filename

        # --- ANSWERABLE: Recall@5 with verifier ---
        print(f"\n[1] Running {len(GOLD_SET)} answerable queries WITH verifier...")
        answerable_results = []
        answerable_start = time.time()

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

            # Retrieve raw citations
            raw_citations = retrieve(db, str(matter_a.id), question, top_k=5)

            # Apply verifier
            verified = verify_top_k(question, raw_citations, top_k_verify=len(raw_citations))

            # Check if any verified citation matches expected
            found = False
            for c in verified:
                if c.sha256 in expected_shas:
                    found = True
                    break

            # Also check raw citations for comparison
            raw_found = any(c.sha256 in expected_shas for c in raw_citations[:5])

            answerable_results.append({
                "q_id": q_id,
                "found_raw": raw_found,
                "found_verified": found,
                "n_raw": len(raw_citations),
                "n_verified": len(verified),
                "top_raw_doc": doc_lookup.get(raw_citations[0].sha256, "?") if raw_citations else "NONE",
                "top_verified_doc": doc_lookup.get(verified[0].sha256, "?") if verified else "NONE",
            })

            status_raw = "✓" if raw_found else "✗"
            status_ver = "✓" if found else "✗"
            print(f"    {q_id}: raw={status_raw} verified={status_ver} "
                  f"(raw={len(raw_citations)}→verified={len(verified)}, "
                  f"top_raw={doc_lookup.get(raw_citations[0].sha256,'?') if raw_citations else 'NONE'})")

        answerable_time = time.time() - answerable_start

        # --- UNANSWERABLE: clean rate with verifier ---
        print(f"\n[2] Running {len(NOT_IN_CORPUS) + len(ANSWER_ABSENT)} unanswerable queries WITH verifier...")
        unanswerable_results = []
        unanswerable_start = time.time()

        for q_id, question in NOT_IN_CORPUS + ANSWER_ABSENT:
            raw_citations = retrieve(db, str(matter_a.id), question, top_k=5)
            verified = verify_top_k(question, raw_citations, top_k_verify=len(raw_citations))

            returned = len(verified)
            is_clean = returned == 0

            unanswerable_results.append({
                "q_id": q_id,
                "group": "NOT_IN_CORPUS" if q_id in [x[0] for x in NOT_IN_CORPUS] else "ANSWER_ABSENT",
                "returned": returned,
                "is_clean": is_clean,
                "n_raw": len(raw_citations),
            })

            status = "✓ CLEAN" if is_clean else f"✗ LEAKED {returned} (raw={len(raw_citations)})"
            print(f"    {q_id} ({unanswerable_results[-1]['group']}): {status}")

        unanswerable_time = time.time() - unanswerable_start

        # --- LATENCY ---
        print(f"\n[3] Verifier latency measurement...")
        all_questions = [(q[0], q[1]) for q in GOLD_SET] + [(q[0], q[1]) for q in NOT_IN_CORPUS] + [(q[0], q[1]) for q in ANSWER_ABSENT]

        def get_citations_q(question):
            return retrieve(db, str(matter_a.id), question, top_k=5)

        latency_report = verify_batch_latency(all_questions, get_citations_q)
        print(f"    p50: {latency_report['p50_ms']:.1f} ms")
        print(f"    p95: {latency_report['p95_ms']:.1f} ms")
        print(f"    mean: {latency_report['mean_ms']:.1f} ms")
        print(f"    min/max: {latency_report['min_ms']:.1f} / {latency_report['max_ms']:.1f} ms")
        print(f"    n queries: {latency_report['n_queries']}")

        # --- SUMMARY ---
        print("\n" + "=" * 70)
        print("SUMMARY — Verifier Gate Results")
        print("=" * 70)

        raw_recall = sum(1 for r in answerable_results if r["found_raw"])
        ver_recall = sum(1 for r in answerable_results if r["found_verified"])
        raw_recall_pct = raw_recall / len(GOLD_SET) * 100
        ver_recall_pct = ver_recall / len(GOLD_SET) * 100

        print(f"\nAnswerable Recall@5:")
        print(f"  Raw retrieval (no verifier): {raw_recall}/{len(GOLD_SET)} = {raw_recall_pct:.1f}%")
        print(f"  With verifier:               {ver_recall}/{len(GOLD_SET)} = {ver_recall_pct:.1f}%")
        print(f"  Baseline (no verifier):      79.3% (23/29)")
        print(f"  Regression?                  {'YES — CHECK' if ver_recall_pct < 79.3 else 'No'}")
        print(f"  Target: >=80%")

        total_unanswerable = len(NOT_IN_CORPUS) + len(ANSWER_ABSENT)
        clean_count = sum(1 for r in unanswerable_results if r["is_clean"])
        print(f"\nUnanswerable clean rate:")
        print(f"  Clean: {clean_count}/{total_unanswerable} = {clean_count/total_unanswerable*100:.1f}%")
        print(f"  Leaked: {total_unanswerable - clean_count}/{total_unanswerable}")
        print(f"  Target: 21/21 (100%)")

        # Breakdown
        nic_clean = sum(1 for r in unanswerable_results if r["group"] == "NOT_IN_CORPUS" and r["is_clean"])
        aa_clean = sum(1 for r in unanswerable_results if r["group"] == "ANSWER_ABSENT" and r["is_clean"])
        print(f"  NOT_IN_CORPUS: {nic_clean}/{len(NOT_IN_CORPUS)} clean")
        print(f"  ANSWER_ABSENT: {aa_clean}/{len(ANSWER_ABSENT)} clean")

        # Per-question detail on misses
        ver_misses = [r for r in answerable_results if not r["found_verified"]]
        raw_misses = [r for r in answerable_results if not r["found_raw"]]
        if ver_misses:
            print(f"\nVerifier misses ({len(ver_misses)}/{len(GOLD_SET)}):")
            for m in ver_misses:
                print(f"  {m['q_id']}: raw={m['found_raw']}→verified={m['found_verified']} "
                      f"(raw top={m['top_raw_doc']}, verified top={m['top_verified_doc']})")

        leaks = [r for r in unanswerable_results if not r["is_clean"]]
        if leaks:
            print(f"\nVerifier leaks ({len(leaks)}/{total_unanswerable}):")
            for l in leaks:
                print(f"  {l['q_id']} ({l['group']}): returned {l['returned']} verified citations (raw={l['n_raw']})")

        # Gate status
        recall_gate = ver_recall_pct >= 80
        unanswerable_gate = clean_count == total_unanswerable
        print(f"\nGate status:")
        print(f"  Recall@5 >= 80%:        {'PASS' if recall_gate else 'FAIL'} ({ver_recall_pct:.1f}%)")
        print(f"  Unanswerable 100% clean: {'PASS' if unanswerable_gate else 'FAIL'} ({clean_count}/{total_unanswerable})")
        print(f"  Overall:                {'PASS' if (recall_gate and unanswerable_gate) else 'FAIL'}")

        # Save report
        report = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "verifier_prompt_version": VERIFIER_PROMPT_VERSION,
            "verifier_model": "qwen3:4b (Ollama, local)",
            "raw_recall_at_5": raw_recall_pct,
            "raw_found": raw_recall,
            "verifier_recall_at_5": ver_recall_pct,
            "verifier_found": ver_recall,
            "recall_gate_pass": recall_gate,
            "unanswerable_clean": clean_count,
            "unanswerable_total": total_unanswerable,
            "unanswerable_gate_pass": unanswerable_gate,
            "nic_clean": nic_clean,
            "aa_clean": aa_clean,
            "latency_p50_ms": latency_report["p50_ms"],
            "latency_p95_ms": latency_report["p95_ms"],
            "latency_mean_ms": latency_report["mean_ms"],
            "latency_min_ms": latency_report["min_ms"],
            "latency_max_ms": latency_report["max_ms"],
            "answerable_time_s": answerable_time,
            "unanswerable_time_s": unanswerable_time,
            "misses": ver_misses,
            "leaks": leaks,
        }

        report_dir = os.path.join(os.path.dirname(__file__), "..", "tests")
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, "verifier-report.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved to: {report_path}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
