import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.organization_service.service import OrganizationService
from backend.services.user_service.service import UserService
from backend.services.notification_service.service import NotificationService
from backend.models.notification import Notification

@pytest.mark.asyncio
async def test_notification_dispatch_safe_template_and_dlq(db_session: AsyncSession):
    # 1. Setup organization and user
    org = await OrganizationService.create_organization(db_session, "Notif District", "NOTIFDIST")
    user = await UserService.create_user(db_session, org.id, "user.notif@school.edu", "Pass123!", "User Notif", "Teacher")

    # 2. Test Safe Template Formatting & In-App Dispatch
    dispatched = await NotificationService.dispatch_notification(
        session=db_session,
        user=user,
        template_code="ASSIGNMENT_SUBMISSION",
        template_params={"title": "Fractions Diagnostic Quiz"},
        channels=["IN_APP"]
    )

    assert len(dispatched) == 1
    notif = dispatched[0]
    assert notif.status == "SENT"
    assert "Fractions Diagnostic Quiz" in notif.title
    assert "New Submission:" in notif.title

    # 3. Test Failure Retry & Dead-Letter Queue (DLQ) Transition
    fail_notif = Notification(
        id=uuid.uuid4(),
        organization_id=org.id,
        user_id=user.id,
        channel="EMAIL",
        template_code="ASSIGNMENT_DUE",
        title="FAIL_EMAIL Assignment Reminder",
        body="Body text",
        status="PENDING",
        retry_count=0,
        max_retries=3
    )
    db_session.add(fail_notif)
    await db_session.commit()

    # Attempt 1 -> Retry 1 (FAILED)
    await NotificationService.deliver_notification(db_session, fail_notif)
    assert fail_notif.retry_count == 1
    assert fail_notif.status == "FAILED"

    # Attempt 2 -> Retry 2 (FAILED)
    await NotificationService.deliver_notification(db_session, fail_notif)
    assert fail_notif.retry_count == 2
    assert fail_notif.status == "FAILED"

    # Attempt 3 -> Retry 3 (DEAD_LETTER)
    await NotificationService.deliver_notification(db_session, fail_notif)
    assert fail_notif.retry_count == 3
    assert fail_notif.status == "DEAD_LETTER"
