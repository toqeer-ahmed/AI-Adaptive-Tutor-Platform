import uuid
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from backend.models.user import User, Role, UserRole
from backend.models.class_model import Class, Enrollment
from backend.services.user_service.auth import hash_password

class UserService:
    @staticmethod
    async def create_user(
        session: AsyncSession,
        organization_id: uuid.UUID,
        email: str,
        password: str,
        full_name: str,
        role_name: str,
        school_id: Optional[uuid.UUID] = None
    ) -> User:
        # Check if email already exists
        existing = await session.execute(select(User).where(User.email == email.lower()))
        if existing.scalars().first():
            raise ValueError(f"User with email '{email}' already exists.")

        user = User(
            id=uuid.uuid4(),
            organization_id=organization_id,
            school_id=school_id,
            email=email.lower(),
            password_hash=hash_password(password),
            full_name=full_name
        )
        session.add(user)
        await session.flush()

        # Resolve role
        role_res = await session.execute(select(Role).where(Role.name == role_name))
        role = role_res.scalars().first()
        if not role:
            raise ValueError(f"Role '{role_name}' does not exist.")

        user_role = UserRole(user_id=user.id, role_id=role.id)
        session.add(user_role)
        await session.commit()

        return await UserService.get_user_by_id(session, user.id)

    @staticmethod
    async def get_user_by_id(session: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        result = await session.execute(
            select(User)
            .options(selectinload(User.roles).selectinload(UserRole.role))
            .where(User.id == user_id)
        )
        return result.scalars().first()

    @staticmethod
    async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
        result = await session.execute(
            select(User)
            .options(selectinload(User.roles).selectinload(UserRole.role))
            .where(User.email == email.lower())
        )
        return result.scalars().first()

class ClassService:
    @staticmethod
    async def create_class(
        session: AsyncSession,
        organization_id: uuid.UUID,
        school_id: uuid.UUID,
        teacher_id: uuid.UUID,
        name: str,
        grade_level: int,
        academic_year: str
    ) -> Class:
        cls = Class(
            id=uuid.uuid4(),
            organization_id=organization_id,
            school_id=school_id,
            teacher_id=teacher_id,
            name=name,
            grade_level=grade_level,
            academic_year=academic_year
        )
        session.add(cls)
        await session.commit()
        await session.refresh(cls)
        return cls

    @staticmethod
    async def enroll_student(
        session: AsyncSession,
        organization_id: uuid.UUID,
        class_id: uuid.UUID,
        student_id: uuid.UUID
    ) -> Enrollment:
        enrollment = Enrollment(
            id=uuid.uuid4(),
            organization_id=organization_id,
            class_id=class_id,
            student_id=student_id
        )
        session.add(enrollment)
        await session.commit()
        await session.refresh(enrollment)
        return enrollment
