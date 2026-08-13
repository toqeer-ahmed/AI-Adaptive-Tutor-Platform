import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.api.deps import get_db, get_current_user
from backend.services.notification_service.service import NotificationService
from backend.models.notification import Notification
from backend.models.user import User

router = APIRouter(prefix="/notifications", tags=["Notification Infrastructure"])

class DispatchNotificationRequest(BaseModel):
    user_id: str
    template_code: str
    template_params: Dict[str, Any] = {}
    channels: Optional[List[str]] = None

@router.get("", response_model=dict)
async def get_user_notifications(
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    stmt = select(Notification).where(
        Notification.user_id == current_user.id,
        Notification.organization_id == current_user.organization_id,
        Notification.channel == "IN_APP"
    )

    if unread_only:
        stmt = stmt.where(Notification.is_read == False)

    stmt = stmt.order_by(Notification.created_at.desc())

    res = await session.execute(stmt)
    notifications = res.scalars().all()

    return {
        "data": [
            {
                "id": str(n.id),
                "template_code": n.template_code,
                "title": n.title,
                "body": n.body,
                "status": n.status,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat()
            } for n in notifications
        ],
        "error": None,
        "meta": {"count": len(notifications)}
    }

@router.patch("/{notification_id}/read", response_model=dict)
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    notif_uuid = uuid.UUID(notification_id)
    stmt = select(Notification).where(
        Notification.id == notif_uuid,
        Notification.user_id == current_user.id
    )
    res = await session.execute(stmt)
    notif = res.scalars().first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found.")

    notif.is_read = True
    await session.commit()

    return {
        "data": {"id": str(notif.id), "is_read": True},
        "error": None,
        "meta": {}
    }

@router.post("/dispatch", response_model=dict)
async def dispatch_notification_event(
    req: DispatchNotificationRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    target_user_uuid = uuid.UUID(req.user_id)
    target_stmt = select(User).where(User.id == target_user_uuid)
    res = await session.execute(target_stmt)
    target_user = res.scalars().first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found.")

    dispatched = await NotificationService.dispatch_notification(
        session=session,
        user=target_user,
        template_code=req.template_code,
        template_params=req.template_params,
        channels=req.channels
    )

    return {
        "data": [
            {
                "id": str(n.id),
                "channel": n.channel,
                "title": n.title,
                "status": n.status,
                "retry_count": n.retry_count
            } for n in dispatched
        ],
        "error": None,
        "meta": {"dispatched_count": len(dispatched)}
    }
