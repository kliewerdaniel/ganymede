#!/usr/bin/env python3
"""Threshold sweep for cross-encoder verifier on gold set.

Phase 1: Collect cross-encoder scores for every (question, citation) pair.
Phase 2: Sweep thresholds 0.0–1.0, compute recall and answer-absent.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.services.retrieval import retrieve
from app.services.query_expansion import expand_query
from app.services.verifier import verify_answer, VERIFIER_MODEL

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


def collect_scores():
    """Phase 1: collect cross-encoder scores for every question."""
    db = SessionLocal()
    data = {"verifier_model": VERIFIER_MODEL, "answerable": [], "answer_absent": []}

    print(f"=== Phase 1: Collecting scores ({VERIFIER_MODEL}) ===")
    for q_id, question in ANSWERABLE:
        expanded = expand_query(question)
        raw = retrieve(db, MATTER_ID, expanded, top_k=5)
        scores = []
        for cite in raw:
            result = verify_answer(question, cite.quoted_text)
            scores.append({"score": result["score"], "latency_ms": result["latency_ms"]})
        max_score = max(s["score"] for s in scores) if scores else 0
        data["answerable"].append({"q_id": q_id, "question": question, "scores": scores, "max_score": max_score})
        print(f"  A {q_id}: max={max_score:.4f} ({len(scores)} citations)", flush=True)

    for q_id, question in ANSWER_ABSENT:
        expanded = expand_query(question)
        raw = retrieve(db, MATTER_ID, expanded, top_k=5)
        scores = []
        for cite in raw:
            result = verify_answer(question, cite.quoted_text)
            scores.append({"score": result["score"], "latency_ms": result["latency_ms"]})
        max_score = max(s["score"] for s in scores) if scores else 0
        data["answer_absent"].append({"q_id": q_id, "question": question, "scores": scores, "max_score": max_score})
        print(f"  AA {q_id}: max={max_score:.4f} ({len(scores)} citations)", flush=True)

    db.close()

    output_path = os.path.join(os.path.dirname(__file__), "ce-scores.json")
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\nScores saved to {output_path}")
    return data


def sweep(data):
    """Phase 2: sweep thresholds and find best operating point."""
    answerable = data["answerable"]
    answer_absent = data["answer_absent"]

    results = []
    threshold = 0.0
    while threshold <= 1.0:
        found = sum(1 for q in answerable if q["max_score"] >= threshold)
        clean = sum(1 for q in answer_absent if q["max_score"] < threshold)
        results.append({
            "threshold": round(threshold, 4),
            "answerable_found": found,
            "answerable_total": len(answerable),
            "answerable_recall_pct": round(100 * found / len(answerable), 1),
            "answer_absent_clean": clean,
            "answer_absent_total": len(answer_absent),
            "answer_absent_pass_pct": round(100 * clean / len(answer_absent), 1),
        })
        threshold += 0.005

    # Find best: max recall with answer-absent >= 20/21
    best = None
    for r in results:
        if r["answer_absent_clean"] >= 20:
            if best is None or r["answerable_found"] > best["answerable_found"]:
                best = r

    print("\n=== Best threshold (answer-absent >= 20/21) ===")
    if best:
        print(f"  Threshold: {best['threshold']}")
        print(f"  Answerable: {best['answerable_found']}/{best['answerable_total']} ({best['answerable_recall_pct']}%)")
        print(f"  Answer-absent: {best['answer_absent_clean']}/{best['answer_absent_total']} ({best['answer_absent_pass_pct']}%)")
    else:
        print("  No threshold achieves >= 20/21 answer-absent clean")

    print("\n=== Top 10 by recall ===")
    sorted_r = sorted(results, key=lambda x: (-x["answerable_found"], x["threshold"]))
    for r in sorted_r[:10]:
        aa_flag = " <-- BEST" if r == best else ""
        print(f"  T={r['threshold']:.4f}: A={r['answerable_found']}/{r['answerable_total']} ({r['answerable_recall_pct']}%), AA={r['answer_absent_clean']}/{r['answer_absent_total']} ({r['answer_absent_pass_pct']}%) {aa_flag}")

    output_path = os.path.join(os.path.dirname(__file__), "threshold-sweep-results.json")
    with open(output_path, "w") as f:
        json.dump({"sweep": results, "best": best}, f, indent=2)
    print(f"\nFull sweep saved to {output_path}")
    return best


if __name__ == "__main__":
    # Collect scores (or reuse if exists)
    scores_path = os.path.join(os.path.dirname(__file__), "ce-scores.json")
    if os.path.exists(scores_path):
        print(f"Loading existing scores from {scores_path}")
        with open(scores_path) as f:
            data = json.load(f)
    else:
        data = collect_scores()

    sweep(data)
