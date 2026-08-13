import uuid
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_db, get_current_user
from backend.services.adaptive_engine.service import AdaptiveLearningService
from backend.models.user import User

router = APIRouter(prefix="/adaptive", tags=["Adaptive Learning Engine"])

class AdaptiveDecideRequest(BaseModel):
    concept_id: str
    curriculum_version_id: str

@router.post("/decide", response_model=dict)
async def get_adaptive_decision(
    req: AdaptiveDecideRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    try:
        decision = await AdaptiveLearningService.get_next_learning_decision(
            session=session,
            student=current_user,
            concept_id=uuid.UUID(req.concept_id),
            curriculum_version_id=uuid.UUID(req.curriculum_version_id)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "data": {
            "decision": decision.decision,
            "target_concept_id": decision.target_concept_id,
            "recommended_difficulty": decision.recommended_difficulty,
            "reason": decision.reason,
            "priority_level": decision.priority_level
        },
        "error": None,
        "meta": {}
    }
