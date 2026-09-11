# Ganymede API — Chunker Service

"""Split pages into overlapping chunks with provenance."""

import hashlib
from dataclasses import dataclass
from typing import List
from sqlalchemy.orm import Session
from app.models import Page, Chunk

# Larger chunks capture more context for better embedding discrimination
CHUNK_SIZE = 2048
CHUNK_OVERLAP = 512


@dataclass
class ChunkResult:
    """A chunk with provenance."""
    page_id: str
    document_id: str
    matter_id: str
    chunk_index: int
    text: str
    start_offset: int
    end_offset: int
    content_hash: str
    parser_version: str


def compute_content_hash(text: str) -> str:
    """Compute SHA-256 hash of chunk text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def chunk_page(db: Session, page: Page) -> List[Chunk]:
    """Split a page into overlapping chunks. Only creates chunks that don't already exist."""
    chunks = []
    text = page.text
    text_len = len(text)

    if text_len == 0:
        return chunks

    # Get existing chunk indices for this page
    existing_indices = set(
        r[0] for r in db.query(Chunk.chunk_index).filter(Chunk.page_id == page.id).all()
    )

    chunk_index = 0
    start = 0

    while start < text_len:
        end = min(start + CHUNK_SIZE, text_len)
        chunk_text = text[start:end]
        content_hash = compute_content_hash(chunk_text)

        # Check if this chunk already exists (by content hash)
        existing = db.query(Chunk).filter(
            Chunk.page_id == page.id,
            Chunk.content_hash == content_hash,
        ).first()

        if not existing and chunk_index not in existing_indices:
            chunk = Chunk(
                page_id=page.id,
                document_id=page.document_id,
                matter_id=page.document.matter_id,
                chunk_index=chunk_index,
                text=chunk_text,
                start_offset=start,
                end_offset=end,
                content_hash=content_hash,
                parser_version=page.parser_version,
            )
            db.add(chunk)
            chunks.append(chunk)

        chunk_index += 1
        start += CHUNK_SIZE - CHUNK_OVERLAP

        # Prevent infinite loop on tiny pages
        if CHUNK_SIZE - CHUNK_OVERLAP <= 0:
            break

    return chunks


def chunk_all_pages(db: Session, matter_id: str = None) -> int:
    """Chunk all pages. Returns total chunks created."""
    query = db.query(Page).join(Page.document)
    if matter_id:
        query = query.filter(Page.document.has(matter_id=matter_id))

    pages = query.all()
    total_chunks = 0

    for page in pages:
        chunks = chunk_page(db, page)
        total_chunks += len(chunks)

    db.commit()
    return total_chunks
