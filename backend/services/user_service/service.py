import uuid
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from backend.models.user import User, Role, UserRole
from backend.models.organization import Organization, School
from backend.models.class_model import Class, Enrollment
from backend.models.security import ParentStudentLink
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

        if isinstance(organization_id, str):
            organization_id = uuid.UUID(organization_id)
        if school_id and isinstance(school_id, str):
            school_id = uuid.UUID(school_id)

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
            role = Role(id=uuid.uuid4(), name=role_name, description=f"{role_name} role")
            session.add(role)
            await session.flush()

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

    @staticmethod
    async def list_organization_users(
        session: AsyncSession,
        organization_id: uuid.UUID,
        school_id: Optional[uuid.UUID] = None
    ) -> List[User]:
        stmt = (
            select(User)
            .options(selectinload(User.roles).selectinload(UserRole.role))
            .where(User.organization_id == organization_id)
        )
        if school_id:
            stmt = stmt.where(User.school_id == school_id)
        stmt = stmt.order_by(User.created_at.desc())
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def seed_default_dev_accounts(session: AsyncSession) -> None:
        """
        Seeds standard development organization, school, class, and 7 role-based test accounts.
        Password for all test accounts: Pass123!
        """
        from backend.services.organization_service.service import OrganizationService, SchoolService

        # 1. Organization
        org = await OrganizationService.get_organization_by_code(session, "DIST-101")
        if not org:
            org = await OrganizationService.create_organization(session, "District 101 Innovation", "DIST-101")

        # 2. School
        schools = await SchoolService.list_schools(session, org.id)
        if schools:
            school = schools[0]
        else:
            school = await SchoolService.create_school(session, org.id, "Oakridge Middle School", "SCH-OAK-01")

        # 3. 7 Standard Role Accounts
        standard_accounts = [
            ("student@school.edu", "Alex Johnson", "Student", school.id),
            ("teacher@school.edu", "Mrs. Sarah Davis", "Teacher", school.id),
            ("parent@family.com", "Michael Johnson", "Parent", None),
            ("schooladmin@school.edu", "Principal Robert Vance", "SchoolAdmin", school.id),
            ("orgadmin@district.edu", "Director Elena Rostova", "OrgAdmin", None),
            ("curriculum@district.edu", "Dr. Marcus Chen", "CurriculumManager", None),
            ("platformadmin@platform.com", "Antigravity SysAdmin", "SuperAdmin", None),
        ]

        created_users = {}
        for email, full_name, role_name, s_id in standard_accounts:
            existing = await UserService.get_user_by_email(session, email)
            if not existing:
                u = await UserService.create_user(
                    session=session,
                    organization_id=org.id,
                    email=email,
                    password="Pass123!",
                    full_name=full_name,
                    role_name=role_name,
                    school_id=s_id
                )
                created_users[role_name] = u
            else:
                created_users[role_name] = existing

        # 4. Class Setup
        teacher_user = created_users.get("Teacher")
        student_user = created_users.get("Student")

        cls_res = await session.execute(
            select(Class).where(
                Class.organization_id == org.id,
                Class.name == "Grade 6 Mathematics - Section A"
            )
        )
        cls = cls_res.scalars().first()

        if not cls and teacher_user:
            cls = await ClassService.create_class(
                session=session,
                organization_id=org.id,
                school_id=school.id,
                teacher_id=teacher_user.id,
                name="Grade 6 Mathematics - Section A",
                grade_level=6,
                academic_year="2026-2027"
            )

        # 5. Class Enrollment for Student
        if cls and student_user:
            enr_res = await session.execute(
                select(Enrollment).where(
                    Enrollment.class_id == cls.id,
                    Enrollment.student_id == student_user.id
                )
            )
            if not enr_res.scalars().first():
                await ClassService.enroll_student(
                    session=session,
                    organization_id=org.id,
                    class_id=cls.id,
                    student_id=student_user.id
                )

        # 6. Parent-Child Link
        parent_user = created_users.get("Parent")
        if parent_user and student_user:
            link_res = await session.execute(
                select(ParentStudentLink).where(
                    ParentStudentLink.parent_id == parent_user.id,
                    ParentStudentLink.student_id == student_user.id
                )
            )
            if not link_res.scalars().first():
                link = ParentStudentLink(
                    id=uuid.uuid4(),
                    organization_id=org.id,
                    parent_id=parent_user.id,
                    student_id=student_user.id
                )
                session.add(link)
                await session.commit()



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

    @staticmethod
    async def get_classes_for_user(session: AsyncSession, user: User) -> List[Class]:
        roles = [ur.role.name for ur in user.roles]
        if "Teacher" in roles:
            stmt = select(Class).where(
                Class.organization_id == user.organization_id,
                Class.teacher_id == user.id
            )
        elif "Student" in roles:
            stmt = select(Class).join(Enrollment, Enrollment.class_id == Class.id).where(
                Class.organization_id == user.organization_id,
                Enrollment.student_id == user.id
            )
        elif "SchoolAdmin" in roles and user.school_id:
            stmt = select(Class).where(
                Class.organization_id == user.organization_id,
                Class.school_id == user.school_id
            )
        else: # OrgAdmin, SuperAdmin
            stmt = select(Class).where(Class.organization_id == user.organization_id)

        stmt = stmt.order_by(Class.grade_level.asc(), Class.name.asc())
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get_class_students(session: AsyncSession, class_id: uuid.UUID) -> List[User]:
        stmt = (
            select(User)
            .join(Enrollment, Enrollment.student_id == User.id)
            .options(selectinload(User.roles).selectinload(UserRole.role))
            .where(Enrollment.class_id == class_id)
            .order_by(User.full_name.asc())
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())

