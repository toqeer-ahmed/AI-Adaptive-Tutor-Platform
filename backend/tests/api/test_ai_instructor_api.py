import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.organization_service.service import OrganizationService
from backend.services.user_service.service import UserService
from backend.services.user_service.auth import create_access_token
from backend.services.curriculum_service.service import CurriculumService

@pytest.mark.asyncio
async def test_grade_6_student_tutor_workflow(async_client: AsyncClient, db_session: AsyncSession):
    # 1. Setup Organization, Student
    org = await OrganizationService.create_organization(db_session, "Tutor District", "TUTORDIST")
    student = await UserService.create_user(db_session, org.id, "stud@tutor.edu", "Pass123!", "Grade 6 Student", "Student")
    s_token, _ = create_access_token(str(student.id), str(org.id), roles=["Student"])
    headers = {"Authorization": f"Bearer {s_token}"}

    # 2. Setup Curriculum & Concept
    curr = await CurriculumService.create_curriculum(db_session, student, "Grade 6 Math", 6, "Mathematics")
    ch = await CurriculumService.create_chapter(db_session, curr.versions[0].id, "Fractions")
    tp = await CurriculumService.create_topic(db_session, ch.id, "Adding Fractions")
    cp = await CurriculumService.create_concept(db_session, tp.id, "Common Denominator")

    # 3. Initialize Tutor Session
    sess_res = await async_client.post(
        "/api/v1/tutor/sessions",
        json={"concept_id": str(cp.id), "curriculum_version_id": str(curr.versions[0].id), "mode": "explanation"},
        headers=headers
    )
    assert sess_res.status_code == 200
    session_id = sess_res.json()["data"]["session_id"]

    # 4. Student asks: "Why do I need a common denominator?"
    turn1_res = await async_client.post(
        "/api/v1/tutor/turn",
        json={
            "session_id": session_id,
            "student_message": "Why do I need a common denominator?",
            "mode": "explanation",
            "provider": "mock"
        },
        headers=headers
    )
    assert turn1_res.status_code == 200
    turn1_data = turn1_res.json()["data"]
    assert "tutor_response" in turn1_data
    assert turn1_data["mode"] == "explanation"

    # 5. Follow-up turn requesting a hint
    turn2_res = await async_client.post(
        "/api/v1/tutor/turn",
        json={
            "session_id": session_id,
            "student_message": "Can you give me a hint for 1/3 + 1/4?",
            "mode": "hint",
            "provider": "mock"
        },
        headers=headers
    )
    assert turn2_res.status_code == 200
    turn2_data = turn2_res.json()["data"]
    assert turn2_data["mode"] == "hint"

    # 6. Check Session History
    hist_res = await async_client.get(f"/api/v1/tutor/sessions/{session_id}/history", headers=headers)
    assert hist_res.status_code == 200
    assert hist_res.json()["meta"]["turn_count"] == 2
