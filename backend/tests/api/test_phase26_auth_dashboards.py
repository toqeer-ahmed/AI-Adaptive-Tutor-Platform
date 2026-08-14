import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.user_service.service import UserService
from backend.services.user_service.auth import create_access_token

@pytest.mark.asyncio
async def test_seed_default_dev_accounts(db_session: AsyncSession):
    # Test that seed_default_dev_accounts seeds all 7 role accounts and connections
    await UserService.seed_default_dev_accounts(db_session)

    roles_to_check = [
        "student@school.edu",
        "teacher@school.edu",
        "parent@family.com",
        "schooladmin@school.edu",
        "orgadmin@district.edu",
        "curriculum@district.edu",
        "platformadmin@platform.com",
    ]

    for email in roles_to_check:
        user = await UserService.get_user_by_email(db_session, email)
        assert user is not None, f"Expected user {email} to exist"
        assert len(user.roles) > 0

@pytest.mark.asyncio
async def test_authentication_all_7_roles(db_session: AsyncSession, async_client: AsyncClient):
    await UserService.seed_default_dev_accounts(db_session)

    # 1. Student Login
    res = await async_client.post("/api/v1/auth/login", json={"email": "student@school.edu", "password": "Pass123!"})
    assert res.status_code == 200
    student_data = res.json()["data"]
    assert "access_token" in student_data
    assert "Student" in student_data["user"]["roles"]

    # 2. Teacher Login
    res = await async_client.post("/api/v1/auth/login", json={"email": "teacher@school.edu", "password": "Pass123!"})
    assert res.status_code == 200
    teacher_data = res.json()["data"]
    assert "Teacher" in teacher_data["user"]["roles"]

    # 3. Parent Login
    res = await async_client.post("/api/v1/auth/login", json={"email": "parent@family.com", "password": "Pass123!"})
    assert res.status_code == 200
    parent_data = res.json()["data"]
    assert "Parent" in parent_data["user"]["roles"]

    # 4. SchoolAdmin Login
    res = await async_client.post("/api/v1/auth/login", json={"email": "schooladmin@school.edu", "password": "Pass123!"})
    assert res.status_code == 200
    assert "SchoolAdmin" in res.json()["data"]["user"]["roles"]

    # 5. OrgAdmin Login
    res = await async_client.post("/api/v1/auth/login", json={"email": "orgadmin@district.edu", "password": "Pass123!"})
    assert res.status_code == 200
    assert "OrgAdmin" in res.json()["data"]["user"]["roles"]

    # 6. CurriculumManager Login
    res = await async_client.post("/api/v1/auth/login", json={"email": "curriculum@district.edu", "password": "Pass123!"})
    assert res.status_code == 200
    assert "CurriculumManager" in res.json()["data"]["user"]["roles"]

    # 7. SuperAdmin Login
    res = await async_client.post("/api/v1/auth/login", json={"email": "platformadmin@platform.com", "password": "Pass123!"})
    assert res.status_code == 200
    assert "SuperAdmin" in res.json()["data"]["user"]["roles"]

@pytest.mark.asyncio
async def test_auth_me_profile_and_non_enumeration(db_session: AsyncSession, async_client: AsyncClient):
    await UserService.seed_default_dev_accounts(db_session)

    # Invalid password returns generic error (preventing enumeration)
    res = await async_client.post("/api/v1/auth/login", json={"email": "student@school.edu", "password": "WrongPassword!"})
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]

    # Non-existent email returns same generic error
    res = await async_client.post("/api/v1/auth/login", json={"email": "nonexistent@school.edu", "password": "WrongPassword!"})
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]

    # Valid login and GET /me
    login_res = await async_client.post("/api/v1/auth/login", json={"email": "teacher@school.edu", "password": "Pass123!"})
    token = login_res.json()["data"]["access_token"]

    me_res = await async_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()["data"]
    assert me_data["email"] == "teacher@school.edu"
    assert "Teacher" in me_data["roles"]

@pytest.mark.asyncio
async def test_classes_and_student_roster_rbac(db_session: AsyncSession, async_client: AsyncClient):
    await UserService.seed_default_dev_accounts(db_session)

    teacher = await UserService.get_user_by_email(db_session, "teacher@school.edu")
    student = await UserService.get_user_by_email(db_session, "student@school.edu")

    teacher_token, _ = create_access_token(str(teacher.id), str(teacher.organization_id), str(teacher.school_id), ["Teacher"])
    student_token, _ = create_access_token(str(student.id), str(student.organization_id), str(student.school_id), ["Student"])

    # Teacher lists their classes
    res = await async_client.get("/api/v1/classes", headers={"Authorization": f"Bearer {teacher_token}"})
    assert res.status_code == 200
    classes = res.json()["data"]
    assert len(classes) >= 1
    class_id = classes[0]["id"]

    # Teacher views class roster
    roster_res = await async_client.get(f"/api/v1/classes/{class_id}/students", headers={"Authorization": f"Bearer {teacher_token}"})
    assert roster_res.status_code == 200
    students = roster_res.json()["data"]
    assert any(s["email"] == "student@school.edu" for s in students)

@pytest.mark.asyncio
async def test_user_directory_rbac_isolation(db_session: AsyncSession, async_client: AsyncClient):
    await UserService.seed_default_dev_accounts(db_session)

    student = await UserService.get_user_by_email(db_session, "student@school.edu")
    org_admin = await UserService.get_user_by_email(db_session, "orgadmin@district.edu")

    student_token, _ = create_access_token(str(student.id), str(student.organization_id), None, ["Student"])
    admin_token, _ = create_access_token(str(org_admin.id), str(org_admin.organization_id), None, ["OrgAdmin"])

    # Student attempting to access user directory is DENIED (403)
    res = await async_client.get("/api/v1/users", headers={"Authorization": f"Bearer {student_token}"})
    assert res.status_code == 403

    # OrgAdmin is AUTHORIZED (200)
    res = await async_client.get("/api/v1/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    users = res.json()["data"]
    assert len(users) >= 7

@pytest.mark.asyncio
async def test_profile_update_and_privilege_integrity(db_session: AsyncSession, async_client: AsyncClient):
    await UserService.seed_default_dev_accounts(db_session)

    student = await UserService.get_user_by_email(db_session, "student@school.edu")
    token, _ = create_access_token(str(student.id), str(student.organization_id), None, ["Student"])

    # Update display name
    res = await async_client.patch(
        "/api/v1/users/me/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"full_name": "Alexander Johnson Jr."}
    )
    assert res.status_code == 200
    assert res.json()["data"]["full_name"] == "Alexander Johnson Jr."
    assert res.json()["data"]["roles"] == ["Student"]

    # Verify DB persisted
    updated = await UserService.get_user_by_id(db_session, student.id)
    assert updated.full_name == "Alexander Johnson Jr."
