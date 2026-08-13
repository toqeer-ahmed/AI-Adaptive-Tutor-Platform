import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from backend.models.base import Base, UUIDPrimaryKeyMixin

class AnalyticsSummaryProvenance(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "analytics_summary_provenance"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    summary_type = Column(String(100), nullable=False, index=True) # TEACHER_CLASS_SUMMARY, STUDENT_RECOMMENDATION_EXPLANATION
    source_metric_ids = Column(JSONB, nullable=False, default=list) # List of UUIDs of student_masteries, assessment_attempts, etc.
    generated_summary_text = Column(Text, nullable=False)
    ai_model_name = Column(String(100), nullable=False, default="gpt-4o-mini")
    prompt_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
