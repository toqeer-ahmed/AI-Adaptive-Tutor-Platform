import uuid
import hashlib
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.models.class_model import Class, Enrollment
from backend.models.mastery import StudentMastery
from backend.models.misconception import StudentMisconception
from backend.models.assessment import AssessmentAttempt
from backend.models.analytics import AnalyticsSummaryProvenance
from backend.models.user import User
from backend.services.ai_orchestration.contracts import AIRequest
from backend.services.ai_orchestration.model_router import ModelRouter

class AnalyticsAggregationService:
    @staticmethod
    async def get_deterministic_class_metrics(
        session: AsyncSession,
        class_id: uuid.UUID,
        organization_id: uuid.UUID
    ) -> Dict[str, Any]:
        cls_stmt = select(Class).where(Class.id == class_id, Class.organization_id == organization_id)
        cls_res = await session.execute(cls_stmt)
        class_obj = cls_res.scalars().first()
        if not class_obj:
            raise ValueError("Class not found or organization mismatch.")

        enr_stmt = select(Enrollment).options(selectinload(Enrollment.student)).where(Enrollment.class_id == class_id)
        enr_res = await session.execute(enr_stmt)
        enrollments = enr_res.scalars().all()
        student_ids = [e.student_id for e in enrollments]

        if not student_ids:
            return {
                "class_id": str(class_id),
                "class_name": class_obj.name,
                "student_count": 0,
                "class_average_mastery": 0.0,
                "concept_heatmap": [],
                "students_remediation": [],
                "students_challenge": [],
                "misconception_trends": [],
                "completion_rate": 1.0,
                "source_metric_ids": []
            }

        sm_stmt = select(StudentMastery).where(StudentMastery.student_id.in_(student_ids))
        sm_res = await session.execute(sm_stmt)
        masteries = sm_res.scalars().all()

        source_metric_ids = [str(m.id) for m in masteries]
        avg_mastery = sum(m.mastery_score for m in masteries) / len(masteries) if masteries else 0.0

        remediation = []
        challenge = []
        student_map = {e.student_id: e.student.full_name for e in enrollments if e.student}

        for m in masteries:
            s_name = student_map.get(m.student_id, "Student")
            if m.mastery_score < 0.40 and s_name not in [s["name"] for s in remediation]:
                remediation.append({"student_id": str(m.student_id), "name": s_name, "mastery_score": m.mastery_score})
            elif m.mastery_score >= 0.90 and s_name not in [s["name"] for s in challenge]:
                challenge.append({"student_id": str(m.student_id), "name": s_name, "mastery_score": m.mastery_score})

        # Misconception Trends
        misc_stmt = select(StudentMisconception).options(selectinload(StudentMisconception.taxonomy)).where(
            StudentMisconception.student_id.in_(student_ids),
            StudentMisconception.status.in_(["DETECTED", "PERSISTENT"])
        )
        misc_res = await session.execute(misc_stmt)
        misconceptions = misc_res.scalars().all()

        source_metric_ids.extend([str(mc.id) for mc in misconceptions])

        misc_counts: Dict[str, Dict[str, Any]] = {}
        for m in misconceptions:
            code = m.taxonomy.code if m.taxonomy else "UNKNOWN"
            name = m.taxonomy.name if m.taxonomy else "Misconception"
            if code not in misc_counts:
                misc_counts[code] = {"code": code, "name": name, "count": 0}
            misc_counts[code]["count"] += 1

        return {
            "class_id": str(class_id),
            "class_name": class_obj.name,
            "student_count": len(student_ids),
            "class_average_mastery": round(avg_mastery, 2),
            "remediation_count": len(remediation),
            "challenge_count": len(challenge),
            "misconception_trends": list(misc_counts.values()),
            "source_metric_ids": source_metric_ids
        }

    @staticmethod
    async def generate_ai_class_summary_with_provenance(
        session: AsyncSession,
        class_id: uuid.UUID,
        teacher: User,
        provider: str = "mock"
    ) -> AnalyticsSummaryProvenance:
        metrics = await AnalyticsAggregationService.get_deterministic_class_metrics(session, class_id, teacher.organization_id)

        system_prompt = """
You are a helpful educational analytics summary assistant.
Summarize the pre-computed class metrics for the teacher in clear, encouraging natural language.

RULES:
- Do NOT make up any metrics or change any scores.
- Use the exact numbers provided in the input JSON.
"""

        user_prompt = f"Deterministic Metrics: {metrics}"
        prompt_hash = hashlib.sha256((system_prompt + user_prompt).encode('utf-8')).hexdigest()

        ai_req = AIRequest(
            task_type="ANALYTICS_SUMMARY",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2
        )

        ai_resp = await ModelRouter.execute_task(
            session=session,
            request=ai_req,
            organization_id=teacher.organization_id,
            user_id=teacher.id,
            preferred_provider=provider
        )

        summary_text = ai_resp.content_text or (
            f"Class '{metrics['class_name']}' is averaging {metrics['class_average_mastery'] * 100}% mastery with "
            f"{metrics['remediation_count']} students needing remediation and {metrics['challenge_count']} ready for challenge."
        )

        provenance = AnalyticsSummaryProvenance(
            id=uuid.uuid4(),
            organization_id=teacher.organization_id,
            summary_type="TEACHER_CLASS_SUMMARY",
            source_metric_ids=metrics["source_metric_ids"],
            generated_summary_text=summary_text,
            ai_model_name=ai_resp.model or "gpt-4o-mini",
            prompt_hash=prompt_hash
        )

        session.add(provenance)
        await session.commit()
        await session.refresh(provenance)

        return provenance
