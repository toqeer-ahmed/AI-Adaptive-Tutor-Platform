import pytest
import uuid
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.organization_service.service import OrganizationService
from backend.services.user_service.service import UserService
from backend.services.class_service.service import ClassService
from backend.services.mastery_service.service import MasteryService
from backend.services.mastery_service.policy import MasteryEvent
from backend.api.routers.analytics import get_class_analytics, get_authorized_student_detail

@pytest.mark.asyncio
async def test_teacher_class_analytics_and_cross_class_security(db_session: AsyncSession):
    org = await OrganizationService.create_organization(db_session, "Teacher District", "TEACHDIST")
    teacher1 = await UserService.create_user(db_session, org.id, "teach1@school.edu", "Pass123!", "Teacher One", "Teacher")
    teacher2 = await UserService.create_user(db_session, org.id, "teach2@school.edu", "Pass123!", "Teacher Two", "Teacher")
    student = await UserService.create_user(db_session, org.id, "stud.tch@school.edu", "Pass123!", "Student Teach", "Student")

    # 1. Create Class 1 assigned to Teacher 1
    class1 = await ClassService.create_class(db_session, teacher1, "Period 1 Math", 6, "Mathematics")
    await ClassService.enroll_student(db_session, class1.id, student.id)

    # 2. Record learning event for student
    concept_id = uuid.uuid4()
    curr_ver_id = uuid.uuid4()
    event = MasteryEvent(
        student_id=student.id,
        concept_id=concept_id,
        curriculum_version_id=curr_ver_id,
        is_correct=True,
        item_difficulty=3
    )
    await MasteryService.record_learning_event(db_session, org.id, event)

    # 3. Teacher 1 accesses Class 1 analytics -> Allowed
    analytics_resp = await get_class_analytics(
        class_id=str(class1.id),
        current_user=teacher1,
        session=db_session
    )
    data = analytics_resp["data"]
    assert data["student_count"] == 1
    assert data["class_average_mastery"] >= 0.0

    # 4. Teacher 2 (unassigned) attempts to access Class 1 analytics -> Must raise HTTP 403 Forbidden
    with pytest.raises(HTTPException) as exc_info:
        await get_class_analytics(
            class_id=str(class1.id),
            current_user=teacher2,
            session=db_session
        )
    assert exc_info.value.status_code == 403
    assert "Cross-class access denied" in exc_info.value.detail

    # 5. Teacher 1 fetches authorized raw student detail -> Allowed
    stud_detail = await get_authorized_student_detail(
        student_id=str(student.id),
        current_user=teacher1,
        session=db_session
    )
    assert "raw_mastery_score" in stud_detail["data"]["masteries"][0]
