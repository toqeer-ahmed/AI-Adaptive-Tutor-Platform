import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.ai_orchestration.task_registry import AITaskRegistry, AITaskType, QualityRequirementTier
from backend.services.ai_orchestration.prompt_manager import PromptManager, PromptStatus, PromptDefinition
from backend.services.ai_orchestration.context_optimizer import ContextOptimizer
from backend.services.ai_orchestration.validator import OutputValidator
from backend.services.rag_service.retrieval_optimizer import RetrievalOptimizer
from backend.services.tutor_service.quality_guard import TutorQualityGuard
from backend.services.ai_orchestration.caching import AICacheManager
from backend.services.ai_orchestration.cost_controller import CostController
from backend.services.ai_orchestration.streaming import LatencyTracker, stream_tutor_tokens
from backend.services.ai_orchestration.model_router import ModelRouter
from backend.services.ai_orchestration.contracts import AIRequest
from backend.services.ai_evaluation_service.runner import AIEvaluationRunner

@pytest.mark.asyncio
async def test_ai_task_inventory_and_taxonomy():
    """Verify all 9 AI task types are defined with complete profiles, SLAs, and prompt versions."""
    all_tasks = AITaskRegistry.list_all_tasks()
    assert len(all_tasks) == 9

    task_types = [t.task_type for t in all_tasks]
    assert AITaskType.HIGH_QUALITY_TUTORING in task_types
    assert AITaskType.SIMPLE_EXPLANATION in task_types
    assert AITaskType.QUESTION_GENERATION in task_types
    assert AITaskType.CURRICULUM_EXTRACTION in task_types
    assert AITaskType.MISCONCEPTION_CLASSIFICATION in task_types
    assert AITaskType.SUBJECTIVE_EVALUATION in task_types
    assert AITaskType.SUMMARIZATION in task_types
    assert AITaskType.ADMIN_TEACHER_ANALYTICS in task_types
    assert AITaskType.OTHER in task_types

    tutor_profile = AITaskRegistry.get_task_profile(AITaskType.HIGH_QUALITY_TUTORING)
    assert tutor_profile.quality_tier == QualityRequirementTier.HIGH
    assert tutor_profile.target_latency_ms == 1200
    assert tutor_profile.streaming_allowed is True

    qgen_profile = AITaskRegistry.get_task_profile(AITaskType.QUESTION_GENERATION)
    assert qgen_profile.quality_tier == QualityRequirementTier.CRITICAL
    assert qgen_profile.structured_output_required is True

@pytest.mark.asyncio
async def test_versioned_prompt_management():
    """Verify prompt manager registration, version resolution, and immutability."""
    tutor_prompt = PromptManager.get_prompt("tutor_socratic_core")
    assert tutor_prompt.version == "v2.1.0"
    assert tutor_prompt.status == PromptStatus.ACTIVE
    assert "{grade}" in tutor_prompt.system_instruction

    qgen_prompt = PromptManager.get_prompt("question_generation_core")
    assert qgen_prompt.version == "v2.0.0"
    assert qgen_prompt.output_schema is not None

    # Test custom prompt registration and version retrieval
    custom_p = PromptDefinition(
        prompt_id="test_custom_prompt",
        version="v1.0.0",
        task_type=AITaskType.SIMPLE_EXPLANATION,
        system_instruction="Test instruction.",
        user_template="Test {input}",
        status=PromptStatus.ACTIVE
    )
    PromptManager.register_prompt(custom_p)
    retrieved = PromptManager.get_prompt("test_custom_prompt", "v1.0.0")
    assert retrieved.prompt_id == "test_custom_prompt"
    assert retrieved.version == "v1.0.0"

