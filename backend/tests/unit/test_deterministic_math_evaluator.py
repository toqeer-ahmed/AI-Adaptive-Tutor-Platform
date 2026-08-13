import pytest
from backend.services.assessment_service.evaluator import DeterministicMathEvaluator

def test_numeric_fraction_parsing_and_evaluation():
    # 3/4 fraction
    is_correct, score, feedback = DeterministicMathEvaluator.evaluate_question(
        question_type="numeric",
        submitted_answer="3/4",
        correct_answer={"value": 0.75, "tolerance": 0.01}
    )
    assert is_correct is True
    assert score == 1.0

def test_numeric_tolerance_evaluation():
    is_correct, score, _ = DeterministicMathEvaluator.evaluate_question(
        question_type="numeric",
        submitted_answer="3.1415",
        correct_answer={"value": 3.14, "tolerance": 0.01}
    )
    assert is_correct is True

def test_mcq_evaluation():
    is_correct, score, _ = DeterministicMathEvaluator.evaluate_question(
        question_type="mcq",
        submitted_answer="B",
        correct_answer="b"
    )
    assert is_correct is True
    assert score == 1.0

def test_multi_select_evaluation():
    is_correct, score, _ = DeterministicMathEvaluator.evaluate_question(
        question_type="multi_select",
        submitted_answer=["A", "C"],
        correct_answer=["c", "a"]
    )
    assert is_correct is True

def test_ordering_evaluation():
    is_correct, score, _ = DeterministicMathEvaluator.evaluate_question(
        question_type="ordering",
        submitted_answer=["Step 1", "Step 2", "Step 3"],
        correct_answer=["Step 1", "Step 2", "Step 3"]
    )
    assert is_correct is True
