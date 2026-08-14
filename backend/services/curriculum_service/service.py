import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from backend.models.curriculum import (
    Curriculum,
    CurriculumVersion,
    Chapter,
    Topic,
    Concept,
    Skill,
    LearningObjective,
    ConceptPrerequisite,
    SourceDocument
)
from backend.models.user import User
from backend.services.audit_service import AuditService

class CurriculumService:
    @staticmethod
    async def create_curriculum(
        session: AsyncSession,
        creator: User,
        name: str,
        grade_level: int,
        subject_name: str,
        description: Optional[str] = None
    ) -> Curriculum:
        curriculum = Curriculum(
            id=uuid.uuid4(),
            organization_id=creator.organization_id,
            created_by_id=creator.id,
            name=name,
            grade_level=grade_level,
            subject_name=subject_name,
            description=description
        )
        session.add(curriculum)
        await session.flush()

        # Create initial Version 1 in DRAFT state
        version = CurriculumVersion(
            id=uuid.uuid4(),
            curriculum_id=curriculum.id,
            version_number=1,
            status="DRAFT",
            created_by_id=creator.id,
            change_log="Initial curriculum draft created."
        )
        session.add(version)
        await session.commit()

        await AuditService.log_event(
            session=session,
            action="CURRICULUM_CREATED",
            resource_type="curriculum",
            actor_id=creator.id,
            organization_id=creator.organization_id,
            resource_id=str(curriculum.id),
            details={"name": name, "grade_level": grade_level, "subject": subject_name}
        )

        return await CurriculumService.get_curriculum_by_id(session, curriculum.id)

    @staticmethod
    async def get_curriculum_by_id(session: AsyncSession, curriculum_id: uuid.UUID) -> Optional[Curriculum]:
        result = await session.execute(
            select(Curriculum)
            .options(selectinload(Curriculum.versions))
            .where(Curriculum.id == curriculum_id)
        )
        return result.scalars().first()

    @staticmethod
    async def list_curricula(session: AsyncSession, organization_id: uuid.UUID) -> List[Curriculum]:
        result = await session.execute(
            select(Curriculum)
            .options(selectinload(Curriculum.versions))
            .where(Curriculum.organization_id == organization_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_version_by_id(session: AsyncSession, version_id: uuid.UUID) -> Optional[CurriculumVersion]:
        result = await session.execute(
            select(CurriculumVersion)
            .options(
                selectinload(CurriculumVersion.chapters)
                .selectinload(Chapter.topics)
                .selectinload(Topic.concepts)
                .selectinload(Concept.skills),
                selectinload(CurriculumVersion.chapters)
                .selectinload(Chapter.topics)
                .selectinload(Topic.concepts)
                .selectinload(Concept.learning_objectives)
            )
            .where(CurriculumVersion.id == version_id)
        )
        return result.scalars().first()

    @staticmethod
    async def create_new_version(
        session: AsyncSession,
        curriculum_id: uuid.UUID,
        creator: User,
        change_log: str
    ) -> CurriculumVersion:
        # Get highest existing version number
        res = await session.execute(
            select(CurriculumVersion)
            .where(CurriculumVersion.curriculum_id == curriculum_id)
            .order_by(CurriculumVersion.version_number.desc())
        )
        latest_ver = res.scalars().first()
        next_ver_num = (latest_ver.version_number + 1) if latest_ver else 1

        new_version = CurriculumVersion(
            id=uuid.uuid4(),
            curriculum_id=curriculum_id,
            version_number=next_ver_num,
            status="DRAFT",
            created_by_id=creator.id,
            change_log=change_log
        )
        session.add(new_version)
        await session.commit()
        await session.refresh(new_version)

        return new_version

    @staticmethod
    async def transition_version_status(
        session: AsyncSession,
        version_id: uuid.UUID,
        target_status: str,
        actor: User
    ) -> CurriculumVersion:
        version = await CurriculumService.get_version_by_id(session, version_id)
        if not version:
            raise ValueError("Curriculum version not found.")

        current_status = version.status
        user_roles = [ur.role.name for ur in actor.roles]

        # Valid transitions check
        valid_transitions = {
            "DRAFT": ["REVIEW"],
            "REVIEW": ["DRAFT", "APPROVED"],
            "APPROVED": ["PUBLISHED", "DRAFT"],
            "PUBLISHED": ["ARCHIVED"],
            "ARCHIVED": []
        }

        if target_status not in valid_transitions.get(current_status, []):
            raise ValueError(f"Invalid state transition from '{current_status}' to '{target_status}'.")

        # Authorization rules
        if target_status in ["APPROVED", "PUBLISHED"]:
            allowed_approvers = ["SuperAdmin", "OrgAdmin", "SchoolAdmin", "ContentManager", "Teacher"]
            if not any(r in user_roles for r in allowed_approvers):
                raise PermissionError(f"User role(s) unauthorized to set state to '{target_status}'.")

        if target_status == "APPROVED":
            version.approved_by_id = actor.id

        if target_status == "PUBLISHED":
            version.published_by_id = actor.id
            version.published_at = datetime.now(timezone.utc)
            await AuditService.log_event(
                session=session,
                action="CURRICULUM_PUBLISHED",
                resource_type="curriculum_version",
                actor_id=actor.id,
                organization_id=actor.organization_id,
                resource_id=str(version.id),
                details={"version_number": version.version_number}
            )

        version.status = target_status
        await session.commit()
        return version

    # Immutability Guard Helper
    @staticmethod
    def _assert_mutable(version: CurriculumVersion):
        if version.status in ["PUBLISHED", "ARCHIVED"]:
            raise ValueError(f"Cannot modify a {version.status} curriculum version. Changes require a new DRAFT version.")

    # Hierarchy Builders
    @staticmethod
    async def create_chapter(
        session: AsyncSession,
        version_id: uuid.UUID,
        name: str,
        description: Optional[str] = None,
        sequence_order: int = 1,
        source_document_id: Optional[uuid.UUID] = None,
        source_page: Optional[int] = None,
        source_section: Optional[str] = None,
        source_chunk_id: Optional[str] = None
    ) -> Chapter:
        version = await CurriculumService.get_version_by_id(session, version_id)
        if not version:
            raise ValueError("Curriculum version not found.")
        CurriculumService._assert_mutable(version)

        chapter = Chapter(
            id=uuid.uuid4(),
            curriculum_version_id=version_id,
            name=name,
            description=description,
            sequence_order=sequence_order,
            source_document_id=source_document_id,
            source_page=source_page,
            source_section=source_section,
            source_chunk_id=source_chunk_id
        )
        session.add(chapter)
        await session.commit()
        await session.refresh(chapter)
        return chapter

    @staticmethod
    async def create_topic(
        session: AsyncSession,
        chapter_id: uuid.UUID,
        name: str,
        description: Optional[str] = None,
        sequence_order: int = 1,
        source_document_id: Optional[uuid.UUID] = None,
        source_page: Optional[int] = None,
        source_section: Optional[str] = None,
        source_chunk_id: Optional[str] = None
    ) -> Topic:
        chapter_res = await session.execute(select(Chapter).where(Chapter.id == chapter_id))
        chapter = chapter_res.scalars().first()
        if not chapter:
            raise ValueError("Chapter not found.")

        version = await CurriculumService.get_version_by_id(session, chapter.curriculum_version_id)
        CurriculumService._assert_mutable(version)

        topic = Topic(
            id=uuid.uuid4(),
            chapter_id=chapter_id,
            name=name,
            description=description,
            sequence_order=sequence_order,
            source_document_id=source_document_id,
            source_page=source_page,
            source_section=source_section,
            source_chunk_id=source_chunk_id
        )
        session.add(topic)
        await session.commit()
        await session.refresh(topic)
        return topic

    @staticmethod
    async def create_concept(
        session: AsyncSession,
        topic_id: uuid.UUID,
        name: str,
        description: Optional[str] = None,
        difficulty_level: int = 3,
        sequence_order: int = 1,
        source_document_id: Optional[uuid.UUID] = None,
        source_page: Optional[int] = None,
        source_section: Optional[str] = None,
        source_chunk_id: Optional[str] = None
    ) -> Concept:
        topic_res = await session.execute(select(Topic).where(Topic.id == topic_id))
        topic = topic_res.scalars().first()
        if not topic:
            raise ValueError("Topic not found.")

        chapter_res = await session.execute(select(Chapter).where(Chapter.id == topic.chapter_id))
        chapter = chapter_res.scalars().first()

        version = await CurriculumService.get_version_by_id(session, chapter.curriculum_version_id)
        CurriculumService._assert_mutable(version)

        concept = Concept(
            id=uuid.uuid4(),
            topic_id=topic_id,
            name=name,
            description=description,
            difficulty_level=difficulty_level,
            sequence_order=sequence_order,
            source_document_id=source_document_id,
            source_page=source_page,
            source_section=source_section,
            source_chunk_id=source_chunk_id
        )
        session.add(concept)
        await session.commit()
        await session.refresh(concept)
        return concept

    @staticmethod
    async def create_learning_objective(
        session: AsyncSession,
        concept_id: uuid.UUID,
        code: str,
        description: str,
        bloom_taxonomy_level: str = "Understand",
        source_document_id: Optional[uuid.UUID] = None,
        source_page: Optional[int] = None,
        source_section: Optional[str] = None,
        source_chunk_id: Optional[str] = None
    ) -> LearningObjective:
        concept_res = await session.execute(select(Concept).where(Concept.id == concept_id))
        concept = concept_res.scalars().first()
        if not concept:
            raise ValueError("Concept not found.")

        topic_res = await session.execute(select(Topic).where(Topic.id == concept.topic_id))
        topic = topic_res.scalars().first()
        chapter_res = await session.execute(select(Chapter).where(Chapter.id == topic.chapter_id))
        chapter = chapter_res.scalars().first()
        version = await CurriculumService.get_version_by_id(session, chapter.curriculum_version_id)
        CurriculumService._assert_mutable(version)

        lo = LearningObjective(
            id=uuid.uuid4(),
            concept_id=concept_id,
            code=code,
            description=description,
            bloom_taxonomy_level=bloom_taxonomy_level,
            source_document_id=source_document_id,
            source_page=source_page,
            source_section=source_section,
            source_chunk_id=source_chunk_id
        )
        session.add(lo)
        await session.commit()
        await session.refresh(lo)
        return lo
