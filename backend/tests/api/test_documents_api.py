import pytest
import io
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.organization_service.service import OrganizationService
from backend.services.user_service.service import UserService
from backend.services.user_service.auth import create_access_token

@pytest.mark.asyncio
async def test_end_to_end_pdf_document_ingestion_pipeline(async_client: AsyncClient, db_session: AsyncSession):
    # 1. Create Organization and Teacher
    org = await OrganizationService.create_organization(db_session, "Doc District", "DOCDIST")
    teacher = await UserService.create_user(
        db_session, org.id, "teacher@docdist.edu", "Pass123!", "Doc Teacher", "Teacher"
    )

    token, _ = create_access_token(str(teacher.id), str(org.id), roles=["Teacher"])
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Upload valid PDF syllabus
    sample_pdf_bytes = b"%PDF-1.4\n1 0 obj\n/Type /Page\n(Chapter 1: Fractions and Decimals. This chapter covers basic operations.) Tj\nendobj\n"
    files = {"file": ("math_syllabus.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}

    upload_res = await async_client.post("/api/v1/documents/upload", files=files, headers=headers)
    assert upload_res.status_code == 200
    doc_data = upload_res.json()["data"]
    doc_id = doc_data["id"]
    assert doc_data["status"] == "COMPLETED"

    # 3. Verify status endpoint
    status_res = await async_client.get(f"/api/v1/documents/{doc_id}/status", headers=headers)
    assert status_res.status_code == 200
    assert status_res.json()["data"]["status"] == "COMPLETED"

    # 4. Verify chunks endpoint preserves page metadata
    chunks_res = await async_client.get(f"/api/v1/documents/{doc_id}/chunks", headers=headers)
    assert chunks_res.status_code == 200
    chunks = chunks_res.json()["data"]
    assert len(chunks) > 0
    assert chunks[0]["page_number"] is not None
    assert "Fractions" in chunks[0]["text"]

@pytest.mark.asyncio
async def test_cross_tenant_document_access_isolation(async_client: AsyncClient, db_session: AsyncSession):
    # Setup Org A and Org B
    org_a = await OrganizationService.create_organization(db_session, "Doc Org A", "DOCORGA")
    org_b = await OrganizationService.create_organization(db_session, "Doc Org B", "DOCORGB")

    teacher_a = await UserService.create_user(db_session, org_a.id, "t_a@docorga.com", "Pass123!", "Teacher A", "Teacher")
    teacher_b = await UserService.create_user(db_session, org_b.id, "t_b@docorgb.com", "Pass123!", "Teacher B", "Teacher")

    token_a, _ = create_access_token(str(teacher_a.id), str(org_a.id), roles=["Teacher"])
    token_b, _ = create_access_token(str(teacher_b.id), str(org_b.id), roles=["Teacher"])

    # Upload document under Org A
    sample_pdf_bytes = b"%PDF-1.4\n(Secret Org A Syllabus) Tj\n"
    files = {"file": ("secret_a.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
    upload_res = await async_client.post("/api/v1/documents/upload", files=files, headers={"Authorization": f"Bearer {token_a}"})
    doc_id = upload_res.json()["data"]["id"]

    # Teacher B (Org B) attempts to read Org A document status -> Must be 404/Forbidden
    status_res = await async_client.get(f"/api/v1/documents/{doc_id}/status", headers={"Authorization": f"Bearer {token_b}"})
    assert status_res.status_code == 404

    # Teacher B (Org B) attempts to read Org A document chunks -> Must be 404/Forbidden
    chunks_res = await async_client.get(f"/api/v1/documents/{doc_id}/chunks", headers={"Authorization": f"Bearer {token_b}"})
    assert chunks_res.status_code == 404
