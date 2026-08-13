import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.models.assessment import (
    QuestionBankItem,
    Assessment,
    AssessmentQuestion,
    AssessmentAttempt,
    StudentAnswer
)
from backend.models.user import User
from backend.services.assessment_service.evaluator import DeterministicMathEvaluator
from backend.services.audit_service import AuditService

class AssessmentService:
    @staticmethod
    async def approve_question(session: AsyncSession, question_id: uuid.UUID, actor: User) -> QuestionBankItem:
        q_res = await session.execute(select(QuestionBankItem).where(QuestionBankItem.id == question_id))
        q = q_res.scalars().first()
        if not q:
            raise ValueError("Question not found.")

        q.validation_status = "APPROVED"
        await session.commit()
        return q

    @staticmethod
    async def reject_question(session: AsyncSession, question_id: uuid.UUID, actor: User) -> QuestionBankItem:
        q_res = await session.execute(select(QuestionBankItem).where(QuestionBankItem.id == question_id))
        q = q_res.scalars().first()
        if not q:
            raise ValueError("Question not found.")

        q.validation_status = "REJECTED"
        await session.commit()
        return q

    @staticmethod
    async def create_assessment(
        session: AsyncSession,
        creator: User,
        title: str,
        class_id: Optional[uuid.UUID],
        question_ids: List[uuid.UUID],
        description: Optional[str] = None,
        assessment_type: str = "QUIZ",
        max_attempts: int = 1,
        due_at: Optional[datetime] = None
    ) -> Assessment:
        assessment = Assessment(
            id=uuid.uuid4(),
            organization_id=creator.organization_id,
            school_id=creator.school_id,
            class_id=class_id,
            created_by_id=creator.id,
            title=title,
            description=description,
            assessment_type=assessment_type,
            max_attempts=max_attempts,
            due_at=due_at,
            is_published=True
        )
        session.add(assessment)
        await session.flush()

        # Attach questions
        for idx, q_id in enumerate(question_ids, 1):
            aq = AssessmentQuestion(
                id=uuid.uuid4(),
                assessment_id=assessment.id,
                question_id=q_id,
                sequence_order=idx,
                points=1.0
            )
            session.add(aq)

        await session.commit()
        await session.refresh(assessment)

        await AuditService.log_event(
            session=session,
            action="ASSESSMENT_CREATED",
            resource_type="assessment",
            actor_id=creator.id,
            organization_id=creator.organization_id,
            resource_id=str(assessment.id),
            details={"title": title, "question_count": len(question_ids)}
        )

        return assessment

    @staticmethod
    async def start_attempt(session: AsyncSession, assessment_id: uuid.UUID, student: User) -> AssessmentAttempt:
        ass_res = await session.execute(select(Assessment).where(Assessment.id == assessment_id))
        ass = ass_res.scalars().first()
        if not ass:
            raise ValueError("Assessment not found.")

        # Check existing attempts
        att_res = await session.execute(
            select(AssessmentAttempt)
            .where(AssessmentAttempt.assessment_id == assessment_id, AssessmentAttempt.student_id == student.id)
        )
        existing = att_res.scalars().all()
        if len(existing) >= ass.max_attempts:
            raise ValueError(f"Maximum attempt limit ({ass.max_attempts}) reached for this assessment.")

        attempt = AssessmentAttempt(
            id=uuid.uuid4(),
            assessment_id=assessment_id,
            student_id=student.id,
            attempt_number=len(existing) + 1,
            status="IN_PROGRESS"
        )
        session.add(attempt)
        await session.commit()
        return attempt

    @staticmethod
    async def submit_answer(
        session: AsyncSession,
        attempt_id: uuid.UUID,
        question_id: uuid.UUID,
        submitted_answer: Any
    ) -> StudentAnswer:
        att_res = await session.execute(select(AssessmentAttempt).where(AssessmentAttempt.id == attempt_id))
        attempt = att_res.scalars().first()
        if not attempt or attempt.status != "IN_PROGRESS":
            raise ValueError("Attempt is not active.")

        q_res = await session.execute(select(QuestionBankItem).where(QuestionBankItem.id == question_id))
        question = q_res.scalars().first()
        if not question:
            raise ValueError("Question not found.")

        # Deterministic Evaluation
        is_correct, pts_mult, feedback = DeterministicMathEvaluator.evaluate_question(
            question_type=question.question_type,
            submitted_answer=submitted_answer,
            correct_answer=question.correct_answer_json
        )

        # Check if existing answer
        ans_res = await session.execute(
            select(StudentAnswer)
            .where(StudentAnswer.attempt_id == attempt_id, StudentAnswer.question_id == question_id)
        )
        answer = ans_res.scalars().first()

        if not answer:
            answer = StudentAnswer(
                id=uuid.uuid4(),
                attempt_id=attempt_id,
                question_id=question_id,
                submitted_answer_json=submitted_answer,
                is_correct=is_correct,
                points_awarded=pts_mult,
                feedback=feedback
            )
            session.add(answer)
        else:
            answer.submitted_answer_json = submitted_answer
            answer.is_correct = is_correct
            answer.points_awarded = pts_mult
            answer.feedback = feedback

        await session.commit()
        return answer

    @staticmethod
    async def submit_attempt(session: AsyncSession, attempt_id: uuid.UUID) -> AssessmentAttempt:
        att_res = await session.execute(
            select(AssessmentAttempt)
            .options(
                selectinload(AssessmentAttempt.answers),
                selectinload(AssessmentAttempt.assessment).selectinload(Assessment.questions)
            )
            .where(AssessmentAttempt.id == attempt_id)
        )
        attempt = att_res.scalars().first()
        if not attempt:
            raise ValueError("Attempt not found.")

        # Calculate final score deterministically
        total_score = sum(ans.points_awarded for ans in attempt.answers if ans.points_awarded is not None)
        max_score = float(len(attempt.assessment.questions))

        attempt.score = total_score
        attempt.max_score = max_score
        attempt.status = "GRADED"
        attempt.submitted_at = datetime.now(timezone.utc)

        await session.commit()
        return attempt

    @staticmethod
    async def teacher_override_score(
        session: AsyncSession,
        answer_id: uuid.UUID,
        teacher: User,
        new_points: float,
        feedback: Optional[str] = None
    ) -> StudentAnswer:
        ans_res = await session.execute(select(StudentAnswer).where(StudentAnswer.id == answer_id))
        answer = ans_res.scalars().first()
        if not answer:
            raise ValueError("Student answer record not found.")

        old_points = answer.points_awarded
        answer.points_awarded = new_points
        answer.teacher_override = True
        if feedback:
            answer.feedback = feedback

        await session.commit()

        await AuditService.log_event(
            session=session,
            action="GRADE_OVERRIDDEN",
            resource_type="student_answer",
            actor_id=teacher.id,
            organization_id=teacher.organization_id,
            resource_id=str(answer_id),
            details={"old_points": old_points, "new_points": new_points, "reason": feedback}
        )

        return answer
