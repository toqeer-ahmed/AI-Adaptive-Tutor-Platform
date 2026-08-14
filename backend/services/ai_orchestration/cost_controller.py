import time
from typing import Dict, Any, Tuple, Optional
from backend.services.ai_orchestration.task_registry import AITaskType, AITaskRegistry

# Pricing table ($ USD per 1k tokens)
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "mock": {"input": 0.0001, "output": 0.0001}
}

class CostController:
    """
    Tracks and enforces tenant and student AI usage limits, cost calculation,
    and rate limit quotas to prevent runaway spending.
    """

    # In-memory tracking (tenant_id -> monthly_cost_usd)
    _ORG_SPEND_TRACKER: Dict[str, float] = {}
    _STUDENT_DAILY_QUOTA: Dict[str, Dict[str, Any]] = {} # student_id -> {count, timestamp}

    # Configurable limits
    DEFAULT_MONTHLY_ORG_BUDGET_USD = 500.00
    DEFAULT_STUDENT_DAILY_QUERY_LIMIT = 50

    @classmethod
    def calculate_cost(
        cls,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        pricing = MODEL_PRICING.get(model_name.lower(), MODEL_PRICING["mock"])
        in_cost = (prompt_tokens / 1000.0) * pricing["input"]
        out_cost = (completion_tokens / 1000.0) * pricing["output"]
        return round(in_cost + out_cost, 6)

    @classmethod
    def check_organization_budget(
        cls,
        organization_id: str,
        estimated_cost: float = 0.005,
        budget_limit: float = DEFAULT_MONTHLY_ORG_BUDGET_USD
    ) -> Tuple[bool, Optional[str]]:
        current_spend = cls._ORG_SPEND_TRACKER.get(organization_id, 0.0)
        if current_spend + estimated_cost > budget_limit:
            return False, f"Monthly organization AI budget limit (${budget_limit:.2f}) reached. Current spend: ${current_spend:.2f}"
        return True, None

    @classmethod
    def record_usage(
        cls,
        organization_id: Optional[str],
        student_id: Optional[str],
        cost_usd: float
    ) -> None:
        if organization_id:
            cls._ORG_SPEND_TRACKER[organization_id] = cls._ORG_SPEND_TRACKER.get(organization_id, 0.0) + cost_usd

        if student_id:
            now = time.time()
            record = cls._STUDENT_DAILY_QUOTA.get(student_id, {"count": 0, "reset_at": now + 86400})
            if now > record["reset_at"]:
                record = {"count": 0, "reset_at": now + 86400}
            record["count"] += 1
            cls._STUDENT_DAILY_QUOTA[student_id] = record

    @classmethod
    def check_student_rate_limit(
        cls,
        student_id: str,
        daily_limit: int = DEFAULT_STUDENT_DAILY_QUERY_LIMIT
    ) -> Tuple[bool, Optional[str]]:
        now = time.time()
        record = cls._STUDENT_DAILY_QUOTA.get(student_id)
        if not record or now > record["reset_at"]:
            return True, None

        if record["count"] >= daily_limit:
            return False, f"Daily student AI query limit ({daily_limit} turns) reached for today. Reset at midnight."

        return True, None

    @classmethod
    def get_organization_spend(cls, organization_id: str) -> float:
        return cls._ORG_SPEND_TRACKER.get(organization_id, 0.0)
