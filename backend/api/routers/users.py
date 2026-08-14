import uuid
from typing import Optional
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.deps import get_db, get_current_user, require_roles
from backend.services.user_service.service import UserService
from backend.services.security_service import SecurityService
from backend.services.audit_service import AuditService
from backend.models.user import User

router = APIRouter(prefix="/users", tags=["Users"])

class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str
    school_id: Optional[str] = None

@router.post("", response_model=dict, dependencies=[Depends(require_roles(["OrgAdmin", "SchoolAdmin", "SuperAdmin"]))])
async def create_user(
    req: CreateUserRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    school_uuid = uuid.UUID(req.school_id) if req.school_id else None
    
    try:
        user = await UserService.create_user(
            session=session,
            organization_id=current_user.organization_id,
            email=req.email,
            password=req.password,
            full_name=req.full_name,
            role_name=req.role,
            school_id=school_uuid
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    await AuditService.log_event(
        session=session,
        action="USER_CREATED",
        resource_type="user",
        actor_id=current_user.id,
        organization_id=current_user.organization_id,
        resource_id=str(user.id),
        details={"email": user.email, "role": req.role}
    )

    roles = [ur.role.name for ur in user.roles]
    return {
        "data": {
            "id": str(user.id),
            "organization_id": str(user.organization_id),
            "school_id": str(user.school_id) if user.school_id else None,
            "email": user.email,
            "full_name": user.full_name,
            "roles": roles,
            "created_at": user.created_at.isoformat()
        },
        "error": None,
        "meta": {}
    }

class UpdateProfileRequest(BaseModel):
    full_name: str

@router.get("", response_model=dict, dependencies=[Depends(require_roles(["OrgAdmin", "SchoolAdmin", "SuperAdmin"]))])
async def list_users(
    school_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    school_uuid = uuid.UUID(school_id) if school_id else current_user.school_id
    users = await UserService.list_organization_users(session, current_user.organization_id, school_uuid)
    return {
        "data": [
            {
                "id": str(u.id),
                "organization_id": str(u.organization_id),
                "school_id": str(u.school_id) if u.school_id else None,
                "email": u.email,
                "full_name": u.full_name,
                "is_active": u.is_active,
                "roles": [ur.role.name for ur in u.roles],
                "created_at": u.created_at.isoformat() if hasattr(u, 'created_at') and u.created_at else None
            } for u in users
        ],
        "error": None,
        "meta": {"count": len(users)}
    }

@router.patch("/me/profile", response_model=dict)
async def update_my_profile(
    req: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    current_user.full_name = req.full_name.strip()
    await session.commit()
    await session.refresh(current_user)

    roles = [ur.role.name for ur in current_user.roles]
    return {
        "data": {
            "id": str(current_user.id),
            "email": current_user.email,
            "full_name": current_user.full_name,
            "roles": roles
        },
        "error": None,
        "meta": {}
    }

@router.get("/{user_id}", response_model=dict)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    try:
        target_uuid = uuid.UUID(user_id)
        target_user = await SecurityService.verify_student_record_access(session, current_user, target_uuid)
    except (PermissionError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    roles = [ur.role.name for ur in target_user.roles]
    return {
        "data": {
            "id": str(target_user.id),
            "organization_id": str(target_user.organization_id),
            "email": target_user.email,
            "full_name": target_user.full_name,
            "roles": roles
        },
        "error": None,
        "meta": {}
    }



