import uuid
import time
import logging
from typing import Optional, List, Dict, Any, Type
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.ai_orchestration.contracts import AIRequest, AIResponse
from backend.services.ai_orchestration.providers.base import LLMProviderAdapter
from backend.services.ai_orchestration.providers.mock_provider import MockLLMProvider
from backend.services.ai_orchestration.providers.openai_provider import OpenAIProvider
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
        preferred_provider: str = "mock"
    ) -> AIResponse:
        """
        Routes task execution to provider adapter and logs usage to DB.
        """
        fallback_reason = None
        fallback_occurred = False

        try:
            adapter = cls.get_provider(preferred_provider)
            response = await adapter.generate_structured(request)
        except Exception as primary_err:
            logging.getLogger(__name__).warning(
                f"Primary AI Provider '{preferred_provider}' failed: {primary_err}. Initiating automatic provider fallback."
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

        # Log usage to DB with complete provenance
        usage_record = ModelUsageRecord(
            id=uuid.uuid4(),
            organization_id=organization_id,
            user_id=user_id,
            provider=response.provider,
            model=response.model,
            task_type=request.task_type,
            prompt_version="v1.0",
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            total_tokens=response.total_tokens,
            latency_ms=response.latency_ms,
            cost_usd=response.cost_usd,
            validation_result="FALLBACK_USED" if fallback_occurred else "PASSED",
            failure_reason=fallback_reason
        )
        session.add(usage_record)
        await session.commit()

        return response
