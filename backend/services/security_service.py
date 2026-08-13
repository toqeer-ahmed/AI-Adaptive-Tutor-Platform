import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.models.user import User, UserRole
from backend.models.class_model import Class, Enrollment
from backend.models.security import ParentStudentLink, SupportGrant

class SecurityService:
    @staticmethod
    async def verify_class_access(session: AsyncSession, requester: User, class_id: uuid.UUID) -> Class:
        """
        Verifies that the requester can access the target class.
        - Must be in same Organization (unless SuperAdmin)
        - If Teacher: must be assigned teacher of the class
        - If Student: must be enrolled in the class
        """
        result = await session.execute(select(Class).where(Class.id == class_id))
        target_class = result.scalars().first()
        if not target_class:
            raise ValueError("Class not found.")

        user_roles = [ur.role.name for ur in requester.roles]
        
        # SuperAdmin bypass
        if "SuperAdmin" in user_roles:
            return target_class

        # Organization boundary check
        if requester.organization_id != target_class.organization_id:
            raise PermissionError("Forbidden: Cannot access class in foreign organization.")

        # Teacher specific ownership check
        if "Teacher" in user_roles and "OrgAdmin" not in user_roles and "SchoolAdmin" not in user_roles:
            if target_class.teacher_id != requester.id:
                raise PermissionError("Forbidden: Teacher is not assigned to this class.")

        # Student specific enrollment check
        if "Student" in user_roles and "Teacher" not in user_roles and "OrgAdmin" not in user_roles:
            enrollment_res = await session.execute(
                select(Enrollment).where(
                    Enrollment.class_id == class_id,
                    Enrollment.student_id == requester.id
                )
            )
            if not enrollment_res.scalars().first():
                raise PermissionError("Forbidden: Student is not enrolled in this class.")

        return target_class

    @staticmethod
    async def verify_student_record_access(session: AsyncSession, requester: User, student_id: uuid.UUID) -> User:
        """
        Verifies that requester can access the target student's record.
        - Student themselves
        - OrgAdmin / SchoolAdmin in same organization
        - Teacher of a class where the student is enrolled
        - Linked Parent
        """
        res = await session.execute(select(User).where(User.id == student_id))
        student = res.scalars().first()
        if not student:
            raise ValueError("Student not found.")

        user_roles = [ur.role.name for ur in requester.roles]

        if "SuperAdmin" in user_roles:
            return student

        if requester.organization_id != student.organization_id:
            raise PermissionError("Forbidden: Cannot access student in foreign organization.")

        # Student self access
        if requester.id == student_id:
            return student

        # Admins in same org
        if "OrgAdmin" in user_roles or "SchoolAdmin" in user_roles:
            return student

        # Parent link check
        if "Parent" in user_roles:
            link_res = await session.execute(
                select(ParentStudentLink).where(
                    ParentStudentLink.parent_id == requester.id,
                    ParentStudentLink.student_id == student_id
                )
            )
            if link_res.scalars().first():
                return student

        # Teacher check
        if "Teacher" in user_roles:
            # Check if teacher shares any class with this student
            teacher_class_res = await session.execute(
                select(Enrollment)
                .join(Class, Enrollment.class_id == Class.id)
                .where(
                    Class.teacher_id == requester.id,
                    Enrollment.student_id == student_id
                )
            )
            if teacher_class_res.scalars().first():
                return student

        raise PermissionError("Forbidden: Unauthorized access to student record.")

    @staticmethod
    async def verify_support_access(session: AsyncSession, support_user: User, target_org_id: uuid.UUID) -> bool:
        """
        Support users require an active SupportGrant for the target organization.
        """
        user_roles = [ur.role.name for ur in support_user.roles]
        if "SuperAdmin" in user_roles:
            return True

        if "Support" not in user_roles:
            return False

        now = datetime.now(timezone.utc)
        res = await session.execute(
            select(SupportGrant).where(
                SupportGrant.support_user_id == support_user.id,
                SupportGrant.organization_id == target_org_id,
                SupportGrant.is_active == True,
                SupportGrant.starts_at <= now,
                SupportGrant.expires_at >= now
            )
        )
        return res.scalars().first() is not None
