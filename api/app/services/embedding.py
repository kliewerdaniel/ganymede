# Ganymede API — Embedding Service

"""Generate and cache embeddings using a local model."""

import hashlib
import logging
import os
from typing import List
from sqlalchemy.orm import Session
from app.models import Chunk, ChunkEmbedding

logger = logging.getLogger(__name__)

# Model configuration
DEFAULT_MODEL_NAME = "nomic-embed-text"
DEFAULT_MODEL_VERSION = "latest"
EMBEDDING_DIMENSION = 768

# Ollama endpoints to try (in order)
# localhost works on host, host.docker.internal works inside Docker container
OLLAMA_ENDPOINTS = [
    "http://localhost:11434",
    "http://host.docker.internal:11434",
]


def get_embedding(text: str, model_name: str = DEFAULT_MODEL_NAME) -> List[float]:
    """
    Generate an embedding for the given text.
    Uses Ollama's embedding API (local, no external calls).
    Falls back to random embeddings if Ollama is not available.
    """
    for endpoint in OLLAMA_ENDPOINTS:
        try:
            import requests
            response = requests.post(
                f"{endpoint}/api/embeddings",
                json={"model": model_name, "prompt": text},
                timeout=10,
            )
            if response.status_code == 200:
                return response.json()["embedding"]
        except Exception as e:
            logger.debug(f"Ollama endpoint {endpoint} failed: {e}")
            continue

    logger.warning(f"Ollama not available, using random embedding fallback")
    # Fallback: deterministic random embedding based on content hash
    h = hashlib.sha256(text.encode()).hexdigest()
    import random
    rng = random.Random(h)
    return [rng.uniform(-1, 1) for _ in range(EMBEDDING_DIMENSION)]


def embed_chunk(db: Session, chunk: Chunk, model_name: str = DEFAULT_MODEL_NAME) -> ChunkEmbedding:
    """Embed a chunk. Always generates a fresh embedding."""
    vector = get_embedding(chunk.text, model_name)

    embedding = ChunkEmbedding(
        chunk_id=chunk.id,
        vector=vector,  # Store as plain list (double precision[])
        model_name=model_name,
        model_version=DEFAULT_MODEL_VERSION,
        content_hash=chunk.content_hash,
    )
    db.add(embedding)
    return embedding


def embed_all_chunks(db: Session, matter_id: str = None, model_name: str = DEFAULT_MODEL_NAME) -> int:
    """Embed all chunks that don't have embeddings. Returns total embeddings created."""
    query = db.query(Chunk).outerjoin(ChunkEmbedding).filter(ChunkEmbedding.id == None)
    if matter_id:
        query = query.filter(Chunk.matter_id == matter_id)

    chunks = query.all()
    total = 0

    for chunk in chunks:
        embed_chunk(db, chunk, model_name)
        total += 1

    db.commit()
    return total
