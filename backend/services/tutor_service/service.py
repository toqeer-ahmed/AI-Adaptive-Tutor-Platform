import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.models.tutor import TutorSession, TutorTurn
from backend.models.curriculum import Concept
from backend.models.user import User
from backend.services.adaptive_engine.service import AdaptiveLearningService
from backend.services.rag_service.retrieval import HybridRAGRetrievalEngine
from backend.services.rag_service.context_builder import ContextBuilder
from backend.services.tutor_service.prompts import TutorPromptRegistry
from backend.services.tutor_service.validator import TutorOutputValidator
from backend.services.ai_orchestration.contracts import AIRequest
from backend.services.ai_orchestration.model_router import ModelRouter
from backend.services.audit_service import AuditService

class TutorService:
    @staticmethod
    async def create_session(
        session: AsyncSession,
        student: User,
        concept_id: uuid.UUID,
        curriculum_version_id: uuid.UUID,
        initial_mode: str = "explanation"
    ) -> TutorSession:
        tutor_session = TutorSession(
            id=uuid.uuid4(),
            organization_id=student.organization_id,
            student_id=student.id,
            concept_id=concept_id,
            curriculum_version_id=curriculum_version_id,
            current_mode=initial_mode,
            is_active=True
        )
        session.add(tutor_session)
        await session.commit()
        await session.refresh(tutor_session)
        return tutor_session

    @staticmethod
    async def execute_turn(
        session: AsyncSession,
        session_id: uuid.UUID,
        student: User,
        student_message: str,
        override_mode: Optional[str] = None,
        provider: str = "mock"
    ) -> TutorTurn:
        # Fetch Session
        ts_res = await session.execute(
            select(TutorSession)
            .options(selectinload(TutorSession.turns))
            .where(TutorSession.id == session_id, TutorSession.organization_id == student.organization_id)
        )
        ts = ts_res.scalars().first()
        if not ts:
            raise ValueError("Tutor session not found or forbidden.")

        # 1. Evaluate Adaptive Learning Engine (Determines WHAT activity/mode is needed)
        adaptive_decision = await AdaptiveLearningService.get_next_learning_decision(
            session=session,
            student=student,
            concept_id=ts.concept_id,
            curriculum_version_id=ts.curriculum_version_id
        )

        mode = override_mode or ts.current_mode or "explanation"

        # 2. Retrieve Approved Curriculum Context via RAG (Strict Tenant Isolation)
        cp_res = await session.execute(select(Concept).where(Concept.id == ts.concept_id))
        concept = cp_res.scalars().first()
        concept_name = concept.name if concept else "General"

        rag_result = await HybridRAGRetrievalEngine.retrieve_relevant_chunks(
            session=session,
            query_text=student_message,
            organization_id=student.organization_id
        )

        rag_context_text = ContextBuilder.build_rag_prompt_context(rag_result)

        # 3. Assemble Prompts
        system_prompt = TutorPromptRegistry.SYSTEM_PROMPT_TEMPLATE.format(
            grade=6,
            subject="Mathematics",
            mode=mode,
            retrieved_curriculum=rag_context_text
        )

        user_prompt = TutorPromptRegistry.build_user_message(
            student_message=student_message,
            concept_name=concept_name,
            mastery_status=adaptive_decision.decision
        )

        # 4. Execute AI Completion
        ai_req = AIRequest(
            task_type="TUTOR_TURN",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3
        )

        ai_resp = await ModelRouter.execute_task(
            session=session,
            request=ai_req,
            organization_id=student.organization_id,
            user_id=student.id,
            preferred_provider=provider
        )

        tutor_raw_response = ai_resp.content_text

        # 5. Output & Safety Validation
        is_safe, fail_reason = TutorOutputValidator.validate_tutor_turn(
            student_message=student_message,
            tutor_response=tutor_raw_response,
            has_rag_context=rag_result.get("has_context", False)
        )

        if not is_safe:
            tutor_final_response = f"I am sorry, but I cannot process that request: {fail_reason}"
        else:
            tutor_final_response = tutor_raw_response

        # 6. Record Turn Record
        sources_cited = rag_result.get("chunks", [])

        turn = TutorTurn(
            id=uuid.uuid4(),
            session_id=ts.id,
            student_message=student_message,
            tutor_response=tutor_final_response,
            mode=mode,
            sources_cited=sources_cited,
            token_usage={
                "prompt_tokens": ai_resp.prompt_tokens,
                "completion_tokens": ai_resp.completion_tokens,
                "total_tokens": ai_resp.total_tokens,
                "cost_usd": ai_resp.cost_usd
            }
        )
        session.add(turn)
        await session.commit()

        await AuditService.log_event(
            session=session,
            action="TUTOR_TURN_EXECUTED",
            resource_type="tutor_session",
            actor_id=student.id,
            organization_id=student.organization_id,
            resource_id=str(ts.id),
            details={"mode": mode, "is_safe": is_safe}
        )

        return turn
