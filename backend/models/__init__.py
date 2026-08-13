from backend.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin
from backend.models.organization import Organization, School
from backend.models.user import User, Role, UserRole, Permission, RolePermission
from backend.models.class_model import Class, Enrollment
from backend.models.audit import AuditLogEntry
from backend.models.security import (
    TokenRevocation,
    PasswordResetToken,
    EmailVerificationToken,
    ParentStudentLink,
    SupportGrant
)
from backend.models.curriculum import (
    SourceDocument,
    DocumentChunk,
    Curriculum,
    CurriculumVersion,
    Chapter,
    Topic,
    Concept,
    Skill,
    LearningObjective,
    ConceptPrerequisite
)
from backend.models.ai import ModelUsageRecord
from backend.models.rag import CurriculumVectorEmbeddings
from backend.models.assessment import (
    QuestionBankItem,
    Assessment,
    AssessmentQuestion,
    AssessmentAttempt,
    StudentAnswer
)
from backend.models.mastery import StudentMastery, MasteryHistoryLog
from backend.models.tutor import TutorSession, TutorTurn
from backend.models.misconception import MisconceptionTaxonomy, StudentMisconception

__all__ = [
    "Base",
    "UUIDPrimaryKeyMixin",
    "TimestampMixin",
    "Organization",
    "School",
    "User",
    "Role",
    "UserRole",
    "Permission",
    "RolePermission",
    "Class",
    "Enrollment",
    "AuditLogEntry",
    "TokenRevocation",
    "PasswordResetToken",
    "EmailVerificationToken",
    "ParentStudentLink",
    "SupportGrant",
    "SourceDocument",
    "DocumentChunk",
    "Curriculum",
    "CurriculumVersion",
    "Chapter",
    "Topic",
    "Concept",
    "Skill",
    "LearningObjective",
    "ConceptPrerequisite",
    "ModelUsageRecord",
    "CurriculumVectorEmbeddings",
    "QuestionBankItem",
    "Assessment",
    "AssessmentQuestion",
    "AssessmentAttempt",
    "StudentAnswer",
    "StudentMastery",
    "MasteryHistoryLog",
    "TutorSession",
    "TutorTurn",
    "MisconceptionTaxonomy",
    "StudentMisconception"
]
