import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.api.deps import get_db, get_current_user, require_roles
from backend.services.analytics_service.service import AnalyticsAggregationService
from backend.models.analytics import AnalyticsSummaryProvenance
from backend.models.class_model import Class, Enrollment
from backend.models.mastery import StudentMastery
from backend.models.misconception import StudentMisconception
from backend.models.assessment import AssessmentAttempt
from backend.models.user import User

router = APIRouter(prefix="/analytics", tags=["Teacher Analytics & Provenance"])

@router.get("/class/{class_id}", response_model=dict)
async def get_class_analytics(
    class_id: str,
    current_user: User = Depends(require_roles(["Teacher", "SchoolAdmin", "SuperAdmin"])),
    session: AsyncSession = Depends(get_db)
):
    cls_uuid = uuid.UUID(class_id)

    # Security Guard: Verify teacher access
    cls_stmt = select(Class).where(
        Class.id == cls_uuid,
        Class.organization_id == current_user.organization_id
    )
    cls_res = await session.execute(cls_stmt)
    class_obj = cls_res.scalars().first()
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found or unauthorized.")

    user_roles = [ur.role.name for ur in current_user.roles] if hasattr(current_user, 'roles') and current_user.roles else []
    if "Teacher" in user_roles and "SuperAdmin" not in user_roles and "SchoolAdmin" not in user_roles:
        if class_obj.teacher_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cross-class access denied. Teacher is not assigned to this class."
            )

    metrics = await AnalyticsAggregationService.get_deterministic_class_metrics(session, cls_uuid, current_user.organization_id)

    return {
        "data": metrics,
        "error": None,
        "meta": {}
    }

@router.post("/class/{class_id}/summary", response_model=dict)
async def generate_ai_class_summary(
    class_id: str,
    current_user: User = Depends(require_roles(["Teacher", "SchoolAdmin", "SuperAdmin"])),
    session: AsyncSession = Depends(get_db)
):
    cls_uuid = uuid.UUID(class_id)
    provenance = await AnalyticsAggregationService.generate_ai_class_summary_with_provenance(
        session=session,
        class_id=cls_uuid,
        teacher=current_user,
        provider="mock"
    )

    return {
        "data": {
            "provenance_id": str(provenance.id),
            "summary_type": provenance.summary_type,
            "generated_summary_text": provenance.generated_summary_text,
            "ai_model_name": provenance.ai_model_name,
            "prompt_hash": provenance.prompt_hash,
            "source_metric_count": len(provenance.source_metric_ids),
            "created_at": provenance.created_at.isoformat()
        },
        "error": None,
        "meta": {}
    }

@router.get("/provenance/{provenance_id}", response_model=dict)
async def get_provenance_trace(
    provenance_id: str,
    current_user: User = Depends(require_roles(["Teacher", "SchoolAdmin", "SuperAdmin"])),
    session: AsyncSession = Depends(get_db)
):
    prov_uuid = uuid.UUID(provenance_id)
    stmt = select(AnalyticsSummaryProvenance).where(
        AnalyticsSummaryProvenance.id == prov_uuid,
        AnalyticsSummaryProvenance.organization_id == current_user.organization_id
    )
    res = await session.execute(stmt)
    prov = res.scalars().first()

    if not prov:
        raise HTTPException(status_code=404, detail="Provenance trace record not found.")

    return {
        "data": {
            "provenance_id": str(prov.id),
            "organization_id": str(prov.organization_id),
            "summary_type": prov.summary_type,
            "source_metric_ids": prov.source_metric_ids,
            "generated_summary_text": prov.generated_summary_text,
            "ai_model_name": prov.ai_model_name,
            "prompt_hash": prov.prompt_hash,
            "created_at": prov.created_at.isoformat()
        },
        "error": None,
        "meta": {}
    }
