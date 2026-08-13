import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.api.deps import get_db, get_current_user
from backend.services.tutor_service.service import TutorService
from backend.models.tutor import TutorSession, TutorTurn
from backend.models.user import User

router = APIRouter(prefix="/tutor", tags=["AI Instructor"])

class CreateSessionRequest(BaseModel):
    concept_id: str
    curriculum_version_id: str
    mode: Optional[str] = "explanation"

class ExecuteTurnRequest(BaseModel):
    session_id: str
    student_message: str
    mode: Optional[str] = None
    provider: Optional[str] = "mock"

@router.post("/sessions", response_model=dict)
async def create_tutor_session(
    req: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    try:
        ts = await TutorService.create_session(
            session=session,
            student=current_user,
            concept_id=uuid.UUID(req.concept_id),
            curriculum_version_id=uuid.UUID(req.curriculum_version_id),
            initial_mode=req.mode or "explanation"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "data": {
            "session_id": str(ts.id),
            "concept_id": str(ts.concept_id),
            "current_mode": ts.current_mode,
            "created_at": ts.created_at.isoformat()
        },
        "error": None,
        "meta": {}
    }

@router.post("/turn", response_model=dict)
async def execute_tutor_turn(
    req: ExecuteTurnRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    try:
        turn = await TutorService.execute_turn(
            session=session,
            session_id=uuid.UUID(req.session_id),
            student=current_user,
            student_message=req.student_message,
            override_mode=req.mode,
            provider=req.provider or "mock"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "data": {
            "turn_id": str(turn.id),
            "student_message": turn.student_message,
            "tutor_response": turn.tutor_response,
            "mode": turn.mode,
            "sources_cited": turn.sources_cited,
            "created_at": turn.created_at.isoformat()
        },
        "error": None,
        "meta": {}
    }

@router.get("/sessions/{session_id}/history", response_model=dict)
async def get_session_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    sess_uuid = uuid.UUID(session_id)
    stmt = (
        select(TutorSession)
        .options(selectinload(TutorSession.turns))
        .where(TutorSession.id == sess_uuid, TutorSession.organization_id == current_user.organization_id)
    )
    res = await session.execute(stmt)
    ts = res.scalars().first()
    if not ts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found or forbidden.")

    return {
        "data": [
            {
                "id": str(tr.id),
                "student_message": tr.student_message,
                "tutor_response": tr.tutor_response,
                "mode": tr.mode,
                "sources_cited": tr.sources_cited,
                "created_at": tr.created_at.isoformat()
            } for tr in ts.turns
        ],
        "error": None,
        "meta": {"turn_count": len(ts.turns)}
    }
