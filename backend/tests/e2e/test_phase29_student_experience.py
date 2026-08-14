import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.api.main import app
from backend.models.user import User, Role, UserRole
from backend.models.organization import Organization, School
from backend.models.class_model import Class
from backend.models.curriculum import Curriculum, CurriculumVersion, Chapter, Topic, Concept
from backend.models.mastery import StudentMastery
from backend.models.assessment import QuestionBankItem, Assessment, AssessmentQuestion, AssessmentAttempt, StudentAnswer
from backend.services.user_service.auth import hash_password, create_access_token
from backend.services.adaptive_engine.engine import AdaptiveDecisionEngine, AdaptiveContext

@pytest.mark.asyncio
async def test_full_phase29_student_learning_journey_e2e(db_session: AsyncSession, async_client: AsyncClient):
    """
    Complete Student E2E Lifecycle:
    Login -> Dashboard -> Subject/Topic -> Lesson -> AI Socratic Tutor -> Practice -> Grading -> Mastery -> Next Adaptive Decision.
    """
    # 1. Setup Organization, School, and Student User
    org = Organization(id=uuid.uuid4(), name="Phase 29 Academy", code="PHASE29")
    school = School(id=uuid.uuid4(), organization_id=org.id, name="Middle School North", code="MSN")
    
    role_res = await db_session.execute(select(Role).where(Role.name == "Student"))
    student_role = role_res.scalars().first()
    if not student_role:
        student_role = Role(id=uuid.uuid4(), name="Student", description="Student Role")
        db_session.add(student_role)
    
    db_session.add_all([org, school])
    await db_session.commit()

    student_user = User(
        id=uuid.uuid4(),
        organization_id=org.id,
        school_id=school.id,
        email="alex.student@phase29.edu",
        password_hash=hash_password("StudentSecret123!"),
        full_name="Alex Rivera",
        is_active=True
    )
    db_session.add(student_user)
    await db_session.commit()

    ur = UserRole(user_id=student_user.id, role_id=student_role.id)
    db_session.add(ur)
    await db_session.commit()

    # 2. Setup Grade 6 Mathematics Curriculum, Chapter, Topic, Concept
    curr = Curriculum(
        id=uuid.uuid4(),
        organization_id=org.id,
        created_by_id=student_user.id,
        name="Grade 6 Math Standards",
        grade_level=6,
        subject_name="Mathematics"
    )
    db_session.add(curr)
    await db_session.commit()

    curr_v = CurriculumVersion(
        id=uuid.uuid4(),
        curriculum_id=curr.id,
        version_number=1,
        status="PUBLISHED",
        created_by_id=student_user.id
    )
    chap = Chapter(id=uuid.uuid4(), curriculum_version_id=curr_v.id, name="Chapter 1: Fractions", sequence_order=1)
    topic = Topic(id=uuid.uuid4(), chapter_id=chap.id, name="Adding Unlike Fractions", sequence_order=1)
    concept = Concept(
        id=uuid.uuid4(),
        topic_id=topic.id,
        name="Least Common Denominators (LCM)",
        description="Finding least common denominators before adding fractions",
        difficulty_level=3,
        sequence_order=1
    )
    db_session.add_all([curr_v, chap, topic, concept])
    await db_session.commit()

    token, _ = create_access_token(user_id=str(student_user.id), organization_id=str(org.id), school_id=str(school.id), roles=["Student"])
    headers = {"Authorization": f"Bearer {token}"}
    client = async_client

    # -------------------------------------------------------------
    # STEP A: Student Auth & Profile Verification
    # -------------------------------------------------------------
    me_resp = await client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    me_data = me_resp.json()["data"]
    assert me_data["email"] == "alex.student@phase29.edu"
    assert "Student" in me_data["roles"]

    # -------------------------------------------------------------
    # STEP B: List Subjects & Curriculum Catalog
    # -------------------------------------------------------------
    curr_resp = await client.get("/api/v1/curricula", headers=headers)
    assert curr_resp.status_code == 200
    curricula = curr_resp.json()["data"]
    assert len(curricula) >= 1
    assert curricula[0]["name"] == "Grade 6 Math Standards"

    # -------------------------------------------------------------
    # STEP C: AI Socratic Tutor Session & Hint Mode Turn
    # -------------------------------------------------------------
    tutor_sess_resp = await client.post(
        "/api/v1/tutor/sessions",
        json={
            "concept_id": str(concept.id),
            "curriculum_version_id": str(curr_v.id),
            "mode": "socratic"
        },
        headers=headers
    )
    assert tutor_sess_resp.status_code == 200
    sess_id = tutor_sess_resp.json()["data"]["session_id"]

    # Execute Socratic turn
    turn_resp = await client.post(
        "/api/v1/tutor/turn",
        json={
            "session_id": sess_id,
            "student_message": "How do I add 1/3 and 1/6? Give me a hint.",
            "mode": "hint"
        },
        headers=headers
    )
    assert turn_resp.status_code == 200
    turn_data = turn_resp.json()["data"]
    assert "tutor_response" in turn_data
    # Verify no direct homework leak in hint mode
    assert "the answer is 1/2" not in turn_data["tutor_response"].lower()

    # -------------------------------------------------------------
    # STEP D: Practice Question & Deterministic Evaluation
    # -------------------------------------------------------------
    q_item = QuestionBankItem(
        id=uuid.uuid4(),
        organization_id=org.id,
        curriculum_version_id=curr_v.id,
        concept_id=concept.id,
        difficulty=3,
        question_type="mcq",
        question_text="What is 1/3 + 1/6 in simplest form?",
        options_json=["1/2", "2/9", "3/6", "2/6"],
        correct_answer_json="1/2",
        explanation="Convert 1/3 to 2/6. 2/6 + 1/6 = 3/6 = 1/2.",
        created_by_id=student_user.id
    )
    db_session.add(q_item)
    await db_session.commit()

    assessment = Assessment(
        id=uuid.uuid4(),
        organization_id=org.id,
        created_by_id=student_user.id,
        title="Fraction LCM Checkpoint",
        assessment_type="QUIZ",
        is_published=True
    )
    db_session.add(assessment)
    await db_session.commit()

    assoc = AssessmentQuestion(
        id=uuid.uuid4(),
        assessment_id=assessment.id,
        question_id=q_item.id,
        sequence_order=1,
        points=1.0
    )
    db_session.add(assoc)
    await db_session.commit()

    # Start Assessment Attempt
    start_resp = await client.post(
        f"/api/v1/assessments/{assessment.id}/start",
        headers=headers
    )
    assert start_resp.status_code == 200
    attempt_id = start_resp.json()["data"]["attempt_id"]

    # Submit Question Answer
    ans_resp = await client.post(
        f"/api/v1/attempts/{attempt_id}/answer",
        json={
            "question_id": str(q_item.id),
            "submitted_answer": "1/2"
        },
        headers=headers
    )
    assert ans_resp.status_code == 200
    ans_data = ans_resp.json()["data"]
    assert ans_data["is_correct"] is True

    # Finalize and Submit Attempt
    sub_resp = await client.post(
        f"/api/v1/attempts/{attempt_id}/submit",
        headers=headers
    )
    assert sub_resp.status_code == 200
    sub_data = sub_resp.json()["data"]
    assert sub_data["score"] == 1.0

    # -------------------------------------------------------------
    # STEP E: Deterministic Mastery Update & Qualitative Band
    # -------------------------------------------------------------
    m_res = await db_session.execute(
        select(StudentMastery).where(
            StudentMastery.student_id == student_user.id,
            StudentMastery.concept_id == concept.id
        )
    )
    mastery = m_res.scalars().first()
    assert mastery is not None
    assert mastery.correct_count >= 1
    assert mastery.mastery_score > 0.0

    # -------------------------------------------------------------
    # STEP F: Authoritative Adaptive Recommendation
    # -------------------------------------------------------------
    adapt_ctx = AdaptiveContext(
        student_id=student_user.id,
        concept_id=concept.id,
        curriculum_version_id=curr_v.id,
        mastery_score=0.88,
        confidence=0.9,
        attempt_count=3,
        recent_performance=[True, True, True]
    )
    decision = AdaptiveDecisionEngine.make_decision(adapt_ctx)
    assert decision.decision in ["PROGRESS", "CHALLENGE"]

    # -------------------------------------------------------------
    # STEP G: Security Isolation - Cross-Tenant Access Rejection
    # -------------------------------------------------------------
    other_org = Organization(id=uuid.uuid4(), name="Other Academy", code="OTHER")
    db_session.add(other_org)
    await db_session.commit()

    other_assessment = Assessment(
        id=uuid.uuid4(),
        organization_id=other_org.id,
        created_by_id=uuid.uuid4(),
        title="Private Other Org Exam",
        assessment_type="QUIZ"
    )
    db_session.add(other_assessment)
    await db_session.commit()

    unauth_resp = await client.get(f"/api/v1/assessments/{other_assessment.id}", headers=headers)
    assert unauth_resp.status_code in [403, 404]
