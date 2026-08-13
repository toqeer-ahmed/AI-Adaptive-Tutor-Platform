import re
from typing import Dict, Any, Tuple, List

class OutputValidator:
    @staticmethod
    def validate_extraction_output(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Executes 6-Step Output Validation on LLM curriculum extraction output.
        Returns (is_valid, list_of_validation_errors).
        """
        errors = []

        # 1. JSON Schema Validation
        required_root_keys = ["grade_level", "subject_name", "chapters"]
        for k in required_root_keys:
            if k not in data:
                errors.append(f"Schema Error: Missing root key '{k}'.")

        if errors:
            return False, errors

        # 2. Grade-Level Validation (Grades 4-8)
        grade = data.get("grade_level")
        if not isinstance(grade, int) or grade < 4 or grade > 8:
            errors.append(f"Grade Validation Error: Grade level {grade} is outside allowed range (4 to 8).")

        # 3. Structural Hierarchy Validation
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

                                # 4. Source-Reference Validation
                                if "source_page" not in cp and "source_section" not in cp:
                                    errors.append(f"Source Reference Error: Concept '{cp_name}' is missing source evidence.")

                                # 5. Duplicate Concept Detection
                                if cp_name.lower() in concept_names:
                                    errors.append(f"Duplicate Concept Error: Duplicate concept name '{cp_name}' detected.")
                                else:
                                    concept_names.add(cp_name.lower())

                                # Check Learning Objectives
                                los = cp.get("learning_objectives", [])
                                if not isinstance(los, list) or len(los) == 0:
                                    errors.append(f"Structural Error: Concept '{cp_name}' has no learning objectives.")

        # 6. Safety & Injection Guardrails Check
        json_str = str(data).lower()
        injection_keywords = ["ignore previous instructions", "system prompt", "admin access", "grant permission"]
        for kw in injection_keywords:
            if kw in json_str:
                errors.append(f"Safety Violation: Prompt injection attempt detected in LLM output ({kw}).")

        is_valid = len(errors) == 0
        return is_valid, errors
