import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from backend.models.base import Base, UUIDPrimaryKeyMixin

class CurriculumVectorEmbeddings(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "curriculum_vector_embeddings"

    chunk_id = Column(UUID(as_uuid=True), ForeignKey("document_chunks.id", ondelete="CASCADE"), nullable=True, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="SET NULL"), nullable=True, index=True)
    curriculum_id = Column(UUID(as_uuid=True), ForeignKey("curricula.id", ondelete="CASCADE"), nullable=False, index=True)
    curriculum_version_id = Column(UUID(as_uuid=True), ForeignKey("curriculum_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    grade = Column(Integer, nullable=False, index=True)
    subject = Column(String(100), nullable=False, index=True)
    chapter = Column(String(255), nullable=True)
    topic = Column(String(255), nullable=True)
    concept = Column(String(255), nullable=True)
    learning_objective = Column(String(255), nullable=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("source_documents.id", ondelete="SET NULL"), nullable=True)
    page_number = Column(Integer, nullable=True)
    section = Column(String(255), nullable=True)
    text_content = Column(Text, nullable=False)
    approval_status = Column(String(50), nullable=False, default="PUBLISHED", index=True) # PUBLISHED, DRAFT, ARCHIVED
    embedding_model = Column(String(100), nullable=False, default="text-embedding-3-small")
    embedding_dimension = Column(Integer, nullable=False, default=1536)
    embedding_version = Column(String(50), nullable=False, default="v1.0")
    embedding_vector = Column(JSONB, nullable=False) # JSON array of floats representing 1536-dim vector
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
