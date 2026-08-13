import uuid
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.audit import AuditLogEntry

class AuditService:
    @staticmethod
    async def log_event(
        session: AsyncSession,
        action: str,
        resource_type: str,
        actor_id: Optional[uuid.UUID] = None,
        organization_id: Optional[uuid.UUID] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> AuditLogEntry:
        entry = AuditLogEntry(
            id=uuid.uuid4(),
            organization_id=organization_id,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address
        )
        session.add(entry)
        await session.commit()
        return entry
