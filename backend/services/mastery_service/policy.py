import uuid
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class MasteryEvent(BaseModel):
    student_id: uuid.UUID
    concept_id: uuid.UUID
    curriculum_version_id: uuid.UUID
    is_correct: bool
    item_difficulty: int = Field(default=3, ge=1, le=5)
    response_time_sec: float = 0.0
    misconceptions: List[str] = []

class MasteryUpdate(BaseModel):
    new_mastery_score: float
    new_confidence: float
    new_status: str
    attempt_count: int
    correct_count: int
    incorrect_count: int
    recent_performance: List[bool]
    next_review_due_at: datetime

class MasteryPolicyV1:
    POLICY_VERSION = "v1.0"
    MASTERY_THRESHOLD = 0.85
    CONFIDENCE_THRESHOLD = 0.60
    REMEDIATION_THRESHOLD = 0.40

    @classmethod
    def calculate_update(
        cls,
        current_mastery: float,
        current_confidence: float,
        current_attempt_count: int,
        current_correct_count: int,
        current_incorrect_count: int,
        recent_performance: List[bool],
        event: MasteryEvent,
        now: Optional[datetime] = None
    ) -> MasteryUpdate:
        if now is None:
            now = datetime.now(timezone.utc)

        # 1. Base update step K scaled by difficulty (1-5, standard = 3)
        diff_weight = float(event.item_difficulty) / 3.0
        k_step = 0.10 * diff_weight

        # 2. Mastery Score Update Formula
        if event.is_correct:
            # Mastery increase is proportional to remaining un-mastered distance (1.0 - current)
            new_mastery = min(1.0, current_mastery + k_step * (1.0 - current_mastery))
            new_correct_count = current_correct_count + 1
            new_incorrect_count = current_incorrect_count
        else:
            # Incorrect attempt reduces mastery scaled by current mastery
            new_mastery = max(0.0, current_mastery - k_step * current_mastery * 1.2)
            new_correct_count = current_correct_count
            new_incorrect_count = current_incorrect_count + 1

        new_mastery = round(new_mastery, 4)
        new_attempt_count = current_attempt_count + 1

        # 3. Confidence Calculation
        # Confidence grows asymptotically with number of practice attempts
        new_confidence = round(1.0 - (1.0 / (1.0 + 0.3 * new_attempt_count)), 4)

        # 4. Recent Performance Window (keep last 5 attempts)
        new_recent = list(recent_performance) + [event.is_correct]
        if len(new_recent) > 5:
            new_recent = new_recent[-5:]

        # 5. Status Transition Boundaries
        if new_mastery >= cls.MASTERY_THRESHOLD and new_confidence >= cls.CONFIDENCE_THRESHOLD:
            new_status = "MASTERED"
            days_until_review = 7
        elif new_mastery < cls.REMEDIATION_THRESHOLD and new_attempt_count >= 3:
            new_status = "NEEDS_REMEDIATION"
            days_until_review = 1
        else:
            new_status = "IN_PROGRESS"
            days_until_review = 3

        next_review = now + timedelta(days=days_until_review)

        return MasteryUpdate(
            new_mastery_score=new_mastery,
            new_confidence=new_confidence,
            new_status=new_status,
            attempt_count=new_attempt_count,
            correct_count=new_correct_count,
            incorrect_count=new_incorrect_count,
            recent_performance=new_recent,
            next_review_due_at=next_review
        )
