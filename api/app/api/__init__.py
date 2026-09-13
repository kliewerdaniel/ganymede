# Ganymede API — API Routes

"""FastAPI route handlers."""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.cors import setup_cors
from app.schemas import (
    MatterCreate, MatterResponse,
    UserCreate, UserResponse,
    DocumentResponse, PageResponse, IngestionStatusResponse,
    UploadResponse, QueryRequest, QueryResponse, CitationResponse,
)
from app.services.ingestion import ingest_document, get_ingestion_status
from app.services.antivirus import scan_file
from app.services.retrieval import retrieve
from app.services.query_expansion import expand_query
from app.services.verifier import verify_top_k, verify_top_k_fast_path
from app.models import Matter, User, Document, Page

router = APIRouter()


# --- Health Check ---

@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "ganymede-api", "version": "0.1.0"}


# --- Matter Routes ---

@router.post("/matters", response_model=MatterResponse, status_code=status.HTTP_201_CREATED)
def create_matter(matter: MatterCreate, db: Session = Depends(get_db)):
    """Create a new matter."""
    db_matter = Matter(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        name=matter.name,
        description=matter.description,
        cause_number=matter.cause_number,
        court=matter.court,
    )
    db.add(db_matter)
    db.commit()
    db.refresh(db_matter)
    return db_matter


@router.get("/matters", response_model=List[MatterResponse])
def list_matters(db: Session = Depends(get_db)):
    """List all matters."""
    return db.query(Matter).all()


@router.get("/matters/{matter_id}", response_model=MatterResponse)
def get_matter(matter_id: str, db: Session = Depends(get_db)):
    """Get a matter by ID."""
    matter = db.query(Matter).filter(Matter.id == matter_id).first()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
    return matter


# --- User Routes ---

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user."""
    db_user = User(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        email=user.email,
        name=user.name,
        role=user.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/users", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db)):
    """List all users."""
    return db.query(User).all()


# --- Document Routes ---

@router.post("/matters/{matter_id}/documents", response_model=UploadResponse)
async def upload_document(
    matter_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload and ingest a document."""
    # Verify matter exists
    matter = db.query(Matter).filter(Matter.id == matter_id).first()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")

    # Read file bytes
    file_bytes = await file.read()

    # Ingest document
    doc = ingest_document(
        db=db,
        matter_id=matter_id,
        filename=file.filename,
        file_bytes=file_bytes,
        mime_type=file.content_type or "application/octet-stream",
    )

    return UploadResponse(
        document_id=doc.id,
        filename=doc.original_filename,
        sha256=doc.sha256,
        ingestion_status=doc.ingestion_status,
        is_duplicate=doc.is_duplicate,
        duplicate_of_id=doc.duplicate_of_id,
    )


@router.get("/matters/{matter_id}/documents", response_model=List[DocumentResponse])
def list_documents(matter_id: str, db: Session = Depends(get_db)):
    """List all documents in a matter."""
    matter = db.query(Matter).filter(Matter.id == matter_id).first()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
    return db.query(Document).filter(Document.matter_id == matter_id, Document.is_duplicate == False).all()


