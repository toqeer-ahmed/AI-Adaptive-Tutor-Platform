import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.services.organization_service.service import OrganizationService
from backend.services.user_service.service import UserService, ClassService
from backend.services.curriculum_service.service import CurriculumService
from backend.services.assessment_service.service import AssessmentService
from backend.services.mastery_service.service import MasteryService
from backend.services.mastery_service.policy import MasteryEvent
from backend.services.adaptive_engine.service import AdaptiveLearningService
from backend.services.tutor_service.service import TutorService
from backend.services.analytics_service.service import AnalyticsAggregationService
from backend.models.organization import School
from backend.models.assessment import QuestionBankItem

@pytest.mark.asyncio
async def test_complete_end_to_end_platform_lifecycle_scenario(db_session: AsyncSession):
    """
    Complete E2E Automated Scenario:
    1. Teacher creates organization -> creates school -> creates class
    2. Uploads Grade 6 Mathematics syllabus -> approves curriculum -> publishes curriculum
    3. Creates assignment
    4. Student logs in & completes questions -> deterministic grading occurs
    5. Mastery updates -> Adaptive engine chooses next activity
    6. AI Instructor teaches next activity -> Teacher sees analytics
    """
    # -----------------------------------------------------------------
    # STEP 1: Teacher creates Organization, School & Grade 6 Math Class
    # -----------------------------------------------------------------
    org = await OrganizationService.create_organization(db_session, "Apex Education District", "APEXDIST")
    teacher = await UserService.create_user(db_session, org.id, "teacher.apex@school.edu", "Pass123!", "Teacher Apex", "Teacher")

    school = School(
        id=uuid.uuid4(),
        organization_id=org.id,
        name="Apex Middle School",
        code="AMS01"
    )
    db_session.add(school)
    await db_session.commit()

    math_class = await ClassService.create_class(
        session=db_session,
        organization_id=org.id,
        school_id=school.id,
        teacher_id=teacher.id,
        name="Grade 6 Accelerated Math",
        grade_level=6,
        academic_year="2026-2027"
    )
    assert math_class.id is not None

    # -----------------------------------------------------------------
    # STEP 2: Upload Grade 6 Math Syllabus, Approve & Publish Curriculum
    # -----------------------------------------------------------------
    created_curriculum = await CurriculumService.create_curriculum(
        session=db_session,
        creator=teacher,
        name="Grade 6 Mathematics Core",
        grade_level=6,
        subject_name="Mathematics"
    )

    curriculum = await CurriculumService.get_curriculum_by_id(db_session, created_curriculum.id)
    ver_id = curriculum.versions[0].id

    # Transition DRAFT -> REVIEW -> APPROVED -> PUBLISHED
    await CurriculumService.transition_version_status(db_session, ver_id, "REVIEW", teacher)
    await CurriculumService.transition_version_status(db_session, ver_id, "APPROVED", teacher)
    published_version = await CurriculumService.transition_version_status(db_session, ver_id, "PUBLISHED", teacher)
    assert published_version.status == "PUBLISHED"

    # Create Chapter, Topic, Concept
    draft_ver = await CurriculumService.create_new_version(db_session, curriculum.id, teacher, "Draft version 2")
    chapter = await CurriculumService.create_chapter(db_session, draft_ver.id, "Fractions & Decimals")
    topic = await CurriculumService.create_topic(db_session, chapter.id, "Adding Unlike Fractions")
    concept = await CurriculumService.create_concept(db_session, topic.id, "Least Common Denominator", difficulty_level=3)

    # -----------------------------------------------------------------
    # STEP 3: Teacher Creates Question Bank Item & Assessment
    # -----------------------------------------------------------------
    item = QuestionBankItem(
        id=uuid.uuid4(),
        organization_id=org.id,
        concept_id=concept.id,
        curriculum_version_id=published_version.id,
        created_by_id=teacher.id,
        question_text="What is 1/3 + 1/6 in simplest form?",
        question_type="MULTIPLE_CHOICE",
        correct_answer_json="1/2",
        options_json=["2/9", "3/6", "1/2", "2/3"],
        difficulty=3,
        validation_status="APPROVED"
    )
    db_session.add(item)
    await db_session.commit()

    assessment = await AssessmentService.create_assessment(
        session=db_session,
        creator=teacher,
        title="Grade 6 Fractions Quiz 1",
        class_id=math_class.id,
        question_ids=[item.id]
    )
    assert assessment.id is not None

    # -----------------------------------------------------------------
    # STEP 4: Student Logs In & Enrolls in Class
    # -----------------------------------------------------------------
    student = await UserService.create_user(db_session, org.id, "student.apex@school.edu", "Pass123!", "Student Apex", "Student")
    await ClassService.enroll_student(db_session, org.id, math_class.id, student.id)

    # -----------------------------------------------------------------
    # STEP 5: Student Completes Quiz & Deterministic Grading Occurs
    # -----------------------------------------------------------------
    attempt = await AssessmentService.start_attempt(db_session, assessment.id, student)

    # Student submits answer ("1/2")
    await AssessmentService.submit_answer(
        session=db_session,
        attempt_id=attempt.id,
        question_id=item.id,
        submitted_answer="1/2"
    )

    graded_attempt = await AssessmentService.submit_attempt(
        session=db_session,
        attempt_id=attempt.id
    )

    assert graded_attempt.status == "GRADED"
    assert graded_attempt.score == 1.0

    # -----------------------------------------------------------------
    # STEP 6: Mastery Updates & Adaptive Engine Chooses Next Activity
    # -----------------------------------------------------------------
    event = MasteryEvent(
        student_id=student.id,
        concept_id=concept.id,
        curriculum_version_id=published_version.id,
        is_correct=True,
        item_difficulty=3
    )
    mastery_rec = await MasteryService.record_learning_event(db_session, org.id, event)
    assert mastery_rec.mastery_score > 0.0

    decision = await AdaptiveLearningService.get_next_learning_decision(
        session=db_session,
        student=student,
        concept_id=concept.id,
        curriculum_version_id=published_version.id
    )

    assert decision.decision in ["PROGRESS", "CHALLENGE", "REINFORCE", "REMEDIATE"]

    # -----------------------------------------------------------------
    # STEP 7: AI Instructor Teaches Next Activity
    # -----------------------------------------------------------------
    tutor_session = await TutorService.create_session(
        session=db_session,
        student=student,
        concept_id=concept.id,
        curriculum_version_id=published_version.id,
        initial_mode=decision.decision.lower()
    )

    turn = await TutorService.execute_turn(
        session=db_session,
        session_id=tutor_session.id,
        student=student,
        student_message="Can you explain how finding the least common denominator works?",
        provider="mock"
    )

    assert turn.tutor_response is not None
    assert len(turn.tutor_response) > 0

    # -----------------------------------------------------------------
    # STEP 8: Teacher Views Deterministic Class Analytics
    # -----------------------------------------------------------------
    metrics = await AnalyticsAggregationService.get_deterministic_class_metrics(
        session=db_session,
        class_id=math_class.id,
        organization_id=org.id
    )

    assert metrics["student_count"] == 1
    assert metrics["class_average_mastery"] >= 0.0
