import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from backend.models.base import Base, UUIDPrimaryKeyMixin

class SubjectiveEvaluationLog(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "subjective_evaluation_logs"

    answer_id = Column(UUID(as_uuid=True), ForeignKey("student_answers.id", ondelete="CASCADE"), nullable=False, index=True)
    evaluator_type = Column(String(50), nullable=False, default="AI_PROPOSAL") # AI_PROPOSAL, TEACHER_ACCEPT, TEACHER_OVERRIDE
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    score_proposed = Column(Float, nullable=False, default=0.0)
    score_final = Column(Float, nullable=False, default=0.0)
    rubric_json = Column(JSONB, nullable=False, default=dict)
    feedback = Column(Text, nullable=True)
    confidence = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
