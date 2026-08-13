import pytest
import io
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.organization_service.service import OrganizationService
from backend.services.user_service.service import UserService
from backend.services.user_service.auth import create_access_token
from backend.services.curriculum_service.service import CurriculumService

@pytest.mark.asyncio
async def test_end_to_end_ai_curriculum_extraction_and_human_approval_flow(
    async_client: AsyncClient,
    db_session: AsyncSession
):
    # 1. Create Organization, Admin, Teacher
    org = await OrganizationService.create_organization(db_session, "AI District", "AIDIST")
    admin = await UserService.create_user(db_session, org.id, "admin@aidist.edu", "Pass123!", "AI Admin", "OrgAdmin")

    token, _ = create_access_token(str(admin.id), str(org.id), roles=["OrgAdmin"])
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Upload PDF Syllabus
    sample_pdf_bytes = b"%PDF-1.4\n(Chapter 1: Fractions and Decimals. Adding Fractions with Common Denominator.) Tj\n"
    files = {"file": ("math_g6_syllabus.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
    up_res = await async_client.post("/api/v1/documents/upload", files=files, headers=headers)
    doc_id = up_res.json()["data"]["id"]

    # 3. Create target Curriculum
    curr = await CurriculumService.create_curriculum(db_session, admin, "Grade 6 AI Math", 6, "Mathematics")

    # 4. Trigger AI Extraction from Document
    ext_res = await async_client.post(
        f"/api/v1/curricula/{curr.id}/extract",
        json={"document_id": doc_id, "provider": "mock"},
        headers=headers
    )
    assert ext_res.status_code == 200
    ext_data = ext_res.json()["data"]
    version_id = ext_data["version_id"]

    # CRITICAL CHECK: AI extraction must NOT auto-publish. Version MUST be in REVIEW / DRAFT state!
    assert ext_data["status"] in ["REVIEW", "DRAFT"]
    assert ext_data["status"] != "PUBLISHED"

    # 5. Teacher inspects proposed version tree
    tree_res = await async_client.get(f"/api/v1/curricula/versions/{version_id}", headers=headers)
    assert tree_res.status_code == 200
    tree_data = tree_res.json()["data"]
    assert len(tree_data["chapters"]) > 0
    assert tree_data["status"] in ["REVIEW", "DRAFT"]

    # 6. Human Reviewer approves and publishes version
    app_res = await async_client.post(
        f"/api/v1/curricula/versions/{version_id}/status",
        json={"status": "APPROVED"},
        headers=headers
    )
    assert app_res.status_code == 200

    pub_res = await async_client.post(
        f"/api/v1/curricula/versions/{version_id}/status",
        json={"status": "PUBLISHED"},
        headers=headers
    )
    assert pub_res.status_code == 200
    assert pub_res.json()["data"]["status"] == "PUBLISHED"
