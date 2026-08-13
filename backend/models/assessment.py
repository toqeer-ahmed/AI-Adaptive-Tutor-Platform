import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from backend.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin

class QuestionBankItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "question_bank_items"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    curriculum_version_id = Column(UUID(as_uuid=True), ForeignKey("curriculum_versions.id", ondelete="SET NULL"), nullable=True, index=True)
    learning_objective_id = Column(UUID(as_uuid=True), ForeignKey("learning_objectives.id", ondelete="SET NULL"), nullable=True, index=True)
    concept_id = Column(UUID(as_uuid=True), ForeignKey("concepts.id", ondelete="SET NULL"), nullable=True, index=True)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills.id", ondelete="SET NULL"), nullable=True, index=True)
    difficulty = Column(Integer, nullable=False, default=3)
    question_type = Column(String(50), nullable=False, index=True) # mcq, multi_select, true_false, fill_blank, numeric, short_answer, matching, ordering
    question_text = Column(Text, nullable=False)
    options_json = Column(JSONB, nullable=True)
    correct_answer_json = Column(JSONB, nullable=False)
    explanation = Column(Text, nullable=True)
    rubric_json = Column(JSONB, nullable=True)
    source_reference = Column(String(255), nullable=True)
    generation_method = Column(String(50), nullable=False, default="MANUAL") # MANUAL, AI_GENERATED
    validation_status = Column(String(50), nullable=False, default="PROPOSED", index=True) # PROPOSED, APPROVED, REJECTED
    version = Column(Integer, nullable=False, default=1)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

class Assessment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "assessments"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="SET NULL"), nullable=True, index=True)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    assessment_type = Column(String(50), nullable=False, default="QUIZ") # QUIZ, ASSIGNMENT
    max_attempts = Column(Integer, nullable=False, default=1)
    time_limit_minutes = Column(Integer, nullable=True)
    available_from = Column(DateTime(timezone=True), nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=True)
    is_published = Column(Boolean, nullable=False, default=False)

    questions = relationship("AssessmentQuestion", back_populates="assessment", cascade="all, delete-orphan", order_by="AssessmentQuestion.sequence_order")
    attempts = relationship("AssessmentAttempt", back_populates="assessment", cascade="all, delete-orphan")

class AssessmentQuestion(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "assessment_questions"

    assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(UUID(as_uuid=True), ForeignKey("question_bank_items.id", ondelete="CASCADE"), nullable=False, index=True)
    sequence_order = Column(Integer, nullable=False, default=1)
    points = Column(Float, nullable=False, default=1.0)

    assessment = relationship("Assessment", back_populates="questions")
    question = relationship("QuestionBankItem")

class AssessmentAttempt(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "assessment_attempts"

    assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    attempt_number = Column(Integer, nullable=False, default=1)
    status = Column(String(50), nullable=False, default="IN_PROGRESS") # IN_PROGRESS, SUBMITTED, GRADED
    score = Column(Float, nullable=True)
    max_score = Column(Float, nullable=True)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    submitted_at = Column(DateTime(timezone=True), nullable=True)

    assessment = relationship("Assessment", back_populates="attempts")
    answers = relationship("StudentAnswer", back_populates="attempt", cascade="all, delete-orphan")

class StudentAnswer(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "student_answers"

    attempt_id = Column(UUID(as_uuid=True), ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(UUID(as_uuid=True), ForeignKey("question_bank_items.id", ondelete="CASCADE"), nullable=False, index=True)
    submitted_answer_json = Column(JSONB, nullable=False)
    is_correct = Column(Boolean, nullable=True)
    points_awarded = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    teacher_override = Column(Boolean, nullable=False, default=False)
    answered_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    attempt = relationship("AssessmentAttempt", back_populates="answers")
    question = relationship("QuestionBankItem")
