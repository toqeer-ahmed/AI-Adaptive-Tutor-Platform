import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin

class Class(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "classes"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    grade_level = Column(Integer, nullable=False)
    academic_year = Column(String(20), nullable=False)

    organization = relationship("Organization", back_populates="classes")
    school = relationship("School", back_populates="classes")
    teacher = relationship("User", back_populates="taught_classes")
    enrollments = relationship("Enrollment", back_populates="class_obj", cascade="all, delete-orphan")

class Enrollment(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "enrollments"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    enrolled_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    class_obj = relationship("Class", back_populates="enrollments")
    student = relationship("User", back_populates="enrollments")

    __table_args__ = (
        UniqueConstraint("class_id", "student_id", name="uq_class_student_enrollment"),
    )
