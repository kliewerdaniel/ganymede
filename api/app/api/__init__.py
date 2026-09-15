# Ganymede API — API Routes

"""FastAPI route handlers."""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import create_access_token, decode_access_token, hash_password, verify_password
from app.core.deps import get_current_user, get_current_active_user
from app.core.rbac import can_access_matter
from app.core.sanitizer import sanitize_query, detect_injection
from app.core.audit import log_action as log_audit, query_audit_log
from app.core.config import get_settings
from app.schemas import (
    MatterCreate, MatterResponse,
    UserCreate, UserResponse, LoginRequest, TokenResponse,
    DocumentResponse, PageResponse, IngestionStatusResponse,
    UploadResponse, QueryRequest, QueryResponse, CitationResponse,
)
from app.services.ingestion import ingest_document, get_ingestion_status
from app.services.retrieval import retrieve
from app.services.query_expansion import expand_query
from app.models import Matter, User, Document, Page, AuditLog

settings = get_settings()

router = APIRouter()


# --- Health Check ---

@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "ganymede-api", "version": "0.1.0"}


# --- Matter Routes ---

@router.post("/matters", response_model=MatterResponse, status_code=status.HTTP_201_CREATED)
def create_matter(
    matter: MatterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new matter."""
    db_matter = Matter(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        name=matter.name,
        description=matter.description,
        cause_number=matter.cause_number,
        court=matter.court,
    )
    db.add(db_matter)
    db.commit()
    db.refresh(db_matter)
    
    log_audit(
        db, str(current_user.tenant_id), str(current_user.id),
        "matter.create", "matter", str(db_matter.id),
    )
    
    return db_matter


@router.get("/matters", response_model=List[MatterResponse])
def list_matters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all matters."""
    if current_user.role == "administrator":
        return db.query(Matter).all()
    return db.query(Matter).filter(
        Matter.tenant_id == current_user.tenant_id
    ).all()


@router.get("/matters/{matter_id}", response_model=MatterResponse)
def get_matter(
    matter_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a matter by ID."""
    matter = db.query(Matter).filter(Matter.id == matter_id).first()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
    can_access_matter(current_user, matter_id, db)
    return matter


# --- User Routes ---

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user."""
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user = User(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        email=user.email,
        name=user.name,
        password_hash=hash_password(user.password),
        role=user.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/users", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all users (admin only)."""
    if current_user.role != "administrator":
        raise HTTPException(status_code=403, detail="Admin access required")
    return db.query(User).all()


# --- Auth Routes ---

@router.post("/auth/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT."""
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash or ""):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")
    
    token = create_access_token(
        user_id=str(user.id),
        role=user.role,
        expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    
    log_audit(
        db, str(user.tenant_id), str(user.id),
        "auth.login", "session",
    )
    
    return TokenResponse(
        access_token=token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(
            id=user.id,
            tenant_id=user.tenant_id,
            email=user.email,
            name=user.name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
        ),
    )


@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user (development only)."""
    return create_user(user, db)


@router.get("/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_active_user)):
    """Get current authenticated user."""
    return current_user


# --- Audit Log Routes ---

@router.get("/audit")
def get_audit_log(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get audit log entries (admin only)."""
    if current_user.role != "administrator":
        raise HTTPException(status_code=403, detail="Admin access required")
    entries, total = query_audit_log(db, str(current_user.tenant_id), limit=limit, offset=offset)
    return {"entries": entries, "total": total}


# --- Document Routes ---

@router.post("/matters/{matter_id}/documents", response_model=UploadResponse)
async def upload_document(
    matter_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Upload and ingest a document."""
    matter = db.query(Matter).filter(Matter.id == matter_id).first()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
    can_access_matter(current_user, matter_id, db)
    
    file_bytes = await file.read()
    
    doc = ingest_document(
        db=db,
        matter_id=matter_id,
        filename=file.filename,
        file_bytes=file_bytes,
        mime_type=file.content_type or "application/octet-stream",
    )
    
    log_audit(
        db, str(current_user.tenant_id), str(current_user.id),
        "document.upload", "document", str(doc.id),
        {"filename": file.filename, "size": len(file_bytes)},
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
def list_documents(
    matter_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all documents in a matter."""
    matter = db.query(Matter).filter(Matter.id == matter_id).first()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
    can_access_matter(current_user, matter_id, db)
    return db.query(Document).filter(Document.matter_id == matter_id, Document.is_duplicate == False).all()


@router.get("/documents/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a document by ID."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    can_access_matter(current_user, str(doc.matter_id), db)
    return doc


@router.get("/documents/{document_id}/pages", response_model=List[PageResponse])
def get_document_pages(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all pages for a document."""
    pages = db.query(Page).filter(Page.document_id == document_id).order_by(Page.page_number).all()
    return pages


@router.get("/documents/{document_id}/status", response_model=IngestionStatusResponse)
def get_document_status(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
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
    current_user: User = Depends(get_current_active_user),
):
    """Query a matter's documents. Returns ranked citations."""
    matter = db.query(Matter).filter(Matter.id == matter_id).first()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
    can_access_matter(current_user, matter_id, db)
    
    # Sanitize input
    clean_query = sanitize_query(request.query_text)
    injection = detect_injection(clean_query)
    if injection:
        log_audit(
            db, str(current_user.tenant_id), str(current_user.id),
            "query.injection_detected", "matter", matter_id,
            {"matched": injection, "query_prefix": clean_query[:100]},
        )
        raise HTTPException(status_code=400, detail="Query blocked: suspicious pattern detected")
    
    citations = retrieve(
        db=db,
        matter_id=matter_id,
        query_text=clean_query,
        top_k=request.top_k or 10,
    )
    
    log_audit(
        db, str(current_user.tenant_id), str(current_user.id),
        "query.submit", "matter", matter_id,
        {"result_count": len(citations)},
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
    current_user: User = Depends(get_current_active_user),
):
    """Submit a question for async processing. Returns immediately with query_id."""
    from app.services.async_verification import submit_query
    from app.core.database import SessionLocal

    matter = db.query(Matter).filter(Matter.id == matter_id).first()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
    can_access_matter(current_user, matter_id, db)
    
    query_id = submit_query(
        matter_id=matter_id,
        question=request.query_text,
        db_session_factory=SessionLocal,
        top_k=request.top_k or 5,
    )
    
    log_audit(
        db, str(current_user.tenant_id), str(current_user.id),
        "query.submit_async", "matter", matter_id,
        {"query_id": query_id},
    )
    
    return {"query_id": query_id, "status": "pending"}


@router.get("/ask/{query_id}/status")
def get_query_status(
    query_id: str,
    current_user: User = Depends(get_current_active_user),
):
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
    feedback: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Submit feedback on a citation."""
    log_audit(
        db, str(current_user.tenant_id), str(current_user.id),
        "citation.feedback", "citation", citation_id,
        {"feedback": feedback},
    )
    return {"status": "received", "citation_id": citation_id, "feedback": feedback}


# --- Verified Q&A Route ---

@router.post("/matters/{matter_id}/ask")
def ask_matter(
    matter_id: str,
    request: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Ask a question and get raw citations (UNVERIFIED)."""
    matter = db.query(Matter).filter(Matter.id == matter_id).first()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
    can_access_matter(current_user, matter_id, db)
    
    expanded_query = expand_query(request.query_text)
    
    raw_citations = retrieve(
        db=db,
        matter_id=matter_id,
        query_text=expanded_query,
        top_k=request.top_k or 5,
    )
    
    return {
        "matter_id": matter_id,
        "query_text": request.query_text,
        "expanded_query": expanded_query,
        "answer": f"Found {len(raw_citations)} raw passage(s) — UNVERIFIED. Use /ask-async for verified results.",
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
            for c in raw_citations
        ],
        "result_count": len(raw_citations),
        "raw_count": len(raw_citations),
        "verified": False,
    }
