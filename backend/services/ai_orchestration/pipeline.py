import uuid
import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.models.curriculum import (
    SourceDocument,
    DocumentChunk,
    Curriculum,
    CurriculumVersion,
    Chapter,
    Topic,
    Concept,
    Skill,
    LearningObjective
)
from backend.models.user import User
from backend.services.ai_orchestration.prompt_manager import PromptRegistry
from backend.services.ai_orchestration.contracts import AIRequest
from backend.services.ai_orchestration.model_router import ModelRouter
from backend.services.ai_orchestration.validator import OutputValidator
from backend.services.curriculum_service.service import CurriculumService
from backend.services.audit_service import AuditService

logger = logging.getLogger(__name__)

class CurriculumExtractionPipeline:
    @staticmethod
    async def extract_from_document(
        session: AsyncSession,
        document_id: uuid.UUID,
        curriculum_id: uuid.UUID,
        actor: User,
        provider: str = "mock"
    ) -> CurriculumVersion:
        # 1. Fetch document and chunks
        doc_res = await session.execute(select(SourceDocument).where(SourceDocument.id == document_id))
        doc = doc_res.scalars().first()
        if not doc:
            raise ValueError(f"Source document {document_id} not found.")

        chunks_res = await session.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        )
        chunks = chunks_res.scalars().all()
        if not chunks:
            raise ValueError(f"Document {document_id} has no extracted text chunks. Ingestion required first.")

        document_text = "\n\n".join([f"[Page {c.page_number} | {c.section or 'Section'}]: {c.text}" for c in chunks])

        # 2. Build Prompts
        system_prompt = PromptRegistry.CURRICULUM_EXTRACTION_SYSTEM_PROMPT
        user_prompt = PromptRegistry.build_curriculum_extraction_user_prompt(document_text)

        request = AIRequest(
            task_type="CURRICULUM_EXTRACTION",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.1
        )

        # 3. Execute LLM Task
        ai_response = await ModelRouter.execute_task(
            session=session,
            request=request,
            organization_id=actor.organization_id,
            user_id=actor.id,
            preferred_provider=provider,
            prompt_version="v2.0.0"
        )

        extracted_data = ai_response.content_json or {}

        # 4. Run 6-Step Validation Pipeline
        is_valid, validation_errors = OutputValidator.validate_extraction_output(extracted_data)

        # 5. Create new CurriculumVersion in DRAFT / REVIEW state (NEVER PUBLISHED)
        new_version = await CurriculumService.create_new_version(
            session=session,
            curriculum_id=curriculum_id,
            creator=actor,
            change_log=f"AI Extracted proposed version from '{doc.file_name}'. Validation: {'PASSED' if is_valid else 'FAILED'}"
        )

        new_version.status = "REVIEW" if is_valid else "DRAFT"
        new_version.metadata_json = {
            "source_document_id": str(document_id),
            "ai_extracted": True,
            "provider": ai_response.provider,
            "model": ai_response.model,
            "validation_passed": is_valid,
            "validation_errors": validation_errors,
            "token_cost": ai_response.cost_usd
        }

        # 6. Populate proposed hierarchy tree nodes into version
        if is_valid and "chapters" in extracted_data:
            for ch_data in extracted_data["chapters"]:
                ch = await CurriculumService.create_chapter(
                    session=session,
                    version_id=new_version.id,
                    name=ch_data["name"],
                    description=ch_data.get("description"),
                    sequence_order=ch_data.get("sequence_order", 1),
                    source_document_id=doc.id,
                    source_page=ch_data.get("source_page"),
                    source_section=ch_data.get("source_section")
                )

                for tp_data in ch_data.get("topics", []):
                    tp = await CurriculumService.create_topic(
                        session=session,
                        chapter_id=ch.id,
                        name=tp_data["name"],
                        description=tp_data.get("description"),
                        sequence_order=tp_data.get("sequence_order", 1),
                        source_document_id=doc.id,
                        source_page=tp_data.get("source_page"),
                        source_section=tp_data.get("source_section")
                    )

                    for cp_data in tp_data.get("concepts", []):
                        cp = await CurriculumService.create_concept(
                            session=session,
                            topic_id=tp.id,
                            name=cp_data["name"],
                            description=cp_data.get("description"),
                            difficulty_level=cp_data.get("difficulty_level", 3),
                            sequence_order=cp_data.get("sequence_order", 1),
                            source_document_id=doc.id,
                            source_page=cp_data.get("source_page"),
                            source_section=cp_data.get("source_section")
                        )

                        for sk_name in cp_data.get("skills", []):
                            sk = Skill(id=uuid.uuid4(), concept_id=cp.id, name=sk_name)
                            session.add(sk)

                        for lo_data in cp_data.get("learning_objectives", []):
                            await CurriculumService.create_learning_objective(
                                session=session,
                                concept_id=cp.id,
                                code=lo_data["code"],
                                description=lo_data["description"],
                                bloom_taxonomy_level=lo_data.get("bloom_taxonomy_level", "Understand"),
                                source_document_id=doc.id,
                                source_page=lo_data.get("source_page"),
                                source_section=lo_data.get("source_section")
                            )

        await session.commit()

        await AuditService.log_event(
            session=session,
            action="CURRICULUM_AI_EXTRACTION_COMPLETED",
            resource_type="curriculum_version",
            actor_id=actor.id,
            organization_id=actor.organization_id,
            resource_id=str(new_version.id),
            details={"document_id": str(document_id), "validation_passed": is_valid}
        )

        return new_version
