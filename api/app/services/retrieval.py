# Ganymede API — Retrieval Service

"""Hybrid retrieval: FTS + vector fusion with reranking."""

import logging
import math
import re
from dataclasses import dataclass
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from app.models import Chunk, ChunkEmbedding, Document, Matter
from app.services.embedding import get_embedding, DEFAULT_MODEL_NAME

logger = logging.getLogger(__name__)

# Minimum similarity threshold for returning results
MIN_VECTOR_SIMILARITY = 0.5


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
    """Build an OR-based tsquery from query text.
    
    Extracts meaningful terms and joins them with OR for broader matching.
    """
    # Remove common stop words and extract terms
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
    
    # Extract words (alphanumeric)
    words = re.findall(r'[a-zA-Z]+', query_text.lower())
    # Filter out stop words and short words
    terms = [w for w in words if w not in stop_words and len(w) > 2]
    
    if not terms:
        # Fallback: use all words
        terms = [w for w in words if len(w) > 1]
    
    # Join with OR for broader matching
    return ' | '.join(terms)


def fts_search(db: Session, matter_id: str, query_text: str, top_k: int = 20) -> List[dict]:
    """Full-text search over chunks in a matter."""
    _ensure_fts_index(db)
    
    # Build OR-based tsquery for broader matching
    tsquery = _build_or_tsquery(query_text)
    
    if not tsquery:
        return []

    sql = text("""
        SELECT c.id, c.text, c.document_id, c.page_id, c.start_offset, c.end_offset,
               c.parser_version, c.content_hash, d.sha256,
               ts_rank(to_tsvector('english', c.text), to_tsquery('english', :query)) AS rank
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE c.matter_id = :matter_id
          AND to_tsvector('english', c.text) @@ to_tsquery('english', :query)
        ORDER BY rank DESC
        LIMIT :top_k
    """)

    results = db.execute(sql, {
        "matter_id": matter_id,
        "query": tsquery,
        "top_k": top_k,
    }).fetchall()

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
        Chunk.matter_id == matter_id
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
    k: int = 60,
    fts_weight: float = 0.6,
    vector_weight: float = 0.4,
) -> List[dict]:
    """Fuse FTS and vector results using Reciprocal Rank Fusion.
    
    FTS gets higher weight because exact term matches are stronger signals
    for this type of legal document retrieval.
    """
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
    """Rerank fused results. Falls back to RRF score."""
    if not fused_results:
        return []

    fused_results.sort(key=lambda x: x.get("rrf_score", 0), reverse=True)
    return fused_results[:top_k]


def deduplicate_by_document(results: List[dict], top_k: int = 5) -> List[dict]:
    """
    Deduplicate results by document.
    Returns top_k results from distinct documents.
    """
    seen_docs = set()
    deduped = []
    for r in results:
        doc_id = r["document_id"]
        if doc_id not in seen_docs:
            seen_docs.add(doc_id)
            deduped.append(r)
            if len(deduped) >= top_k:
                break
    return deduped


def retrieve(
    db: Session,
    matter_id: str,
    query_text: str,
    top_k: int = 10,
) -> List[Citation]:
    """
    Main retrieval function.
    FTS + vector fusion with reranking.
    Returns ranked citations with document-level deduplication.
    """
    fts_results = fts_search(db, matter_id, query_text, top_k=30)
    vector_results = vector_search(db, matter_id, query_text, top_k=30)

    # Check if we have any good matches
    best_vector_sim = vector_results[0]["vector_similarity"] if vector_results else 0
    if not fts_results and best_vector_sim < MIN_VECTOR_SIMILARITY:
        return []

    fused = reciprocal_rank_fusion(fts_results, vector_results)
    ranked = rerank(db, query_text, fused, top_k=top_k * 4)  # Get more results for dedup

    # Deduplicate by document to ensure diversity in top results
    deduped = deduplicate_by_document(ranked, top_k=top_k)

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
