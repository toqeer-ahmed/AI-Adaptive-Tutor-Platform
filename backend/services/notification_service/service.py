import uuid
from datetime import datetime, timezone
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.models.notification import Notification, NotificationPreference
from backend.models.user import User

# Provider Interface Abstraction
class NotificationProvider(ABC):
    @abstractmethod
    async def send(self, notification: Notification) -> bool:
        pass

class InAppProvider(NotificationProvider):
    async def send(self, notification: Notification) -> bool:
        # In-app notifications are persisted in DB and queried directly
        return True

class EmailProvider(NotificationProvider):
    async def send(self, notification: Notification) -> bool:
        # Simulates SMTP email delivery
        if "fail_email" in notification.title.lower():
            raise RuntimeError("SMTP Connection Timeout: Failed to reach mail server.")
        return True

class PushProvider(NotificationProvider):
    async def send(self, notification: Notification) -> bool:
        # Future Mobile Push Notification Provider Adapter
        return True

# Safe Template Registry (PII & sensitive metric sanitization)
TEMPLATES: Dict[str, Dict[str, str]] = {
    "ASSIGNMENT_SUBMISSION": {
        "title": "New Submission: {title}",
        "body": "A student submitted an attempt for '{title}'. Login to the teacher dashboard to review."
    },
    "CURRICULUM_REVIEW_PENDING": {
        "title": "Curriculum Review Required: {title}",
        "body": "Document '{title}' AI extractions are pending your teacher review and approval."
    },
    "ASSESSMENT_STATUS": {
        "title": "Assessment Status: {title}",
        "body": "Grading for assessment '{title}' has been completed."
    },
    "ASSIGNMENT_DUE": {
        "title": "Assignment Reminder: {title}",
        "body": "Your assignment '{title}' is due on {due_date}. Open your student portal to complete it."
    },
    "FEEDBACK_AVAILABLE": {
        "title": "Feedback Available: {title}",
        "body": "Teacher feedback for '{title}' is available to view in your student portal."
    },
    "RECOMMENDED_PRACTICE": {
        "title": "Practice Recommended: {concept_name}",
        "body": "A new practice activity is ready for topic '{concept_name}'."
    },
    "PERMITTED_PARENT_DIGEST": {
        "title": "Learning Update for {child_name}",
        "body": "Weekly qualitative progress update for {child_name} is available in the parent portal."
    }
}

class NotificationService:
    @staticmethod
    async def dispatch_notification(
        session: AsyncSession,
        user: User,
        template_code: str,
        template_params: Dict[str, Any],
        channels: Optional[List[str]] = None
    ) -> List[Notification]:
        """
        Asynchronously creates and dispatches notifications across authorized channels.
        Non-blocking: Does not fail main transaction!
        """
        if channels is None:
            channels = ["IN_APP", "EMAIL"]

        template = TEMPLATES.get(template_code, {
            "title": "Notification: {title}",
            "body": "You have a new learning update."
        })

        # Sanitize parameters & format title/body
        safe_params = {k: str(v) for k, v in template_params.items()}
        formatted_title = template["title"].format(**safe_params)
        formatted_body = template["body"].format(**safe_params)

        notifications = []
        for channel in channels:
            notif = Notification(
                id=uuid.uuid4(),
                organization_id=user.organization_id,
                user_id=user.id,
                channel=channel,
                template_code=template_code,
                title=formatted_title,
                body=formatted_body,
                status="PENDING",
                retry_count=0,
                max_retries=3,
                context_data=safe_params
            )
            session.add(notif)
            notifications.append(notif)

        await session.commit()

        # Execute immediate initial delivery attempt asynchronously
        for notif in notifications:
            await NotificationService.deliver_notification(session, notif)

        return notifications

    @staticmethod
    async def deliver_notification(session: AsyncSession, notification: Notification) -> bool:
        provider_map = {
            "IN_APP": InAppProvider(),
            "EMAIL": EmailProvider(),
            "PUSH": PushProvider()
        }

        provider = provider_map.get(notification.channel, InAppProvider())

        try:
            success = await provider.send(notification)
            if success:
                notification.status = "SENT"
                notification.sent_at = datetime.now(timezone.utc)
                await session.commit()
                return True
        except Exception as e:
            notification.retry_count += 1
            notification.error_log = str(e)

            if notification.retry_count >= notification.max_retries:
                # Transition to DEAD_LETTER queue upon max retries exhausted
                notification.status = "DEAD_LETTER"
            else:
                notification.status = "FAILED"

            await session.commit()
            return False

        return False
