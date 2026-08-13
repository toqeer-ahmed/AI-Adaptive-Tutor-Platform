import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.organization_service.service import OrganizationService
from backend.services.user_service.service import UserService
from backend.services.user_service.auth import create_access_token

@pytest.mark.asyncio
async def test_end_to_end_manual_curriculum_publishing_flow(async_client: AsyncClient, db_session: AsyncSession):
    # 1. Create Organization & Teacher
    org = await OrganizationService.create_organization(db_session, "Springfield District", "SPRING")
    teacher = await UserService.create_user(
        db_session, org.id, "edna@springfield.edu", "Pass123!", "Edna Krabappel", "Teacher"
    )

    token, _ = create_access_token(str(teacher.id), str(org.id), roles=["Teacher"])
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Curriculum (Grade 6 Mathematics)
    res_curr = await async_client.post(
        "/api/v1/curricula",
        json={"name": "Grade 6 Core Curriculum", "grade_level": 6, "subject_name": "Mathematics"},
        headers=headers
    )
    assert res_curr.status_code == 200
    curr_data = res_curr.json()["data"]
    curriculum_id = curr_data["id"]
    version_id = curr_data["versions"][0]["id"]

    # 3. Create Chapter: Fractions
    res_ch = await async_client.post(
        f"/api/v1/curricula/versions/{version_id}/chapters",
        json={"name": "Fractions", "sequence_order": 1},
        headers=headers
    )
    assert res_ch.status_code == 200
    chapter_id = res_ch.json()["data"]["id"]

    # 4. Create Topic: Adding Fractions
    res_tp = await async_client.post(
        f"/api/v1/curricula/chapters/{chapter_id}/topics",
        json={"name": "Adding Fractions", "sequence_order": 1},
        headers=headers
    )
    assert res_tp.status_code == 200
    topic_id = res_tp.json()["data"]["id"]

    # 5. Create Concept: Common Denominator
    res_cp = await async_client.post(
        f"/api/v1/curricula/topics/{topic_id}/concepts",
        json={"name": "Common Denominator", "difficulty_level": 3, "sequence_order": 1},
        headers=headers
    )
    assert res_cp.status_code == 200
    concept_id = res_cp.json()["data"]["id"]

    # 6. Create Objective: MATH-G6-FRAC-001
    res_lo = await async_client.post(
        f"/api/v1/curricula/concepts/{concept_id}/objectives",
        json={"code": "MATH-G6-FRAC-001", "description": "Find least common denominator to add fractions"},
        headers=headers
    )
    assert res_lo.status_code == 200

    # 7. Transition: DRAFT -> REVIEW
    res_rev = await async_client.post(
        f"/api/v1/curricula/versions/{version_id}/status",
        json={"status": "REVIEW"},
        headers=headers
    )
    assert res_rev.status_code == 200

    # 8. Transition: REVIEW -> APPROVED (using OrgAdmin user)
    admin = await UserService.create_user(
        db_session, org.id, "admin@springfield.edu", "Pass123!", "Admin User", "OrgAdmin"
    )
    admin_token, _ = create_access_token(str(admin.id), str(org.id), roles=["OrgAdmin"])
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    res_app = await async_client.post(
        f"/api/v1/curricula/versions/{version_id}/status",
        json={"status": "APPROVED"},
        headers=admin_headers
    )
    assert res_app.status_code == 200

    # 9. Transition: APPROVED -> PUBLISHED
    res_pub = await async_client.post(
        f"/api/v1/curricula/versions/{version_id}/status",
        json={"status": "PUBLISHED"},
        headers=admin_headers
    )
    assert res_pub.status_code == 200
    assert res_pub.json()["data"]["status"] == "PUBLISHED"

    # 10. Attempt to modify published curriculum tree -> Must return 400 Bad Request
    res_fail = await async_client.post(
        f"/api/v1/curricula/versions/{version_id}/chapters",
        json={"name": "Decimals"},
        headers=headers
    )
    assert res_fail.status_code == 400
    assert "cannot modify a published curriculum version" in res_fail.json()["detail"].lower()
