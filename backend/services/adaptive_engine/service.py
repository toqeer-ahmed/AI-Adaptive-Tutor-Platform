import uuid
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.models.curriculum import ConceptPrerequisite, Concept
from backend.models.mastery import StudentMastery
from backend.models.user import User
from backend.services.mastery_service.service import MasteryService
from backend.services.adaptive_engine.engine import AdaptiveDecisionEngine, AdaptiveContext, AdaptiveDecision

class AdaptiveLearningService:
    @staticmethod
    async def get_next_learning_decision(
        session: AsyncSession,
        student: User,
        concept_id: uuid.UUID,
        curriculum_version_id: uuid.UUID
    ) -> AdaptiveDecision:
        # 1. Fetch student concept mastery
        sm = await MasteryService.get_or_create_mastery(
            session=session,
            organization_id=student.organization_id,
            student_id=student.id,
            concept_id=concept_id,
            curriculum_version_id=curriculum_version_id
        )

        # 2. Fetch prerequisite concepts
        prereq_res = await session.execute(
            select(ConceptPrerequisite)
            .where(ConceptPrerequisite.concept_id == concept_id)
        )
        prereqs = prereq_res.scalars().all()

        prereq_masteries: Dict[str, float] = {}
        for p in prereqs:
            p_sm = await MasteryService.get_or_create_mastery(
                session=session,
                organization_id=student.organization_id,
                student_id=student.id,
                concept_id=p.prerequisite_concept_id,
                curriculum_version_id=curriculum_version_id
            )
            prereq_masteries[str(p.prerequisite_concept_id)] = p_sm.mastery_score

        # 3. Assemble Adaptive Context
        ctx = AdaptiveContext(
            student_id=student.id,
            concept_id=concept_id,
            curriculum_version_id=curriculum_version_id,
            mastery_score=sm.mastery_score,
            confidence=sm.confidence,
            attempt_count=sm.attempt_count,
            misconceptions=sm.misconception_tags or [],
            prerequisite_masteries=prereq_masteries,
            recent_performance=sm.recent_performance or [],
            next_review_due_at=sm.next_review_due_at
        )

        # 4. Make 100% Deterministic Decision (Zero LLM calls)
        return AdaptiveDecisionEngine.make_decision(ctx)
