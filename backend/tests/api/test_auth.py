import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.organization_service.service import OrganizationService
from backend.services.user_service.service import UserService, ClassService

@pytest.mark.asyncio
async def test_end_to_end_phase_0_flow(async_client: AsyncClient, db_session: AsyncSession):
    # 1. Create Organization
    org = await OrganizationService.create_organization(db_session, "Springfield District", "SPRINGFIELD")

    # 2. Create OrgAdmin User
    admin = await UserService.create_user(
        db_session,
        organization_id=org.id,
        email="admin@springfield.edu",
        password="AdminSecretPassword123!",
        full_name="Springfield Admin",
        role_name="OrgAdmin"
    )

    # 3. Login to get access token
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@springfield.edu", "password": "AdminSecretPassword123!"}
    )
    assert login_res.status_code == 200
    token_data = login_res.json()["data"]
    access_token = token_data["access_token"]
    assert access_token is not None

    headers = {"Authorization": f"Bearer {access_token}"}

    # 4. Create School
    school_res = await async_client.post(
        f"/api/v1/organizations/{org.id}/schools",
        json={"name": "Springfield Elementary", "code": "SP-ELEM"},
        headers=headers
    )
    assert school_res.status_code == 200
    school_id = school_res.json()["data"]["id"]

    # 5. Create Teacher & Student
    teacher = await UserService.create_user(
        db_session,
        organization_id=org.id,
        email="teacher@springfield.edu",
        password="TeacherPassword123!",
        full_name="Mrs. Krabappel",
        role_name="Teacher",
        school_id=school_id
    )

    student = await UserService.create_user(
        db_session,
        organization_id=org.id,
        email="bart@springfield.edu",
        password="StudentPassword123!",
        full_name="Bart Simpson",
        role_name="Student",
        school_id=school_id
    )

    # 6. Create Class
    class_res = await async_client.post(
        "/api/v1/classes",
        json={
            "school_id": school_id,
            "teacher_id": str(teacher.id),
            "name": "Grade 4 Mathematics",
            "grade_level": 4,
            "academic_year": "2026-2027"
        },
        headers=headers
    )
    assert class_res.status_code == 200
    class_id = class_res.json()["data"]["id"]

    # 7. Enroll Student in Class
    enroll_res = await async_client.post(
        f"/api/v1/classes/{class_id}/enroll",
        json={"student_id": str(student.id)},
        headers=headers
    )
    assert enroll_res.status_code == 200
    assert enroll_res.json()["data"]["student_id"] == str(student.id)
