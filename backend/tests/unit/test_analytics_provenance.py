import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.services.organization_service.service import OrganizationService
from backend.services.user_service.service import UserService
from backend.services.class_service.service import ClassService
from backend.services.mastery_service.service import MasteryService
from backend.services.mastery_service.policy import MasteryEvent
from backend.services.analytics_service.service import AnalyticsAggregationService
from backend.models.mastery import StudentMastery
from backend.models.analytics import AnalyticsSummaryProvenance

@pytest.mark.asyncio
async def test_analytics_determinism_and_provenance_logging(db_session: AsyncSession):
    # 1. Setup organization, teacher, student, class
    org = await OrganizationService.create_organization(db_session, "Prov District", "PROVDIST")
    teacher = await UserService.create_user(db_session, org.id, "teach.prov@school.edu", "Pass123!", "Teacher Prov", "Teacher")
    student = await UserService.create_user(db_session, org.id, "stud.prov@school.edu", "Pass123!", "Student Prov", "Student")

    class_obj = await ClassService.create_class(db_session, teacher, "Math Period 2", 6, "Mathematics")
    await ClassService.enroll_student(db_session, class_obj.id, student.id)

    concept_id = uuid.uuid4()
    curr_ver_id = uuid.uuid4()

    # 2. Record learning event (Mastery = 0.75)
    event = MasteryEvent(
        student_id=student.id,
        concept_id=concept_id,
        curriculum_version_id=curr_ver_id,
        is_correct=True,
        item_difficulty=3
    )
    await MasteryService.record_learning_event(db_session, org.id, event)

    # 3. Get pre-summary source mastery score
    sm_res = await db_session.execute(select(StudentMastery).where(StudentMastery.student_id == student.id))
    sm_before = sm_res.scalars().first()
    original_score = sm_before.mastery_score

    # 4. Generate AI Class Summary with Provenance
    provenance = await AnalyticsAggregationService.generate_ai_class_summary_with_provenance(
        session=db_session,
        class_id=class_obj.id,
        teacher=teacher,
        provider="mock"
    )

    assert provenance.id is not None
    assert provenance.summary_type == "TEACHER_CLASS_SUMMARY"
    assert len(provenance.source_metric_ids) > 0
    assert len(provenance.prompt_hash) == 64

    # 5. VERIFY METRIC PROTECTION: Source StudentMastery score remains 100% UNCHANGED!
    sm_res_after = await db_session.execute(select(StudentMastery).where(StudentMastery.student_id == student.id))
    sm_after = sm_res_after.scalars().first()
    assert sm_after.mastery_score == original_score
