import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.api.deps import get_db, get_current_user, require_roles
from backend.services.assessment_service.question_generator import QuestionGenerationEngine
from backend.services.assessment_service.service import AssessmentService
from backend.models.assessment import QuestionBankItem, Assessment, AssessmentAttempt, StudentAnswer
from backend.models.user import User

router = APIRouter(tags=["Assessments"])

class GenerateQuestionsRequest(BaseModel):
    concept_id: str
    count: int = 10
    provider: Optional[str] = "mock"

class CreateAssessmentRequest(BaseModel):
    title: str
    class_id: Optional[str] = None
    question_ids: List[str]
    description: Optional[str] = None
    assessment_type: str = "QUIZ"
    max_attempts: int = 1

class SubmitAnswerRequest(BaseModel):
    question_id: str
    submitted_answer: Any

class GradeOverrideRequest(BaseModel):
    new_points: float
    feedback: Optional[str] = None

# --- Question Bank Endpoints ---
@router.post("/api/v1/questions/generate", response_model=dict, dependencies=[Depends(require_roles(["Teacher", "ContentManager", "OrgAdmin", "SuperAdmin"]))])
async def generate_ai_questions(
    req: GenerateQuestionsRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    try:
        items = await QuestionGenerationEngine.generate_questions_for_concept(
            session=session,
            concept_id=uuid.UUID(req.concept_id),
            creator=current_user,
            count=req.count,
            provider=req.provider or "mock"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "data": [
            {
                "id": str(q.id),
                "question_type": q.question_type,
                "question_text": q.question_text,
                "options": q.options_json,
                "correct_answer": q.correct_answer_json,
                "validation_status": q.validation_status
            } for q in items
        ],
        "error": None,
        "meta": {"generated_count": len(items)}
    }

@router.get("/api/v1/questions", response_model=dict)
async def list_question_bank(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    res = await session.execute(
        select(QuestionBankItem)
        .where(QuestionBankItem.organization_id == current_user.organization_id)
        .order_by(QuestionBankItem.created_at.desc())
    )
    items = res.scalars().all()
    return {
        "data": [
            {
                "id": str(q.id),
                "question_type": q.question_type,
                "question_text": q.question_text,
                "options": q.options_json,
                "correct_answer": q.correct_answer_json,
                "validation_status": q.validation_status
            } for q in items
        ],
        "error": None,
        "meta": {"count": len(items)}
    }

@router.post("/api/v1/questions/{question_id}/approve", response_model=dict, dependencies=[Depends(require_roles(["Teacher", "ContentManager", "OrgAdmin", "SuperAdmin"]))])
async def approve_question(
    question_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    q = await AssessmentService.approve_question(session, uuid.UUID(question_id), current_user)
    return {"data": {"id": str(q.id), "status": q.validation_status}, "error": None, "meta": {}}

@router.post("/api/v1/questions/{question_id}/reject", response_model=dict, dependencies=[Depends(require_roles(["Teacher", "ContentManager", "OrgAdmin", "SuperAdmin"]))])
async def reject_question(
    question_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    q = await AssessmentService.reject_question(session, uuid.UUID(question_id), current_user)
    return {"data": {"id": str(q.id), "status": q.validation_status}, "error": None, "meta": {}}

# --- Assessment Endpoints ---
@router.post("/api/v1/assessments", response_model=dict, dependencies=[Depends(require_roles(["Teacher", "OrgAdmin", "SchoolAdmin", "SuperAdmin"]))])
async def create_assessment(
    req: CreateAssessmentRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    class_uuid = uuid.UUID(req.class_id) if req.class_id else None
    q_uuids = [uuid.UUID(q) for q in req.question_ids]

    ass = await AssessmentService.create_assessment(
        session=session,
        creator=current_user,
        title=req.title,
        class_id=class_uuid,
        question_ids=q_uuids,
        description=req.description,
        assessment_type=req.assessment_type,
        max_attempts=req.max_attempts
    )

    return {
        "data": {
            "id": str(ass.id),
            "title": ass.title,
            "assessment_type": ass.assessment_type,
            "question_count": len(q_uuids)
        },
        "error": None,
        "meta": {}
    }

@router.get("/api/v1/assessments", response_model=dict)
async def list_assessments(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    res = await session.execute(
        select(Assessment)
        .options(selectinload(Assessment.questions).selectinload(AssessmentQuestion.question))
        .where(Assessment.organization_id == current_user.organization_id)
    )
    assessments = res.scalars().all()
    return {
        "data": [
            {
                "id": str(a.id),
                "title": a.title,
                "assessment_type": a.assessment_type,
                "max_attempts": a.max_attempts,
                "questions": [
                    {
                        "id": str(aq.question.id),
                        "question_type": aq.question.question_type,
                        "question_text": aq.question.question_text,
                        "options": aq.question.options_json
                    } for aq in a.questions
                ]
            } for a in assessments
        ],
        "error": None,
        "meta": {"count": len(assessments)}
    }

@router.post("/api/v1/assessments/{assessment_id}/start", response_model=dict)
async def start_assessment_attempt(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    try:
        attempt = await AssessmentService.start_attempt(session, uuid.UUID(assessment_id), current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "data": {
            "attempt_id": str(attempt.id),
            "attempt_number": attempt.attempt_number,
            "status": attempt.status
        },
        "error": None,
        "meta": {}
    }

@router.post("/api/v1/attempts/{attempt_id}/answer", response_model=dict)
async def submit_single_answer(
    attempt_id: str,
    req: SubmitAnswerRequest,
    session: AsyncSession = Depends(get_db)
):
    try:
        ans = await AssessmentService.submit_answer(
            session=session,
            attempt_id=uuid.UUID(attempt_id),
            question_id=uuid.UUID(req.question_id),
            submitted_answer=req.submitted_answer
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "data": {
            "answer_id": str(ans.id),
            "is_correct": ans.is_correct,
            "points_awarded": ans.points_awarded,
            "feedback": ans.feedback
        },
        "error": None,
        "meta": {}
    }

@router.post("/api/v1/attempts/{attempt_id}/submit", response_model=dict)
async def submit_assessment_attempt(
    attempt_id: str,
    session: AsyncSession = Depends(get_db)
):
    try:
        attempt = await AssessmentService.submit_attempt(session, uuid.UUID(attempt_id))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "data": {
            "attempt_id": str(attempt.id),
            "status": attempt.status,
            "score": attempt.score,
            "max_score": attempt.max_score,
            "percentage": (attempt.score / (attempt.max_score or 1.0)) * 100
        },
        "error": None,
        "meta": {}
    }

@router.post("/api/v1/answers/{answer_id}/override", response_model=dict, dependencies=[Depends(require_roles(["Teacher", "OrgAdmin", "SchoolAdmin", "SuperAdmin"]))])
async def teacher_override_grade(
    answer_id: str,
    req: GradeOverrideRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    ans = await AssessmentService.teacher_override_score(
        session=session,
        answer_id=uuid.UUID(answer_id),
        teacher=current_user,
        new_points=req.new_points,
        feedback=req.feedback
    )

    return {
        "data": {
            "answer_id": str(ans.id),
            "points_awarded": ans.points_awarded,
            "teacher_override": ans.teacher_override,
            "feedback": ans.feedback
        },
        "error": None,
        "meta": {}
    }