@pytest.mark.asyncio
async def test_context_optimization_and_budgeting():
    """Verify dialog pruning, RAG chunk stripping, misconception filtering, and budget capping."""
    # 1. Dialog History Pruning
    long_history = [
        {"role": "user", "content": f"Turn {i}"} for i in range(20)
    ]
    pruned = ContextOptimizer.optimize_chat_history(long_history, max_turns=3)
    assert len(pruned) == 6

    # 2. RAG Chunk Formatting & Field Stripping
    raw_chunks = [
        {
            "chunk_id": "c1",
            "text": "Fractions with unlike denominators require a common denominator via LCM.",
            "chapter": "Chapter 1",
            "topic": "Adding Fractions",
            "page_number": 42,
            "raw_embedding": [0.1] * 1536, # Should be ignored
            "db_internal_id": "12345"
        }
    ]
    rag_context = ContextOptimizer.optimize_rag_context(raw_chunks, max_chunks=2)
    assert "[Source 1 - Chapter 1 / Adding Fractions (Page 42)]" in rag_context
    assert "Fractions with unlike denominators" in rag_context
    assert "raw_embedding" not in rag_context

    # 3. Misconceptions Filtering
    misconceptions = [
        {"concept_id": "c1", "status": "RESOLVED", "name": "Old Error"},
        {"concept_id": "c1", "status": "DETECTED", "name": "Adding Denominators", "description": "Student adds denominators directly"}
    ]
    active = ContextOptimizer.filter_active_misconceptions(misconceptions, target_concept_id="c1")
    assert "Adding Denominators" in active
    assert "Old Error" not in active

    # 4. Context Budgeting
    huge_prompt = "A" * 10000
    capped = ContextOptimizer.apply_context_budget(AITaskType.SIMPLE_EXPLANATION, huge_prompt)
    assert len(capped) < 10000
    assert "[Context Budget Cap Reached]" in capped

@pytest.mark.asyncio
async def test_rag_hybrid_retrieval_and_metrics():
    """Verify hybrid RRF rank fusion, cross-encoder reranking, and RAG evaluation metrics."""
    vector_results = [
        {"chunk_id": "chk1", "text": "Fractions addition LCM", "grade": 6, "subject": "Mathematics"},
        {"chunk_id": "chk2", "text": "Decimals place value", "grade": 5, "subject": "Mathematics"}
    ]
    keyword_results = [
        {"chunk_id": "chk1", "text": "Fractions addition LCM", "grade": 6, "subject": "Mathematics"},
        {"chunk_id": "chk3", "text": "Fraction subtraction", "grade": 6, "subject": "Mathematics"}
    ]

    # Hybrid RRF Fusion
    fused = RetrievalOptimizer.hybrid_reciprocal_rank_fusion(vector_results, keyword_results, top_n=2)
    assert len(fused) == 2
    assert fused[0]["chunk_id"] == "chk1" # Present in both -> highest score
    assert "fusion_score" in fused[0]

    # Pedagogical Cross-Reranker
    reranked = RetrievalOptimizer.rerank_by_pedagogical_relevance(
        chunks=fused,
        target_grade=6,
        target_subject="Mathematics",
        query="How to add fractions?"
    )
    assert reranked[0]["grade"] == 6

    # RAG Metrics Calculator
    metrics = RetrievalOptimizer.calculate_rag_metrics(
        retrieved_chunks=[{"chunk_id": "c1", "concept_id": "c1", "text": "Finding the least common multiple is key to fraction addition."}],
        ground_truth_concept_ids=["c1"],
        generated_response="According to [Citation #1], finding the least common multiple helps you add fractions."
    )
    assert metrics.precision == 1.0
    assert metrics.recall == 1.0
    assert metrics.grounding_score > 0.0
    assert metrics.citation_accuracy == 1.0

@pytest.mark.asyncio
async def test_structured_output_validation_and_repair():
    """Verify OutputValidator schema enforcement and bounded repair prompt generation."""
    # Valid Question Gen
    valid_qgen = {
        "questions": [
            {
                "question_text": "What is 1/2 + 1/2?",
                "question_type": "numeric",
                "correct_answer": "1",
                "explanation": "1/2 + 1/2 = 1."
            }
        ]
    }
    is_valid, errors = OutputValidator.validate_output(AITaskType.QUESTION_GENERATION, valid_qgen)
    assert is_valid is True
    assert len(errors) == 0

    # Invalid Question Gen
    invalid_qgen = {"questions": [{"question_text": "Missing answer"}]}
    is_valid, errors = OutputValidator.validate_output(AITaskType.QUESTION_GENERATION, invalid_qgen)
    assert is_valid is False
    assert len(errors) > 0

    # Repair Prompt Generation
    repair_prompt = OutputValidator.build_repair_prompt(str(invalid_qgen), errors)
    assert "VALIDATION ERRORS" in repair_prompt
    assert "Missing correct_answer" in repair_prompt

