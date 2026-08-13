import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from backend.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin

class Organization(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "organizations"

    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    settings = Column(JSONB, nullable=False, default=dict)
    is_active = Column(Boolean, default=True, nullable=False)

    schools = relationship("School", back_populates="organization", cascade="all, delete-orphan")
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    classes = relationship("Class", back_populates="organization", cascade="all, delete-orphan")

class School(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "schools"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)

    organization = relationship("Organization", back_populates="schools")
    users = relationship("User", back_populates="school")
    classes = relationship("Class", back_populates="school")
