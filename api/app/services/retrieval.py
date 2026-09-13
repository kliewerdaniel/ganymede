# Ganymede API — Retrieval Service

"""Hybrid retrieval: FTS + vector fusion with reranking."""

import logging
import math
import os
import re
from dataclasses import dataclass
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from app.models import Chunk, ChunkEmbedding, Document, Matter
from app.services.embedding import get_embedding, DEFAULT_MODEL_NAME

logger = logging.getLogger(__name__)

# Minimum similarity threshold for returning results
MIN_VECTOR_SIMILARITY = 0.55

# RRF abstention gate: if the top fused result's RRF score is below this,
# no document is a strong enough match — return nothing.
RRF_ABSTENTION_THRESHOLD = 0.003

# ReRanker: try local cross-encoder if available.
# Set via RECRANKER_MODEL_PATH env var; defaults to locally-cached
# cross-encoder/ms-marco-MiniLM-L-6-v2 (sentence-transformers).
# If unset or load fails, falls back to RRF score ordering.
_DEFAULT_RERANKER_PATH = os.path.expanduser(
    "~/.cache/huggingface/hub/models--cross-encoder--ms-marco-MiniLM-L-6-v2/"
    "snapshots/233902d25c440f23af6f7d6e94d2946bac0bee0a"
)
RECRANKER_MODEL_PATH = os.environ.get("RECRANKER_MODEL_PATH", _DEFAULT_RERANKER_PATH)


@dataclass
class Citation:
    """A citation object — the frozen schema for retrieval results."""
    matter_id: str
    document_id: str
    sha256: str
    page: int
    start_offset: int
    end_offset: int
    quoted_text: str
    parser_version: str
    retrieval_scores: dict
    access_scope: str
    model_version: str


def _ensure_fts_index(db: Session):
    """Create FTS index if it doesn't exist."""
    db.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_chunks_fts ON chunks
        USING gin(to_tsvector('english', text))
    """))
    db.commit()


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0
    return dot / (norm_a * norm_b)


def _build_or_tsquery(query_text: str) -> str:
    """Build an OR-based tsquery from query text."""
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                  'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                  'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                  'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in',
                  'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into',
                  'through', 'during', 'before', 'after', 'above', 'below',
                  'between', 'under', 'again', 'further', 'then', 'once',
                  'here', 'there', 'when', 'where', 'why', 'how', 'all',
                  'each', 'few', 'more', 'most', 'other', 'some', 'such',
                  'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than',
                  'too', 'very', 'just', 'because', 'but', 'and', 'or',
                  'if', 'while', 'what', 'which', 'who', 'whom', 'this',
                  'that', 'these', 'those', 'am', 'it', 'its', 'i', 'my',
                  'me', 'we', 'our', 'you', 'your', 'he', 'she', 'him',
                  'his', 'her', 'they', 'them', 'their', 'what', 'which'}
    
    words = re.findall(r'[a-zA-Z]+', query_text.lower())
    terms = [w for w in words if w not in stop_words and len(w) > 2]
    
    if not terms:
        terms = [w for w in words if len(w) > 1]
    
    return ' | '.join(terms)


def fts_search(db: Session, matter_id: str, query_text: str, top_k: int = 20) -> List[dict]:
    """Full-text search over chunks in a matter."""
    _ensure_fts_index(db)
    
    tsquery = _build_or_tsquery(query_text)
    
    if not tsquery:
        return []

    sql = text("""
        SELECT DISTINCT ON (d.sha256) 
               c.id, c.text, c.document_id, c.page_id, c.start_offset, c.end_offset,
               c.parser_version, c.content_hash, d.sha256,
               ts_rank(to_tsvector('english', c.text), to_tsquery('english', :query)) AS rank
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE c.matter_id = :matter_id
          AND to_tsvector('english', c.text) @@ to_tsquery('english', :query)
          AND d.is_duplicate = false
        ORDER BY d.sha256, rank DESC
        LIMIT :top_k
    """)

    results = db.execute(sql, {
        "matter_id": matter_id,
        "query": tsquery,
        "top_k": top_k,
    }).fetchall()

    # Re-rank after dedup
    results = sorted(results, key=lambda r: float(r[9]), reverse=True)

    return [
        {
            "chunk_id": str(r[0]),
            "text": r[1],
            "document_id": str(r[2]),
            "page_id": str(r[3]),
            "start_offset": r[4],
            "end_offset": r[5],
            "parser_version": r[6],
            "content_hash": r[7],
            "sha256": r[8],
            "fts_rank": float(r[9]),
        }
        for r in results
    ]


def vector_search(db: Session, matter_id: str, query_text: str, top_k: int = 20) -> List[dict]:
    """Vector similarity search over chunks in a matter (computed in Python)."""
    query_embedding = get_embedding(query_text)

    rows = db.query(Chunk, ChunkEmbedding, Document).join(
        ChunkEmbedding, Chunk.id == ChunkEmbedding.chunk_id
    ).join(
        Document, Chunk.document_id == Document.id
    ).filter(
        Chunk.matter_id == matter_id,
        Document.is_duplicate == False,
    ).all()

    if not rows:
        return []

    results = []
    for chunk, embedding, doc in rows:
        if embedding.vector is None:
            continue
        vec = embedding.vector
        if hasattr(vec, 'to_numpy'):
            vec = vec.to_numpy().tolist()
        elif hasattr(vec, 'to_list'):
            vec = vec.to_list()
        similarity = cosine_similarity(query_embedding, vec)
        results.append({
            "chunk_id": str(chunk.id),
            "text": chunk.text,
            "document_id": str(chunk.document_id),
            "page_id": str(chunk.page_id),
            "start_offset": chunk.start_offset,
            "end_offset": chunk.end_offset,
            "parser_version": chunk.parser_version,
            "content_hash": chunk.content_hash,
            "sha256": doc.sha256,
            "vector_similarity": similarity,
        })

    results.sort(key=lambda x: x["vector_similarity"], reverse=True)
    return results[:top_k]


def reciprocal_rank_fusion(
    fts_results: List[dict],
    vector_results: List[dict],
    k: int = 30,
    fts_weight: float = 0.65,
    vector_weight: float = 0.35,
) -> List[dict]:
    """Fuse FTS and vector results using Reciprocal Rank Fusion."""
    scores = {}

    for rank, r in enumerate(fts_results):
        chunk_id = r["chunk_id"]
        scores[chunk_id] = scores.get(chunk_id, 0) + fts_weight / (k + rank + 1)

    for rank, r in enumerate(vector_results):
        chunk_id = r["chunk_id"]
        scores[chunk_id] = scores.get(chunk_id, 0) + vector_weight / (k + rank + 1)

    all_results = {r["chunk_id"]: r for r in fts_results + vector_results}

    fused = []
    for chunk_id, rrf_score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        if chunk_id in all_results:
            r = all_results[chunk_id].copy()
            r["rrf_score"] = rrf_score
            fused.append(r)

    return fused


def rerank(
    db: Session,
    query_text: str,
    fused_results: List[dict],
    top_k: int = 10,
) -> List[dict]:
    """Rerank fused results. Uses local cross-encoder if RECRANKER_MODEL_PATH is set,
    otherwise falls back to RRF score ordering. Applies RRF abstention gate:
    if the top result's RRF score is below RRF_ABSTENTION_THRESHOLD, returns empty."""
    if not fused_results:
        return []

    # Apply RRF abstention gate
    if fused_results[0].get("rrf_score", 0) < RRF_ABSTENTION_THRESHOLD:
        return []

    if RECRANKER_MODEL_PATH:
        try:
            import numpy as np
            model = _load_reranker()
            reranked = _rerank_with_model(model, query_text, fused_results)
            reranked.sort(key=lambda x: x.get("reranker_score", 0), reverse=True)
            for r in reranked:
                r["rrf_score"] = r.get("rrf_score", 0)  # preserve RRF score in output
            return reranked[:top_k]
        except Exception as e:
            logger.warning(f"Cross-encoder reranking failed, falling back to RRF: {e}")

    # Fallback: RRF score ordering
    fused_results.sort(key=lambda x: x.get("rrf_score", 0), reverse=True)
    return fused_results[:top_k]


