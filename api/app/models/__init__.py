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
    ingestion_jobs = relationship("IngestionJob", back_populates="document")

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
    document = relationship("Document")
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
