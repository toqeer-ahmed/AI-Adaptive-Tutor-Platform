import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.ai_orchestration.contracts import AIRequest
from backend.services.ai_orchestration.model_router import ModelRouter
from backend.services.ai_orchestration.providers.mock_provider import MockLLMProvider
from backend.services.organization_service.service import OrganizationService

@pytest.mark.asyncio
async def test_mock_provider_structured_generation():
    provider = MockLLMProvider()
    req = AIRequest(task_type="CURRICULUM_EXTRACTION", system_prompt="Sys", user_prompt="User")
    resp = await provider.generate_structured(req)

    assert resp.provider == "mock"
    assert resp.content_json is not None
    assert resp.content_json["grade_level"] == 6
    assert len(resp.content_json["chapters"]) > 0

@pytest.mark.asyncio
async def test_model_router_execution_and_usage_logging(db_session: AsyncSession):
    org = await OrganizationService.create_organization(db_session, "AI Org", "AIORG")
    req = AIRequest(task_type="CURRICULUM_EXTRACTION", system_prompt="Sys", user_prompt="User")

    resp = await ModelRouter.execute_task(
        session=db_session,
        request=req,
        organization_id=org.id,
        preferred_provider="mock"
    )

    assert resp.provider == "mock"
    assert resp.total_tokens > 0
