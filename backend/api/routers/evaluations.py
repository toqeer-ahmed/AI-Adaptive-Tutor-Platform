import uuid
from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.api.deps import get_db, get_current_user, require_roles
from backend.services.evaluation_service.service import SubjectiveEvaluationService
from backend.models.assessment import StudentAnswer, QuestionBankItem
from backend.models.user import User

router = APIRouter(prefix="/evaluations", tags=["Subjective Answer Evaluation"])

class EvaluateSubjectiveRequest(BaseModel):
    answer_id: str

class TeacherReviewRequest(BaseModel):
    action: str = Field(..., description="ACCEPT or OVERRIDE")
    new_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    feedback: Optional[str] = None

@router.post("/subjective/evaluate", response_model=dict)
async def trigger_subjective_evaluation(
    req: EvaluateSubjectiveRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    answer = await SubjectiveEvaluationService.evaluate_subjective_answer(
        session=session,
        answer_id=uuid.UUID(req.answer_id),
        actor=current_user,
        provider="mock"
    )

    return {
        "data": {
            "answer_id": str(answer.id),
            "evaluation_status": answer.evaluation_status,
            "points_awarded": answer.points_awarded,
            "feedback": answer.feedback,
            "ai_evaluation_json": answer.ai_evaluation_json
        },
        "error": None,
        "meta": {}
    }

@router.get("/pending", response_model=dict)
async def list_pending_teacher_reviews(
    current_user: User = Depends(require_roles(["Teacher", "SchoolAdmin", "SuperAdmin"])),
    session: AsyncSession = Depends(get_db)
):
    stmt = (
        select(StudentAnswer)
        .options(selectinload(StudentAnswer.question))
        .where(StudentAnswer.evaluation_status == "NEEDS_TEACHER_REVIEW")
        .order_by(StudentAnswer.answered_at.desc())
    )
    res = await session.execute(stmt)
    answers = res.scalars().all()

    return {
        "data": [
            {
                "answer_id": str(ans.id),
                "question_id": str(ans.question_id),
                "question_text": ans.question.question_text if ans.question else "",
                "question_type": ans.question.question_type if ans.question else "",
                "rubric_json": ans.question.rubric_json if ans.question else {},
                "submitted_answer": ans.submitted_answer_json,
                "ai_evaluation_json": ans.ai_evaluation_json,
                "evaluation_status": ans.evaluation_status,
                "answered_at": ans.answered_at.isoformat()
            } for ans in answers
        ],
        "error": None,
        "meta": {"count": len(answers)}
    }

@router.post("/answers/{answer_id}/review", response_model=dict)
async def teacher_review_answer(
    answer_id: str,
    req: TeacherReviewRequest,
    current_user: User = Depends(require_roles(["Teacher", "SchoolAdmin", "SuperAdmin"])),
    session: AsyncSession = Depends(get_db)
):
    ans_uuid = uuid.UUID(answer_id)
    if req.action.upper() == "ACCEPT":
        ans = await SubjectiveEvaluationService.teacher_review_accept(session, ans_uuid, current_user)
    elif req.action.upper() == "OVERRIDE":
        if req.new_score is None:
            raise HTTPException(status_code=400, detail="new_score is required for OVERRIDE action.")
        feedback_text = req.feedback or "Score overridden by teacher."
        ans = await SubjectiveEvaluationService.teacher_review_override(session, ans_uuid, current_user, req.new_score, feedback_text)
    else:
        raise HTTPException(status_code=400, detail="Action must be ACCEPT or OVERRIDE.")

    return {
        "data": {
            "answer_id": str(ans.id),
            "evaluation_status": ans.evaluation_status,
            "points_awarded": ans.points_awarded,
            "feedback": ans.feedback,
            "teacher_override": ans.teacher_override
        },
        "error": None,
        "meta": {}
    }
