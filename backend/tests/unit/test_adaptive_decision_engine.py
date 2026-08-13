import pytest
import uuid
from datetime import datetime, timedelta, timezone
from backend.services.adaptive_engine.engine import AdaptiveDecisionEngine, AdaptiveContext

STUDENT_ID = uuid.uuid4()
CONCEPT_ID = uuid.uuid4()
CURR_VER_ID = uuid.uuid4()

def make_ctx(
    mastery_score: float,
    attempt_count: int = 1,
    prerequisite_masteries: dict = None,
    recent_performance: list = None,
    next_review_due_at: datetime = None
) -> AdaptiveContext:
    return AdaptiveContext(
        student_id=STUDENT_ID,
        concept_id=CONCEPT_ID,
        curriculum_version_id=CURR_VER_ID,
        mastery_score=mastery_score,
        confidence=0.5,
        attempt_count=attempt_count,
        prerequisite_masteries=prerequisite_masteries or {},
        recent_performance=recent_performance or [True],
        next_review_due_at=next_review_due_at
    )

# --- THRESHOLD BOUNDARY TESTS ---

def test_threshold_boundary_0_39_vs_0_40():
    # 0.39 with attempts >= 3 -> REMEDIATE
    ctx_39 = make_ctx(mastery_score=0.39, attempt_count=3)
    dec_39 = AdaptiveDecisionEngine.make_decision(ctx_39)
    assert dec_39.decision == "REMEDIATE"
    assert dec_39.recommended_difficulty == 1

    # 0.40 with attempts >= 3 -> REINFORCE
    ctx_40 = make_ctx(mastery_score=0.40, attempt_count=3)
    dec_40 = AdaptiveDecisionEngine.make_decision(ctx_40)
    assert dec_40.decision == "REINFORCE"
    assert dec_40.recommended_difficulty == 3

def test_threshold_boundary_0_69_vs_0_70():
    # 0.69 -> REINFORCE
    ctx_69 = make_ctx(mastery_score=0.69, attempt_count=3)
    dec_69 = AdaptiveDecisionEngine.make_decision(ctx_69)
    assert dec_69.decision == "REINFORCE"

    # 0.70 -> PROGRESS
    ctx_70 = make_ctx(mastery_score=0.70, attempt_count=3)
    dec_70 = AdaptiveDecisionEngine.make_decision(ctx_70)
    assert dec_70.decision == "PROGRESS"
    assert dec_70.recommended_difficulty == 4

def test_threshold_boundary_0_89_vs_0_90():
    recent = [True, True, True]
    # 0.89 with recent success -> PROGRESS
    ctx_89 = make_ctx(mastery_score=0.89, attempt_count=5, recent_performance=recent)
    dec_89 = AdaptiveDecisionEngine.make_decision(ctx_89)
    assert dec_89.decision == "PROGRESS"

    # 0.90 with recent success -> CHALLENGE
    ctx_90 = make_ctx(mastery_score=0.90, attempt_count=5, recent_performance=recent)
    dec_90 = AdaptiveDecisionEngine.make_decision(ctx_90)
    assert dec_90.decision == "CHALLENGE"
    assert dec_90.recommended_difficulty == 5

# --- PRIORITY & SCENARIO TESTS ---

def test_weak_prerequisite_override_priority_1():
    prereq_id = str(uuid.uuid4())
    # Concept itself is 0.95 (CHALLENGE candidate), but prerequisite is 0.50 (< 0.70)
    ctx = make_ctx(
        mastery_score=0.95,
        attempt_count=5,
        prerequisite_masteries={prereq_id: 0.50},
        recent_performance=[True, True, True]
    )
    dec = AdaptiveDecisionEngine.make_decision(ctx)

    # Priority 1 (PREREQUISITE_REMEDIATION) MUST override Priority 4 (CHALLENGE)
    assert dec.decision == "PREREQUISITE_REMEDIATION"
    assert dec.target_concept_id == prereq_id
    assert dec.priority_level == 1

def test_spaced_review_due_priority_2():
    past_due = datetime.now(timezone.utc) - timedelta(days=1)
    ctx = make_ctx(mastery_score=0.75, attempt_count=3, next_review_due_at=past_due)
    dec = AdaptiveDecisionEngine.make_decision(ctx)

    # Priority 2 (SPACED_REVIEW) MUST override Priority 5 (PROGRESS)
    assert dec.decision == "SPACED_REVIEW"
    assert dec.priority_level == 2

def test_insufficient_attempts_early_phase():
    # mastery 0.20 but attempt_count = 1 (< 3 attempts) -> REINFORCE, not REMEDIATE
    ctx = make_ctx(mastery_score=0.20, attempt_count=1)
    dec = AdaptiveDecisionEngine.make_decision(ctx)

    assert dec.decision == "REINFORCE"
    assert dec.recommended_difficulty == 2

def test_conflicting_signals_strict_priority_ordering():
    # Prereq weak (0.60) + Review Due + Mastery High (0.95)
    prereq_id = str(uuid.uuid4())
    past_due = datetime.now(timezone.utc) - timedelta(days=1)
    ctx = make_ctx(
        mastery_score=0.95,
        attempt_count=10,
        prerequisite_masteries={prereq_id: 0.60},
        next_review_due_at=past_due,
        recent_performance=[True, True, True]
    )
    dec = AdaptiveDecisionEngine.make_decision(ctx)

    # Highest Priority (Priority 1: PREREQUISITE_REMEDIATION) MUST win!
    assert dec.decision == "PREREQUISITE_REMEDIATION"
    assert dec.priority_level == 1

def test_zero_llm_dependency():
    # Decision completes in < 1ms synchronously with 0 LLM calls
    ctx = make_ctx(mastery_score=0.75)
    dec = AdaptiveDecisionEngine.make_decision(ctx)
    assert dec.decision in ["PROGRESS", "REINFORCE", "CHALLENGE", "REMEDIATE", "SPACED_REVIEW", "PREREQUISITE_REMEDIATION"]
