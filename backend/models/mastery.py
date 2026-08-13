import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from backend.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin

class StudentMastery(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "student_mastery"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_id = Column(UUID(as_uuid=True), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True)
    curriculum_version_id = Column(UUID(as_uuid=True), ForeignKey("curriculum_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    mastery_score = Column(Float, nullable=False, default=0.0, index=True)
    confidence = Column(Float, nullable=False, default=0.0)
    attempt_count = Column(Integer, nullable=False, default=0)
    correct_count = Column(Integer, nullable=False, default=0)
    incorrect_count = Column(Integer, nullable=False, default=0)
    recent_performance = Column(JSONB, nullable=False, default=list)
    historical_performance = Column(JSONB, nullable=False, default=list)
    average_response_time = Column(Float, nullable=False, default=0.0)
    last_difficulty = Column(Integer, nullable=False, default=3)
    status = Column(String(50), nullable=False, default="NOT_STARTED", index=True) # NOT_STARTED, IN_PROGRESS, NEEDS_REMEDIATION, MASTERED, REVIEW_DUE
    misconception_tags = Column(JSONB, nullable=False, default=list)
    last_practiced_at = Column(DateTime(timezone=True), nullable=True)
    next_review_due_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("student_id", "concept_id", "curriculum_version_id", name="uq_student_concept_version"),
    )

class MasteryHistoryLog(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "mastery_history_logs"

    student_mastery_id = Column(UUID(as_uuid=True), ForeignKey("student_mastery.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_id = Column(UUID(as_uuid=True), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    curriculum_version_id = Column(UUID(as_uuid=True), ForeignKey("curriculum_versions.id", ondelete="CASCADE"), nullable=False)
    policy_version = Column(String(50), nullable=False, default="v1.0")
    event_type = Column(String(50), nullable=False, default="ASSESSMENT_ATTEMPT")
    is_correct = Column(Boolean, nullable=False)
    item_difficulty = Column(Integer, nullable=False, default=3)
    previous_mastery = Column(Float, nullable=False)
    new_mastery = Column(Float, nullable=False)
    previous_status = Column(String(50), nullable=False)
    new_status = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
