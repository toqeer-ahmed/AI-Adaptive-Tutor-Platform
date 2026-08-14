import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.organization_service.service import OrganizationService, SchoolService
from backend.services.user_service.service import UserService
from backend.services.user_service.auth import create_access_token

@pytest.mark.asyncio
async def test_cross_tenant_school_creation_forbidden(async_client: AsyncClient, db_session: AsyncSession):
    # 1. Create Organization A & Organization B
    org_a = await OrganizationService.create_organization(db_session, "Org A", "ORGA")
    org_b = await OrganizationService.create_organization(db_session, "Org B", "ORGB")

    # 2. Create OrgAdmin User for Org B
    user_b = await UserService.create_user(
        db_session,
        organization_id=org_b.id,
        email="admin@orgb.com",
        password="Password123!",
        full_name="Org B Admin",
        role_name="OrgAdmin"
    )

    # 3. Generate token for Org B user
    token_b, _ = create_access_token(
        user_id=str(user_b.id),
        organization_id=str(org_b.id),
        roles=["OrgAdmin"]
    )

    # 4. Attempt to create a school under Org A using Org B credentials
    headers = {"Authorization": f"Bearer {token_b}"}
    response = await async_client.post(
        f"/api/v1/organizations/{org_a.id}/schools",
        json={"name": "Hacked School", "code": "HACK"},
        headers=headers
    )

    # Must be Forbidden (403)
    assert response.status_code == 403
    assert "foreign organization" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_cross_tenant_school_listing_isolation(async_client: AsyncClient, db_session: AsyncSession):
    # 1. Create Org A and Org B
    org_a = await OrganizationService.create_organization(db_session, "Org Alpha", "ORGALPHA")
    org_b = await OrganizationService.create_organization(db_session, "Org Beta", "ORGBETA")

    # 2. Create school under Org A
    await SchoolService.create_school(db_session, org_a.id, "Alpha Academy", "ALPHA1")

    # 3. Create User in Org B
    user_b = await UserService.create_user(
        db_session,
        organization_id=org_b.id,
        email="teacher@orgbeta.com",
        password="Password123!",
        full_name="Beta Teacher",
        role_name="Teacher"
    )

    token_b, _ = create_access_token(
        user_id=str(user_b.id),
        organization_id=str(org_b.id),
        roles=["Teacher"]
    )

    headers = {"Authorization": f"Bearer {token_b}"}
    response = await async_client.get(
        f"/api/v1/organizations/{org_a.id}/schools",
        headers=headers
    )

    assert response.status_code == 403
    assert "foreign organization" in response.json()["detail"].lower()
