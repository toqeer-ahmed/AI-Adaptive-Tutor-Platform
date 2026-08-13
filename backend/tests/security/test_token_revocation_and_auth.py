import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.organization_service.service import OrganizationService
from backend.services.user_service.service import UserService

@pytest.mark.asyncio
async def test_token_revocation_on_logout(async_client: AsyncClient, db_session: AsyncSession):
    org = await OrganizationService.create_organization(db_session, "Revoke Org", "REVORG")
    user = await UserService.create_user(db_session, org.id, "user@rev.com", "Pass123!", "Rev User", "Teacher")

    # Login
    login_res = await async_client.post("/api/v1/auth/login", json={"email": "user@rev.com", "password": "Pass123!"})
    assert login_res.status_code == 200
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify active access
    me_res = await async_client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200

    # Logout
    logout_res = await async_client.post("/api/v1/auth/logout", headers=headers)
    assert logout_res.status_code == 200

    # Try to reuse revoked token -> Must be 401 Unauthorized
    me_res_after = await async_client.get("/api/v1/auth/me", headers=headers)
    assert me_res_after.status_code == 401
    assert "revoked" in me_res_after.json()["detail"].lower()

@pytest.mark.asyncio
async def test_refresh_token_rotation(async_client: AsyncClient, db_session: AsyncSession):
    org = await OrganizationService.create_organization(db_session, "Rotate Org", "ROTORG")
    user = await UserService.create_user(db_session, org.id, "user@rot.com", "Pass123!", "Rot User", "Student")

    login_res = await async_client.post("/api/v1/auth/login", json={"email": "user@rot.com", "password": "Pass123!"})
    refresh_token_1 = login_res.json()["data"]["refresh_token"]

    # Rotate refresh token
    ref_res = await async_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token_1})
    assert ref_res.status_code == 200
    refresh_token_2 = ref_res.json()["data"]["refresh_token"]
    assert refresh_token_1 != refresh_token_2

    # Attempt to reuse old refresh token -> Must fail (401)
    ref_res_reuse = await async_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token_1})
    assert ref_res_reuse.status_code == 401

@pytest.mark.asyncio
async def test_password_reset_workflow(async_client: AsyncClient, db_session: AsyncSession):
    org = await OrganizationService.create_organization(db_session, "Reset Org", "RESETORG")
    user = await UserService.create_user(db_session, org.id, "user@reset.com", "OldPass123!", "Reset User", "Teacher")

    # Request reset
    req_res = await async_client.post("/api/v1/auth/password-reset/request", json={"email": "user@reset.com"})
    assert req_res.status_code == 200

    # Confirm reset
    conf_res = await async_client.post("/api/v1/auth/password-reset/confirm", json={
        "user_id": str(user.id),
        "raw_token": "dummy-demo-token",
        "new_password": "NewPass456!"
    })
    assert conf_res.status_code == 200

    # Verify old password fails
    old_login = await async_client.post("/api/v1/auth/login", json={"email": "user@reset.com", "password": "OldPass123!"})
    assert old_login.status_code == 401

    # Verify new password succeeds
    new_login = await async_client.post("/api/v1/auth/login", json={"email": "user@reset.com", "password": "NewPass456!"})
    assert new_login.status_code == 200
