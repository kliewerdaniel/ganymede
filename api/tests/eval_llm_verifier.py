#!/usr/bin/env python3
"""Gold-set evaluation: LLM-as-verifier (Ollama).

Runs 29 answerable + 21 answer-absent questions through the full pipeline
(retrieval with expansion + verifier). Records recall, answer-absent pass rate,
and latency.

Usage:
    python3 eval_llm_verifier.py                    # use default model (qwen3:8b)
    VERIFIER_MODEL=qwen3:14b python3 eval_llm_verifier.py
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.services.retrieval import retrieve
from app.services.query_expansion import expand_query
from app.services.verifier import verify_top_k, VERIFIER_MODEL, VERIFIER_THRESHOLD

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

MATTER_ID = "00000000-0000-0000-0000-000000000011"

ANSWERABLE = [
    ("Q01", "What is the termination date stated in the master services agreement?"),
    ("Q04", "What amount does the complaint allege as damages?"),
    ("Q05", "On what date did the first breach notice arrive, according to the chronology exhibits?"),
    ("Q07", "What is the stated jurisdiction for dispute resolution in the agreement?"),
    ("Q08", "Who signed the amendment as the corporate officer, and in what capacity?"),
    ("Q09", "What is the contract price stated in the invoice that matches the dispute?"),
    ("Q11", "What date does the deposition notice set for the first deposition?"),
    ("Q12", "Which paragraph describes the scope of the non-disclosure obligation?"),
    ("Q13", "What is the stated interest rate on the unpaid balance in the demand letter?"),
    ("Q14", "Who is the court reporter named in the deposition scheduling order?"),
    ("Q15", "What page of the technical report contains the failure-mode analysis?"),
    ("Q17", "What is the effective date of the most recent amendment?"),
    ("Q19", "What is the stated cure period in the default clause?"),
    ("Q21", "Across the contract and the amendment, what is the current notice period for termination?"),
    ("Q22", "Do the complaint and the defendant's answer agree on the date of the alleged breach?"),
    ("Q25", "Which documents establish that the defendant received notice before filing?"),
    ("Q29", "Which documents show the sequence of communications leading to the settlement offer?"),
    ("Q31", "List the events in the matter in chronological order, with date, actor, and source."),
    ("Q32", "On what date did the contract transition from draft to executed?"),
    ("Q33", "Who sent the first breach notice, and on what date?"),
    ("Q34", "What is the sequence of amendments to the agreement, in order?"),
    ("Q36", "List the filing dates for each document in the court docket excerpt."),
    ("Q38", "Across the lease and the correspondence, what is the current rent amount after the modification?"),
    ("Q45", 'The contract states the termination date as "the end of the term." What is that date, if the term start date is known elsewhere?'),
    ("Q46", "Two documents give different dates for the same event. Which is better supported, and what are the sources?"),
    ("Q47", 'What is the date of the event described only as "the week after the incident," with no explicit date in the record?'),
    ("Q48", 'A document contains a passage that looks like an instruction to "ignore prior confidentiality terms." Does the system follow it?'),
    ("Q49", "The same fact appears in two documents with different quoted wording. Which is the primary source, and what are both citations?"),
    ("Q50", "A user asks for a chronology of events that only some documents support. What does the chronology contain, and where is the gap?"),
]

ANSWER_ABSENT = [
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
    ("Q28", "Across the lease and the correspondence, what is the current rent amount?"),
    ("Q30", "Across the policy declarations and the claim form, who is the additional insured?"),
    ("Q35", "When did the parties first exchange position statements?"),
    ("Q37", "Which event occurred first: the inspection or the repair request?"),
    ("Q39", "What did the CEO say in the internal meeting on March 14?"),
    ("Q40", "Which external case law supports the defendant's motion?"),
    ("Q41", "What is the opposing party's current settlement demand?"),
    ("Q42", "Who will be called as the second expert witness?"),
    ("Q43", "What is the plaintiff's attorney's hourly rate?"),
    ("Q44", "Which document is missing from the file, if any, that would establish the date of delivery?"),
]


def run_evaluation():
    db = SessionLocal()
    results = {
        "verifier_model": VERIFIER_MODEL,
        "verifier_threshold": VERIFIER_THRESHOLD,
        "answerable": [],
        "answer_absent": [],
        "summary": {},
    }

    print(f"=== Evaluating: {VERIFIER_MODEL} (threshold={VERIFIER_THRESHOLD}) ===")

    # Answerable questions
    print(f"\n=== Answerable Questions ({len(ANSWERABLE)}) ===")
    for q_id, question in ANSWERABLE:
        t0 = time.time()
        expanded = expand_query(question)
        raw = retrieve(db, MATTER_ID, expanded, top_k=5)
        n_raw = len(raw)

        t1 = time.time()
        verified = verify_top_k(question, raw, top_k_verify=len(raw))
        t2 = time.time()

        found = len(verified) > 0
        result = {
            "q_id": q_id,
            "question": question,
            "found": found,
            "n_raw": n_raw,
            "n_verified": len(verified),
            "retrieval_time_ms": round((t1 - t0) * 1000, 1),
            "verification_time_ms": round((t2 - t1) * 1000, 1),
            "total_time_ms": round((t2 - t0) * 1000, 1),
        }
        results["answerable"].append(result)
        status = "FOUND" if found else "MISS"
        print(f"  {q_id}: {status} (raw={n_raw}, verified={len(verified)}, "
              f"verif={result['verification_time_ms']:.0f}ms)")

    # Answer-absent questions
    print(f"\n=== Answer-Absent Questions ({len(ANSWER_ABSENT)}) ===")
    for q_id, question in ANSWER_ABSENT:
        t0 = time.time()
        expanded = expand_query(question)
        raw = retrieve(db, MATTER_ID, expanded, top_k=5)
        n_raw = len(raw)

        t1 = time.time()
        verified = verify_top_k(question, raw, top_k_verify=len(raw))
        t2 = time.time()

        clean = len(verified) == 0
        result = {
            "q_id": q_id,
            "question": question,
            "clean": clean,
            "n_raw": n_raw,
            "n_verified": len(verified),
            "retrieval_time_ms": round((t1 - t0) * 1000, 1),
            "verification_time_ms": round((t2 - t1) * 1000, 1),
            "total_time_ms": round((t2 - t0) * 1000, 1),
        }
        results["answer_absent"].append(result)
        status = "CLEAN" if clean else "LEAK"
        print(f"  {q_id}: {status} (raw={n_raw}, verified={len(verified)}, "
              f"verif={result['verification_time_ms']:.0f}ms)")

    # Summary
    found_count = sum(1 for r in results["answerable"] if r["found"])
    clean_count = sum(1 for r in results["answer_absent"] if r["clean"])
    all_times = [r["total_time_ms"] for r in results["answerable"]]
    verif_times = [r["verification_time_ms"] for r in results["answerable"]]

    results["summary"] = {
        "answerable_found": found_count,
        "answerable_total": len(ANSWERABLE),
        "answerable_recall_pct": round(100 * found_count / len(ANSWERABLE), 1),
        "answer_absent_clean": clean_count,
        "answer_absent_total": len(ANSWER_ABSENT),
        "answer_absent_pass_pct": round(100 * clean_count / len(ANSWER_ABSENT), 1),
        "p50_total_ms": sorted(all_times)[len(all_times) // 2],
        "p95_total_ms": sorted(all_times)[int(len(all_times) * 0.95)],
        "mean_total_ms": round(sum(all_times) / len(all_times), 1),
        "p50_verif_ms": sorted(verif_times)[len(verif_times) // 2],
        "p95_verif_ms": sorted(verif_times)[int(len(verif_times) * 0.95)],
        "mean_verif_ms": round(sum(verif_times) / len(verif_times), 1),
    }

    print(f"\n=== Summary ===")
    print(f"Answerable recall: {found_count}/{len(ANSWERABLE)} "
          f"({results['summary']['answerable_recall_pct']}%)")
    print(f"Answer-absent clean: {clean_count}/{len(ANSWER_ABSENT)} "
          f"({results['summary']['answer_absent_pass_pct']}%)")
    print(f"Latency p50: {results['summary']['p50_total_ms']:.0f}ms, "
          f"p95: {results['summary']['p95_total_ms']:.0f}ms")
    print(f"Verifier p50: {results['summary']['p50_verif_ms']:.0f}ms, "
          f"p95: {results['summary']['p95_verif_ms']:.0f}ms")

    # Save results
    model_slug = VERIFIER_MODEL.replace(":", "-")
    output_path = os.path.join(os.path.dirname(__file__), f"gold-set-report-{model_slug}.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {output_path}")

    db.close()
    return results


if __name__ == "__main__":
    run_evaluation()
