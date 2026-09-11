# Ganymede API — Pydantic Schemas

"""Pydantic schemas for request/response validation."""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List


# --- Tenant Schemas ---

class TenantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class TenantResponse(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- User Schemas ---

class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(default="attorney", pattern="^(administrator|attorney|paralegal|reviewer|it_operator)$")


class UserResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    name: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- Matter Schemas ---

class MatterCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    cause_number: Optional[str] = Field(None, max_length=100)
    court: Optional[str] = Field(None, max_length=255)


class MatterResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    description: Optional[str]
    cause_number: Optional[str]
    court: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# --- Matter Membership Schemas ---

class MatterMembershipCreate(BaseModel):
    user_id: uuid.UUID
    role: str = Field(..., pattern="^(administrator|attorney|paralegal|reviewer)$")


class MatterMembershipResponse(BaseModel):
    id: uuid.UUID
    matter_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- Document Schemas ---

class DocumentResponse(BaseModel):
    id: uuid.UUID
    matter_id: uuid.UUID
    filename: str
    original_filename: str
    mime_type: str
    size_bytes: int
    sha256: str
    page_count: Optional[int]
    parser_version: Optional[str]
    ingestion_status: str
    ingestion_error: Optional[str]
    is_duplicate: bool
    duplicate_of_id: Optional[uuid.UUID]
    created_at: datetime

    class Config:
        from_attributes = True


class PageResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    page_number: int
    text: str
    start_offset: int
    end_offset: int
    parser_version: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- Ingestion Job Schemas ---

class IngestionJobResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    status: str
    stage: Optional[str]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# --- Upload Schemas ---

class UploadResponse(BaseModel):
    document_id: uuid.UUID
    filename: str
    sha256: str
    ingestion_status: str
    is_duplicate: bool
    duplicate_of_id: Optional[uuid.UUID] = None


class IngestionStatusResponse(BaseModel):
    document_id: uuid.UUID
    status: str
    stage: Optional[str]
    error_message: Optional[str]
    page_count: Optional[int]
    parser_version: Optional[str]
