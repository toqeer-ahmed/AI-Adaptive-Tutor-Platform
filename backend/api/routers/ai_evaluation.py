import uuid
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.api.deps import get_db, get_current_user, require_roles
from backend.services.ai_evaluation_service.runner import AIEvaluationRunner
from backend.models.ai_evaluation import AIEvalRun
from backend.models.user import User

router = APIRouter(prefix="/ai-evaluations", tags=["AI Evaluation Framework"])

class RunBenchmarkRequest(BaseModel):
    model_name: str = "gpt-4o-mini"
    provider: str = "mock"
    prompt_version: str = "v1.2.0"
    dataset_version: str = "v1.0"
    simulate_injection_failure: bool = False

@router.post("/benchmark/run", response_model=dict)
async def run_benchmark_evaluations(
    req: RunBenchmarkRequest,
    current_user: User = Depends(require_roles(["SuperAdmin", "OrgAdmin"])),
    session: AsyncSession = Depends(get_db)
):
    eval_run = await AIEvaluationRunner.execute_evaluation_run(
        session=session,
        organization_id=current_user.organization_id,
        model_name=req.model_name,
        provider=req.provider,
        prompt_version=req.prompt_version,
        dataset_version=req.dataset_version,
        simulate_injection_failure=req.simulate_injection_failure
    )

    return {
        "data": {
            "eval_run_id": str(eval_run.id),
            "model_name": eval_run.model_name,
            "provider": eval_run.provider,
            "prompt_version": eval_run.prompt_version,
            "dataset_version": eval_run.dataset_version,
            "overall_accuracy": eval_run.overall_accuracy,
            "category_scores": eval_run.category_scores_json,
            "failures": eval_run.failures_json,
            "passed_release_gate": eval_run.passed_release_gate,
            "evaluated_at": eval_run.evaluated_at.isoformat()
        },
        "error": None,
        "meta": {}
    }

@router.get("/runs", response_model=dict)
async def list_evaluation_runs(
    current_user: User = Depends(require_roles(["SuperAdmin", "OrgAdmin", "Teacher"])),
    session: AsyncSession = Depends(get_db)
):
    stmt = (
        select(AIEvalRun)
        .where(AIEvalRun.organization_id == current_user.organization_id)
        .order_by(AIEvalRun.evaluated_at.desc())
    )
    res = await session.execute(stmt)
    runs = res.scalars().all()

    return {
        "data": [
            {
                "eval_run_id": str(r.id),
                "model_name": r.model_name,
                "provider": r.provider,
                "prompt_version": r.prompt_version,
                "dataset_version": r.dataset_version,
                "overall_accuracy": r.overall_accuracy,
                "passed_release_gate": r.passed_release_gate,
                "failure_count": len(r.failures_json or []),
                "evaluated_at": r.evaluated_at.isoformat()
            } for r in runs
        ],
        "error": None,
        "meta": {"count": len(runs)}
    }
