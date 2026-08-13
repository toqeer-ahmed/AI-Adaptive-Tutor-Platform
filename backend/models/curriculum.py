import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from backend.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin

class SourceDocument(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "source_documents"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)

class Curriculum(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "curricula"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    grade_level = Column(Integer, nullable=False, index=True)
    subject_name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)

    versions = relationship("CurriculumVersion", back_populates="curriculum", cascade="all, delete-orphan")

class CurriculumVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "curriculum_versions"

    curriculum_id = Column(UUID(as_uuid=True), ForeignKey("curricula.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False, default="DRAFT", index=True) # DRAFT, REVIEW, APPROVED, PUBLISHED, ARCHIVED
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    approved_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    published_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    change_log = Column(Text, nullable=True)
    metadata_json = Column(JSONB, nullable=False, default=dict)
    published_at = Column(DateTime(timezone=True), nullable=True)

    curriculum = relationship("Curriculum", back_populates="versions")
    chapters = relationship("Chapter", back_populates="curriculum_version", cascade="all, delete-orphan", order_by="Chapter.sequence_order")

    __table_args__ = (
        UniqueConstraint("curriculum_id", "version_number", name="uq_curriculum_version_number"),
    )

class Chapter(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "chapters"

    curriculum_version_id = Column(UUID(as_uuid=True), ForeignKey("curriculum_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    sequence_order = Column(Integer, nullable=False, default=1)
    source_document_id = Column(UUID(as_uuid=True), ForeignKey("source_documents.id", ondelete="SET NULL"), nullable=True)
    source_page = Column(Integer, nullable=True)
    source_section = Column(String(255), nullable=True)
    source_chunk_id = Column(String(255), nullable=True)

    curriculum_version = relationship("CurriculumVersion", back_populates="chapters")
    topics = relationship("Topic", back_populates="chapter", cascade="all, delete-orphan", order_by="Topic.sequence_order")

class Topic(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "topics"

    chapter_id = Column(UUID(as_uuid=True), ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    sequence_order = Column(Integer, nullable=False, default=1)
    source_document_id = Column(UUID(as_uuid=True), ForeignKey("source_documents.id", ondelete="SET NULL"), nullable=True)
    source_page = Column(Integer, nullable=True)
    source_section = Column(String(255), nullable=True)
    source_chunk_id = Column(String(255), nullable=True)

    chapter = relationship("Chapter", back_populates="topics")
    concepts = relationship("Concept", back_populates="topic", cascade="all, delete-orphan", order_by="Concept.sequence_order")

class Concept(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "concepts"

    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    difficulty_level = Column(Integer, nullable=False, default=3)
    sequence_order = Column(Integer, nullable=False, default=1)
    source_document_id = Column(UUID(as_uuid=True), ForeignKey("source_documents.id", ondelete="SET NULL"), nullable=True)
    source_page = Column(Integer, nullable=True)
    source_section = Column(String(255), nullable=True)
    source_chunk_id = Column(String(255), nullable=True)

    topic = relationship("Topic", back_populates="concepts")
    skills = relationship("Skill", back_populates="concept", cascade="all, delete-orphan")
    learning_objectives = relationship("LearningObjective", back_populates="concept", cascade="all, delete-orphan")

class Skill(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "skills"

    concept_id = Column(UUID(as_uuid=True), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    concept = relationship("Concept", back_populates="skills")

class LearningObjective(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "learning_objectives"

    concept_id = Column(UUID(as_uuid=True), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)
    bloom_taxonomy_level = Column(String(50), nullable=False, default="Understand")
    source_document_id = Column(UUID(as_uuid=True), ForeignKey("source_documents.id", ondelete="SET NULL"), nullable=True)
    source_page = Column(Integer, nullable=True)
    source_section = Column(String(255), nullable=True)
    source_chunk_id = Column(String(255), nullable=True)

    concept = relationship("Concept", back_populates="learning_objectives")

class ConceptPrerequisite(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "concept_prerequisites"

    concept_id = Column(UUID(as_uuid=True), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True)
    prerequisite_concept_id = Column(UUID(as_uuid=True), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True)
    relationship_type = Column(String(50), nullable=False, default="STRICT")

    __table_args__ = (
        UniqueConstraint("concept_id", "prerequisite_concept_id", name="uq_concept_prerequisite"),
    )
