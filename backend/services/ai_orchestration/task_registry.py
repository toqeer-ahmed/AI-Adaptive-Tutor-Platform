from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

class AITaskType(str, Enum):
    HIGH_QUALITY_TUTORING = "HIGH_QUALITY_TUTORING"
    SIMPLE_EXPLANATION = "SIMPLE_EXPLANATION"
    QUESTION_GENERATION = "QUESTION_GENERATION"
    CURRICULUM_EXTRACTION = "CURRICULUM_EXTRACTION"
    MISCONCEPTION_CLASSIFICATION = "MISCONCEPTION_CLASSIFICATION"
    SUBJECTIVE_EVALUATION = "SUBJECTIVE_EVALUATION"
    SUMMARIZATION = "SUMMARIZATION"
    ADMIN_TEACHER_ANALYTICS = "ADMIN_TEACHER_ANALYTICS"
    OTHER = "OTHER"

class QualityRequirementTier(str, Enum):
    CRITICAL = "CRITICAL"   # 0 tolerance for hallucination; strict adherence
    HIGH = "HIGH"           # Socratic pedagogy, deep reasoning, rubrics
    STANDARD = "STANDARD"   # Classification, summaries, extraction
    FAST = "FAST"           # Low latency, simple definitions

@dataclass
class TaskProfile:
    task_type: AITaskType
    description: str
    quality_tier: QualityRequirementTier
    primary_model: str
    fallback_model: str
    target_latency_ms: int
    max_input_tokens: int
    max_output_tokens: int
    cost_budget_usd_per_1k: float
    caching_allowed: bool
    streaming_allowed: bool
    structured_output_required: bool
    default_prompt_version: str

