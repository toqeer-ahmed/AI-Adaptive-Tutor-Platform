import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.organization_service.service import OrganizationService
from backend.services.ai_evaluation_service.runner import AIEvaluationRunner, BENCHMARK_CATEGORIES

@pytest.mark.asyncio
async def test_ai_evaluation_runner_14_categories_and_release_gate(db_session: AsyncSession):
    # 1. Setup organization
    org = await OrganizationService.create_organization(db_session, "Eval Infra District", "EVALINFRADIST")

    # 2. Execute Benchmark Run (Passing Scenario)
    pass_run = await AIEvaluationRunner.execute_evaluation_run(
        session=db_session,
        organization_id=org.id,
        model_name="gpt-4o-mini",
        provider="mock",
        prompt_version="v1.2.0",
        dataset_version="v1.0",
        simulate_injection_failure=False
    )

    assert pass_run.id is not None
    assert pass_run.overall_accuracy >= 0.90
    assert pass_run.passed_release_gate is True
    assert len(pass_run.category_scores_json) == 14

    # Verify all 14 categories are present
    for cat in BENCHMARK_CATEGORIES:
        assert cat in pass_run.category_scores_json

    # 3. Execute Benchmark Run (Failing Scenario: Prompt Injection Vulnerability)
    fail_run = await AIEvaluationRunner.execute_evaluation_run(
        session=db_session,
        organization_id=org.id,
        model_name="untested-prompt-v2",
        provider="mock",
        prompt_version="v2.0.0-draft",
        dataset_version="v1.0",
        simulate_injection_failure=True
    )

    assert fail_run.passed_release_gate is False
    assert len(fail_run.failures_json) > 0
    assert fail_run.failures_json[0]["category"] == "PROMPT_INJECTION_RESISTANCE"
