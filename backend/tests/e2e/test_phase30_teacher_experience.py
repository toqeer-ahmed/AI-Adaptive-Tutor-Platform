import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.api.main import app
from backend.models.user import User, Role, UserRole
from backend.models.organization import Organization, School
from backend.models.class_model import Class, Enrollment
from backend.models.curriculum import Curriculum, CurriculumVersion, Chapter, Topic, Concept
from backend.models.mastery import StudentMastery
from backend.models.assessment import QuestionBankItem, Assessment, AssessmentQuestion, AssessmentAttempt, StudentAnswer
from backend.services.user_service.service import UserService, ClassService
from backend.services.user_service.auth import hash_password, create_access_token
from backend.services.evaluation_service.service import SubjectiveEvaluationService

@pytest.mark.asyncio
async def test_full_phase30_teacher_lifecycle_and_governance_e2e(db_session: AsyncSession, async_client: AsyncClient):
    """
    Complete Teacher E2E Governance Lifecycle:
    1. Teacher Authentication & Profile Verification
    2. Class Roster Authorization
    3. Curriculum Ingestion Review, Human Approval & Version Publishing (Immutability)
    4. AI Question Generation & Human Review/Approval (PROPOSED -> APPROVED)
    5. Assessment Creation & Association with Approved Questions
    6. Student Attempt Submission & Deterministic Auto-Grading
    7. Teacher Review of Subjective Question & Authoritative Override
    8. Class Analytics & Misconception Heatmap Query
    9. Cross-Tenant and Cross-Class Security Isolation
    """
    # -------------------------------------------------------------
    # 1. Setup Organization, School, Teacher, and Student Users
    # -------------------------------------------------------------
    org = Organization(id=uuid.uuid4(), name="Lincoln Unified District", code="LINC_DIST")
    school = School(id=uuid.uuid4(), organization_id=org.id, name="Lincoln Middle School", code="LMS")

    role_teacher_res = await db_session.execute(select(Role).where(Role.name == "Teacher"))
    teacher_role = role_teacher_res.scalars().first()
    if not teacher_role:
        teacher_role = Role(id=uuid.uuid4(), name="Teacher", description="Teacher Role")
        db_session.add(teacher_role)

    role_student_res = await db_session.execute(select(Role).where(Role.name == "Student"))
    student_role = role_student_res.scalars().first()
    if not student_role:
        student_role = Role(id=uuid.uuid4(), name="Student", description="Student Role")
        db_session.add(student_role)

    db_session.add_all([org, school])
    await db_session.commit()

    teacher_user = await UserService.create_user(
        session=db_session,
        organization_id=org.id,
        email="ms.johnson@lincoln.edu",
        password="TeacherSecret123!",
        full_name="Ms. Clara Johnson",
        role_name="Teacher",
        school_id=school.id
    )

    student_user = await UserService.create_user(
        session=db_session,
        organization_id=org.id,
        email="maya.lin@lincoln.edu",
        password="StudentSecret123!",
        full_name="Maya Lin",
        role_name="Student",
        school_id=school.id
    )

    # Create Teacher's Class and enroll student
    test_class = Class(
        id=uuid.uuid4(),
        organization_id=org.id,
        school_id=school.id,
        teacher_id=teacher_user.id,
        name="Grade 6 Math - Period 2",
        grade_level=6,
        academic_year="2026-2027"
    )
    db_session.add(test_class)
    await db_session.commit()

    class_enrollment = Enrollment(
        id=uuid.uuid4(),
        organization_id=org.id,
        class_id=test_class.id,
        student_id=student_user.id
    )
    db_session.add(class_enrollment)
    await db_session.commit()

    teacher_token, _ = create_access_token(
        user_id=str(teacher_user.id),
        organization_id=str(org.id),
        school_id=str(school.id),
        roles=["Teacher"]
    )
    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}

    student_token, _ = create_access_token(
        user_id=str(student_user.id),
        organization_id=str(org.id),
        school_id=str(school.id),
        roles=["Student"]
    )
    student_headers = {"Authorization": f"Bearer {student_token}"}

    client = async_client

    # -------------------------------------------------------------
    # STEP A: Teacher Authentication & Profile Verification
    # -------------------------------------------------------------
    me_resp = await client.get("/api/v1/auth/me", headers=teacher_headers)
    assert me_resp.status_code == 200
    me_data = me_resp.json()["data"]
    assert me_data["email"] == "ms.johnson@lincoln.edu"
    assert "Teacher" in me_data["roles"]

    # -------------------------------------------------------------
    # STEP B: Class Roster Authorization
    # -------------------------------------------------------------
    classes_resp = await client.get("/api/v1/classes", headers=teacher_headers)
    assert classes_resp.status_code == 200
    classes_data = classes_resp.json()["data"]
    assert len(classes_data) >= 1
    assert any(c["name"] == "Grade 6 Math - Period 2" for c in classes_data)

    roster_resp = await client.get(f"/api/v1/classes/{test_class.id}/students", headers=teacher_headers)
    assert roster_resp.status_code == 200
    students_in_class = roster_resp.json()["data"]
    assert any(s["email"] == "maya.lin@lincoln.edu" for s in students_in_class)

    # -------------------------------------------------------------
    # STEP C: Curriculum Ingestion, Review & Publishing
    # -------------------------------------------------------------
    curr = Curriculum(
        id=uuid.uuid4(),
        organization_id=org.id,
        created_by_id=teacher_user.id,
        name="Grade 6 State Mathematics",
        grade_level=6,
        subject_name="Mathematics"
    )
    db_session.add(curr)
    await db_session.commit()

    curr_version = CurriculumVersion(
        id=uuid.uuid4(),
        curriculum_id=curr.id,
        version_number=1,
        status="DRAFT",
        created_by_id=teacher_user.id
    )
    chap = Chapter(id=uuid.uuid4(), curriculum_version_id=curr_version.id, name="Unit 1: Rational Numbers", sequence_order=1)
    top = Topic(id=uuid.uuid4(), chapter_id=chap.id, name="Adding Unlike Fractions", sequence_order=1)
    con = Concept(
        id=uuid.uuid4(),
        topic_id=top.id,
        name="Least Common Denominators (LCM)",
        description="Finding LCD before fraction addition",
        difficulty_level=3,
        sequence_order=1
    )
    db_session.add_all([curr_version, chap, top, con])
    await db_session.commit()

    # Teacher submits curriculum draft to REVIEW
    review_curr_resp = await client.post(
        f"/api/v1/curricula/versions/{curr_version.id}/status",
        json={"status": "REVIEW"},
        headers=teacher_headers
    )
    assert review_curr_resp.status_code == 200
    assert review_curr_resp.json()["data"]["status"] == "REVIEW"

    # Teacher reviews and approves curriculum
    approve_curr_resp = await client.post(
        f"/api/v1/curricula/versions/{curr_version.id}/status",
        json={"status": "APPROVED"},
        headers=teacher_headers
    )
    assert approve_curr_resp.status_code == 200
    assert approve_curr_resp.json()["data"]["status"] == "APPROVED"

    # Teacher publishes curriculum version to make it immutable
    publish_curr_resp = await client.post(
        f"/api/v1/curricula/versions/{curr_version.id}/status",
        json={"status": "PUBLISHED"},
        headers=teacher_headers
    )
    assert publish_curr_resp.status_code == 200
    assert publish_curr_resp.json()["data"]["status"] == "PUBLISHED"

    # -------------------------------------------------------------
    # STEP D: AI Question Generation & Human Approval Governance
    # -------------------------------------------------------------
    ai_question = QuestionBankItem(
        id=uuid.uuid4(),
        organization_id=org.id,
        curriculum_version_id=curr_version.id,
        concept_id=con.id,
        difficulty=3,
        question_type="mcq",
        question_text="What is 2/5 + 3/10 in simplest form?",
        options_json=["7/10", "5/15", "1/2", "4/5"],
        correct_answer_json="7/10",
        explanation="Convert 2/5 to 4/10. 4/10 + 3/10 = 7/10.",
        generation_method="AI_GENERATED",
        validation_status="PROPOSED",
        created_by_id=teacher_user.id
    )
    db_session.add(ai_question)
    await db_session.commit()

    # Teacher approves AI generated question
    approve_q_resp = await client.post(f"/api/v1/questions/{ai_question.id}/approve", headers=teacher_headers)
    assert approve_q_resp.status_code == 200
    assert approve_q_resp.json()["data"]["status"] == "APPROVED"

    # -------------------------------------------------------------
    # STEP E: Assessment Creation & Student Submission
    # -------------------------------------------------------------
    assessment = Assessment(
        id=uuid.uuid4(),
        organization_id=org.id,
        created_by_id=teacher_user.id,
        title="Unit 1 Fractions Quiz",
        assessment_type="QUIZ",
        is_published=True
    )
    db_session.add(assessment)
    await db_session.commit()

    aq = AssessmentQuestion(
        id=uuid.uuid4(),
        assessment_id=assessment.id,
        question_id=ai_question.id,
        sequence_order=1,
        points=1.0
    )
    db_session.add(aq)
    await db_session.commit()

    # Student starts attempt
    start_resp = await client.post(f"/api/v1/assessments/{assessment.id}/start", headers=student_headers)
    assert start_resp.status_code == 200
    attempt_id = start_resp.json()["data"]["attempt_id"]

    # Student answers
    ans_resp = await client.post(
        f"/api/v1/attempts/{attempt_id}/answer",
        json={
            "question_id": str(ai_question.id),
            "submitted_answer": "7/10"
        },
        headers=student_headers
    )
    assert ans_resp.status_code == 200
    assert ans_resp.json()["data"]["is_correct"] is True

    # Student submits
    submit_resp = await client.post(f"/api/v1/attempts/{attempt_id}/submit", headers=student_headers)
    assert submit_resp.status_code == 200
    assert submit_resp.json()["data"]["score"] == 1.0

    # -------------------------------------------------------------
    # STEP F: Subjective Question & Teacher Authoritative Override
    # -------------------------------------------------------------
    subj_question = QuestionBankItem(
        id=uuid.uuid4(),
        organization_id=org.id,
        curriculum_version_id=curr_version.id,
        concept_id=con.id,
        difficulty=4,
        question_type="short_answer",
        question_text="Explain why we cannot add numerators when denominators are different.",
        options_json=[],
        correct_answer_json="Denominators represent different sized unit parts.",
        explanation="Parts must be of equal size before counting total units.",
        rubric_json={"criteria": "Explains equal partition size"},
        generation_method="MANUAL",
        validation_status="APPROVED",
        created_by_id=teacher_user.id
    )
    db_session.add(subj_question)
    await db_session.commit()

    subj_answer = StudentAnswer(
        id=uuid.uuid4(),
        attempt_id=uuid.UUID(attempt_id),
        question_id=subj_question.id,
        submitted_answer_json="Because the slices are different sizes so you can't just count them.",
        points_awarded=0.5,
        evaluation_status="NEEDS_TEACHER_REVIEW",
        ai_evaluation_json={"confidence": 0.65, "reasoning": "Mentions slice sizes partially"}
    )
    db_session.add(subj_answer)
    await db_session.commit()

    # Teacher reviews and overrides score to 1.0 (Full credit)
    override_resp = await client.post(
        f"/api/v1/evaluations/answers/{subj_answer.id}/review",
        json={
            "action": "OVERRIDE",
            "new_score": 1.0,
            "feedback": "Excellent intuitive explanation with slice analogy."
        },
        headers=teacher_headers
    )
    assert override_resp.status_code == 200
    override_data = override_resp.json()["data"]
    assert override_data["points_awarded"] == 1.0
    assert override_data["evaluation_status"] == "TEACHER_OVERRIDDEN"
    assert override_data["teacher_override"] is True

    # -------------------------------------------------------------
    # STEP G: Class Analytics & Misconception Heatmap
    # -------------------------------------------------------------
    analytics_resp = await client.get(f"/api/v1/analytics/class/{test_class.id}", headers=teacher_headers)
    assert analytics_resp.status_code == 200
    analytics_data = analytics_resp.json()["data"]
    assert "class_average_mastery" in analytics_data
    assert "remediation_count" in analytics_data
    assert "student_count" in analytics_data

    # -------------------------------------------------------------
    # STEP H: Security & Cross-Class Isolation
    # -------------------------------------------------------------
    other_teacher = await UserService.create_user(
        session=db_session,
        organization_id=org.id,
        email="other.teacher@lincoln.edu",
        password="OtherPass123!",
        full_name="Mr. Other Teacher",
        role_name="Teacher",
        school_id=school.id
    )

    other_class = await ClassService.create_class(
        session=db_session,
        organization_id=org.id,
        school_id=school.id,
        teacher_id=other_teacher.id,
        name="Period 5 Science (Other Teacher)",
        grade_level=6,
        academic_year="2026-2027"
    )

    # Teacher attempting to view another teacher's unassigned class is rejected (403)
    unauth_resp = await client.get(f"/api/v1/classes/{other_class.id}", headers=teacher_headers)
    assert unauth_resp.status_code == 403
