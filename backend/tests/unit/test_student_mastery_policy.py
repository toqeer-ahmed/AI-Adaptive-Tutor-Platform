import pytest
import uuid
from datetime import datetime, timezone
from backend.services.mastery_service.policy import MasteryPolicyV1, MasteryEvent

STUDENT_ID = uuid.uuid4()
CONCEPT_ID = uuid.uuid4()
CURR_VER_ID = uuid.uuid4()

def make_event(is_correct: bool, difficulty: int = 3) -> MasteryEvent:
    return MasteryEvent(
        student_id=STUDENT_ID,
        concept_id=CONCEPT_ID,
        curriculum_version_id=CURR_VER_ID,
        is_correct=is_correct,
        item_difficulty=difficulty
    )

def test_first_attempt_correct():
    event = make_event(is_correct=True, difficulty=3)
    update = MasteryPolicyV1.calculate_update(
        current_mastery=0.0,
        current_confidence=0.0,
        current_attempt_count=0,
        current_correct_count=0,
        current_incorrect_count=0,
        recent_performance=[],
        event=event
    )

    assert update.new_mastery_score > 0.0
    assert update.attempt_count == 1
    assert update.correct_count == 1
    assert update.new_status == "IN_PROGRESS"

def test_repeated_correct_climbing_to_mastered():
    mastery = 0.0
    confidence = 0.0
    attempts = 0
    correct = 0
    incorrect = 0
    recent = []

    # Simulate 10 consecutive correct answers
    for i in range(10):
        event = make_event(is_correct=True, difficulty=3)
        u = MasteryPolicyV1.calculate_update(
            current_mastery=mastery,
            current_confidence=confidence,
            current_attempt_count=attempts,
            current_correct_count=correct,
            current_incorrect_count=incorrect,
            recent_performance=recent,
            event=event
        )
        mastery = u.new_mastery_score
        confidence = u.new_confidence
        attempts = u.attempt_count
        correct = u.correct_count
        recent = u.recent_performance

    assert mastery >= 0.85
    assert confidence >= 0.60
    assert u.new_status == "MASTERED"

def test_repeated_incorrect_dropping_to_remediation():
    mastery = 0.50
    confidence = 0.20
    attempts = 0
    correct = 0
    incorrect = 0
    recent = []

    for i in range(4):
        event = make_event(is_correct=False, difficulty=3)
        u = MasteryPolicyV1.calculate_update(
            current_mastery=mastery,
            current_confidence=confidence,
            current_attempt_count=attempts,
            current_correct_count=correct,
            current_incorrect_count=incorrect,
            recent_performance=recent,
            event=event
        )
        mastery = u.new_mastery_score
        confidence = u.new_confidence
        attempts = u.attempt_count
        incorrect = u.incorrect_count
        recent = u.recent_performance

    assert mastery < 0.40
    assert attempts >= 3
    assert u.new_status == "NEEDS_REMEDIATION"

def test_difficulty_scaling_easy_vs_hard():
    # Easy question (Difficulty 1)
    u_easy = MasteryPolicyV1.calculate_update(
        current_mastery=0.0, current_confidence=0.0, current_attempt_count=0,
        current_correct_count=0, current_incorrect_count=0, recent_performance=[],
        event=make_event(is_correct=True, difficulty=1)
    )

    # Hard question (Difficulty 5)
    u_hard = MasteryPolicyV1.calculate_update(
        current_mastery=0.0, current_confidence=0.0, current_attempt_count=0,
        current_correct_count=0, current_incorrect_count=0, recent_performance=[],
        event=make_event(is_correct=True, difficulty=5)
    )

    # Hard question correct answer yields larger mastery gain than easy question
    assert u_hard.new_mastery_score > u_easy.new_mastery_score

def test_mastery_near_thresholds():
    # Mastery 0.84 (just below 0.85 threshold) -> Should be IN_PROGRESS
    u_below = MasteryPolicyV1.calculate_update(
        current_mastery=0.83, current_confidence=0.70, current_attempt_count=5,
        current_correct_count=4, current_incorrect_count=1, recent_performance=[],
        event=make_event(is_correct=True, difficulty=1)
    )
    # Output mastery ~ 0.835 -> IN_PROGRESS
    if u_below.new_mastery_score < 0.85:
        assert u_below.new_status == "IN_PROGRESS"

def test_deterministic_reproducibility():
    # Given the exact same sequence of events, output MUST be identical
    events = [make_event(True, 3), make_event(False, 3), make_event(True, 4), make_event(True, 5)]

    def run_sequence():
        m, c, att, cor, inc, rec = 0.0, 0.0, 0, 0, 0, []
        for ev in events:
            u = MasteryPolicyV1.calculate_update(m, c, att, cor, inc, rec, ev)
            m, c, att, cor, inc, rec = u.new_mastery_score, u.new_confidence, u.attempt_count, u.correct_count, u.incorrect_count, u.recent_performance
        return m, c, u.new_status

    run1 = run_sequence()
    run2 = run_sequence()

    # Exact deterministic equality
    assert run1 == run2
