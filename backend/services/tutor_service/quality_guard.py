import re
from dataclasses import dataclass
from typing import Tuple, List, Optional

@dataclass
class PedagogicalQualityReport:
    is_acceptable: bool
    grade_level_score: float # Readability score mapped to grade 4-8
    has_premature_answer_leak: bool
    is_socratic_compliant: bool
    has_emotional_dependency_risk: bool
    word_count: int
    feedback_notes: List[str]

class TutorQualityGuard:
    """
    Evaluates AI Tutor responses against pedagogical standards:
    1. Prevents premature answer revelation in HINT or GUIDED_PRACTICE modes.
    2. Enforces concise, Grade 4-8 readability.
    3. Checks for Socratic guiding question presence.
    4. Guards against emotional dependency phrases ("you need me", "only I can teach you").
    """

    ANSWER_LEAK_PATTERNS = [
        r'\bthe answer is\b',
        r'\bthe correct answer is\b',
        r'\bthe solution is\b',
        r'\bequals\s*=\s*\d+',
        r'\bso the answer would be\b'
    ]

    EMOTIONAL_DEPENDENCY_PATTERNS = [
        r'\byou cannot do this without me\b',
        r'\balways rely on me\b',
        r'\bi am your only friend\b',
        r'\bkeep this secret\b',
        r'\bdon\'t tell your teacher\b',
        r'\bdon\'t tell your parents\b'
    ]

    @classmethod
    def evaluate_tutor_response(
        cls,
        mode: str,
        grade: int,
        response_text: str
    ) -> PedagogicalQualityReport:
        notes = []
        words = response_text.split()
        word_count = len(words)

        # 1. Premature answer revelation check in Hint / Guided Practice
        has_leak = False
        if mode in ["hint", "guided_practice", "socratic"]:
            for pat in cls.ANSWER_LEAK_PATTERNS:
                if re.search(pat, response_text, re.IGNORECASE):
                    has_leak = True
                    notes.append("Potential premature answer leak detected in interactive mode.")
                    break

        # 2. Emotional dependency check
        has_dep_risk = False
        for pat in cls.EMOTIONAL_DEPENDENCY_PATTERNS:
            if re.search(pat, response_text, re.IGNORECASE):
                has_dep_risk = True
                notes.append("Violation: Emotional dependency or secrecy phrase detected.")
                break

        # 3. Socratic Compliance Check (should contain at least one question mark when guiding)
        is_socratic = True
        if mode in ["socratic", "guided_practice"] and "?" not in response_text:
            is_socratic = False
            notes.append("Warning: Socratic/Guided mode response lacks a guiding question.")

        # 4. Verbosity / Readability Check
        if word_count > 250:
            notes.append(f"Verbosity warning: Response is {word_count} words (exceeds recommended 250 words).")

        # Estimate grade readability (simple average syllable heuristic)
        avg_word_length = sum(len(w) for w in words) / max(1, word_count)
        estimated_grade = round(min(8.0, max(4.0, (avg_word_length - 3.0) * 2.5 + 4.0)), 1)

        is_acceptable = not has_dep_risk and not (has_leak and mode in ["hint", "guided_practice", "socratic"])

        return PedagogicalQualityReport(
            is_acceptable=is_acceptable,
            grade_level_score=estimated_grade,
            has_premature_answer_leak=has_leak,
            is_socratic_compliant=is_socratic,
            has_emotional_dependency_risk=has_dep_risk,
            word_count=word_count,
            feedback_notes=notes
        )
