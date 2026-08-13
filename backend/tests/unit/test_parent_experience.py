import pytest
import uuid
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.organization_service.service import OrganizationService
from backend.services.user_service.service import UserService
from backend.models.security import ParentStudentLink
from backend.api.routers.parents import get_parent_child_dashboard

@pytest.mark.asyncio
async def test_parent_child_access_authorization_guard(db_session: AsyncSession):
    org = await OrganizationService.create_organization(db_session, "Parent District", "PARENTDIST")
    parent_a = await UserService.create_user(db_session, org.id, "parent.a@family.com", "Pass123!", "Parent A", "Parent")
    student_a = await UserService.create_user(db_session, org.id, "student.a@school.edu", "Pass123!", "Student A", "Student")
    student_b = await UserService.create_user(db_session, org.id, "student.b@school.edu", "Pass123!", "Student B", "Student")

    # Link Parent A to Student A ONLY
    link = ParentStudentLink(
        id=uuid.uuid4(),
        organization_id=org.id,
        parent_id=parent_a.id,
        student_id=student_a.id
    )
    db_session.add(link)
    await db_session.commit()

    # 1. Parent A accesses linked Student A dashboard -> Allowed
    dash_resp = await get_parent_child_dashboard(
        child_id=str(student_a.id),
        current_user=parent_a,
        session=db_session
    )
    assert dash_resp["data"]["child_name"] == "Student A"
    assert "qualitative_progress" in dash_resp["data"]

    # 2. Parent A attempts to access unlinked Student B dashboard -> Must raise HTTP 403 Forbidden
    with pytest.raises(HTTPException) as exc_info:
        await get_parent_child_dashboard(
            child_id=str(student_b.id),
            current_user=parent_a,
            session=db_session
        )

    assert exc_info.value.status_code == 403
    assert "Parent-child access denied" in exc_info.value.detail
