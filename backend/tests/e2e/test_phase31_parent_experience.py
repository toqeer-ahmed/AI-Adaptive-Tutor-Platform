import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.models.organization import Organization, School
from backend.models.user import User, Role, UserRole
from backend.models.class_model import Class, Enrollment
from backend.models.security import ParentStudentLink
from backend.models.curriculum import Curriculum, CurriculumVersion, Chapter, Topic, Concept
from backend.models.mastery import StudentMastery
from backend.models.assessment import Assessment, AssessmentAttempt
from backend.services.user_service.service import UserService, ClassService
from backend.services.user_service.auth import create_access_token

@pytest.mark.asyncio
async def test_full_phase31_parent_lifecycle_and_privacy_e2e(db_session: AsyncSession, async_client: AsyncClient):
    """
    Complete Parent/Guardian E2E Lifecycle & Security Suite:
    1. Parent Authentication & Linked Children Listing
    2. Multi-Child Secure Dashboard Access
    3. Qualitative Progress & Anti-Leakage Validation (No raw floats or internal prompts)
    4. Assignments & Teacher Feedback Tracking
    5. Parent Notification Preferences Configuration
    6. Horizontal Escalation Protection (Unlinked Child in same district -> 403 Forbidden)
    7. Cross-Tenant Security Isolation (Child in foreign district -> 403 Forbidden)
    """
    # -------------------------------------------------------------
    # 1. Setup District, School, Curriculum & Concepts
    # -------------------------------------------------------------
    org_a = Organization(id=uuid.uuid4(), name="Lincoln Unified School District", code="LINC_USD")
    school_a = School(id=uuid.uuid4(), organization_id=org_a.id, name="Lincoln Middle School", code="LMS")
    db_session.add_all([org_a, school_a])
    await db_session.commit()

    # Ensure Roles
    for role_name in ["Parent", "Student", "Teacher", "OrgAdmin", "SchoolAdmin"]:
        r_res = await db_session.execute(select(Role).where(Role.name == role_name))
        if not r_res.scalars().first():
            db_session.add(Role(id=uuid.uuid4(), name=role_name, description=f"{role_name} role"))
    await db_session.commit()

    # Teachers and Classes
    teacher = await UserService.create_user(
        session=db_session,
        organization_id=org_a.id,
        email="ms.clara@lincoln.edu",
        password="TeacherPass123!",
        full_name="Ms. Clara Johnson",
        role_name="Teacher",
        school_id=school_a.id
    )

    class_6a = await ClassService.create_class(
        session=db_session,
        organization_id=org_a.id,
        school_id=school_a.id,
        teacher_id=teacher.id,
        name="Grade 6 Math - Period 2",
        grade_level=6,
        academic_year="2026-2027"
    )

    # -------------------------------------------------------------
    # 2. Setup Parent A with Two Linked Children (Child 1 & Child 2)
    # -------------------------------------------------------------
    parent_a = await UserService.create_user(
        session=db_session,
        organization_id=org_a.id,
        email="elena.lin@family.net",
        password="ParentPass123!",
        full_name="Elena Lin",
        role_name="Parent",
        school_id=school_a.id
    )

    child_1 = await UserService.create_user(
        session=db_session,
        organization_id=org_a.id,
        email="maya.lin@lincoln.edu",
        password="ChildPass123!",
        full_name="Maya Lin",
        role_name="Student",
        school_id=school_a.id
    )

    child_2 = await UserService.create_user(
        session=db_session,
        organization_id=org_a.id,
        email="leo.lin@lincoln.edu",
        password="ChildPass123!",
        full_name="Leo Lin",
        role_name="Student",
        school_id=school_a.id
    )

    # Enroll Child 1
    await ClassService.enroll_student(db_session, org_a.id, class_6a.id, child_1.id)

    # Link Parent A -> Child 1 & Child 2
    link_1 = ParentStudentLink(id=uuid.uuid4(), organization_id=org_a.id, parent_id=parent_a.id, student_id=child_1.id)
    link_2 = ParentStudentLink(id=uuid.uuid4(), organization_id=org_a.id, parent_id=parent_a.id, student_id=child_2.id)
    db_session.add_all([link_1, link_2])
    await db_session.commit()

    # -------------------------------------------------------------
    # 3. Setup Unlinked Child in District A (Child 3)
    # -------------------------------------------------------------
    child_unlinked = await UserService.create_user(
        session=db_session,
        organization_id=org_a.id,
        email="sammy.unlinked@lincoln.edu",
        password="ChildPass123!",
        full_name="Sammy Unlinked",
        role_name="Student",
        school_id=school_a.id
    )

    # -------------------------------------------------------------
    # 4. Setup Curriculum & Mastery for Child 1
    # -------------------------------------------------------------
    curr = Curriculum(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        created_by_id=teacher.id,
        name="Grade 6 Math",
        grade_level=6,
        subject_name="Mathematics",
        description="Grade 6 Mathematics Curriculum"
    )
    curr_v = CurriculumVersion(
        id=uuid.uuid4(),
        curriculum_id=curr.id,
        version_number=1,
        status="PUBLISHED",
        created_by_id=teacher.id
    )
    ch = Chapter(id=uuid.uuid4(), curriculum_version_id=curr_v.id, name="Fractions & Operations", sequence_order=1)
    top = Topic(id=uuid.uuid4(), chapter_id=ch.id, name="Adding Fractions", sequence_order=1)
    con_1 = Concept(id=uuid.uuid4(), topic_id=top.id, name="Like Denominators Addition", sequence_order=1)
    con_2 = Concept(id=uuid.uuid4(), topic_id=top.id, name="Unlike Denominators Addition", sequence_order=2)
    db_session.add_all([curr, curr_v, ch, top, con_1, con_2])
    await db_session.commit()

    # Child 1 Mastery: Concept 1 = 0.85 (Strong), Concept 2 = 0.35 (Growing skill)
    sm_1 = StudentMastery(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        curriculum_version_id=curr_v.id,
        student_id=child_1.id,
        concept_id=con_1.id,
        mastery_score=0.85,
        status="MASTERED",
        attempt_count=6
    )
    sm_2 = StudentMastery(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        curriculum_version_id=curr_v.id,
        student_id=child_1.id,
        concept_id=con_2.id,
        mastery_score=0.35,
        status="PRACTICING",
        attempt_count=3
    )
    db_session.add_all([sm_1, sm_2])
    await db_session.commit()

    # Completed Assessment for Child 1
    assessment = Assessment(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        school_id=school_a.id,
        class_id=class_6a.id,
        title="Fractions Check #1",
        assessment_type="QUIZ",
        is_published=True,
        created_by_id=teacher.id
    )
    db_session.add(assessment)
    await db_session.commit()

    attempt = AssessmentAttempt(
        id=uuid.uuid4(),
        assessment_id=assessment.id,
        student_id=child_1.id,
        status="GRADED",
        score=9.0,
        max_score=10.0
    )
    db_session.add(attempt)
    await db_session.commit()

    # Auth Token for Parent A
    parent_token, _ = create_access_token(
        user_id=str(parent_a.id),
        organization_id=str(org_a.id),
        roles=["Parent"],
        school_id=str(school_a.id)
    )
    parent_headers = {"Authorization": f"Bearer {parent_token}"}
    client = async_client

    # =============================================================
    # STEP A: List Linked Children (Child 1 & Child 2)
    # =============================================================
    children_resp = await client.get("/api/v1/parents/children", headers=parent_headers)
    assert children_resp.status_code == 200
    children_list = children_resp.json()["data"]
    assert len(children_list) == 2
    student_names = [c["student_name"] for c in children_list]
    assert "Maya Lin" in student_names
    assert "Leo Lin" in student_names
    assert "Sammy Unlinked" not in student_names

    # =============================================================
    # STEP B: Parent Accesses Linked Child 1 Dashboard
    # =============================================================
    dash_1_resp = await client.get(f"/api/v1/parents/child/{child_1.id}/dashboard", headers=parent_headers)
    assert dash_1_resp.status_code == 200
    dash_1_data = dash_1_resp.json()["data"]
    assert dash_1_data["child_name"] == "Maya Lin"
    assert "subjects" in dash_1_data
    assert "teacher_notes" in dash_1_data
    assert len(dash_1_data["qualitative_progress"]) >= 2
    assert dash_1_data["qualitative_progress"][0]["qualitative_band"] == "Strong 🌟"

    # =============================================================
    # STEP C: Parent Switches & Accesses Linked Child 2 Dashboard
    # =============================================================
    dash_2_resp = await client.get(f"/api/v1/parents/child/{child_2.id}/dashboard", headers=parent_headers)
    assert dash_2_resp.status_code == 200
    dash_2_data = dash_2_resp.json()["data"]
    assert dash_2_data["child_name"] == "Leo Lin"

    # =============================================================
    # STEP D: Detailed Qualitative Progress & Anti-Leakage
    # =============================================================
    prog_resp = await client.get(f"/api/v1/parents/child/{child_1.id}/progress", headers=parent_headers)
    assert prog_resp.status_code == 200
    prog_data = prog_resp.json()["data"]
    assert len(prog_data["strengths"]) >= 1
    assert "Mastered & Confident" in prog_data["strengths"][0]["qualitative_status"]
    assert len(prog_data["growing_skills"]) >= 1
    assert "Building Skills" in prog_data["growing_skills"][0]["qualitative_status"]

    # Verify no raw floating-point score leakage in json keys
    prog_text = prog_resp.text
    assert "0.85" not in prog_text
    assert "0.35" not in prog_text
    assert "system_prompt" not in prog_text
    assert "internal" not in prog_text.lower() or "internal pii" in prog_text.lower()

    # =============================================================
    # STEP E: Assignments & Teacher Feedback View
    # =============================================================
    assign_resp = await client.get(f"/api/v1/parents/child/{child_1.id}/assignments", headers=parent_headers)
    assert assign_resp.status_code == 200
    assign_data = assign_resp.json()["data"]
    assert "pending_assignments" in assign_data
    assert "completed_assignments" in assign_data
    assert len(assign_data["completed_assignments"]) >= 1
    assert assign_data["completed_assignments"][0]["title"] == "Fractions Check #1"

    # =============================================================
    # STEP F: Parent Notification Preferences (GET & PUT)
    # =============================================================
    notif_get = await client.get("/api/v1/parents/notifications/settings", headers=parent_headers)
    assert notif_get.status_code == 200
    assert notif_get.json()["data"]["digest_frequency"] == "DAILY"

    notif_put = await client.put(
        "/api/v1/parents/notifications/settings",
        json={
            "email_enabled": True,
            "in_app_enabled": True,
            "push_enabled": False,
            "digest_frequency": "WEEKLY"
        },
        headers=parent_headers
    )
    assert notif_put.status_code == 200
    assert notif_put.json()["data"]["digest_frequency"] == "WEEKLY"

    # =============================================================
    # STEP G: Security Check 1 — Horizontal IDOR Escalation (Unlinked Child)
    # =============================================================
    unlinked_resp = await client.get(f"/api/v1/parents/child/{child_unlinked.id}/dashboard", headers=parent_headers)
    assert unlinked_resp.status_code == 403
    assert "access denied" in unlinked_resp.json()["detail"].lower()

    # =============================================================
    # STEP H: Security Check 2 — Cross-Tenant Isolation (Child in Foreign Org)
    # =============================================================
    foreign_org = Organization(id=uuid.uuid4(), name="Metro School District", code="METRO_DIST")
    foreign_school = School(id=uuid.uuid4(), organization_id=foreign_org.id, name="Metro High", code="MHS")
    db_session.add_all([foreign_org, foreign_school])
    await db_session.commit()

    foreign_student = await UserService.create_user(
        session=db_session,
        organization_id=foreign_org.id,
        email="foreign.student@metro.edu",
        password="Pass123!",
        full_name="Foreign Student",
        role_name="Student",
        school_id=foreign_school.id
    )

    foreign_resp = await client.get(f"/api/v1/parents/child/{foreign_student.id}/dashboard", headers=parent_headers)
    assert foreign_resp.status_code in [403, 404]
