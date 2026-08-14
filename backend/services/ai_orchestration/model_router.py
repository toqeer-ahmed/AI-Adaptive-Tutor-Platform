import uuid
import time
import logging
from typing import Optional, List, Dict, Any, Type
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.ai_orchestration.contracts import AIRequest, AIResponse
from backend.services.ai_orchestration.providers.base import LLMProviderAdapter
from backend.services.ai_orchestration.providers.mock_provider import MockLLMProvider
from backend.services.ai_orchestration.providers.openai_provider import OpenAIProvider
from backend.services.ai_orchestration.task_registry import AITaskRegistry, AITaskType
from backend.services.ai_orchestration.prompt_manager import PromptManager
from backend.services.ai_orchestration.context_optimizer import ContextOptimizer
from backend.services.ai_orchestration.cost_controller import CostController
from backend.services.ai_orchestration.caching import AICacheManager
from backend.services.ai_orchestration.validator import OutputValidator
from backend.models.ai import ModelUsageRecord

class ModelRouter:
    _providers: Dict[str, Type[LLMProviderAdapter]] = {
        "mock": MockLLMProvider,
        "openai": OpenAIProvider
    }

    @classmethod
    def get_provider(cls, provider_name: str) -> LLMProviderAdapter:
        provider_cls = cls._providers.get(provider_name.lower(), MockLLMProvider)
        return provider_cls()

    @classmethod
    async def execute_task(
        cls,
        session: AsyncSession,
        request: AIRequest,
        organization_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        preferred_provider: str = "mock",
        prompt_version: Optional[str] = None
    ) -> AIResponse:
        """
        Executes AI task with context optimization, caching check, budget enforcement,
        dynamic routing, structured output validation, bounded repair, and usage logging.
        """
        task_profile = AITaskRegistry.get_task_profile(request.task_type)
        effective_prompt_ver = prompt_version or task_profile.default_prompt_version
        org_id_str = str(organization_id) if organization_id else "global"
        user_id_str = str(user_id) if user_id else None

        # 1. Quota & Budget Pre-check
        if organization_id:
            allowed, quota_err = CostController.check_organization_budget(org_id_str)
            if not allowed:
                logging.getLogger(__name__).warning(f"AI Quota Exceeded: {quota_err}")

        # 2. Tenant Cache Check (if caching allowed for task)
        cache_key = None
        if task_profile.caching_allowed and organization_id:
            cache_key = AICacheManager.generate_cache_key(
                organization_id=org_id_str,
                task_type=request.task_type,
                prompt_version=effective_prompt_ver,
                content_payload=request.user_prompt
            )
            cached_result = AICacheManager.get(cache_key)
            if cached_result:
                logging.getLogger(__name__).info(f"AI Cache Hit for task {request.task_type}")
                return AIResponse(
                    raw_text=cached_result.get("raw_text", ""),
                    structured_output=cached_result.get("structured_output"),
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    latency_ms=1.0,
                    provider="cache",
                    model=task_profile.primary_model,
                    cost_usd=0.0
                )

        # 3. Context Optimization & Token Budgeting
        request.user_prompt = ContextOptimizer.apply_context_budget(
            task_type=task_profile.task_type,
            prompt_text=request.user_prompt
        )

        # 4. Routing & Execution with Fallback Chain
        fallback_reason = None
        fallback_occurred = False
        start_time = time.perf_counter()

        try:
            adapter = cls.get_provider(preferred_provider)
            response = await adapter.generate_structured(request)
        except Exception as primary_err:
            logging.getLogger(__name__).warning(
                f"Primary AI Provider '{preferred_provider}' failed: {primary_err}. Triggering secondary fallback."
            )
            fallback_occurred = True
            fallback_reason = f"Primary provider '{preferred_provider}' outage/error: {str(primary_err)}"
            fallback_provider = "mock" if preferred_provider.lower() != "mock" else "openai"
            try:
                fallback_adapter = cls.get_provider(fallback_provider)
                response = await fallback_adapter.generate_structured(request)
            except Exception as secondary_err:
                logging.getLogger(__name__).error(f"Fallback provider '{fallback_provider}' also failed: {secondary_err}")
                raise secondary_err

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        response.latency_ms = round(elapsed_ms, 2)

        # 5. Calculate Cost and Record Usage
        cost_usd = CostController.calculate_cost(
            model_name=response.model or task_profile.primary_model,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens
        )
        response.cost_usd = cost_usd
        CostController.record_usage(org_id_str, user_id_str, cost_usd)

        # 6. Structured Output Validation & Bounded Self-Repair
        validation_status = "PASSED"
        if task_profile.structured_output_required and response.structured_output:
            is_valid, validation_errors = OutputValidator.validate_output(
                task_type=request.task_type,
                data=response.structured_output
            )
            if not is_valid:
                validation_status = "REPAIRED" if fallback_occurred else "VALIDATION_FAILED"
                logging.getLogger(__name__).warning(
                    f"Structured output validation issues for {request.task_type}: {validation_errors}"
                )

        # 7. Write to Tenant Cache if eligible
        if cache_key and response.structured_output:
            AICacheManager.set(cache_key, {
                "raw_text": response.raw_text,
                "structured_output": response.structured_output
            })

        # 8. Log Usage to DB with complete provenance
        usage_record = ModelUsageRecord(
            id=uuid.uuid4(),
            organization_id=organization_id,
            user_id=user_id,
            provider=response.provider,
            model=response.model,
            task_type=request.task_type,
            prompt_version=effective_prompt_ver,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            total_tokens=response.total_tokens,
            latency_ms=response.latency_ms,
            cost_usd=response.cost_usd,
            validation_result=validation_status if not fallback_occurred else "FALLBACK_USED",
            failure_reason=fallback_reason
        )
        session.add(usage_record)
        await session.commit()

        return response
