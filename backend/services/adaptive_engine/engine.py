import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class AdaptiveContext(BaseModel):
    student_id: uuid.UUID
    concept_id: uuid.UUID
    curriculum_version_id: uuid.UUID
    mastery_score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    attempt_count: int = Field(ge=0)
    misconceptions: List[str] = []
    prerequisite_masteries: Dict[str, float] = {} # prereq_concept_id (str) -> mastery_score (float)
    recent_performance: List[bool] = []
    next_review_due_at: Optional[datetime] = None
    now: Optional[datetime] = None

class AdaptiveDecision(BaseModel):
    decision: str # PREREQUISITE_REMEDIATION, SPACED_REVIEW, REMEDIATE, REINFORCE, PROGRESS, CHALLENGE
    target_concept_id: str
    recommended_difficulty: int # 1 to 5
    reason: str
    priority_level: int

class AdaptiveDecisionEngine:
    """
    100% Deterministic Rule-Based Adaptive Decision Engine.
    Strictly forbids LLM calls in the decision pathway.
    """
    @classmethod
    def make_decision(cls, ctx: AdaptiveContext) -> AdaptiveDecision:
        now = ctx.now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        # -------------------------------------------------------------
        # PRIORITY 1: Weak Prerequisite Check
        # If any prerequisite has mastery < 0.70, route to Prerequisite Remediation
        # -------------------------------------------------------------
        for prereq_id_str, prereq_mastery in ctx.prerequisite_masteries.items():
            if prereq_mastery < 0.70:
                return AdaptiveDecision(
                    decision="PREREQUISITE_REMEDIATION",
                    target_concept_id=prereq_id_str,
                    recommended_difficulty=2,
                    reason=f"Prerequisite concept '{prereq_id_str[:8]}' mastery ({prereq_mastery:.2f}) is below 0.70.",
                    priority_level=1
                )

        # -------------------------------------------------------------
        # PRIORITY 2: Spaced Review Due Check
        # If spaced review date reached or passed, route to Spaced Review
        # -------------------------------------------------------------
        if ctx.next_review_due_at:
            review_due = ctx.next_review_due_at
            if review_due.tzinfo is None:
                review_due = review_due.replace(tzinfo=timezone.utc)
            if review_due <= now:
                return AdaptiveDecision(
                    decision="SPACED_REVIEW",
                    target_concept_id=str(ctx.concept_id),
                    recommended_difficulty=3,
                    reason="Spaced repetition review date has been reached.",
                    priority_level=2
                )

        # -------------------------------------------------------------
        # PRIORITY 3: Severe Remediation Check
        # mastery < 0.40 AND attempts >= 3 -> REMEDIATE
        # -------------------------------------------------------------
        if ctx.mastery_score < 0.40 and ctx.attempt_count >= 3:
            return AdaptiveDecision(
                decision="REMEDIATE",
                target_concept_id=str(ctx.concept_id),
                recommended_difficulty=1,
                reason=f"Mastery score ({ctx.mastery_score:.2f}) < 0.40 after {ctx.attempt_count} attempts.",
                priority_level=3
            )

        # -------------------------------------------------------------
        # PRIORITY 4: Challenge Check
        # mastery >= 0.90 AND recent success (last 3 attempts all True)
        # -------------------------------------------------------------
        recent = ctx.recent_performance[-3:] if len(ctx.recent_performance) >= 3 else ctx.recent_performance
        has_sustained_success = len(recent) >= 2 and all(recent)

        if ctx.mastery_score >= 0.90 and has_sustained_success:
            return AdaptiveDecision(
                decision="CHALLENGE",
                target_concept_id=str(ctx.concept_id),
                recommended_difficulty=5,
                reason=f"High mastery ({ctx.mastery_score:.2f}) with sustained recent success.",
                priority_level=4
            )

        # -------------------------------------------------------------
        # PRIORITY 5: Progress Check
        # 0.70 <= mastery < 0.90 -> PROGRESS
        # -------------------------------------------------------------
        if 0.70 <= ctx.mastery_score < 0.90:
            return AdaptiveDecision(
                decision="PROGRESS",
                target_concept_id=str(ctx.concept_id),
                recommended_difficulty=4,
                reason=f"Solid mastery ({ctx.mastery_score:.2f}); advancing to higher difficulty.",
                priority_level=5
            )

        # -------------------------------------------------------------
        # PRIORITY 6: Reinforce Check
        # 0.40 <= mastery < 0.70 -> REINFORCE
        # -------------------------------------------------------------
        if 0.40 <= ctx.mastery_score < 0.70:
            return AdaptiveDecision(
                decision="REINFORCE",
                target_concept_id=str(ctx.concept_id),
                recommended_difficulty=3,
                reason=f"Moderate mastery ({ctx.mastery_score:.2f}); reinforcing core practice.",
                priority_level=6
            )

        # -------------------------------------------------------------
        # DEFAULT FALLBACK: Insufficient attempts (mastery < 0.40 with attempts < 3)
        # -------------------------------------------------------------
        return AdaptiveDecision(
            decision="REINFORCE",
            target_concept_id=str(ctx.concept_id),
            recommended_difficulty=2,
            reason=f"Early learning phase ({ctx.attempt_count} attempts); reinforcing practice.",
            priority_level=7
        )
