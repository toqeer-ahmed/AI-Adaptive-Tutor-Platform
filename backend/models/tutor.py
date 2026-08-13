import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from backend.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin

class TutorSession(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "tutor_sessions"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_id = Column(UUID(as_uuid=True), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True)
    curriculum_version_id = Column(UUID(as_uuid=True), ForeignKey("curriculum_versions.id", ondelete="CASCADE"), nullable=False)
    current_mode = Column(String(50), nullable=False, default="explanation", index=True) # explanation, socratic, worked_example, guided_practice, hint, remediation, feedback, assessment, challenge
    is_active = Column(Boolean, nullable=False, default=True)

    turns = relationship("TutorTurn", back_populates="session", cascade="all, delete-orphan", order_by="TutorTurn.created_at")

class TutorTurn(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "tutor_turns"

    session_id = Column(UUID(as_uuid=True), ForeignKey("tutor_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    student_message = Column(Text, nullable=False)
    tutor_response = Column(Text, nullable=False)
    mode = Column(String(50), nullable=False)
    sources_cited = Column(JSONB, nullable=False, default=list)
    token_usage = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    session = relationship("TutorSession", back_populates="turns")
