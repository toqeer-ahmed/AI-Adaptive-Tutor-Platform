import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.organization_service.service import OrganizationService, SchoolService
from backend.services.user_service.service import UserService, ClassService
from backend.services.user_service.auth import create_access_token

@pytest.mark.asyncio
async def test_cross_tenant_read_forbidden(async_client: AsyncClient, db_session: AsyncSession):
    # 1. Create Organization A & B
    org_a = await OrganizationService.create_organization(db_session, "Org A", "ORGA")
    org_b = await OrganizationService.create_organization(db_session, "Org B", "ORGB")

    # 2. Create School and Teacher in Org A
    school_a = await SchoolService.create_school(db_session, org_a.id, "School A", "SCHA")
    teacher_a = await UserService.create_user(
        db_session, org_a.id, "teacher@orga.com", "Pass123!", "Teacher A", "Teacher", school_a.id
    )

    # 3. Create OrgAdmin in Org B
    admin_b = await UserService.create_user(
        db_session, org_b.id, "admin@orgb.com", "Pass123!", "Admin B", "OrgAdmin"
    )

    # 4. Auth token for Org B user
    token_b, _ = create_access_token(str(admin_b.id), str(org_b.id), roles=["OrgAdmin"])
    headers = {"Authorization": f"Bearer {token_b}"}

    # 5. Org B user attempts to read Org A schools -> Must be 403 Forbidden
    res1 = await async_client.get(f"/api/v1/organizations/{org_a.id}/schools", headers=headers)
    assert res1.status_code == 403

    # 6. Org B user attempts to read Org A teacher record -> Must be 403 Forbidden
    res2 = await async_client.get(f"/api/v1/users/{teacher_a.id}", headers=headers)
    assert res2.status_code == 403

@pytest.mark.asyncio
async def test_client_supplied_org_id_override_rejected(async_client: AsyncClient, db_session: AsyncSession):
    # Tests that client cannot override organization context by passing organization_id in request body
    org_a = await OrganizationService.create_organization(db_session, "Org Alpha", "ALPHA")
    org_b = await OrganizationService.create_organization(db_session, "Org Beta", "BETA")

    teacher_b = await UserService.create_user(
        db_session, org_b.id, "teacher@beta.com", "Pass123!", "Teacher Beta", "Teacher"
    )

    token_b, _ = create_access_token(str(teacher_b.id), str(org_b.id), roles=["Teacher"])
    headers = {"Authorization": f"Bearer {token_b}"}

    # Teacher Beta tries to create a class supplying Org A's ID
    school_b = await SchoolService.create_school(db_session, org_b.id, "School Beta", "SCHB")
    
    res = await async_client.post(
        "/api/v1/classes",
        json={
            "organization_id": str(org_a.id), # Client tries to override org_id
            "school_id": str(school_b.id),
            "teacher_id": str(teacher_b.id),
            "name": "Hacked Class",
            "grade_level": 5,
            "academic_year": "2026-2027"
        },
        headers=headers
    )

    assert res.status_code == 200
    created_class = res.json()["data"]
    # The server MUST bind the class to Org B (authenticated user's tenant), ignoring client override
    assert created_class["organization_id"] == str(org_b.id)
