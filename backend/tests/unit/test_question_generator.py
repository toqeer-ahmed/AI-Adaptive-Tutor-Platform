import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.organization_service.service import OrganizationService
from backend.services.user_service.service import UserService
from backend.services.curriculum_service.service import CurriculumService
from backend.services.assessment_service.question_generator import QuestionGenerationEngine

@pytest.mark.asyncio
async def test_ai_question_generation_and_validation(db_session: AsyncSession):
    org = await OrganizationService.create_organization(db_session, "Ass District", "ASSDIST")
    teacher = await UserService.create_user(db_session, org.id, "t@assdist.edu", "Pass123!", "T Ass", "Teacher")

    curr = await CurriculumService.create_curriculum(db_session, teacher, "Grade 6 Math", 6, "Mathematics")
    ch = await CurriculumService.create_chapter(db_session, curr.versions[0].id, "Fractions")
    tp = await CurriculumService.create_topic(db_session, ch.id, "Adding Fractions")
    cp = await CurriculumService.create_concept(db_session, tp.id, "Common Denominator")

    items = await QuestionGenerationEngine.generate_questions_for_concept(
        session=db_session,
        concept_id=cp.id,
        creator=teacher,
        count=5,
        provider="mock"
    )

    assert len(items) > 0
    # Items created via generation are placed in PROPOSED or REJECTED status
    for item in items:
        assert item.validation_status in ["PROPOSED", "REJECTED"]
