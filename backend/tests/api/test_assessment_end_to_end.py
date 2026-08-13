import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.organization_service.service import OrganizationService
from backend.services.user_service.service import UserService
from backend.services.user_service.auth import create_access_token
from backend.services.curriculum_service.service import CurriculumService

@pytest.mark.asyncio
async def test_end_to_end_assessment_workflow(async_client: AsyncClient, db_session: AsyncSession):
    # 1. Setup Organization, Teacher, Student
    org = await OrganizationService.create_organization(db_session, "Eval District", "EVALDIST")
    teacher = await UserService.create_user(db_session, org.id, "teacher@eval.edu", "Pass123!", "Teacher Eval", "Teacher")
    student = await UserService.create_user(db_session, org.id, "student@eval.edu", "Pass123!", "Student Eval", "Student")

    t_token, _ = create_access_token(str(teacher.id), str(org.id), roles=["Teacher"])
    s_token, _ = create_access_token(str(student.id), str(org.id), roles=["Student"])

    t_headers = {"Authorization": f"Bearer {t_token}"}
    s_headers = {"Authorization": f"Bearer {s_token}"}

    # 2. Setup Curriculum & Concept
    created_curr = await CurriculumService.create_curriculum(db_session, teacher, "Grade 6 Math", 6, "Mathematics")
    curr = await CurriculumService.get_curriculum_by_id(db_session, created_curr.id)
    ver_id = curr.versions[0].id

    ch = await CurriculumService.create_chapter(db_session, ver_id, "Fractions")
    tp = await CurriculumService.create_topic(db_session, ch.id, "Adding Fractions")
    cp = await CurriculumService.create_concept(db_session, tp.id, "Common Denominator")

    # 3. AI Generates Questions
    gen_res = await async_client.post(
        "/api/v1/questions/generate",
        json={"concept_id": str(cp.id), "count": 5, "provider": "mock"},
        headers=t_headers
    )
    assert gen_res.status_code == 200
    q_items = gen_res.json()["data"]
    q1_id = q_items[0]["id"]
    q2_id = q_items[1]["id"]

    # 4. Teacher Approves Questions
    await async_client.post(f"/api/v1/questions/{q1_id}/approve", json={}, headers=t_headers)
    await async_client.post(f"/api/v1/questions/{q2_id}/approve", json={}, headers=t_headers)

    # 5. Teacher Builds Quiz Assessment
    ass_res = await async_client.post(
        "/api/v1/assessments",
        json={
            "title": "Fractions Unit Quiz",
            "question_ids": [q1_id, q2_id],
            "assessment_type": "QUIZ",
            "max_attempts": 2
        },
        headers=t_headers
    )
    assert ass_res.status_code == 200
    ass_id = ass_res.json()["data"]["id"]

    # 6. Student Starts Assessment Attempt
    start_res = await async_client.post(f"/api/v1/assessments/{ass_id}/start", json={}, headers=s_headers)
    assert start_res.status_code == 200
    attempt_id = start_res.json()["data"]["attempt_id"]

    # 7. Student Submits Answers (Q1 MCQ, Q2 Numeric)
    correct_ans1 = q_items[0]["correct_answer"]
    correct_ans2 = q_items[1]["correct_answer"]

    ans1_res = await async_client.post(
        f"/api/v1/attempts/{attempt_id}/answer",
        json={"question_id": q1_id, "submitted_answer": correct_ans1},
        headers=s_headers
    )
    assert ans1_res.status_code == 200
    assert ans1_res.json()["data"]["is_correct"] is True

    ans2_res = await async_client.post(
        f"/api/v1/attempts/{attempt_id}/answer",
        json={"question_id": q2_id, "submitted_answer": correct_ans2},
        headers=s_headers
    )
    assert ans2_res.status_code == 200
    assert ans2_res.json()["data"]["is_correct"] is True

    # 8. Student Submits Entire Attempt -> Verifies Deterministic Score Calculation
    submit_res = await async_client.post(f"/api/v1/attempts/{attempt_id}/submit", json={}, headers=s_headers)
    assert submit_res.status_code == 200
    score_data = submit_res.json()["data"]
    assert score_data["status"] == "GRADED"
    assert score_data["score"] == 2.0
    assert score_data["percentage"] == 100.0
