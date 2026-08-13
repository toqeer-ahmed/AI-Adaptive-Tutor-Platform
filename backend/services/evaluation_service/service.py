import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.models.assessment import QuestionBankItem, StudentAnswer, AssessmentAttempt
from backend.models.evaluation import SubjectiveEvaluationLog
from backend.models.user import User
from backend.services.ai_orchestration.contracts import AIRequest
from backend.services.ai_orchestration.model_router import ModelRouter
from backend.services.audit_service import AuditService

class SubjectiveEvaluationProposal(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    rubric_criteria_scores: Dict[str, float] = Field(default_factory=dict)
    evidence_quotes: List[str] = Field(default_factory=list)
    feedback: str
    confidence: float = Field(ge=0.0, le=1.0)
    detected_misconceptions: List[str] = Field(default_factory=list)

class SubjectiveEvaluationService:
    HIGH_CONFIDENCE_THRESHOLD = 0.85

    @staticmethod
    async def evaluate_subjective_answer(
        session: AsyncSession,
        answer_id: uuid.UUID,
        actor: User,
        provider: str = "mock"
    ) -> StudentAnswer:
        stmt = (
            select(StudentAnswer)
            .options(selectinload(StudentAnswer.question))
            .where(StudentAnswer.id == answer_id)
        )
        res = await session.execute(stmt)
        answer = res.scalars().first()
        if not answer:
            raise ValueError("Student answer record not found.")

        question = answer.question
        submitted_text = str(answer.submitted_answer_json)
        rubric = question.rubric_json or {"criteria": "Clear mathematical explanation and steps shown."}

        system_prompt = f"""
You are an expert educational rubric evaluator for Grade 4-8 mathematics and science.
Evaluate the student's short/long-answer submission against the question prompt and rubric.

Question: {question.question_text}
Rubric: {rubric}
Expected Answer: {question.correct_answer_json}

Return strict JSON:
{{
  "score": 0.90,
  "rubric_criteria_scores": {{"clarity": 1.0, "accuracy": 0.8}},
  "evidence_quotes": ["student explained common denominator correctly"],
  "feedback": "Great explanation of why common denominators are needed!",
  "confidence": 0.92,
  "detected_misconceptions": []
}}
"""

        ai_req = AIRequest(
            task_type="SUBJECTIVE_EVALUATION",
            system_prompt=system_prompt,
            user_prompt=f"Student Answer: '{submitted_text}'",
            temperature=0.1
        )

        ai_resp = await ModelRouter.execute_task(
            session=session,
            request=ai_req,
            organization_id=actor.organization_id,
            user_id=actor.id,
            preferred_provider=provider
        )

        resp_json = ai_resp.content_json or {}
        proposal = SubjectiveEvaluationProposal(
            score=float(resp_json.get("score", 0.85)),
            rubric_criteria_scores=resp_json.get("rubric_criteria_scores", {"accuracy": 0.85}),
            evidence_quotes=resp_json.get("evidence_quotes", []),
            feedback=resp_json.get("feedback", "Good effort in explaining the steps."),
            confidence=float(resp_json.get("confidence", 0.90)),
            detected_misconceptions=resp_json.get("detected_misconceptions", [])
        )

        # Store AI evaluation proposal in database for auditability
        answer.ai_evaluation_json = proposal.model_dump()

        # Save SubjectiveEvaluationLog record
        ai_log = SubjectiveEvaluationLog(
            id=uuid.uuid4(),
            answer_id=answer.id,
            evaluator_type="AI_PROPOSAL",
            actor_id=None,
            score_proposed=proposal.score,
            score_final=proposal.score,
            rubric_json=proposal.rubric_criteria_scores,
            feedback=proposal.feedback,
            confidence=proposal.confidence
        )
        session.add(ai_log)

        # TEACHER REVIEW POLICY ENGINE
        # Short answers with high confidence (>= 0.85) -> AUTOGRADED
        # Low confidence (< 0.85) OR scenario/long-answer -> NEEDS_TEACHER_REVIEW
        is_short_answer = question.question_type == "short_answer"
        if is_short_answer and proposal.confidence >= SubjectiveEvaluationService.HIGH_CONFIDENCE_THRESHOLD:
            answer.evaluation_status = "AUTOGRADED"
            answer.points_awarded = proposal.score
            answer.is_correct = proposal.score >= 0.70
            answer.feedback = proposal.feedback
        else:
            answer.evaluation_status = "NEEDS_TEACHER_REVIEW"
            answer.points_awarded = None  # Grade pending teacher confirmation
            answer.feedback = "AI evaluation completed; pending teacher review."

        await session.commit()
        await session.refresh(answer)

        return answer

    @staticmethod
    async def teacher_review_accept(
        session: AsyncSession,
        answer_id: uuid.UUID,
        teacher: User
    ) -> StudentAnswer:
        stmt = (
            select(StudentAnswer)
            .options(selectinload(StudentAnswer.question))
            .where(StudentAnswer.id == answer_id)
        )
        res = await session.execute(stmt)
        answer = res.scalars().first()
        if not answer or not answer.ai_evaluation_json:
            raise ValueError("Student answer or AI evaluation proposal not found.")

        ai_proposal = answer.ai_evaluation_json
        proposed_score = float(ai_proposal.get("score", 1.0))
        feedback = ai_proposal.get("feedback", "Teacher approved evaluation.")

        answer.points_awarded = proposed_score
        answer.is_correct = proposed_score >= 0.70
        answer.feedback = feedback
        answer.evaluation_status = "TEACHER_APPROVED"

        log_item = SubjectiveEvaluationLog(
            id=uuid.uuid4(),
            answer_id=answer.id,
            evaluator_type="TEACHER_ACCEPT",
            actor_id=teacher.id,
            score_proposed=proposed_score,
            score_final=proposed_score,
            rubric_json=ai_proposal.get("rubric_criteria_scores", {}),
            feedback=feedback,
            confidence=1.0
        )
        session.add(log_item)
        await session.commit()

        await AuditService.log_event(
            session=session,
            action="SUBJECTIVE_GRADE_APPROVED",
            resource_type="student_answer",
            actor_id=teacher.id,
            organization_id=teacher.organization_id,
            resource_id=str(answer.id),
            details={"approved_score": proposed_score}
        )

        return answer

    @staticmethod
    async def teacher_review_override(
        session: AsyncSession,
        answer_id: uuid.UUID,
        teacher: User,
        new_score: float,
        feedback: str
    ) -> StudentAnswer:
        stmt = (
            select(StudentAnswer)
            .options(selectinload(StudentAnswer.question))
            .where(StudentAnswer.id == answer_id)
        )
        res = await session.execute(stmt)
        answer = res.scalars().first()
        if not answer:
            raise ValueError("Student answer record not found.")

        ai_proposal = answer.ai_evaluation_json or {}
        old_proposed_score = float(ai_proposal.get("score", answer.points_awarded or 0.0))

        answer.points_awarded = new_score
        answer.is_correct = new_score >= 0.70
        answer.feedback = feedback
        answer.teacher_override = True
        answer.evaluation_status = "TEACHER_OVERRIDDEN"

        log_item = SubjectiveEvaluationLog(
            id=uuid.uuid4(),
            answer_id=answer.id,
            evaluator_type="TEACHER_OVERRIDE",
            actor_id=teacher.id,
            score_proposed=old_proposed_score,
            score_final=new_score,
            rubric_json=ai_proposal.get("rubric_criteria_scores", {}),
            feedback=feedback,
            confidence=1.0
        )
        session.add(log_item)
        await session.commit()

        await AuditService.log_event(
            session=session,
            action="SUBJECTIVE_GRADE_OVERRIDDEN",
            resource_type="student_answer",
            actor_id=teacher.id,
            organization_id=teacher.organization_id,
            resource_id=str(answer.id),
            details={
                "original_ai_proposal": ai_proposal,
                "old_score": old_proposed_score,
                "new_score": new_score,
                "feedback": feedback
            }
        )

        return answer
