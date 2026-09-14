#!/usr/bin/env python3
"""Discordance analysis: capture verifier decisions on failing gold-set cases.

Runs the verifier on each retrieved citation for the LEAK and MISS cases
from the qwen3:8b gold-set report. Captures question, passage excerpt,
verifier decision, and quote for each citation.
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
from app.services.verifier import verify_answer, VERIFIER_MODEL

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

MATTER_ID = "00000000-0000-0000-0000-000000000011"

# Cases that FAILED with qwen3:8b — from gold-set-report-qwen3-8b.json
LEAKS = [
    ("Q23", "Across the invoices and the purchase order, what is the total amount ordered?"),
    ("Q30", "Across the policy declarations and the claim form, who is the additional insured?"),
    ("Q35", "When did the parties first exchange position statements?"),
]

MISSES = [
    ("Q01", "What is the termination date stated in the master services agreement?"),
    ("Q04", "What amount does the complaint allege as damages?"),
    ("Q07", "What is the stated jurisdiction for dispute resolution in the agreement?"),
]

db = SessionLocal()
results = {"verifier_model": VERIFIER_MODEL, "leaks": [], "misses": []}

print(f"=== Discordance Analysis: {VERIFIER_MODEL} ===")
print(f"Testing {len(LEAKS)} LEAK cases + {len(MISSES)} MISS cases\n")

# LEAK cases: answer-absent questions that qwen3:8b incorrectly verified YES
print("--- LEAK CASES (answer-absent, should be NO) ---")
for q_id, question in LEAKS:
    print(f"\n{q_id}: {question}")
    case_result = {"q_id": q_id, "question": question, "citations": []}
    
    expanded = expand_query(question)
    raw = retrieve(db, MATTER_ID, expanded, top_k=5)
    
    for i, citation in enumerate(raw):
        t0 = time.time()
        result = verify_answer(question, citation.quoted_text)
        latency = (time.time() - t0) * 1000
        
        passage_preview = citation.quoted_text[:200].replace("\n", " ").strip()
        print(f"  [{i}] doc={citation.document_id[:8]}... page={citation.page} "
              f"decision={result['decision']} latency={latency:.0f}ms")
        print(f"      passage: {passage_preview}...")
        if result["quote"]:
            print(f"      quote: {result['quote'][:100]}...")
        
        case_result["citations"].append({
            "idx": i,
            "document_id": citation.document_id,
            "page": citation.page,
            "passage_preview": passage_preview,
            "decision": result["decision"],
            "quote": (result["quote"] or "")[:200],
            "latency_ms": round(latency, 1),
        })
    
    results["leaks"].append(case_result)

# MISS cases: answerable questions that qwen3:8b incorrectly verified NO
print("\n--- MISS CASES (answerable, should be YES) ---")
for q_id, question in MISSES:
    print(f"\n{q_id}: {question}")
    case_result = {"q_id": q_id, "question": question, "citations": []}
    
    expanded = expand_query(question)
    raw = retrieve(db, MATTER_ID, expanded, top_k=5)
    
    for i, citation in enumerate(raw):
        t0 = time.time()
        result = verify_answer(question, citation.quoted_text)
        latency = (time.time() - t0) * 1000
        
        passage_preview = citation.quoted_text[:200].replace("\n", " ").strip()
        print(f"  [{i}] doc={citation.document_id[:8]}... page={citation.page} "
              f"decision={result['decision']} latency={latency:.0f}ms")
        print(f"      passage: {passage_preview}...")
        if result["quote"]:
            print(f"      quote: {result['quote'][:100]}...")
        
        case_result["citations"].append({
            "idx": i,
            "document_id": citation.document_id,
            "page": citation.page,
            "passage_preview": passage_preview,
            "decision": result["decision"],
            "quote": (result["quote"] or "")[:200],
            "latency_ms": round(latency, 1),
        })
    
    results["misses"].append(case_result)

output_path = os.path.join(os.path.dirname(__file__), "discordance-report.json")
with open(output_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to {output_path}")

db.close()
