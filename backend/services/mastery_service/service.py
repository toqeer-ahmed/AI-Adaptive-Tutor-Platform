import uuid
from datetime import datetime, timezone
from typing import Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.models.mastery import StudentMastery, MasteryHistoryLog
from backend.services.mastery_service.policy import MasteryEvent, MasteryUpdate, MasteryPolicyV1
from backend.services.audit_service import AuditService

def to_uuid(val):
    if isinstance(val, uuid.UUID):
        return val
    if isinstance(val, str):
        return uuid.UUID(val)
    if isinstance(val, int):
        return uuid.UUID(int=val)
    return uuid.UUID("00000000-0000-0000-0000-000000000000")

class MasteryService:
    @staticmethod
    async def get_or_create_mastery(
        session: AsyncSession,
        organization_id: Any,
        student_id: Any,
        concept_id: Any,
        curriculum_version_id: Any
    ) -> StudentMastery:
        org_uuid = to_uuid(organization_id)
        stud_uuid = to_uuid(student_id)
        conc_uuid = to_uuid(concept_id)
        curr_ver_uuid = to_uuid(curriculum_version_id)

        stmt = select(StudentMastery).where(
            StudentMastery.student_id == stud_uuid,
            StudentMastery.concept_id == conc_uuid,
            StudentMastery.curriculum_version_id == curr_ver_uuid
        )
        res = await session.execute(stmt)
        sm = res.scalars().first()

        if not sm:
            sm = StudentMastery(
                id=uuid.uuid4(),
                organization_id=org_uuid,
                student_id=stud_uuid,
                concept_id=conc_uuid,
                curriculum_version_id=curr_ver_uuid,
                mastery_score=0.0,
                confidence=0.0,
                attempt_count=0,
                correct_count=0,
                incorrect_count=0,
                recent_performance=[],
                historical_performance=[],
                status="NOT_STARTED"
            )
            session.add(sm)
            await session.flush()

        return sm

    @staticmethod
    async def record_learning_event(
        session: AsyncSession,
        organization_id: uuid.UUID,
        event: MasteryEvent
    ) -> StudentMastery:
        """
        Processes a student learning event deterministically via MasteryPolicyV1
        and logs reproducible audit history.
        """
        sm = await MasteryService.get_or_create_mastery(
            session=session,
            organization_id=organization_id,
            student_id=event.student_id,
            concept_id=event.concept_id,
            curriculum_version_id=event.curriculum_version_id
        )

        prev_mastery = sm.mastery_score
        prev_status = sm.status

        # Execute deterministic policy update
        update = MasteryPolicyV1.calculate_update(
            current_mastery=sm.mastery_score,
            current_confidence=sm.confidence,
            current_attempt_count=sm.attempt_count,
            current_correct_count=sm.correct_count,
            current_incorrect_count=sm.incorrect_count,
            recent_performance=sm.recent_performance or [],
            event=event
        )

        # Apply update
        sm.mastery_score = update.new_mastery_score
        sm.confidence = update.new_confidence
        sm.status = update.new_status
        sm.attempt_count = update.attempt_count
        sm.correct_count = update.correct_count
        sm.incorrect_count = update.incorrect_count
        sm.recent_performance = update.recent_performance
        sm.last_difficulty = event.item_difficulty
        sm.last_practiced_at = datetime.now(timezone.utc)
        sm.next_review_due_at = update.next_review_due_at

        # Append to historical performance log
        hist = list(sm.historical_performance or [])
        hist.append({
            "is_correct": event.is_correct,
            "mastery_after": update.new_mastery_score,
            "timestamp": sm.last_practiced_at.isoformat()
        })
        sm.historical_performance = hist

        # Log reproducible audit record
        log_entry = MasteryHistoryLog(
            id=uuid.uuid4(),
            student_mastery_id=sm.id,
            student_id=event.student_id,
            concept_id=event.concept_id,
            curriculum_version_id=event.curriculum_version_id,
            policy_version=MasteryPolicyV1.POLICY_VERSION,
            event_type="ASSESSMENT_ATTEMPT",
            is_correct=event.is_correct,
            item_difficulty=event.item_difficulty,
            previous_mastery=prev_mastery,
            new_mastery=update.new_mastery_score,
            previous_status=prev_status,
            new_status=update.new_status
        )
        session.add(log_entry)
        await session.commit()

        return sm
