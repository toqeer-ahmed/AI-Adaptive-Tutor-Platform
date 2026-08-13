import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.api.deps import get_db, get_current_user, require_roles
from backend.models.mastery import StudentMastery
from backend.models.user import User

router = APIRouter(prefix="/mastery", tags=["Student Knowledge Model"])

def get_qualitative_band(score: float) -> str:
    if score < 0.40:
        return "Getting there 💡"
    elif score < 0.75:
        return "On track 📈"
    else:
        return "Strong 🌟"

@router.get("/student/{student_id}", response_model=dict)
async def get_student_knowledge_map(
    student_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    stud_uuid = uuid.UUID(student_id)

    # Authoritative Backend Data Isolation Guard: Students can only view their own data
    user_roles = [ur.role.name for ur in current_user.roles] if hasattr(current_user, 'roles') and current_user.roles else []
    if "Student" in user_roles and current_user.id != stud_uuid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Students can only view their own knowledge map."
        )

    stmt = select(StudentMastery).where(
        StudentMastery.student_id == stud_uuid,
        StudentMastery.organization_id == current_user.organization_id
    ).order_by(StudentMastery.updated_at.desc())

    res = await session.execute(stmt)
    masteries = res.scalars().all()

    return {
        "data": [
            {
                "id": str(m.id),
                "concept_id": str(m.concept_id),
                "curriculum_version_id": str(m.curriculum_version_id),
                "qualitative_band": get_qualitative_band(m.mastery_score),
                "confidence": m.confidence,
                "attempt_count": m.attempt_count,
                "correct_count": m.correct_count,
                "incorrect_count": m.incorrect_count,
                "status": m.status,
                "last_practiced_at": m.last_practiced_at.isoformat() if m.last_practiced_at else None,
                "next_review_due_at": m.next_review_due_at.isoformat() if m.next_review_due_at else None
            } for m in masteries
        ],
        "error": None,
        "meta": {"concept_count": len(masteries)}
    }

@router.get("/concepts/{concept_id}", response_model=dict)
async def get_concept_mastery(
    concept_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    cp_uuid = uuid.UUID(concept_id)
    stmt = select(StudentMastery).where(
        StudentMastery.student_id == current_user.id,
        StudentMastery.concept_id == cp_uuid
    )
    res = await session.execute(stmt)
    sm = res.scalars().first()

    if not sm:
        return {
            "data": {
                "concept_id": concept_id,
                "qualitative_band": get_qualitative_band(0.0),
                "confidence": 0.0,
                "status": "NOT_STARTED",
                "attempt_count": 0
            },
            "error": None,
            "meta": {}
        }

    return {
        "data": {
            "id": str(sm.id),
            "concept_id": str(sm.concept_id),
            "qualitative_band": get_qualitative_band(sm.mastery_score),
            "confidence": sm.confidence,
            "status": sm.status,
            "attempt_count": sm.attempt_count,
            "correct_count": sm.correct_count,
            "incorrect_count": sm.incorrect_count,
            "next_review_due_at": sm.next_review_due_at.isoformat() if sm.next_review_due_at else None
        },
        "error": None,
        "meta": {}
    }
