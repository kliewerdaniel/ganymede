# Ganymede — Initial Database Migration

"""Initial schema for Ganymede ingestion engine."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable UUID extension
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
    
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Tenants table
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="attorney"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
    )

    # Matters table
    op.create_table(
        "matters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("cause_number", sa.String(100), nullable=True),
        sa.Column("court", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Matter memberships table
    op.create_table(
        "matter_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("matter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("matters.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("matter_id", "user_id", name="uq_matter_membership"),
    )

    # Documents table
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("matter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("matters.id"), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.Integer, nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("page_count", sa.Integer, nullable=True),
        sa.Column("parser_version", sa.String(50), nullable=True),
        sa.Column("ingestion_status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("ingestion_error", sa.Text, nullable=True),
        sa.Column("is_duplicate", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("duplicate_of_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Pages table
    op.create_table(
        "pages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("page_number", sa.Integer, nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("start_offset", sa.Integer, nullable=False),
        sa.Column("end_offset", sa.Integer, nullable=False),
        sa.Column("parser_version", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("document_id", "page_number", name="uq_pages_document_page"),
    )

    # Ingestion jobs table
    op.create_table(
        "ingestion_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("stage", sa.String(50), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("started_at", sa.DateTime, nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Indexes
    op.create_index("idx_documents_sha256", "documents", ["sha256"])
    op.create_index("idx_documents_matter_sha256", "documents", ["matter_id", "sha256"])
    op.create_index("idx_ingestion_jobs_document", "ingestion_jobs", ["document_id"])


def downgrade() -> None:
    op.drop_index("idx_ingestion_jobs_document")
    op.drop_index("idx_documents_matter_sha256")
    op.drop_index("idx_documents_sha256")
    op.drop_table("ingestion_jobs")
    op.drop_table("pages")
    op.drop_table("documents")
    op.drop_table("matter_memberships")
    op.drop_table("matters")
    op.drop_table("users")
    op.drop_table("tenants")
