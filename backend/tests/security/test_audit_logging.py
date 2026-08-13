import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.organization_service.service import OrganizationService
from backend.services.user_service.service import UserService
from backend.services.audit_service import AuditService

@pytest.mark.asyncio
async def test_audit_log_generation_for_security_events(async_client: AsyncClient, db_session: AsyncSession):
    org = await OrganizationService.create_organization(db_session, "Audit Org", "AUDITORG")
    user = await UserService.create_user(db_session, org.id, "admin@audit.com", "Pass123!", "Audit Admin", "OrgAdmin")

    # Login -> produces AUTH_LOGIN_SUCCESS audit entry
    login_res = await async_client.post("/api/v1/auth/login", json={"email": "admin@audit.com", "password": "Pass123!"})
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch audit logs
    audit_res = await async_client.get("/api/v1/audit-logs", headers=headers)
    assert audit_res.status_code == 200
    logs = audit_res.json()["data"]

    actions = [l["action"] for l in logs]
    assert "AUTH_LOGIN_SUCCESS" in actions
