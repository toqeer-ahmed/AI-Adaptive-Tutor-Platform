from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.api.deps import get_db, get_current_user, require_roles
from backend.models.audit import AuditLogEntry
from backend.models.user import User

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])

@router.get("", response_model=dict, dependencies=[Depends(require_roles(["OrgAdmin", "SuperAdmin"]))])
async def list_audit_logs(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    # Enforce tenant scoping: OrgAdmin can only view logs for their own organization
    user_roles = [ur.role.name for ur in current_user.roles]
    
    stmt = select(AuditLogEntry)
    if "SuperAdmin" not in user_roles:
        stmt = stmt.where(AuditLogEntry.organization_id == current_user.organization_id)
    
    stmt = stmt.order_by(AuditLogEntry.created_at.desc()).limit(100)
    result = await session.execute(stmt)
    logs = result.scalars().all()

    return {
        "data": [
            {
                "id": str(l.id),
                "organization_id": str(l.organization_id) if l.organization_id else None,
                "actor_id": str(l.actor_id) if l.actor_id else None,
                "action": l.action,
                "resource_type": l.resource_type,
                "resource_id": l.resource_id,
                "details": l.details,
                "created_at": l.created_at.isoformat()
            } for l in logs
        ],
        "error": None,
        "meta": {"count": len(logs)}
    }
