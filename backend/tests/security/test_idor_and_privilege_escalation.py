import pytest
import uuid
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.organization_service.service import OrganizationService, SchoolService
from backend.services.user_service.service import UserService, ClassService
from backend.services.user_service.auth import create_access_token
from backend.models.security import ParentStudentLink, SupportGrant

@pytest.mark.asyncio
async def test_teacher_horizontal_escalation_forbidden(async_client: AsyncClient, db_session: AsyncSession):
    # Setup Org and School
    org = await OrganizationService.create_organization(db_session, "District 1", "DIST1")
    school = await SchoolService.create_school(db_session, org.id, "Main School", "MAIN")

    # Teacher A and Teacher B
    teacher_a = await UserService.create_user(db_session, org.id, "t_a@dist1.edu", "Pass123!", "Teacher A", "Teacher", school.id)
    teacher_b = await UserService.create_user(db_session, org.id, "t_b@dist1.edu", "Pass123!", "Teacher B", "Teacher", school.id)

    # Class B owned by Teacher B
    class_b = await ClassService.create_class(db_session, org.id, school.id, teacher_b.id, "Science 6", 6, "2026")

    # Auth token for Teacher A
    token_a, _ = create_access_token(str(teacher_a.id), str(org.id), roles=["Teacher"])
    headers = {"Authorization": f"Bearer {token_a}"}

    # Teacher A tries to access Class B
    res = await async_client.get(f"/api/v1/classes/{class_b.id}", headers=headers)
    assert res.status_code == 403
    assert "not assigned" in res.json()["detail"].lower()

@pytest.mark.asyncio
async def test_student_horizontal_escalation_forbidden(async_client: AsyncClient, db_session: AsyncSession):
    org = await OrganizationService.create_organization(db_session, "District 2", "DIST2")
    student_a = await UserService.create_user(db_session, org.id, "s_a@dist2.edu", "Pass123!", "Student A", "Student")
    student_b = await UserService.create_user(db_session, org.id, "s_b@dist2.edu", "Pass123!", "Student B", "Student")

    token_a, _ = create_access_token(str(student_a.id), str(org.id), roles=["Student"])
    headers = {"Authorization": f"Bearer {token_a}"}

    # Student A tries to view Student B's record
    res = await async_client.get(f"/api/v1/users/{student_b.id}", headers=headers)
    assert res.status_code == 401 or res.status_code == 403

@pytest.mark.asyncio
async def test_parent_horizontal_escalation_forbidden(async_client: AsyncClient, db_session: AsyncSession):
    org = await OrganizationService.create_organization(db_session, "District 3", "DIST3")
    parent_a = await UserService.create_user(db_session, org.id, "p_a@dist3.edu", "Pass123!", "Parent A", "Parent")
    parent_b = await UserService.create_user(db_session, org.id, "p_b@dist3.edu", "Pass123!", "Parent B", "Parent")
    child_b = await UserService.create_user(db_session, org.id, "c_b@dist3.edu", "Pass123!", "Child B", "Student")

    # Link Parent B to Child B
    link = ParentStudentLink(
        id=uuid.uuid4(),
        organization_id=org.id,
        parent_id=parent_b.id,
        student_id=child_b.id
    )
    db_session.add(link)
    await db_session.commit()

    token_parent_a, _ = create_access_token(str(parent_a.id), str(org.id), roles=["Parent"])
    headers = {"Authorization": f"Bearer {token_parent_a}"}

    # Parent A attempts to access Parent B's Child B details
    res = await async_client.get(f"/api/v1/parents/children/{child_b.id}", headers=headers)
    assert res.status_code in [401, 403, 404]

@pytest.mark.asyncio
async def test_support_user_scope_gating(async_client: AsyncClient, db_session: AsyncSession):
    org = await OrganizationService.create_organization(db_session, "District 4", "DIST4")
    support_user = await UserService.create_user(db_session, org.id, "support@company.com", "Pass123!", "Support Agent", "Support")

    token_supp, _ = create_access_token(str(support_user.id), str(org.id), roles=["Support"])
    headers = {"Authorization": f"Bearer {token_supp}"}

    # Support user without active grant tries to list org audit logs
    res = await async_client.get("/api/v1/audit-logs", headers=headers)
    assert res.status_code == 403