@router.get("/documents/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str, db: Session = Depends(get_db)):
    """Get a document by ID."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.get("/documents/{document_id}/pages", response_model=List[PageResponse])
def get_document_pages(document_id: str, db: Session = Depends(get_db)):
    """Get all pages for a document."""
    pages = db.query(Page).filter(Page.document_id == document_id).order_by(Page.page_number).all()
    return pages


@router.get("/documents/{document_id}/status", response_model=IngestionStatusResponse)
def get_document_status(document_id: str, db: Session = Depends(get_db)):
    """Get ingestion status for a document."""
    doc = get_ingestion_status(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return IngestionStatusResponse(
        document_id=doc.id,
        status=doc.ingestion_status,
        stage=None,
        error_message=doc.ingestion_error,
        page_count=doc.page_count,
        parser_version=doc.parser_version,
    )


# --- Retrieval Routes ---

@router.post("/matters/{matter_id}/query", response_model=QueryResponse)
def query_matter(
    matter_id: str,
    request: QueryRequest,
    db: Session = Depends(get_db),
):
    """
    Query a matter's documents.
    Returns ranked citations (evidence before prose).
    """
    # Verify matter exists
    matter = db.query(Matter).filter(Matter.id == matter_id).first()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")

    # Retrieve citations
    citations = retrieve(
        db=db,
        matter_id=matter_id,
        query_text=request.query_text,
        top_k=request.top_k or 10,
    )

    return QueryResponse(
        matter_id=matter_id,
        query_text=request.query_text,
        citations=[
            CitationResponse(
                document_id=c.document_id,
                sha256=c.sha256,
                page=c.page,
                start_offset=c.start_offset,
                end_offset=c.end_offset,
                quoted_text=c.quoted_text,
                parser_version=c.parser_version,
                retrieval_scores=c.retrieval_scores,
                access_scope=c.access_scope,
                model_version=c.model_version,
            )
            for c in citations
        ],
        result_count=len(citations),
    )


# --- Async Q&A Routes ---

@router.post("/matters/{matter_id}/ask-async")
def ask_matter_async(
    matter_id: str,
    request: QueryRequest,
    db: Session = Depends(get_db),
):
    """
    Submit a question for async processing.
    Returns immediately with query_id. Poll /ask/{query_id}/status for results.
    """
    from app.services.async_verification import submit_query
    from app.core.database import SessionLocal

    matter = db.query(Matter).filter(Matter.id == matter_id).first()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")

    query_id = submit_query(
        matter_id=matter_id,
        question=request.query_text,
        db_session_factory=SessionLocal,
        top_k=request.top_k or 5,
    )

    return {"query_id": query_id, "status": "pending"}


@router.get("/ask/{query_id}/status")
def get_query_status(query_id: str):
    """Get the status of an async query."""
    from app.services.async_verification import get_query_status

    status = get_query_status(query_id)
    if not status:
        raise HTTPException(status_code=404, detail="Query not found")

    return status


# --- Citation Feedback ---

@router.post("/citations/{citation_id}/feedback")
def submit_citation_feedback(
    citation_id: str,
    feedback: str,  # supporting, weak, wrong, inaccessible
    db: Session = Depends(get_db),
):
    """Submit feedback on a citation."""
    # In production, store in audit log
    return {"status": "received", "citation_id": citation_id, "feedback": feedback}


# --- Verified Q&A Route ---

@router.post("/matters/{matter_id}/ask")
def ask_matter(
    matter_id: str,
    request: QueryRequest,
    db: Session = Depends(get_db),
):
    """
    Ask a question and get a verified answer with citations.
    Uses query expansion + verifier for answer-absent precision.
    """
    # Verify matter exists
    matter = db.query(Matter).filter(Matter.id == matter_id).first()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")

    # Apply query expansion
    expanded_query = expand_query(request.query_text)

    # Retrieve raw citations
    raw_citations = retrieve(
        db=db,
        matter_id=matter_id,
        query_text=expanded_query,
        top_k=request.top_k or 5,
    )

    # Apply verifier
    if len(raw_citations) > 0:
        verified_citations = verify_top_k(
            request.query_text,  # Use original question for verification
            raw_citations,
            top_k_verify=len(raw_citations),
        )
    else:
        verified_citations = []

    # Build answer text
    if len(verified_citations) == 0:
        answer_text = "Not found in the approved matter sources."
    else:
        answer_text = f"Found {len(verified_citations)} relevant passage(s) in the matter documents."

    return {
        "matter_id": matter_id,
        "query_text": request.query_text,
        "expanded_query": expanded_query,
        "answer": answer_text,
        "citations": [
            {
                "document_id": str(c.document_id),
                "sha256": c.sha256,
                "page": c.page,
                "start_offset": c.start_offset,
                "end_offset": c.end_offset,
                "quoted_text": c.quoted_text,
                "parser_version": c.parser_version,
                "retrieval_scores": c.retrieval_scores,
                "access_scope": c.access_scope,
                "model_version": c.model_version,
            }
            for c in verified_citations
        ],
        "result_count": len(verified_citations),
        "raw_count": len(raw_citations),
    }