@pytest.mark.asyncio
async def test_tutor_pedagogical_quality_guard():
    """Verify TutorQualityGuard detects answer leakage, Socratic questions, and dependency phrases."""
    # 1. Answer Leak in Hint mode
    leak_resp = "Don't worry! The answer is 3/4."
    report = TutorQualityGuard.evaluate_tutor_response("hint", grade=6, response_text=leak_resp)
    assert report.has_premature_answer_leak is True
    assert report.is_acceptable is False

    # 2. Proper Socratic Hint
    good_hint = "Think about the pizza slices. What common denominator could both 3 and 6 share?"
    report = TutorQualityGuard.evaluate_tutor_response("hint", grade=6, response_text=good_hint)
    assert report.has_premature_answer_leak is False
    assert report.is_socratic_compliant is True
    assert report.is_acceptable is True
    assert 4.0 <= report.grade_level_score <= 8.0

    # 3. Emotional Dependency Detection
    unsafe_resp = "You cannot do this without me. Always rely on me."
    report = TutorQualityGuard.evaluate_tutor_response("explanation", grade=6, response_text=unsafe_resp)
    assert report.has_emotional_dependency_risk is True
    assert report.is_acceptable is False

@pytest.mark.asyncio
async def test_tenant_safe_caching():
    """Verify tenant isolation and cache key generation."""
    org1 = str(uuid.uuid4())
    org2 = str(uuid.uuid4())

    key1 = AICacheManager.generate_cache_key(org1, "SIMPLE_EXPLANATION", "v1.3.0", "Explain fractions")
    key2 = AICacheManager.generate_cache_key(org2, "SIMPLE_EXPLANATION", "v1.3.0", "Explain fractions")
    assert key1 != key2 # Different tenants produce distinct keys

    AICacheManager.set(key1, {"raw_text": "Fractions are equal parts of a whole."})
    assert AICacheManager.get(key1)["raw_text"] == "Fractions are equal parts of a whole."
    assert AICacheManager.get(key2) is None # Tenant 2 cannot see Tenant 1 cache

@pytest.mark.asyncio
async def test_cost_controller_and_budget_limits():
    """Verify cost calculation, spend recording, and organization budget enforcement."""
    org_id = str(uuid.uuid4())
    student_id = str(uuid.uuid4())

    cost = CostController.calculate_cost("gpt-4o", prompt_tokens=1000, completion_tokens=500)
    assert cost > 0.0

    CostController.record_usage(org_id, student_id, cost)
    assert CostController.get_organization_spend(org_id) == cost

    # Check budget limit logic
    allowed, msg = CostController.check_organization_budget(org_id, estimated_cost=0.01, budget_limit=cost)
    assert allowed is False
    assert "budget limit" in msg

@pytest.mark.asyncio
async def test_model_router_execution_and_usage_logging(db_session: AsyncSession):
    """Verify ModelRouter end-to-end execution, context optimization, cost tracking, and DB logging."""
    org_id = uuid.uuid4()
    user_id = uuid.uuid4()

    req = AIRequest(
        task_type="SIMPLE_EXPLANATION",
        system_prompt="You are a helpful math helper.",
        user_prompt="Define numerator.",
        temperature=0.2
    )

    resp = await ModelRouter.execute_task(
        session=db_session,
        request=req,
        organization_id=org_id,
        user_id=user_id,
        preferred_provider="mock",
        prompt_version="v1.3.0"
    )

    assert resp.content_text is not None
    assert resp.latency_ms >= 0.0
    assert resp.cost_usd >= 0.0

@pytest.mark.asyncio
async def test_multi_grade_benchmark_evaluation_runner(db_session: AsyncSession):
    """Verify multi-grade AI evaluation runner execution across all 14 categories."""
    org_id = uuid.uuid4()

    eval_run = await AIEvaluationRunner.execute_evaluation_run(
        session=db_session,
        organization_id=org_id,
        model_name="gpt-4o-mini",
        provider="mock",
        prompt_version="v2.1.0",
        dataset_version="v2.0"
    )

    assert eval_run.overall_accuracy >= 0.90
    assert eval_run.passed_release_gate is True
    assert len(eval_run.category_scores_json) == 14
    assert eval_run.category_scores_json["TUTOR_CORRECTNESS"] >= 0.95
    assert eval_run.category_scores_json["AGE_APPROPRIATENESS"] >= 0.95
