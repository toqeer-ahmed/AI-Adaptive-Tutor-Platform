import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from backend.api.deps import get_db, get_current_user, require_roles
from backend.models.ai import ModelUsageRecord
from backend.models.user import User

router = APIRouter(prefix="/observability", tags=["Production Observability"])

@router.get("/ai-cost", response_model=dict)
async def get_ai_cost_per_organization(
    current_user: User = Depends(require_roles(["SuperAdmin", "OrgAdmin"])),
    session: AsyncSession = Depends(get_db)
):
    stmt = (
        select(
            ModelUsageRecord.organization_id,
            func.sum(ModelUsageRecord.cost_usd).label("total_cost_usd"),
            func.sum(ModelUsageRecord.total_tokens).label("total_tokens"),
            func.count(ModelUsageRecord.id).label("request_count")
        )
        .where(ModelUsageRecord.organization_id == current_user.organization_id)
        .group_by(ModelUsageRecord.organization_id)
    )
    res = await session.execute(stmt)
    row = res.first()

    total_cost = float(row[1]) if row and row[1] else 0.0
    total_tokens = int(row[2]) if row and row[2] else 0
    request_count = int(row[3]) if row and row[3] else 0

    return {
        "data": {
            "organization_id": str(current_user.organization_id),
            "total_cost_usd": round(total_cost, 4),
            "total_tokens": total_tokens,
            "total_requests": request_count,
            "currency": "USD"
        },
        "error": None,
        "meta": {}
    }

@router.get("/ai-usage", response_model=dict)
async def get_ai_usage_metrics(
    current_user: User = Depends(require_roles(["SuperAdmin", "OrgAdmin", "Teacher"])),
    session: AsyncSession = Depends(get_db)
):
    stmt = (
        select(
            ModelUsageRecord.provider,
            ModelUsageRecord.model_name,
            func.count(ModelUsageRecord.id).label("calls"),
            func.sum(ModelUsageRecord.prompt_tokens).label("prompt_tokens"),
            func.sum(ModelUsageRecord.completion_tokens).label("completion_tokens")
        )
        .where(ModelUsageRecord.organization_id == current_user.organization_id)
        .group_by(ModelUsageRecord.provider, ModelUsageRecord.model_name)
    )
    res = await session.execute(stmt)
    rows = res.all()

    usage_breakdown = [
        {
            "provider": row[0],
            "model_name": row[1],
            "call_count": row[2],
            "prompt_tokens": row[3] or 0,
            "completion_tokens": row[4] or 0,
            "total_tokens": (row[3] or 0) + (row[4] or 0)
        } for row in rows
    ]

    return {
        "data": usage_breakdown,
        "error": None,
        "meta": {"count": len(usage_breakdown)}
    }

@router.get("/latency-metrics", response_model=dict)
async def get_latency_metrics(
    current_user: User = Depends(require_roles(["SuperAdmin", "OrgAdmin", "Teacher"])),
    session: AsyncSession = Depends(get_db)
):
    stmt = (
        select(
            func.avg(ModelUsageRecord.latency_ms).label("avg_latency"),
            func.max(ModelUsageRecord.latency_ms).label("max_latency"),
            func.min(ModelUsageRecord.latency_ms).label("min_latency")
        )
        .where(ModelUsageRecord.organization_id == current_user.organization_id)
    )
    res = await session.execute(stmt)
    row = res.first()

    avg_lat = float(row[0]) if row and row[0] else 0.0
    max_lat = float(row[1]) if row and row[1] else 0.0
    min_lat = float(row[2]) if row and row[2] else 0.0

    return {
        "data": {
            "avg_latency_ms": round(avg_lat, 2),
            "max_latency_ms": round(max_lat, 2),
            "min_latency_ms": round(min_lat, 2),
            "p95_estimated_ms": round(avg_lat * 1.25, 2),
            "p99_estimated_ms": round(max_lat, 2)
        },
        "error": None,
        "meta": {}
    }

@router.get("/failures-and-fallbacks", response_model=dict)
async def get_failures_and_fallbacks(
    current_user: User = Depends(require_roles(["SuperAdmin", "OrgAdmin", "Teacher"])),
    session: AsyncSession = Depends(get_db)
):
    # Total calls vs Success/Failure count
    total_stmt = select(func.count(ModelUsageRecord.id)).where(ModelUsageRecord.organization_id == current_user.organization_id)
    total_res = await session.execute(total_stmt)
    total_calls = total_res.scalar() or 0

    success_stmt = select(func.count(ModelUsageRecord.id)).where(
        ModelUsageRecord.organization_id == current_user.organization_id,
        ModelUsageRecord.is_success == True
    )
    success_res = await session.execute(success_stmt)
    success_calls = success_res.scalar() or 0

    failure_calls = total_calls - success_calls
    rejection_rate = round((failure_calls / total_calls * 100), 2) if total_calls > 0 else 0.0

    return {
        "data": {
            "total_requests": total_calls,
            "successful_requests": success_calls,
            "failed_requests": failure_calls,
            "fallback_frequency": 0,
            "validation_rejection_rate_percent": rejection_rate
        },
        "error": None,
        "meta": {}
    }
