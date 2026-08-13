import uuid
from typing import Optional, List, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.api.deps import get_db, get_current_user
from backend.services.misconception_service.service import MisconceptionDetectionService
from backend.models.misconception import StudentMisconception
from backend.models.user import User

router = APIRouter(prefix="/misconceptions", tags=["Misconception Detection"])

class DetectMisconceptionRequest(BaseModel):
    concept_id: str
    curriculum_version_id: str
    is_correct: bool
    submitted_answer: Any
    expected_answer: Any

@router.get("/student/{student_id}", response_model=dict)
async def get_student_misconceptions(
    student_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    stud_uuid = uuid.UUID(student_id)
    stmt = (
        select(StudentMisconception)
        .options(selectinload(StudentMisconception.taxonomy))
        .where(
            StudentMisconception.student_id == stud_uuid,
            StudentMisconception.organization_id == current_user.organization_id
        )
        .order_by(StudentMisconception.updated_at.desc())
    )
    res = await session.execute(stmt)
    smisc_list = res.scalars().all()

    return {
        "data": [
            {
                "id": str(m.id),
                "concept_id": str(m.concept_id),
                "misconception_code": m.taxonomy.code if m.taxonomy else "UNKNOWN",
                "name": m.taxonomy.name if m.taxonomy else "Misconception",
                "description": m.taxonomy.description if m.taxonomy else "",
                "remediation_strategy": m.taxonomy.remediation_strategy if m.taxonomy else "",
                "confidence": m.confidence,
                "status": m.status,
                "evidence_count": len(m.evidence or []),
                "detected_at": m.detected_at.isoformat(),
                "resolved_at": m.resolved_at.isoformat() if m.resolved_at else None
            } for m in smisc_list
        ],
        "error": None,
        "meta": {"count": len(smisc_list)}
    }

@router.post("/detect", response_model=dict)
async def detect_misconception(
    req: DetectMisconceptionRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    smisc = await MisconceptionDetectionService.process_answer_evidence(
        session=session,
        student=current_user,
        concept_id=uuid.UUID(req.concept_id),
        curriculum_version_id=uuid.UUID(req.curriculum_version_id),
        is_correct=req.is_correct,
        submitted_answer=req.submitted_answer,
        expected_answer=req.expected_answer,
        provider="mock"
    )

    if not smisc:
        return {
            "data": None,
            "error": None,
            "meta": {"message": "No high-confidence misconception classified."}
        }

    return {
        "data": {
            "id": str(smisc.id),
            "status": smisc.status,
            "confidence": smisc.confidence,
            "evidence_count": len(smisc.evidence or [])
        },
        "error": None,
        "meta": {}
    }
