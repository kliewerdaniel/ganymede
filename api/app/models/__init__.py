# Ganymede API — Database Models

"""SQLAlchemy models for Ganymede."""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean, Text, ForeignKey, UniqueConstraint, Index, Float, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class AuditLog(Base):
    """Append-only audit log entry."""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(255), nullable=True)
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_audit_logs_tenant_user", "tenant_id", "user_id"),
        Index("idx_audit_logs_action", "action"),
        Index("idx_audit_logs_created_at", "created_at"),
    )


class Tenant(Base):
    """Single-tenant deployment. One row per deployment."""
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    users = relationship("User", back_populates="tenant")
    matters = relationship("Matter", back_populates="tenant")


class User(Base):
    """User account. Belongs to a tenant."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    email = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="attorney")
    is_active = Column(Boolean, default=True, nullable=False)
    password_hash = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    matter_memberships = relationship("MatterMembership", back_populates="user")

    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
    )


class Matter(Base):
    """A legal matter. Belongs to a tenant."""
    __tablename__ = "matters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    cause_number = Column(String(100), nullable=True)
    court = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="matters")
    memberships = relationship("MatterMembership", back_populates="matter")
    documents = relationship("Document", back_populates="matter")


class MatterMembership(Base):
    """User membership in a matter with a role."""
    __tablename__ = "matter_memberships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    matter_id = Column(UUID(as_uuid=True), ForeignKey("matters.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    matter = relationship("Matter", back_populates="memberships")
    user = relationship("User", back_populates="matter_memberships")

    __table_args__ = (
        UniqueConstraint("matter_id", "user_id", name="uq_matter_membership"),
    )


class Document(Base):
    """An uploaded document. Belongs to a matter."""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    matter_id = Column(UUID(as_uuid=True), ForeignKey("matters.id"), nullable=False)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    sha256 = Column(String(64), nullable=False, index=True)
    page_count = Column(Integer, nullable=True)
    parser_version = Column(String(50), nullable=True)
    ingestion_status = Column(String(50), nullable=False, default="pending")
    ingestion_error = Column(Text, nullable=True)
    is_duplicate = Column(Boolean, default=False, nullable=False)
    duplicate_of_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    matter = relationship("Matter", back_populates="documents")
    pages = relationship("Page", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    ingestion_jobs = relationship("IngestionJob", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_documents_matter_sha256", "matter_id", "sha256"),
    )


class Page(Base):
    """A page extracted from a document, with provenance."""
    __tablename__ = "pages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    start_offset = Column(Integer, nullable=False)
    end_offset = Column(Integer, nullable=False)
    parser_version = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    document = relationship("Document", back_populates="pages")
    chunks = relationship("Chunk", back_populates="page")

    __table_args__ = (
        UniqueConstraint("document_id", "page_number", name="uq_pages_document_page"),
    )


class IngestionJob(Base):
    """Track ingestion status for a document."""
    __tablename__ = "ingestion_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    stage = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    document = relationship("Document", back_populates="ingestion_jobs")

    __table_args__ = (
        Index("idx_ingestion_jobs_document", "document_id"),
    )


class Chunk(Base):
    """A chunk of text from a page, with provenance."""
    __tablename__ = "chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    page_id = Column(UUID(as_uuid=True), ForeignKey("pages.id"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    matter_id = Column(UUID(as_uuid=True), ForeignKey("matters.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    start_offset = Column(Integer, nullable=False)
    end_offset = Column(Integer, nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)
    parser_version = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    page = relationship("Page", back_populates="chunks")
    document = relationship("Document", back_populates="chunks")
    matter = relationship("Matter")
    embedding = relationship("ChunkEmbedding", back_populates="chunk", uselist=False)

    __table_args__ = (
        UniqueConstraint("page_id", "chunk_index", name="uq_chunks_page_index"),
        Index("idx_chunks_matter", "matter_id"),
        Index("idx_chunks_content_hash", "content_hash"),
    )


class ChunkEmbedding(Base):
    """Embedding vector for a chunk."""
    __tablename__ = "chunk_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("chunks.id"), nullable=False, unique=True)
    vector = Column(ARRAY(Float), nullable=False)  # Store as double precision[]
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(100), nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    chunk = relationship("Chunk", back_populates="embedding")

    __table_args__ = (
        Index("idx_chunk_embeddings_chunk", "chunk_id"),
        Index("idx_chunk_embeddings_model", "model_name", "model_version"),
    )


# Week 6/8: Structured Artifacts

class Artifact(Base):
    """A structured artifact (chronology, issue_table, memo)."""
    __tablename__ = "artifacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    matter_id = Column(UUID(as_uuid=True), ForeignKey("matters.id"), nullable=False)
    artifact_type = Column(String(50), nullable=False)  # chronology, issue_table, memo
    title = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="draft")  # draft, under_review, approved, rejected
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    rejection_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    rejection_at = Column(DateTime, nullable=True)
    source_query = Column(Text, nullable=True)
    source_citation_ids = Column(JSONB, nullable=True)  # citation IDs used
    content = Column(JSONB, nullable=False)  # artifact-specific content
    metadata_json = Column(JSONB, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    matter = relationship("Matter")
    versions = relationship("ArtifactVersion", back_populates="artifact", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_artifacts_matter", "matter_id"),
        Index("idx_artifacts_type", "artifact_type"),
        Index("idx_artifacts_status", "status"),
    )


class ArtifactVersion(Base):
    """Version history for an artifact."""
    __tablename__ = "artifact_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artifact_id = Column(UUID(as_uuid=True), ForeignKey("artifacts.id"), nullable=False)
    version = Column(Integer, nullable=False)
    content = Column(JSONB, nullable=False)
    change_description = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    artifact = relationship("Artifact", back_populates="versions")

    __table_args__ = (
        UniqueConstraint("artifact_id", "version", name="uq_artifact_version"),
        Index("idx_artifact_versions_artifact", "artifact_id"),
    )


class Approval(Base):
    """Append-only approval ledger entry."""
    __tablename__ = "approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artifact_id = Column(UUID(as_uuid=True), ForeignKey("artifacts.id"), nullable=False)
    action = Column(String(50), nullable=False)  # approve, reject, request_review
    performed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    performed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    prior_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    comment = Column(Text, nullable=True)
    metadata_json = Column(JSONB, nullable=True)

    # Relationships
    artifact = relationship("Artifact")
    performer = relationship("User")

    __table_args__ = (
        Index("idx_approvals_artifact", "artifact_id"),
        Index("idx_approvals_performed_by", "performed_by"),
    )


class CitationFeedback(Base):
    """User feedback on a specific citation."""
    __tablename__ = "citation_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artifact_id = Column(UUID(as_uuid=True), ForeignKey("artifacts.id"), nullable=False)
    citation_document_id = Column(UUID(as_uuid=True), nullable=False)
    citation_page = Column(Integer, nullable=False)
    citation_sha256 = Column(String(64), nullable=False)
    feedback = Column(String(50), nullable=False)  # supporting, weak, wrong, inaccessible
    provided_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    artifact = relationship("Artifact")
    provider = relationship("User")

    __table_args__ = (
        Index("idx_citation_feedback_artifact", "artifact_id"),
        UniqueConstraint("artifact_id", "citation_document_id", "citation_sha256", "provided_by",
                         name="uq_citation_feedback"),
    )
