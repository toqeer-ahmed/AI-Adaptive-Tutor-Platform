import re
import json
from typing import Dict, Any, Tuple, List, Optional
from backend.services.ai_orchestration.task_registry import AITaskType

class OutputValidator:
    """
    Validates LLM structured outputs across all task categories with schema checking,
    grade constraints, duplicate checks, and bounded repair prompt generation.
    """

    @classmethod
    def validate_output(
        cls,
        task_type: AITaskType | str,
        data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        task_str = task_type.value if hasattr(task_type, "value") else str(task_type)
        if task_str == AITaskType.CURRICULUM_EXTRACTION.value:
            return cls.validate_extraction_output(data)
        elif task_str == AITaskType.QUESTION_GENERATION.value:
            return cls.validate_question_generation_output(data)
        elif task_str == AITaskType.MISCONCEPTION_CLASSIFICATION.value:
            return cls.validate_misconception_output(data)
        elif task_str == AITaskType.SUBJECTIVE_EVALUATION.value:
            return cls.validate_subjective_eval_output(data)
        elif task_str == AITaskType.ADMIN_TEACHER_ANALYTICS.value:
            return cls.validate_analytics_output(data)

        return True, []

    @staticmethod
    def validate_extraction_output(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        required_root_keys = ["grade_level", "subject_name", "chapters"]
        for k in required_root_keys:
            if k not in data:
                errors.append(f"Schema Error: Missing root key '{k}'.")

        if errors:
            return False, errors

        grade = data.get("grade_level")
        if not isinstance(grade, int) or grade < 4 or grade > 8:
            errors.append(f"Grade Validation Error: Grade level {grade} is outside allowed range (4 to 8).")

        chapters = data.get("chapters", [])
        if not isinstance(chapters, list) or len(chapters) == 0:
            errors.append("Structural Error: Extraction contains no chapters.")
        else:
            concept_names = set()
            for c_idx, ch in enumerate(chapters):
                if not ch.get("name"):
                    errors.append(f"Structural Error: Chapter {c_idx+1} is missing a name.")

                topics = ch.get("topics", [])
                if not isinstance(topics, list) or len(topics) == 0:
                    errors.append(f"Structural Error: Chapter '{ch.get('name')}' contains no topics.")
                else:
                    for t_idx, tp in enumerate(topics):
                        concepts = tp.get("concepts", [])
                        if not isinstance(concepts, list) or len(concepts) == 0:
                            errors.append(f"Structural Error: Topic '{tp.get('name')}' contains no concepts.")
                        else:
                            for cp in concepts:
                                cp_name = cp.get("name", "").strip()
                                if "source_page" not in cp and "source_section" not in cp:
                                    errors.append(f"Source Reference Error: Concept '{cp_name}' is missing source evidence.")

                                if cp_name.lower() in concept_names:
                                    errors.append(f"Duplicate Concept Error: Duplicate concept name '{cp_name}' detected.")
                                else:
                                    concept_names.add(cp_name.lower())

                                los = cp.get("learning_objectives", [])
                                if not isinstance(los, list) or len(los) == 0:
                                    errors.append(f"Structural Error: Concept '{cp_name}' has no learning objectives.")

        # Safety Check
        json_str = str(data).lower()
        injection_keywords = ["ignore previous instructions", "system prompt", "admin access", "grant permission"]
        for kw in injection_keywords:
            if kw in json_str:
                errors.append(f"Safety Violation: Prompt injection attempt detected in LLM output ({kw}).")

        return len(errors) == 0, errors

    @staticmethod
    def validate_question_generation_output(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        questions = data.get("questions")
        if not isinstance(questions, list) or len(questions) == 0:
            errors.append("Schema Error: Output must contain a non-empty 'questions' list.")
            return False, errors

        for idx, q in enumerate(questions, 1):
            if not q.get("question_text"):
                errors.append(f"Item #{idx}: Missing question_text.")
            if not q.get("question_type"):
                errors.append(f"Item #{idx}: Missing question_type.")
            if "correct_answer" not in q or q.get("correct_answer") is None:
                errors.append(f"Item #{idx}: Missing correct_answer.")

        return len(errors) == 0, errors

    @staticmethod
    def validate_misconception_output(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        required = ["misconception_code", "name", "remediation_strategy", "confidence"]
        for r in required:
            if r not in data:
                errors.append(f"Schema Error: Missing required field '{r}'.")
        return len(errors) == 0, errors

    @staticmethod
    def validate_subjective_eval_output(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        if "proposed_score" not in data or not isinstance(data["proposed_score"], (int, float)):
            errors.append("Schema Error: Missing numerical 'proposed_score'.")
        if "rationale" not in data or not data["rationale"]:
            errors.append("Schema Error: Missing 'rationale'.")
        return len(errors) == 0, errors

    @staticmethod
    def validate_analytics_output(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        if "summary" not in data:
            errors.append("Schema Error: Missing 'summary'.")
        if "struggling_concepts" not in data:
            errors.append("Schema Error: Missing 'struggling_concepts'.")
        return len(errors) == 0, errors

    @staticmethod
    def build_repair_prompt(
        original_output: str,
        validation_errors: List[str]
    ) -> str:
        """
        Builds a targeted repair instruction for the LLM without restarting full context.
        """
        errors_str = "\n".join([f"- {err}" for err in validation_errors])
        return f"""The previous output was invalid according to the required schema.

VALIDATION ERRORS:
{errors_str}

PREVIOUS OUTPUT:
{original_output}

Please fix the errors above and return ONLY the corrected, valid JSON adhering to the schema."""
