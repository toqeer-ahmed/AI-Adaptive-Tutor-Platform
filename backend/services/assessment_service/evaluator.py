import re
import ast
from typing import Any, Tuple, List, Dict

class DeterministicMathEvaluator:
    @staticmethod
    def parse_numeric_val(val: Any) -> float:
        if isinstance(val, (int, float)):
            return float(val)

        val_str = str(val).strip()

        # Handle fractions e.g. "3/4"
        if "/" in val_str:
            parts = val_str.split("/")
            if len(parts) == 2:
                num = float(parts[0].strip())
                den = float(parts[1].strip())
                if den != 0:
                    return num / den

        # Safe arithmetic evaluation via AST
        try:
            parsed = ast.literal_eval(val_str)
            return float(parsed)
        except Exception:
            # Fallback regex extraction of leading float
            match = re.search(r"[-+]?\d*\.\d+|\d+", val_str)
            if match:
                return float(match.group(0))
            raise ValueError(f"Unable to parse numeric value from '{val}'.")

    @staticmethod
    def evaluate_question(question_type: str, submitted_answer: Any, correct_answer: Any) -> Tuple[bool, float, str]:
        """
        Deterministically evaluates student answer against correct answer.
        Returns (is_correct, points_multiplier, feedback).
        """
        qtype = question_type.lower()

        # 1. MCQ
        if qtype == "mcq":
            sub = str(submitted_answer).strip().upper()
            exp = str(correct_answer).strip().upper()
            is_correct = (sub == exp)
            return is_correct, 1.0 if is_correct else 0.0, "Correct!" if is_correct else f"Incorrect. Correct answer is {exp}."

        # 2. Multi-Select
        elif qtype == "multi_select":
            sub_set = set([str(x).strip().upper() for x in (submitted_answer if isinstance(submitted_answer, list) else [submitted_answer])])
            exp_set = set([str(x).strip().upper() for x in (correct_answer if isinstance(correct_answer, list) else [correct_answer])])
            is_correct = (sub_set == exp_set)
            return is_correct, 1.0 if is_correct else 0.0, "Correct!" if is_correct else "Incorrect selection."

        # 3. True / False
        elif qtype == "true_false":
            sub_b = str(submitted_answer).strip().lower() in ["true", "1", "t", "yes"]
            exp_b = str(correct_answer).strip().lower() in ["true", "1", "t", "yes"]
            is_correct = (sub_b == exp_b)
            return is_correct, 1.0 if is_correct else 0.0, "Correct!" if is_correct else f"Incorrect. Correct answer is {exp_b}."

        # 4. Fill-in-the-Blank
        elif qtype == "fill_blank":
            sub_str = str(submitted_answer).strip().lower()
            if isinstance(correct_answer, list):
                is_correct = any(sub_str == str(ans).strip().lower() for ans in correct_answer)
            else:
                is_correct = (sub_str == str(correct_answer).strip().lower())
            return is_correct, 1.0 if is_correct else 0.0, "Correct!" if is_correct else f"Incorrect."

        # 5. Numeric (Deterministic Computation with Tolerance)
        elif qtype == "numeric":
            try:
                sub_num = DeterministicMathEvaluator.parse_numeric_val(submitted_answer)

                if isinstance(correct_answer, dict):
                    exp_num = float(correct_answer.get("value", 0.0))
                    tolerance = float(correct_answer.get("tolerance", 0.001))
                else:
                    exp_num = DeterministicMathEvaluator.parse_numeric_val(correct_answer)
                    tolerance = 0.001

                is_correct = abs(sub_num - exp_num) <= tolerance
                return is_correct, 1.0 if is_correct else 0.0, "Correct!" if is_correct else f"Incorrect. Expected {exp_num} (±{tolerance})."
            except ValueError as e:
                return False, 0.0, f"Invalid numeric input format: {e}"

        # 6. Matching
        elif qtype == "matching":
            if isinstance(submitted_answer, dict) and isinstance(correct_answer, dict):
                is_correct = (submitted_answer == correct_answer)
            else:
                is_correct = False
            return is_correct, 1.0 if is_correct else 0.0, "Correct matching!" if is_correct else "Incorrect pairs."

        # 7. Ordering
        elif qtype == "ordering":
            if isinstance(submitted_answer, list) and isinstance(correct_answer, list):
                is_correct = (submitted_answer == correct_answer)
            else:
                is_correct = False
            return is_correct, 1.0 if is_correct else 0.0, "Correct sequence!" if is_correct else "Incorrect sequence."

        # 8. Short Answer (Basic Exact/Keyword match fallback)
        else:
            sub_str = str(submitted_answer).strip().lower()
            exp_str = str(correct_answer).strip().lower()
            is_correct = (exp_str in sub_str or sub_str in exp_str)
            return is_correct, 1.0 if is_correct else 0.0, "Graded."
