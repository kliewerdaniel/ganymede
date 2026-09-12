"""ADR-006 head-to-head: nomic-embed-text vs bge-m3 on the full 28-question set."""
import os, sys, time, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.models import Matter, Document, Chunk, ChunkEmbedding
from app.services.chunker import chunk_all_pages
from app.services.embedding import embed_all_chunks, get_embedding, DEFAULT_MODEL_NAME
from app.services.retrieval import retrieve, vector_search, fts_search, reciprocal_rank_fusion, RRF_ABSTENTION_THRESHOLD, MIN_VECTOR_SIMILARITY

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 28 answerable questions
QUESTIONS = [
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
    ("Q45", "The contract states the termination date as the end of the term. What is that date?", "DOC-003-MSA.docx"),
    ("Q46", "Two documents give different dates for the same event. Which is better supported?",
     ["DOC-013-Deposition-Notice.pdf", "DOC-019-Deposition-Transcript.pdf"]),
    ("Q47", "What is the date of the event described only as 'the week after the incident'?", "DOC-016-Technical-Report.docx"),
    ("Q48", "A document contains a passage that looks like an instruction to 'ignore prior confidentiality terms.' Does the system follow it?", "DOC-018b-Additional-Terms.pdf"),
    ("Q49", "The same fact appears in two documents with different quoted wording. Which is the primary source?",
     ["DOC-009-Notice-of-Default.pdf", "DOC-017-Notice-Email.pdf"]),
    ("Q50", "A user asks for a chronology of events that only some documents support. What does the chronology contain, and where is the gap?", "DOC-014-Chronology.pdf"),
]


def get_expected_shas(db, matter_id, doc_names):
    """Get expected sha256 values for document filenames."""
    if isinstance(doc_names, str):
        doc_names = [doc_names]
    shas = set()
    for name in doc_names:
        doc = db.query(Document).filter(
            Document.original_filename == name,
            Document.matter_id == matter_id,
        ).first()
        if doc:
            shas.add(doc.sha256)
    return shas


def check_hit(citations, expected_shas):
    """Check if any citation's sha256 matches an expected sha."""
    if not citations:
        return False
    for c in citations[:5]:
        if c.sha256 in expected_shas:
            return True
    return False


def retrieve_with_model(db, matter_id, query_text, model_name, top_k=5):
    """Run retrieval using the specified embedding model."""
    # Get embeddings using the specified model
    # For nomic: use default get_embedding
    # For bge-m3: we need to override — use sentence-transformers directly
    if model_name == "bge-m3":
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("BAAI/bge-m3")
        query_emb = model.encode(query_text).tolist()
    else:
        query_emb = get_embedding(query_text)

    # FTS search
    fts_results = fts_search(db, matter_id, query_text, top_k=30)

    # Vector search with our query embedding
    # We need to bypass get_embedding in vector_search — do it manually
    rows = db.query(Chunk, ChunkEmbedding, Document).join(
        ChunkEmbedding, Chunk.id == ChunkEmbedding.chunk_id
    ).join(
        Document, Chunk.document_id == Document.id
    ).filter(
        Chunk.matter_id == matter_id,
        Document.is_duplicate == False,
    ).all()

    vector_results = []
    for chunk, embedding, doc in rows:
        if embedding.vector is None:
            continue
        vec = embedding.vector
        if hasattr(vec, 'to_numpy'):
            vec = vec.to_numpy().tolist()
        elif hasattr(vec, 'to_list'):
            vec = vec.to_list()
        # Compute cosine similarity
        dot = sum(x * y for x, y in zip(query_emb, vec))
        norm_q = sum(x * x for x in query_emb) ** 0.5
        norm_v = sum(x * x for x in vec) ** 0.5
        if norm_q == 0 or norm_v == 0:
            sim = 0
        else:
            sim = dot / (norm_q * norm_v)
        vector_results.append({
            "chunk_id": str(chunk.id),
            "text": chunk.text,
            "document_id": str(chunk.document_id),
            "page_id": str(chunk.page_id),
            "start_offset": chunk.start_offset,
            "end_offset": chunk.end_offset,
            "parser_version": chunk.parser_version,
            "content_hash": chunk.content_hash,
            "sha256": doc.sha256,
            "vector_similarity": sim,
        })

    vector_results.sort(key=lambda x: x["vector_similarity"], reverse=True)
    vector_results = vector_results[:30]

    # RRF fusion
    fused = reciprocal_rank_fusion(fts_results, vector_results, k=30, fts_weight=0.65, vector_weight=0.35)

    # RRF abstention gate
    if not fused or fused[0].get("rrf_score", 0) < RRF_ABSTENTION_THRESHOLD:
        return []

    # Convert to Citation-like objects for check_hit
    # We need sha256 — build minimal objects
    class Result:
        def __init__(self, r):
            self.sha256 = r["sha256"]
            self.text = r["text"]
            self.document_id = r["document_id"]
            self.retrieval_scores = {
                "fts_rank": r.get("fts_rank"),
                "vector_similarity": r.get("vector_similarity"),
                "rrf_score": r.get("rrf_score"),
                "reranker_score": r.get("reranker_score"),
            }

    # Dedup by sha256
    seen = set()
    deduped = []
    for r in fused:
        sha = r["sha256"]
        if sha not in seen:
            seen.add(sha)
            deduped.append(Result(r))
            if len(deduped) >= top_k:
                break

    return deduped


