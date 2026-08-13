import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from backend.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin

class AIEvalDataset(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ai_eval_datasets"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_name = Column(String(100), nullable=False, index=True)
    version = Column(String(50), nullable=False, default="v1.0")
    category = Column(String(100), nullable=False, index=True) # 14 Categories: CURRICULUM_EXTRACTION, PROMPT_INJECTION, SAFETY, etc.
    items_json = Column(JSONB, nullable=False, default=list)

class AIEvalRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ai_eval_runs"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    model_name = Column(String(100), nullable=False, index=True)
    provider = Column(String(50), nullable=False, index=True)
    prompt_version = Column(String(50), nullable=False, index=True)
    dataset_version = Column(String(50), nullable=False, default="v1.0")
    overall_accuracy = Column(Float, nullable=False, default=0.0)
    category_scores_json = Column(JSONB, nullable=False, default=dict)
    failures_json = Column(JSONB, nullable=False, default=list)
    passed_release_gate = Column(Boolean, nullable=False, default=False, index=True)
    evaluated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
