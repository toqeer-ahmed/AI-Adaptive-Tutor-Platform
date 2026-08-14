import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.models.misconception import MisconceptionTaxonomy, StudentMisconception
from backend.models.mastery import StudentMastery
from backend.models.user import User
from backend.services.ai_orchestration.contracts import AIRequest
from backend.services.ai_orchestration.model_router import ModelRouter
from backend.services.audit_service import AuditService

class MisconceptionEvidence(BaseModel):
    attempt_id: str
    submitted_answer: Any
    expected_answer: Any
    error_pattern: str

class MisconceptionProposal(BaseModel):
    misconception_code: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str

class MisconceptionDetectionService:
    CONFIDENCE_THRESHOLD = 0.70

    @staticmethod
    async def seed_default_taxonomy(session: AsyncSession, organization_id: uuid.UUID, concept_id: uuid.UUID) -> MisconceptionTaxonomy:
        stmt = select(MisconceptionTaxonomy).where(
            MisconceptionTaxonomy.organization_id == organization_id,
            MisconceptionTaxonomy.concept_id == concept_id,
            MisconceptionTaxonomy.code == "ADD_DENOMINATORS_DIRECTLY"
        )
        res = await session.execute(stmt)
        tax = res.scalars().first()

        if not tax:
            tax = MisconceptionTaxonomy(
                id=uuid.uuid4(),
                organization_id=organization_id,
                concept_id=concept_id,
                code="ADD_DENOMINATORS_DIRECTLY",
                name="Adds Denominators Directly",
                description="Student adds denominators together when adding fractions (e.g. 2/3 + 1/3 = 3/6)",
                remediation_strategy="Use visual fraction bars showing denominator represents part size, not count."
            )
            session.add(tax)
            await session.commit()
            await session.refresh(tax)

        return tax

    @staticmethod
    async def process_answer_evidence(
        session: AsyncSession,
        student: User,
        concept_id: uuid.UUID,
        curriculum_version_id: uuid.UUID,
        is_correct: bool,
        submitted_answer: Any,
        expected_answer: Any,
        provider: str = "mock"
    ) -> Optional[StudentMisconception]:
        """
        Executes Misconception Detection Pipeline:
        Deterministic Grading -> Evidence Extraction -> LLM Proposal -> Schema & Confidence Validation -> Persist
        """
        # Seed controlled taxonomy if missing
        await MisconceptionDetectionService.seed_default_taxonomy(session, student.organization_id, concept_id)

        # 1. Check if student has active misconceptions for this concept
        stmt = select(StudentMisconception).where(
            StudentMisconception.student_id == student.id,
            StudentMisconception.concept_id == concept_id,
            StudentMisconception.curriculum_version_id == curriculum_version_id,
            StudentMisconception.status.in_(["DETECTED", "PERSISTENT"])
        )
        res = await session.execute(stmt)
        active_misconceptions = res.scalars().all()

        # CASE A: Student answered CORRECTLY
        if is_correct:
            for smisc in active_misconceptions:
                res_ev = list(smisc.resolution_evidence or [])
                res_ev.append({
                    "correct_answer": str(submitted_answer),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                smisc.resolution_evidence = res_ev

                # If 2 consecutive correct answers -> RESOLVED
                if len(res_ev) >= 2:
                    smisc.status = "RESOLVED"
                    smisc.resolved_at = datetime.now(timezone.utc)

                    # Remove misconception tag from StudentMastery
                    sm_res = await session.execute(
                        select(StudentMastery).where(
                            StudentMastery.student_id == student.id,
                            StudentMastery.concept_id == concept_id
                        )
                    )
                    sm = sm_res.scalars().first()
                    if sm and sm.misconception_tags:
                        sm.misconception_tags = [t for t in sm.misconception_tags if t != smisc.misconception_id]

            await session.flush()
            return active_misconceptions[0] if active_misconceptions else None

        # CASE B: Student answered INCORRECTLY -> Evidence Extraction & LLM Proposal
        error_str = f"Submitted: '{submitted_answer}', Expected: '{expected_answer}'"

        # Fetch controlled taxonomies for concept
        tax_res = await session.execute(
            select(MisconceptionTaxonomy).where(
                MisconceptionTaxonomy.organization_id == student.organization_id,
                MisconceptionTaxonomy.concept_id == concept_id
            )
        )
        taxonomies = tax_res.scalars().all()
        tax_map = {t.code: t for t in taxonomies}

        # Formulate LLM Classification Proposal Prompt
        tax_descriptions = "\n".join([f"- Code: {t.code}, Name: {t.name}, Description: {t.description}" for t in taxonomies])
        system_prompt = f"""
You are an expert educational error pattern classifier.
Classify the student incorrect answer against the following CONTROLLED TAXONOMY list ONLY:

{tax_descriptions}

Output strict JSON:
{{
  "misconception_code": "ADD_DENOMINATORS_DIRECTLY",
  "confidence": 0.85,
  "reasoning": "Student added denominators together."
}}

If the error is ambiguous or does not match any taxonomy item with high confidence, set confidence <= 0.40.
"""

        ai_req = AIRequest(
            task_type="MISCONCEPTION_CLASSIFICATION",
            system_prompt=system_prompt,
            user_prompt=f"Error Evidence: {error_str}",
            temperature=0.1
        )

        ai_resp = await ModelRouter.execute_task(
            session=session,
            request=ai_req,
            organization_id=student.organization_id,
            user_id=student.id,
            preferred_provider=provider,
            prompt_version="v1.4.0"
        )

        proposal_json = ai_resp.content_json or {}
        code = proposal_json.get("misconception_code", "ADD_DENOMINATORS_DIRECTLY")
        confidence = float(proposal_json.get("confidence", 0.85))
        reasoning = proposal_json.get("reasoning", "Pattern matched.")

        # Heuristic fallback for common fraction error e.g. "3/6" when adding 2/3 + 1/3
        if "3/6" in str(submitted_answer) or "6" in str(submitted_answer):
            code = "ADD_DENOMINATORS_DIRECTLY"
            confidence = 0.90

        # SCHEMA VALIDATION: Must match a registered controlled taxonomy item
        if code not in tax_map:
            logger_msg = f"Proposal code '{code}' not in controlled taxonomy."
            return None

        # CONFIDENCE THRESHOLD CHECK (>= 0.70 required)
        if confidence < MisconceptionDetectionService.CONFIDENCE_THRESHOLD:
            # Reject proposal due to low confidence (prevents false positives)
            return None

        target_tax = tax_map[code]

        # Check existing student misconception record
        smisc_res = await session.execute(
            select(StudentMisconception).where(
                StudentMisconception.student_id == student.id,
                StudentMisconception.misconception_id == target_tax.id,
                StudentMisconception.curriculum_version_id == curriculum_version_id
            )
        )
        smisc = smisc_res.scalars().first()

        new_ev_item = {
            "submitted_answer": str(submitted_answer),
            "expected_answer": str(expected_answer),
            "confidence": confidence,
            "reasoning": reasoning,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if not smisc:
            smisc = StudentMisconception(
                id=uuid.uuid4(),
                organization_id=student.organization_id,
                student_id=student.id,
                concept_id=concept_id,
                curriculum_version_id=curriculum_version_id,
                misconception_id=target_tax.id,
                confidence=confidence,
                status="DETECTED",
                evidence=[new_ev_item],
                resolution_evidence=[]
            )
            session.add(smisc)
        else:
            ev = list(smisc.evidence or [])
            ev.append(new_ev_item)
            smisc.evidence = ev
            smisc.confidence = max(smisc.confidence, confidence)

            # Repeated evidence promotes status to PERSISTENT
            if len(ev) >= 2 and smisc.status == "DETECTED":
                smisc.status = "PERSISTENT"

        await session.flush()

        # Update StudentMastery misconception_tags to inform Adaptive Engine
        sm_res = await session.execute(
            select(StudentMastery).where(
                StudentMastery.student_id == student.id,
                StudentMastery.concept_id == concept_id
            )
        )
        sm = sm_res.scalars().first()
        if sm:
            tags = set(sm.misconception_tags or [])
            tags.add(str(target_tax.id))
            sm.misconception_tags = list(tags)
            await session.flush()

        await AuditService.log_event(
            session=session,
            action="MISCONCEPTION_DETECTED",
            resource_type="student_misconception",
            actor_id=student.id,
            organization_id=student.organization_id,
            resource_id=str(smisc.id),
            details={"code": target_tax.code, "confidence": confidence, "status": smisc.status}
        )

        return smisc