class AITaskRegistry:
    """
    Central inventory of all AI tasks across the AI Adaptive Education Platform.
    Defines SLAs, model mappings, fallback chains, token limits, and quality requirements.
    """

    _INVENTORY: Dict[AITaskType, TaskProfile] = {
        AITaskType.HIGH_QUALITY_TUTORING: TaskProfile(
            task_type=AITaskType.HIGH_QUALITY_TUTORING,
            description="Interactive Socratic dialogue, multi-step hints, worked examples, and guided practice for Grades 4-8.",
            quality_tier=QualityRequirementTier.HIGH,
            primary_model="gpt-4o",
            fallback_model="gpt-4o-mini",
            target_latency_ms=1200,
            max_input_tokens=1500,
            max_output_tokens=600,
            cost_budget_usd_per_1k=0.005,
            caching_allowed=False, # Personal student interaction is not cached globally
            streaming_allowed=True,
            structured_output_required=False,
            default_prompt_version="v2.1.0"
        ),
        AITaskType.SIMPLE_EXPLANATION: TaskProfile(
            task_type=AITaskType.SIMPLE_EXPLANATION,
            description="Fast conceptual definitions, math terminology glossary, and single-turn curriculum explanations.",
            quality_tier=QualityRequirementTier.FAST,
            primary_model="gpt-4o-mini",
            fallback_model="gpt-4o-mini",
            target_latency_ms=600,
            max_input_tokens=800,
            max_output_tokens=300,
            cost_budget_usd_per_1k=0.0005,
            caching_allowed=True, # Static explanations can be cached per tenant/concept
            streaming_allowed=True,
            structured_output_required=False,
            default_prompt_version="v1.3.0"
        ),
        AITaskType.QUESTION_GENERATION: TaskProfile(
            task_type=AITaskType.QUESTION_GENERATION,
            description="Synthesizing MCQ, multi-select, and numeric questions with verified correct answers and step-by-step rubrics.",
            quality_tier=QualityRequirementTier.CRITICAL,
            primary_model="gpt-4o",
            fallback_model="gpt-4o-mini",
            target_latency_ms=2500,
            max_input_tokens=2000,
            max_output_tokens=1200,
            cost_budget_usd_per_1k=0.006,
            caching_allowed=False,
            streaming_allowed=False,
            structured_output_required=True,
            default_prompt_version="v2.0.0"
        ),
        AITaskType.CURRICULUM_EXTRACTION: TaskProfile(
            task_type=AITaskType.CURRICULUM_EXTRACTION,
            description="Parsing textbook syllabus documents into hierarchical chapters, topics, concepts, and learning objectives.",
            quality_tier=QualityRequirementTier.HIGH,
            primary_model="gpt-4o",
            fallback_model="gpt-4o-mini",
            target_latency_ms=4000,
            max_input_tokens=4000,
            max_output_tokens=2500,
            cost_budget_usd_per_1k=0.010,
            caching_allowed=False,
            streaming_allowed=False,
            structured_output_required=True,
            default_prompt_version="v2.0.0"
        ),
        AITaskType.MISCONCEPTION_CLASSIFICATION: TaskProfile(
            task_type=AITaskType.MISCONCEPTION_CLASSIFICATION,
            description="Classifying student erroneous steps against domain misconception taxonomy with confidence score.",
            quality_tier=QualityRequirementTier.STANDARD,
            primary_model="gpt-4o-mini",
            fallback_model="gpt-4o-mini",
            target_latency_ms=800,
            max_input_tokens=1000,
            max_output_tokens=400,
            cost_budget_usd_per_1k=0.0008,
            caching_allowed=True,
            streaming_allowed=False,
            structured_output_required=True,
            default_prompt_version="v1.4.0"
        ),
        AITaskType.SUBJECTIVE_EVALUATION: TaskProfile(
            task_type=AITaskType.SUBJECTIVE_EVALUATION,
            description="Proposing grades, rubric adherence scores, and feedback for open-ended reasoning (subject to teacher override).",
            quality_tier=QualityRequirementTier.HIGH,
            primary_model="gpt-4o",
            fallback_model="gpt-4o-mini",
            target_latency_ms=1500,
            max_input_tokens=1500,
            max_output_tokens=500,
            cost_budget_usd_per_1k=0.004,
            caching_allowed=False,
            streaming_allowed=False,
            structured_output_required=True,
            default_prompt_version="v1.5.0"
        ),
        AITaskType.SUMMARIZATION: TaskProfile(
            task_type=AITaskType.SUMMARIZATION,
            description="Synthesizing parent weekly learning summaries and student chapter milestone overviews.",
            quality_tier=QualityRequirementTier.STANDARD,
            primary_model="gpt-4o-mini",
            fallback_model="gpt-4o-mini",
            target_latency_ms=1000,
            max_input_tokens=2000,
            max_output_tokens=400,
            cost_budget_usd_per_1k=0.0006,
            caching_allowed=True,
            streaming_allowed=True,
            structured_output_required=False,
            default_prompt_version="v1.1.0"
        ),
        AITaskType.ADMIN_TEACHER_ANALYTICS: TaskProfile(
            task_type=AITaskType.ADMIN_TEACHER_ANALYTICS,
            description="Class-level mastery heatmap analysis, struggling concept trends, and recommended instructional interventions.",
            quality_tier=QualityRequirementTier.STANDARD,
            primary_model="gpt-4o-mini",
            fallback_model="gpt-4o-mini",
            target_latency_ms=1200,
            max_input_tokens=2500,
            max_output_tokens=800,
            cost_budget_usd_per_1k=0.001,
            caching_allowed=True,
            streaming_allowed=False,
            structured_output_required=True,
            default_prompt_version="v1.2.0"
        ),
        AITaskType.OTHER: TaskProfile(
            task_type=AITaskType.OTHER,
            description="General instructional helpers, adaptive activity generation, and auxiliary educational processing.",
            quality_tier=QualityRequirementTier.STANDARD,
            primary_model="gpt-4o-mini",
            fallback_model="gpt-4o-mini",
            target_latency_ms=1000,
            max_input_tokens=1000,
            max_output_tokens=500,
            cost_budget_usd_per_1k=0.001,
            caching_allowed=False,
            streaming_allowed=False,
            structured_output_required=False,
            default_prompt_version="v1.0.0"
        )
    }

    @classmethod
    def get_task_profile(cls, task_type: AITaskType | str) -> TaskProfile:
        if isinstance(task_type, str):
            try:
                task_type = AITaskType(task_type)
            except ValueError:
                task_type = AITaskType.OTHER
        return cls._INVENTORY.get(task_type, cls._INVENTORY[AITaskType.OTHER])

    @classmethod
    def list_all_tasks(cls) -> List[TaskProfile]:
        return list(cls._INVENTORY.values())
