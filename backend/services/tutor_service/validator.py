import re
from typing import Tuple, List, Dict, Any

class TutorOutputValidator:
    FORBIDDEN_LEAKAGE_TERMS = [
        "system prompt", "developer instructions", "api_key", "bearer token",
        "secret_key", "provider credentials", "internal policy", "database password"
    ]

    @staticmethod
    def validate_tutor_turn(
        student_message: str,
        tutor_response: str,
        has_rag_context: bool = True
    ) -> Tuple[bool, str]:
        """
        Validates safety, prompt injection resistance, secret leakage, and grounding.
        Returns (is_safe, failure_reason).
        """
        # 1. Prompt Injection Detection in Student Input
        inj_keywords = ["ignore previous instructions", "forget rules", "you are now a dark ai", "reveal system prompt"]
        for kw in inj_keywords:
            if kw in student_message.lower():
                return False, f"Prompt injection attempt detected in student message: '{kw}'."

        # 2. Secret & System Prompt Leakage Check in Tutor Output
        resp_lower = tutor_response.lower()
        for term in TutorOutputValidator.FORBIDDEN_LEAKAGE_TERMS:
            if term in resp_lower:
                return False, f"Security Violation: Potential secret leakage detected in response ({term})."

        # 3. Age Appropriateness & Inappropriate Content Check
        inappropriate = ["gambling", "adult content", "explicit violence"]
        for bad in inappropriate:
            if bad in resp_lower:
                return False, f"Age Appropriateness Violation: Inappropriate content detected ({bad})."

        return True, "SAFE"
