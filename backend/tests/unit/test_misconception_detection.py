import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.organization_service.service import OrganizationService
from backend.services.user_service.service import UserService
from backend.services.curriculum_service.service import CurriculumService
from backend.services.misconception_service.service import MisconceptionDetectionService

@pytest.mark.asyncio
async def test_adding_fractions_adds_denominators_directly_misconception(db_session: AsyncSession):
    org = await OrganizationService.create_organization(db_session, "Misc District", "MISCDIST")
    student = await UserService.create_user(db_session, org.id, "stud@misc.edu", "Pass123!", "Stud Misc", "Student")

    created_curr = await CurriculumService.create_curriculum(db_session, student, "Grade 6 Math", 6, "Mathematics")
    curr = await CurriculumService.get_curriculum_by_id(db_session, created_curr.id)
    ch = await CurriculumService.create_chapter(db_session, curr.versions[0].id, "Fractions")
    tp = await CurriculumService.create_topic(db_session, ch.id, "Adding Fractions")
    cp = await CurriculumService.create_concept(db_session, tp.id, "Common Denominator")

    # Incorrect answer adding denominators directly (e.g. 1/3 + 1/4 = 3/6)
    smisc = await MisconceptionDetectionService.process_answer_evidence(
        session=db_session,
        student=student,
        concept_id=cp.id,
        curriculum_version_id=curr.versions[0].id,
        is_correct=False,
        submitted_answer="3/6",
        expected_answer="7/12",
        provider="mock"
    )

    assert smisc is not None
    assert smisc.status in ["DETECTED", "PERSISTENT"]
    assert smisc.student_id == student.id

@pytest.mark.asyncio
async def test_correct_answer_clears_or_does_not_trigger_misconception(db_session: AsyncSession):
    org = await OrganizationService.create_organization(db_session, "Misc District 2", "MISCDIST2")
    student = await UserService.create_user(db_session, org.id, "stud2@misc.edu", "Pass123!", "Stud Misc 2", "Student")

    created_curr = await CurriculumService.create_curriculum(db_session, student, "Grade 6 Math", 6, "Mathematics")
    curr = await CurriculumService.get_curriculum_by_id(db_session, created_curr.id)
    ch = await CurriculumService.create_chapter(db_session, curr.versions[0].id, "Fractions")
    tp = await CurriculumService.create_topic(db_session, ch.id, "Adding Fractions")
    cp = await CurriculumService.create_concept(db_session, tp.id, "Common Denominator")

    # Correct answer 7/12
    smisc = await MisconceptionDetectionService.process_answer_evidence(
        session=db_session,
        student=student,
        concept_id=cp.id,
        curriculum_version_id=curr.versions[0].id,
        is_correct=True,
        submitted_answer="7/12",
        expected_answer="7/12",
        provider="mock"
    )

    assert smisc is None