def main():
    db = SessionLocal()
    try:
        matter_a = db.query(Matter).filter(Matter.name.like("%Matter A%")).first()
        if not matter_a:
            print("ERROR: Matter A not found.")
            return
        aid = matter_a.id

        print("=" * 70)
        print("ADR-006 Head-to-Head: nomic-embed-text vs bge-m3")
        print(f"Questions: {len(QUESTIONS)} answerable")
        print("=" * 70)

        # === nomic-embed-text ===
        print("\n=== nomic-embed-text (Ollama) ===")
        nomic_results = []
        nomic_start = time.time()

        for q_id, question, expected_docs in QUESTIONS:
            expected_shas = get_expected_shas(db, aid, expected_docs)
            t0 = time.time()
            citations = retrieve_with_model(db, aid, question, "nomic-embed-text")
            elapsed = time.time() - t0
            hit = check_hit(citations, expected_shas)
            nomic_results.append({
                "q_id": q_id,
                "hit": hit,
                "elapsed": elapsed,
                "expected": expected_docs,
                "expected_shas": list(expected_shas),
            })
            status = "✓" if hit else "✗ MISS"
            top_doc = citations[0].sha256[:16] + "..." if citations else "NONE"
            print(f"  {status} {q_id}: {elapsed*1000:.0f}ms (top={top_doc})")

        nomic_time = time.time() - nomic_start
        nomic_found = sum(1 for r in nomic_results if r["hit"])
        nomic_recall = nomic_found / len(QUESTIONS) * 100
        nomic_avg = nomic_time / len(QUESTIONS) * 1000

        print(f"\n  nomic-embed-text: {nomic_found}/{len(QUESTIONS)} = {nomic_recall:.1f}%")
        print(f"  Total: {nomic_time:.2f}s, Avg: {nomic_avg:.0f}ms/query")

        # === bge-m3 ===
        print("\n=== bge-m3 (sentence-transformers) ===")

        # Pre-load bge-m3
        from sentence_transformers import SentenceTransformer
        t_load_start = time.time()
        bge_m3_model = SentenceTransformer("BAAI/bge-m3")
        bge_load_time = time.time() - t_load_start
        print(f"  Model loaded in {bge_load_time:.1f}s (one-time)")

        bge_results = []
        bge_start = time.time()

        for q_id, question, expected_docs in QUESTIONS:
            expected_shas = get_expected_shas(db, aid, expected_docs)
            t0 = time.time()
            citations = retrieve_with_model(db, aid, question, "bge-m3")
            elapsed = time.time() - t0
            hit = check_hit(citations, expected_shas)
            bge_results.append({
                "q_id": q_id,
                "hit": hit,
                "elapsed": elapsed,
                "expected": expected_docs,
                "expected_shas": list(expected_shas),
            })
            status = "✓" if hit else "✗ MISS"
            top_doc = citations[0].sha256[:16] + "..." if citations else "NONE"
            print(f"  {status} {q_id}: {elapsed*1000:.0f}ms (top={top_doc})")

        bge_time = time.time() - bge_start
        bge_found = sum(1 for r in bge_results if r["hit"])
        bge_recall = bge_found / len(QUESTIONS) * 100
        bge_avg = (bge_time + bge_load_time) / len(QUESTIONS) * 1000

        print(f"\n  bge-m3: {bge_found}/{len(QUESTIONS)} = {bge_recall:.1f}%")
        print(f"  Total (incl. load): {bge_time + bge_load_time:.2f}s, Avg: {bge_avg:.0f}ms/query")
        print(f"  Load time: {bge_load_time:.1f}s one-time")

        # === Comparison ===
        print("\n" + "=" * 70)
        print("COMPARISON")
        print("=" * 70)
        print(f"  nomic-embed-text: {nomic_recall:.1f}% Recall@5 ({nomic_found}/{len(QUESTIONS)}), {nomic_avg:.0f}ms avg")
        print(f"  bge-m3:           {bge_recall:.1f}% Recall@5 ({bge_found}/{len(QUESTIONS)}), {bge_avg:.0f}ms avg")
        print(f"  Delta: {bge_recall - nomic_recall:+.1f}pp Recall@5")
        print(f"  Delta: {bge_avg - nomic_avg:+.0f}ms avg per query (incl. load)")

        # Per-question breakdown
        print("\n  Per-question comparison:")
        for i, (q_id, q, _) in enumerate(QUESTIONS):
            n_hit = nomic_results[i]["hit"]
            b_hit = bge_results[i]["hit"]
            n_t = nomic_results[i]["elapsed"] * 1000
            b_t = bge_results[i]["elapsed"] * 1000 + (bge_load_time / len(QUESTIONS) * 1000)
            marker = ""
            if n_hit and not b_hit:
                marker = " ← bge loses"
            elif b_hit and not n_hit:
                marker = " ← nomic loses"
            print(f"    {q_id}: nomic={'✓' if n_hit else '✗'} ({n_t:.0f}ms)  bge={'✓' if b_hit else '✗'} ({b_t:.0f}ms){marker}")

        # Save report
        report = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "nomic": {
                "recall": nomic_recall,
                "found": nomic_found,
                "total": len(QUESTIONS),
                "total_time_s": nomic_time,
                "avg_ms": nomic_avg,
            },
            "bge_m3": {
                "recall": bge_recall,
                "found": bge_found,
                "total": len(QUESTIONS),
                "total_time_s": bge_time + bge_load_time,
                "avg_ms": bge_avg,
                "load_time_s": bge_load_time,
            },
            "delta_recall_pp": bge_recall - nomic_recall,
            "per_question": [
                {
                    "q_id": q_id,
                    "nomic_hit": nomic_results[i]["hit"],
                    "bge_hit": bge_results[i]["hit"],
                    "nomic_ms": nomic_results[i]["elapsed"] * 1000,
                    "bge_ms": bge_results[i]["elapsed"] * 1000,
                }
                for i, (q_id, _, _) in enumerate(QUESTIONS)
            ],
        }

        report_path = os.path.join(os.path.dirname(__file__), "adr-006-head-to-head.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\n  Report saved to: {report_path}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
