import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.models.curriculum import CurriculumVersion, Chapter, Topic, Concept, LearningObjective
from backend.models.rag import CurriculumVectorEmbeddings
from backend.services.rag_service.embedding import EmbeddingProvider, MockEmbeddingProvider

class CurriculumVectorIndexer:
    @staticmethod
    async def index_curriculum_version(
        session: AsyncSession,
        version_id: uuid.UUID,
        embedding_provider: Optional[EmbeddingProvider] = None
    ) -> int:
        if embedding_provider is None:
            embedding_provider = MockEmbeddingProvider()

        # Fetch version with full tree
        stmt = (
            select(CurriculumVersion)
            .options(
                selectinload(CurriculumVersion.curriculum),
                selectinload(CurriculumVersion.chapters)
                .selectinload(Chapter.topics)
                .selectinload(Topic.concepts)
                .selectinload(Concept.learning_objectives)
            )
            .where(CurriculumVersion.id == version_id)
        )
        res = await session.execute(stmt)
        version = res.scalars().first()
        if not version:
            raise ValueError("Curriculum version not found.")

        meta = embedding_provider.get_metadata()
        indexed_count = 0

        # Iterate tree nodes
        for ch in version.chapters:
            for tp in ch.topics:
                for cp in tp.concepts:
                    # Construct text for embedding
                    lo_texts = [f"Objective [{lo.code}]: {lo.description}" for lo in cp.learning_objectives]
                    full_text = f"Chapter: {ch.name}. Topic: {tp.name}. Concept: {cp.name} - {cp.description or ''}. {' '.join(lo_texts)}"

                    vector = await embedding_provider.generate_embedding(full_text)

                    # Delete existing vector for this concept if re-indexing
                    existing = await session.execute(
                        select(CurriculumVectorEmbeddings).where(
                            CurriculumVectorEmbeddings.curriculum_version_id == version.id,
                            CurriculumVectorEmbeddings.concept == cp.name
                        )
                    )
                    for old_v in existing.scalars().all():
                        await session.delete(old_v)

                    vec_record = CurriculumVectorEmbeddings(
                        id=uuid.uuid4(),
                        organization_id=version.curriculum.organization_id,
                        curriculum_id=version.curriculum.id,
                        curriculum_version_id=version.id,
                        grade=version.curriculum.grade_level,
                        subject=version.curriculum.subject_name,
                        chapter=ch.name,
                        topic=tp.name,
                        concept=cp.name,
                        learning_objective=cp.learning_objectives[0].code if cp.learning_objectives else None,
                        document_id=cp.source_document_id or ch.source_document_id,
                        page_number=cp.source_page or ch.source_page,
                        section=cp.source_section or ch.source_section,
                        text_content=full_text,
                        approval_status=version.status, # PUBLISHED, DRAFT, ARCHIVED
                        embedding_model=meta["embedding_model"],
                        embedding_dimension=meta["embedding_dimension"],
                        embedding_version=meta["embedding_version"],
                        embedding_vector=vector
                    )
                    session.add(vec_record)
                    indexed_count += 1

        await session.commit()
        return indexed_count
