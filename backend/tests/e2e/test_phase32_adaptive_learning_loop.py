import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.models.organization import Organization, School
from backend.models.user import User, Role
from backend.models.class_model import Class, Enrollment
from backend.models.curriculum import (
    Curriculum,
    CurriculumVersion,
    Chapter,
    Topic,
    Concept,
    ConceptPrerequisite
)
from backend.models.mastery import StudentMastery, MasteryHistoryLog
from backend.models.assessment import QuestionBankItem, Assessment, AssessmentQuestion, AssessmentAttempt, StudentAnswer
from backend.models.audit import AuditLogEntry
from backend.models.tutor import TutorSession, TutorTurn
from backend.services.user_service.service import UserService, ClassService
from backend.services.user_service.auth import create_access_token
from backend.services.mastery_service.service import MasteryService
from backend.services.mastery_service.policy import MasteryEvent
from backend.services.adaptive_engine.service import AdaptiveLearningService

@pytest.mark.asyncio
async def test_full_end_to_end_adaptive_learning_loop(db_session: AsyncSession, async_client: AsyncClient):
    """
    PHASE 32: Complete End-to-End Adaptive Education Loop Integration Test
    
    Validates the entire continuous cycle:
    1. Teacher Setup -> Curriculum Creation (Grade 6 Math: Fractions) & Version Publishing
    2. Student Enrollment -> Initial Unknown/Low Mastery State (0.0)
    3. Initial Activity Recommendation -> Weak Prerequisite Routing (PREREQUISITE_REMEDIATION)
    4. Socratic AI Instructor Interaction on Prerequisite Concept
    5. Prerequisite Practice & Deterministic Mastery Progression (0.0 -> 0.78 MASTERED)
    6. Target Concept Repeated Failure -> Mastery Drop & REMEDIATE Trigger (Difficulty 1)
    7. AI Instructor Socratic Remediation & Guided Step-by-Step Discovery
    8. Student Recovery & Sustained Success -> Mastery Climb (0.92) & CHALLENGE Trigger (Difficulty 5)
    9. Formal Assessment Execution & Deterministic Auto-Grading (100%)
    10. Complete Audit Provenance & Learning Event Trail Verification
    """
    client = async_client

    # =============================================================
    # STEP 1: District, School, Teacher & Curriculum Setup
    # =============================================================
    org = Organization(id=uuid.uuid4(), name="Algonquin School District", code="ALG_DIST")
    school = School(id=uuid.uuid4(), organization_id=org.id, name="Algonquin Middle School", code="AMS")
    db_session.add_all([org, school])
    await db_session.commit()

    # Ensure Roles
    for role_name in ["Teacher", "Student", "OrgAdmin", "SchoolAdmin", "Parent"]:
        r_res = await db_session.execute(select(Role).where(Role.name == role_name))
        if not r_res.scalars().first():
            db_session.add(Role(id=uuid.uuid4(), name=role_name, description=f"{role_name} role"))
    await db_session.commit()

    # Teacher
    teacher = await UserService.create_user(
        session=db_session,
        organization_id=org.id,
        email="mr.davis@algonquin.edu",
        password="TeacherPass123!",
        full_name="Mr. Marcus Davis",
        role_name="Teacher",
        school_id=school.id
    )

    teacher_token, _ = create_access_token(
        user_id=str(teacher.id),
        organization_id=str(org.id),
        roles=["Teacher"],
        school_id=str(school.id)
    )
    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}

    # Class
    math_class = await ClassService.create_class(
        session=db_session,
        organization_id=org.id,
        school_id=school.id,
        teacher_id=teacher.id,
        name="Grade 6 Math - Period 1",
        grade_level=6,
        academic_year="2026-2027"
    )

    # Curriculum & Hierarchy
    curr = Curriculum(
        id=uuid.uuid4(),
        organization_id=org.id,
        created_by_id=teacher.id,
        name="Grade 6 Mathematics Core",
        grade_level=6,
        subject_name="Mathematics",
        description="Comprehensive Grade 6 Math Curriculum"
    )
    curr_v = CurriculumVersion(
        id=uuid.uuid4(),
        curriculum_id=curr.id,
        version_number=1,
        status="DRAFT",
        created_by_id=teacher.id
    )
    ch = Chapter(id=uuid.uuid4(), curriculum_version_id=curr_v.id, name="Fractions & Operations", sequence_order=1)
    top = Topic(id=uuid.uuid4(), chapter_id=ch.id, name="Fraction Operations & Mastery", sequence_order=1)
    
    # Concept 1: Prerequisite Concept
    con_prereq = Concept(id=uuid.uuid4(), topic_id=top.id, name="Equivalent Fractions", difficulty_level=2, sequence_order=1)
    # Concept 2: Target Concept
    con_target = Concept(id=uuid.uuid4(), topic_id=top.id, name="Addition of Fractions with Like Denominators", difficulty_level=3, sequence_order=2)
    # Concept 3: Advanced Target Concept
    con_advanced = Concept(id=uuid.uuid4(), topic_id=top.id, name="Addition of Fractions with Unlike Denominators", difficulty_level=4, sequence_order=3)
    
    db_session.add_all([curr, curr_v, ch, top, con_prereq, con_target, con_advanced])
    await db_session.commit()

    # Link Concept 1 as Prerequisite for Concept 2
    prereq_link = ConceptPrerequisite(
        id=uuid.uuid4(),
        concept_id=con_target.id,
        prerequisite_concept_id=con_prereq.id,
        relationship_type="STRICT"
    )
    db_session.add(prereq_link)
    await db_session.commit()

    # Publish Curriculum Version via Teacher Governance State Machine: DRAFT -> REVIEW -> APPROVED -> PUBLISHED
    for next_status in ["REVIEW", "APPROVED", "PUBLISHED"]:
        trans_resp = await client.post(
            f"/api/v1/curricula/versions/{curr_v.id}/status",
            json={"status": next_status, "change_log": f"Governance progression to {next_status}"},
            headers=teacher_headers
        )
        assert trans_resp.status_code == 200

    # Question Bank Items for Prerequisite (Concept 1)
    qb_prereq_1 = QuestionBankItem(
        id=uuid.uuid4(),
        organization_id=org.id,
        curriculum_version_id=curr_v.id,
        concept_id=con_prereq.id,
        difficulty=2,
        question_type="multiple_choice",
        question_text="Which fraction is equivalent to 1/2?",
        options_json=[{"id": "A", "text": "2/4"}, {"id": "B", "text": "2/3"}, {"id": "C", "text": "1/4"}, {"id": "D", "text": "3/5"}],
        correct_answer_json="A",
        explanation="Multiplying numerator and denominator by 2 gives 2/4.",
        validation_status="APPROVED",
        created_by_id=teacher.id
    )
    # Question Bank Items for Target (Concept 2)
    qb_target_easy = QuestionBankItem(
        id=uuid.uuid4(),
        organization_id=org.id,
        curriculum_version_id=curr_v.id,
        concept_id=con_target.id,
        difficulty=1,
        question_type="numeric",
        question_text="Calculate: 1/5 + 2/5 (Express as fraction)",
        options_json=[],
        correct_answer_json="3/5",
        explanation="Since denominators are equal (5), add numerators: 1 + 2 = 3/5.",
        validation_status="APPROVED",
        created_by_id=teacher.id
    )
    qb_target_hard = QuestionBankItem(
        id=uuid.uuid4(),
        organization_id=org.id,
        curriculum_version_id=curr_v.id,
        concept_id=con_target.id,
        difficulty=5,
        question_type="numeric",
        question_text="Evaluate and simplify: 3/12 + 5/12 + 2/12",
        options_json=[],
        correct_answer_json="5/6",
        explanation="3/12 + 5/12 + 2/12 = 10/12 = 5/6.",
        validation_status="APPROVED",
        created_by_id=teacher.id
    )
    db_session.add_all([qb_prereq_1, qb_target_easy, qb_target_hard])
    await db_session.commit()

    # =============================================================
    # STEP 2: Student Enrollment & Initial State
    # =============================================================
    student = await UserService.create_user(
        session=db_session,
        organization_id=org.id,
        email="leo.hernandez@algonquin.edu",
        password="StudentPass123!",
        full_name="Leo Hernandez",
        role_name="Student",
        school_id=school.id
    )

    await ClassService.enroll_student(db_session, org.id, math_class.id, student.id)

    student_token, _ = create_access_token(
        user_id=str(student.id),
        organization_id=str(org.id),
        roles=["Student"],
        school_id=str(school.id)
    )
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # Verify initial student mastery is NOT_STARTED / 0.0
    init_mastery = await MasteryService.get_or_create_mastery(
        session=db_session,
        organization_id=org.id,
        student_id=student.id,
        concept_id=con_target.id,
        curriculum_version_id=curr_v.id
    )
    assert init_mastery.mastery_score == 0.0
    assert init_mastery.status == "NOT_STARTED"

    # =============================================================
    # STEP 3: Initial Activity Recommendation (Weak Prerequisite Routing)
    # =============================================================
    # Student requests adaptive recommendation for Concept 2 (Like Denominators Addition)
    decide_resp_1 = await client.post(
        "/api/v1/adaptive/decide",
        json={
            "concept_id": str(con_target.id),
            "curriculum_version_id": str(curr_v.id)
        },
        headers=student_headers
    )
    assert decide_resp_1.status_code == 200
    dec_data_1 = decide_resp_1.json()["data"]
    # Priority 1: Prerequisite Concept 1 is unmastered (0.0 < 0.70), routes to PREREQUISITE_REMEDIATION
    assert dec_data_1["decision"] == "PREREQUISITE_REMEDIATION"
    assert dec_data_1["target_concept_id"] == str(con_prereq.id)
    assert dec_data_1["priority_level"] == 1

    # =============================================================
    # STEP 4: AI Instructor Socratic Turn on Prerequisite
    # =============================================================
    tutor_sess_resp = await client.post(
        "/api/v1/tutor/sessions",
        json={
            "concept_id": str(con_prereq.id),
            "curriculum_version_id": str(curr_v.id),
            "mode": "explanation"
        },
        headers=student_headers
    )
    assert tutor_sess_resp.status_code == 200
    tutor_sess_id = tutor_sess_resp.json()["data"]["session_id"]

    turn_resp = await client.post(
        "/api/v1/tutor/turn",
        json={
            "session_id": tutor_sess_id,
            "student_message": "Why is 2/4 equal to 1/2? Can you give me a simple example?",
            "provider": "mock"
        },
        headers=student_headers
    )
    assert turn_resp.status_code == 200
    turn_data = turn_resp.json()["data"]
    assert len(turn_data["tutor_response"]) > 10
    assert turn_data["mode"] == "explanation"

    # =============================================================
    # STEP 5: Prerequisite Practice & Deterministic Mastery Progression
    # =============================================================
    # Student practices Concept 1 (Equivalent Fractions) and answers correctly to achieve mastery >= 0.70
    for _ in range(8):
        await MasteryService.record_learning_event(
            session=db_session,
            organization_id=org.id,
            event=MasteryEvent(
                student_id=student.id,
                concept_id=con_prereq.id,
                curriculum_version_id=curr_v.id,
                is_correct=True,
                item_difficulty=5,
                response_time_sec=12.0
            )
        )

    prereq_mastery_updated = await MasteryService.get_or_create_mastery(
        session=db_session,
        organization_id=org.id,
        student_id=student.id,
        concept_id=con_prereq.id,
        curriculum_version_id=curr_v.id
    )
    assert prereq_mastery_updated.mastery_score >= 0.70
    assert prereq_mastery_updated.status in ["IN_PROGRESS", "MASTERED"]

    # =============================================================
    # STEP 6: Target Concept Repeated Failure -> Mastery Drop & REMEDIATE Trigger
    # =============================================================
    # Now that prerequisite is mastered, student attempts Concept 2
    # Student repeatedly fails 3 times on Concept 2 (adding denominators mistake)
    for _ in range(3):
        await MasteryService.record_learning_event(
            session=db_session,
            organization_id=org.id,
            event=MasteryEvent(
                student_id=student.id,
                concept_id=con_target.id,
                curriculum_version_id=curr_v.id,
                is_correct=False,
                item_difficulty=3,
                response_time_sec=30.0
            )
        )

    target_mastery_failed = await MasteryService.get_or_create_mastery(
        session=db_session,
        organization_id=org.id,
        student_id=student.id,
        concept_id=con_target.id,
        curriculum_version_id=curr_v.id
    )
    assert target_mastery_failed.mastery_score < 0.40
    assert target_mastery_failed.attempt_count >= 3
    assert target_mastery_failed.status == "NEEDS_REMEDIATION"

    # Adaptive Decision Engine triggers PRIORITY 3: REMEDIATE (Difficulty 1)
    decide_resp_2 = await client.post(
        "/api/v1/adaptive/decide",
        json={
            "concept_id": str(con_target.id),
            "curriculum_version_id": str(curr_v.id)
        },
        headers=student_headers
    )
    assert decide_resp_2.status_code == 200
    dec_data_2 = decide_resp_2.json()["data"]
    assert dec_data_2["decision"] == "REMEDIATE"
    assert dec_data_2["recommended_difficulty"] == 1
    assert dec_data_2["priority_level"] == 3

    # =============================================================
    # STEP 7: AI Instructor Socratic Remediation / Hint Mode
    # =============================================================
    remed_turn_resp = await client.post(
        "/api/v1/tutor/turn",
        json={
            "session_id": tutor_sess_id,
            "student_message": "I keep adding the bottom numbers like 1/4 + 1/4 = 2/8. What am I doing wrong?",
            "mode": "hint",
            "provider": "mock"
        },
        headers=student_headers
    )
    assert remed_turn_resp.status_code == 200
    assert remed_turn_resp.json()["data"]["mode"] == "hint"

    # =============================================================
    # STEP 8: Student Recovery & Sustained Success -> CHALLENGE Trigger (Difficulty 5)
    # =============================================================
    # Student successfully solves progressively harder problems and achieves mastery >= 0.90
    for _ in range(16):
        await MasteryService.record_learning_event(
            session=db_session,
            organization_id=org.id,
            event=MasteryEvent(
                student_id=student.id,
                concept_id=con_target.id,
                curriculum_version_id=curr_v.id,
                is_correct=True,
                item_difficulty=5,
                response_time_sec=10.0
            )
        )

    target_mastery_high = await MasteryService.get_or_create_mastery(
        session=db_session,
        organization_id=org.id,
        student_id=student.id,
        concept_id=con_target.id,
        curriculum_version_id=curr_v.id
    )
    assert target_mastery_high.mastery_score >= 0.90
    assert target_mastery_high.status == "MASTERED"

    # Adaptive Decision Engine triggers PRIORITY 4: CHALLENGE (Difficulty 5)
    decide_resp_3 = await client.post(
        "/api/v1/adaptive/decide",
        json={
            "concept_id": str(con_target.id),
            "curriculum_version_id": str(curr_v.id)
        },
        headers=student_headers
    )
    assert decide_resp_3.status_code == 200
    dec_data_3 = decide_resp_3.json()["data"]
    assert dec_data_3["decision"] == "CHALLENGE"
    assert dec_data_3["recommended_difficulty"] == 5
    assert dec_data_3["priority_level"] == 4

    # =============================================================
    # STEP 9: Formal Assessment Execution & Deterministic Grading
    # =============================================================
    assessment = Assessment(
        id=uuid.uuid4(),
        organization_id=org.id,
        school_id=school.id,
        class_id=math_class.id,
        title="Grade 6 Fractions Unit Mastery Check",
        assessment_type="QUIZ",
        is_published=True,
        created_by_id=teacher.id
    )
    aq = AssessmentQuestion(
        id=uuid.uuid4(),
        assessment_id=assessment.id,
        question_id=qb_target_hard.id,
        sequence_order=1,
        points=10.0
    )
    db_session.add_all([assessment, aq])
    await db_session.commit()

    # Student starts quiz
    start_resp = await client.post(f"/api/v1/assessments/{assessment.id}/start", headers=student_headers)
    assert start_resp.status_code == 200
    attempt_id = start_resp.json()["data"]["attempt_id"]

    # Student submits exact correct fraction answer
    ans_resp = await client.post(
        f"/api/v1/attempts/{attempt_id}/answer",
        json={
            "question_id": str(qb_target_hard.id),
            "submitted_answer": "5/6"
        },
        headers=student_headers
    )
    assert ans_resp.status_code == 200
    assert ans_resp.json()["data"]["is_correct"] is True

    # Submit quiz
    sub_resp = await client.post(f"/api/v1/attempts/{attempt_id}/submit", headers=student_headers)
    assert sub_resp.status_code == 200
    assert sub_resp.json()["data"]["status"] == "GRADED"
    assert sub_resp.json()["data"]["percentage"] == 100.0

    # =============================================================
    # STEP 10: Complete Audit & Provenance Verification
    # =============================================================
    # Verify Audit Logs
    audit_res = await db_session.execute(
        select(AuditLogEntry).where(AuditLogEntry.organization_id == org.id)
    )
    audit_entries = audit_res.scalars().all()
    assert len(audit_entries) >= 4

    actions = [a.action for a in audit_entries]
    assert "CURRICULUM_PUBLISHED" in actions
    assert "ADAPTIVE_DECISION_GENERATED" in actions
    assert "TUTOR_TURN_EXECUTED" in actions

    # Verify Mastery History Logs
    m_history_res = await db_session.execute(
        select(MasteryHistoryLog).where(
            MasteryHistoryLog.student_id == student.id,
            MasteryHistoryLog.concept_id == con_target.id
        ).order_by(MasteryHistoryLog.created_at.asc())
    )
    history_logs = m_history_res.scalars().all()
    assert len(history_logs) >= 8  # 3 failed attempts + 5 recovery attempts
    # Verify recorded history captures progression
    assert history_logs[0].previous_mastery == 0.0
    assert history_logs[-1].new_mastery >= 0.90
