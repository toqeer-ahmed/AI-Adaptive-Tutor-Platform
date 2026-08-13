import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.services.organization_service.service import OrganizationService
from backend.services.user_service.service import UserService
from backend.services.assessment_service.service import AssessmentService
from backend.services.evaluation_service.service import SubjectiveEvaluationService
from backend.models.assessment import QuestionBankItem, AssessmentAttempt, StudentAnswer
from backend.models.audit import AuditLogEntry

@pytest.mark.asyncio
async def test_subjective_evaluation_pipeline_and_teacher_override(db_session: AsyncSession):
    # 1. Setup district, teacher, and student
    org = await OrganizationService.create_organization(db_session, "Eval District", "EVALDIST")
    teacher = await UserService.create_user(db_session, org.id, "teach.eval@school.edu", "Pass123!", "Teacher Eval", "Teacher")
    student = await UserService.create_user(db_session, org.id, "stud.eval@school.edu", "Pass123!", "Student Eval", "Student")

    # 2. Create Short Answer Question Bank Item
    question = QuestionBankItem(
        id=uuid.uuid4(),
        organization_id=org.id,
        difficulty=3,
        question_type="short_answer",
        question_text="Explain why 2/3 and 4/6 are equivalent fractions.",
        correct_answer_json={"explanation": "They represent the same proportion of a whole."},
        rubric_json={"criteria": "Clear explanation of proportional equality."},
        generation_method="MANUAL",
        validation_status="APPROVED",
        created_by_id=teacher.id
    )
    db_session.add(question)
    await db_session.commit()

    # 3. Create Assessment & Attempt
    assessment = await AssessmentService.create_assessment(
        session=db_session,
        creator=teacher,
        title="Fractions Subjective Quiz",
        class_id=None,
        question_ids=[question.id]
    )
    attempt = await AssessmentService.start_attempt(db_session, assessment.id, student)

    # 4. Submit Short Answer
    answer = await AssessmentService.submit_answer(
        session=db_session,
        attempt_id=attempt.id,
        question_id=question.id,
        submitted_answer="Multiplying 2/3 by 2/2 gives 4/6, which is equivalent."
    )

    # 5. Trigger AI Subjective Evaluation
    evaluated_ans = await SubjectiveEvaluationService.evaluate_subjective_answer(
        session=db_session,
        answer_id=answer.id,
        actor=teacher,
        provider="mock"
    )

    assert evaluated_ans.ai_evaluation_json is not None
    assert evaluated_ans.ai_evaluation_json["confidence"] >= 0.85
    assert evaluated_ans.evaluation_status in ["AUTOGRADED", "NEEDS_TEACHER_REVIEW"]

    # 6. Test Teacher Accept Flow
    approved_ans = await SubjectiveEvaluationService.teacher_review_accept(
        session=db_session,
        answer_id=answer.id,
        teacher=teacher
    )
    assert approved_ans.evaluation_status == "TEACHER_APPROVED"
    assert approved_ans.points_awarded > 0.0

    # 7. Test Teacher Grade Override Flow
    overridden_ans = await SubjectiveEvaluationService.teacher_review_override(
        session=db_session,
        answer_id=answer.id,
        teacher=teacher,
        new_score=1.0,
        feedback="Perfect mathematical reasoning shown."
    )
    assert overridden_ans.evaluation_status == "TEACHER_OVERRIDDEN"
    assert overridden_ans.teacher_override is True
    assert overridden_ans.points_awarded == 1.0

    # 8. Verify Audit Event Logged
    audit_res = await db_session.execute(
        select(AuditLogEntry).where(
            AuditLogEntry.action == "SUBJECTIVE_GRADE_OVERRIDDEN",
            AuditLogEntry.resource_id == str(answer.id)
        )
    )
    audit_log = audit_res.scalars().first()
    assert audit_log is not None
    assert audit_log.details["new_score"] == 1.0
    assert audit_log.details["original_ai_proposal"] is not None
