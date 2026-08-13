import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from backend.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin

class MisconceptionTaxonomy(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "misconception_taxonomies"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_id = Column(UUID(as_uuid=True), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    remediation_strategy = Column(Text, nullable=True)

class StudentMisconception(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "student_misconceptions"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_id = Column(UUID(as_uuid=True), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True)
    curriculum_version_id = Column(UUID(as_uuid=True), ForeignKey("curriculum_versions.id", ondelete="CASCADE"), nullable=False)
    misconception_id = Column(UUID(as_uuid=True), ForeignKey("misconception_taxonomies.id", ondelete="CASCADE"), nullable=False, index=True)
    confidence = Column(Float, nullable=False, default=0.0)
    status = Column(String(50), nullable=False, default="DETECTED", index=True) # DETECTED, PERSISTENT, RESOLVED
    evidence = Column(JSONB, nullable=False, default=list)
    resolution_evidence = Column(JSONB, nullable=False, default=list)
    detected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    taxonomy = relationship("MisconceptionTaxonomy")

    __table_args__ = (
        UniqueConstraint("student_id", "misconception_id", "curriculum_version_id", name="uq_student_misconception_version"),
    )
