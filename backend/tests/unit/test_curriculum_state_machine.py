import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.organization_service.service import OrganizationService
from backend.services.user_service.service import UserService
from backend.services.curriculum_service.service import CurriculumService

@pytest.mark.asyncio
async def test_curriculum_version_state_machine(db_session: AsyncSession):
    org = await OrganizationService.create_organization(db_session, "Curr Org", "CURRORG")
    admin = await UserService.create_user(db_session, org.id, "admin@curr.com", "Pass123!", "Curr Admin", "OrgAdmin")

    # 1. Create Curriculum (creates Version 1 in DRAFT)
    curr = await CurriculumService.create_curriculum(db_session, admin, "Grade 6 Math", 6, "Mathematics")
    version = curr.versions[0]
    assert version.status == "DRAFT"

    # 2. DRAFT -> REVIEW
    v_review = await CurriculumService.transition_version_status(db_session, version.id, "REVIEW", admin)
    assert v_review.status == "REVIEW"

    # 3. REVIEW -> APPROVED
    v_approved = await CurriculumService.transition_version_status(db_session, version.id, "APPROVED", admin)
    assert v_approved.status == "APPROVED"
    assert v_approved.approved_by_id == admin.id

    # 4. APPROVED -> PUBLISHED
    v_pub = await CurriculumService.transition_version_status(db_session, version.id, "PUBLISHED", admin)
    assert v_pub.status == "PUBLISHED"
    assert v_pub.published_by_id == admin.id
    assert v_pub.published_at is not None

    # 5. Invalid transition from PUBLISHED back to APPROVED
    with pytest.raises(ValueError):
        await CurriculumService.transition_version_status(db_session, version.id, "APPROVED", admin)

@pytest.mark.asyncio
async def test_published_version_immutability(db_session: AsyncSession):
    org = await OrganizationService.create_organization(db_session, "Immut Org", "IMMUTORG")
    admin = await UserService.create_user(db_session, org.id, "admin@immut.com", "Pass123!", "Immut Admin", "OrgAdmin")

    curr = await CurriculumService.create_curriculum(db_session, admin, "Grade 6 Math", 6, "Mathematics")
    version = curr.versions[0]

    # Add chapter while in DRAFT
    ch = await CurriculumService.create_chapter(db_session, version.id, "Fractions")
    assert ch.name == "Fractions"

    # Publish version
    await CurriculumService.transition_version_status(db_session, version.id, "REVIEW", admin)
    await CurriculumService.transition_version_status(db_session, version.id, "APPROVED", admin)
    await CurriculumService.transition_version_status(db_session, version.id, "PUBLISHED", admin)

    # Attempt to add another chapter to PUBLISHED version -> Must throw ValueError
    with pytest.raises(ValueError) as exc:
        await CurriculumService.create_chapter(db_session, version.id, "Decimals")

    assert "cannot modify a published curriculum version" in str(exc.value).lower()
