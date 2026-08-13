import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.organization_service.service import OrganizationService
from backend.services.user_service.service import UserService
from backend.services.curriculum_service.service import CurriculumService
from backend.services.misconception_service.service import MisconceptionDetectionService

@pytest.mark.asyncio
async def test_misconception_pipeline_detection_and_persistence(db_session: AsyncSession):
    org = await OrganizationService.create_organization(db_session, "Misc District", "MISCDIST")
    student = await UserService.create_user(db_session, org.id, "stud.misc@school.edu", "Pass123!", "Student Misc", "Student")

    curr = await CurriculumService.create_curriculum(db_session, student, "Grade 6 Math", 6, "Mathematics")
    ch = await CurriculumService.create_chapter(db_session, curr.versions[0].id, "Fractions")
    tp = await CurriculumService.create_topic(db_session, ch.id, "Adding Fractions")
    cp = await CurriculumService.create_concept(db_session, tp.id, "Common Denominator")

    # 1. Correct answer first -> No misconception detected
    smisc_correct = await MisconceptionDetectionService.process_answer_evidence(
        session=db_session,
        student=student,
        concept_id=cp.id,
        curriculum_version_id=curr.versions[0].id,
        is_correct=True,
        submitted_answer="1",
        expected_answer="1"
    )
    assert smisc_correct is None

    # 2. Incorrect attempt 1 ("3/6") -> DETECTED status
    smisc_1 = await MisconceptionDetectionService.process_answer_evidence(
        session=db_session,
        student=student,
        concept_id=cp.id,
        curriculum_version_id=curr.versions[0].id,
        is_correct=False,
        submitted_answer="3/6",
        expected_answer="1"
    )
    assert smisc_1 is not None
    assert smisc_1.status == "DETECTED"
    assert len(smisc_1.evidence) == 1

    # 3. Repeated incorrect attempt 2 ("3/6") -> Promoted to PERSISTENT status
    smisc_2 = await MisconceptionDetectionService.process_answer_evidence(
        session=db_session,
        student=student,
        concept_id=cp.id,
        curriculum_version_id=curr.versions[0].id,
        is_correct=False,
        submitted_answer="3/6",
        expected_answer="1"
    )
    assert smisc_2.status == "PERSISTENT"
    assert len(smisc_2.evidence) == 2

    # 4. Two consecutive correct attempts -> Transitions status to RESOLVED
    await MisconceptionDetectionService.process_answer_evidence(
        session=db_session,
        student=student,
        concept_id=cp.id,
        curriculum_version_id=curr.versions[0].id,
        is_correct=True,
        submitted_answer="1",
        expected_answer="1"
    )
    smisc_res = await MisconceptionDetectionService.process_answer_evidence(
        session=db_session,
        student=student,
        concept_id=cp.id,
        curriculum_version_id=curr.versions[0].id,
        is_correct=True,
        submitted_answer="1",
        expected_answer="1"
    )
    assert smisc_res.status == "RESOLVED"
    assert smisc_res.resolved_at is not None
