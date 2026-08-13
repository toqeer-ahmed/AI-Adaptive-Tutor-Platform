import uuid
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.api.deps import get_db, get_current_user, require_roles
from backend.services.security_service import SecurityService
from backend.services.audit_service import AuditService
from backend.models.security import ParentStudentLink
from backend.models.user import User

router = APIRouter(prefix="/parents", tags=["Parents"])

class LinkChildRequest(BaseModel):
    student_id: str

@router.post("/children", response_model=dict, dependencies=[Depends(require_roles(["OrgAdmin", "SchoolAdmin", "Parent", "SuperAdmin"]))])
async def link_child(
    req: LinkChildRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    student_uuid = uuid.UUID(req.student_id)
    # Verify student exists in same organization
    student = await SecurityService.verify_student_record_access(session, current_user, student_uuid)

    link = ParentStudentLink(
        id=uuid.uuid4(),
        organization_id=current_user.organization_id,
        parent_id=current_user.id,
        student_id=student_uuid
    )
    session.add(link)
    await session.commit()

    await AuditService.log_event(
        session=session,
        action="PARENT_CHILD_LINK_CREATED",
        resource_type="parent_student_link",
        actor_id=current_user.id,
        organization_id=current_user.organization_id,
        resource_id=str(link.id),
        details={"parent_id": str(current_user.id), "student_id": str(student_uuid)}
    )

    return {
        "data": {
            "id": str(link.id),
            "parent_id": str(link.parent_id),
            "student_id": str(link.student_id),
            "created_at": link.created_at.isoformat()
        },
        "error": None,
        "meta": {}
    }

@router.get("/children/{student_id}", response_model=dict, dependencies=[Depends(require_roles(["Parent", "OrgAdmin", "SuperAdmin"]))])
async def get_child_details(
    student_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    student_uuid = uuid.UUID(student_id)
    # Enforces parent-child linkage check & IDOR protection
    student = await SecurityService.verify_student_record_access(session, current_user, student_uuid)

    return {
        "data": {
            "id": str(student.id),
            "organization_id": str(student.organization_id),
            "full_name": student.full_name,
            "email": student.email
        },
        "error": None,
        "meta": {}
    }