def _load_reranker():
    """Load a local cross-encoder model. Must be set via RECRANKER_MODEL_PATH."""
    import sentence_transformers
    if not RECRANKER_MODEL_PATH:
        raise RuntimeError("RECRANKER_MODEL_PATH is not set — cannot load cross-encoder")
    return sentence_transformers.CrossEncoder(RECRANKER_MODEL_PATH)


def _rerank_with_model(model, query: str, results: List[dict]) -> List[dict]:
    """Score each result with the cross-encoder and attach reranker_score."""
    pairs = [(query, r["text"]) for r in results]
    scores = model.predict(pairs)
    for r, s in zip(results, scores):
        r["reranker_score"] = float(s)
    return results


def deduplicate_by_sha256(results: List[dict], top_k: int = 5) -> List[dict]:
    """Deduplicate results by sha256."""
    seen_sha = set()
    deduped = []
    for r in results:
        sha = r["sha256"]
        if sha not in seen_sha:
            seen_sha.add(sha)
            deduped.append(r)
            if len(deduped) >= top_k:
                break
    return deduped


def retrieve(
    db: Session,
    matter_id: str,
    query_text: str,
    top_k: int = 10,
    use_expansion: bool = True,
) -> List[Citation]:
    """Main retrieval function.

    Args:
        db: database session
        matter_id: matter to search
        query_text: the user's question
        top_k: number of results to return
        use_expansion: whether to apply query expansion (default: True)
    """
    # Apply query expansion
    if use_expansion:
        from app.services.query_expansion import expand_query
        expanded_text = expand_query(query_text)
    else:
        expanded_text = query_text

    fts_results = fts_search(db, matter_id, expanded_text, top_k=30)
    vector_results = vector_search(db, matter_id, expanded_text, top_k=30)

    best_vector_sim = vector_results[0]["vector_similarity"] if vector_results else 0
    if not fts_results and best_vector_sim < MIN_VECTOR_SIMILARITY:
        return []

    fused = reciprocal_rank_fusion(fts_results, vector_results)
    if not fused or fused[0].get("rrf_score", 0) < RRF_ABSTENTION_THRESHOLD:
        return []

    ranked = rerank(db, query_text, fused, top_k=top_k * 4)

    deduped = deduplicate_by_sha256(ranked, top_k=top_k)

    citations = []
    for r in deduped:
        citation = Citation(
            matter_id=matter_id,
            document_id=r["document_id"],
            sha256=r["sha256"],
            page=1,
            start_offset=r["start_offset"],
            end_offset=r["end_offset"],
            quoted_text=r["text"],
            parser_version=r["parser_version"],
            retrieval_scores={
                "fts_rank": r.get("fts_rank"),
                "vector_similarity": r.get("vector_similarity"),
                "rrf_score": r.get("rrf_score"),
                "reranker_score": r.get("reranker_score"),
            },
            access_scope="matter",
            model_version=DEFAULT_MODEL_NAME,
        )
        citations.append(citation)

    return citations
