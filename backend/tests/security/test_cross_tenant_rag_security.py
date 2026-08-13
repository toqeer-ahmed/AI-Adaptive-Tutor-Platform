import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.organization_service.service import OrganizationService
from backend.services.user_service.service import UserService
from backend.services.user_service.auth import create_access_token
from backend.services.curriculum_service.service import CurriculumService
from backend.services.rag_service.indexer import CurriculumVectorIndexer

@pytest.mark.asyncio
async def test_cross_tenant_rag_security_isolation(async_client: AsyncClient, db_session: AsyncSession):
    # 1. Setup Tenant A and Tenant B
    org_a = await OrganizationService.create_organization(db_session, "RAG District A", "RAGDISTA")
    org_b = await OrganizationService.create_organization(db_session, "RAG District B", "RAGDISTB")

    student_a = await UserService.create_user(db_session, org_a.id, "stud_a@raga.edu", "Pass123!", "Student A", "Student")
    admin_b = await UserService.create_user(db_session, org_b.id, "admin_b@ragb.edu", "Pass123!", "Admin B", "OrgAdmin")

    token_a, _ = create_access_token(str(student_a.id), str(org_a.id), roles=["Student"])
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Admin B creates and publishes curriculum in Tenant B
    curr_b = await CurriculumService.create_curriculum(db_session, admin_b, "Grade 6 Math B", 6, "Mathematics")
    v_b = curr_b.versions[0]
    await CurriculumService.create_chapter(db_session, v_b.id, "Tenant B Secret Chapter")

    # Admin B approves & publishes version
    await CurriculumService.transition_version_status(db_session, v_b.id, "REVIEW", admin_b)
    await CurriculumService.transition_version_status(db_session, v_b.id, "APPROVED", admin_b)
    pub_v_b = await CurriculumService.transition_version_status(db_session, v_b.id, "PUBLISHED", admin_b)

    # Index Tenant B published curriculum into vector store
    await CurriculumVectorIndexer.index_curriculum_version(db_session, pub_v_b.id)

    # 3. Student A (Tenant A) queries RAG -> MUST return ZERO results from Tenant B
    res = await async_client.post(
        "/api/v1/rag/query",
        json={"query": "Tenant B Secret Chapter", "grade": 6, "subject": "Mathematics"},
        headers=headers_a
    )
    assert res.status_code == 200
    data = res.json()["data"]

    # CRITICAL SECURITY CHECK: Cross-tenant query MUST NOT return Tenant B data
    assert data["has_context"] is False
    assert len(data["sources"]) == 0
    assert "couldn't find that in the approved course material" in data["fallback_response"].lower()

@pytest.mark.asyncio
async def test_draft_and_archived_curriculum_exclusion_from_student_rag(
    async_client: AsyncClient,
    db_session: AsyncSession
):
    # 1. Setup Tenant and Student
    org = await OrganizationService.create_organization(db_session, "RAG Security Org", "RAGSEC")
    admin = await UserService.create_user(db_session, org.id, "admin@ragsec.edu", "Pass123!", "Admin Sec", "OrgAdmin")
    student = await UserService.create_user(db_session, org.id, "student@ragsec.edu", "Pass123!", "Student Sec", "Student")

    token_s, _ = create_access_token(str(student.id), str(org.id), roles=["Student"])
    headers = {"Authorization": f"Bearer {token_s}"}

    # 2. Create Draft Curriculum (not published)
    curr = await CurriculumService.create_curriculum(db_session, admin, "Draft Math", 6, "Mathematics")
    v_draft = curr.versions[0]
    await CurriculumService.create_chapter(db_session, v_draft.id, "Unpublished Draft Fractions")

    # Index draft version directly with DRAFT status
    await CurriculumVectorIndexer.index_curriculum_version(db_session, v_draft.id)

    # 3. Student queries RAG -> Draft curriculum MUST NOT be retrieved
    res = await async_client.post(
        "/api/v1/rag/query",
        json={"query": "Unpublished Draft Fractions", "grade": 6, "subject": "Mathematics"},
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()["data"]

    # CRITICAL SECURITY CHECK: Student RAG query MUST NOT retrieve DRAFT curriculum
    assert data["has_context"] is False
    assert len(data["sources"]) == 0
