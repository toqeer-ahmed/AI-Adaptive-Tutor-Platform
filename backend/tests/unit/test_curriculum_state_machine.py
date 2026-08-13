import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.organization_service.service import OrganizationService
from backend.services.user_service.service import UserService
from backend.services.curriculum_service.service import CurriculumService

@pytest.mark.asyncio
async def test_curriculum_version_state_machine(db_session: AsyncSession):
    org = await OrganizationService.create_organization(db_session, "State District", "STDIST")
    admin = await UserService.create_user(db_session, org.id, "admin@stdist.edu", "Pass123!", "Admin St", "OrgAdmin")

    created_curr = await CurriculumService.create_curriculum(db_session, admin, "Grade 6 Math", 6, "Mathematics")
    curr = await CurriculumService.get_curriculum_by_id(db_session, created_curr.id)
    ver = curr.versions[0]

    assert ver.status == "DRAFT"

    # DRAFT -> REVIEW
    v_rev = await CurriculumService.transition_version_status(db_session, ver.id, "REVIEW", admin)
    assert v_rev.status == "REVIEW"

    # REVIEW -> APPROVED
    v_app = await CurriculumService.transition_version_status(db_session, ver.id, "APPROVED", admin)
    assert v_app.status == "APPROVED"

    # APPROVED -> PUBLISHED
    v_pub = await CurriculumService.transition_version_status(db_session, ver.id, "PUBLISHED", admin)
    assert v_pub.status == "PUBLISHED"

    # PUBLISHED -> ARCHIVED
    v_arch = await CurriculumService.transition_version_status(db_session, ver.id, "ARCHIVED", admin)
    assert v_arch.status == "ARCHIVED"

@pytest.mark.asyncio
async def test_published_version_immutability(db_session: AsyncSession):
    org = await OrganizationService.create_organization(db_session, "State District 2", "STDIST2")
    admin = await UserService.create_user(db_session, org.id, "admin2@stdist.edu", "Pass123!", "Admin St 2", "OrgAdmin")

    created_curr = await CurriculumService.create_curriculum(db_session, admin, "Grade 6 Math", 6, "Mathematics")
    curr = await CurriculumService.get_curriculum_by_id(db_session, created_curr.id)
    ver = curr.versions[0]

    await CurriculumService.transition_version_status(db_session, ver.id, "REVIEW", admin)
    await CurriculumService.transition_version_status(db_session, ver.id, "APPROVED", admin)
    await CurriculumService.transition_version_status(db_session, ver.id, "PUBLISHED", admin)

    # Attempting to edit chapter under published version must fail
    with pytest.raises(HTTPException) as exc_info:
        await CurriculumService.create_chapter(db_session, ver.id, "Immutable Chapter")
    assert exc_info.value.status_code == 400
    assert "Immutable" in exc_info.value.detail or "PUBLISHED" in exc_info.value.detail
