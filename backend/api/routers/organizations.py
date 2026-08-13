import uuid
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.deps import get_db, get_current_user, require_roles
from backend.services.organization_service.service import OrganizationService, SchoolService
from backend.models.user import User

router = APIRouter(prefix="/organizations", tags=["Organizations"])

class CreateOrgRequest(BaseModel):
    name: str
    code: str
    settings: Optional[dict] = None

class CreateSchoolRequest(BaseModel):
    name: str
    code: str

@router.post("", response_model=dict, dependencies=[Depends(require_roles(["SuperAdmin"]))])
async def create_organization(req: CreateOrgRequest, session: AsyncSession = Depends(get_db)):
    existing = await OrganizationService.get_organization_by_code(session, req.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Organization with code '{req.code}' already exists."
        )
    
    org = await OrganizationService.create_organization(
        session=session,
        name=req.name,
        code=req.code,
        settings_dict=req.settings
    )
    
    return {
        "data": {
            "id": str(org.id),
            "name": org.name,
            "code": org.code,
            "settings": org.settings,
            "created_at": org.created_at.isoformat()
        },
        "error": None,
        "meta": {}
    }

@router.post("/{org_id}/schools", response_model=dict, dependencies=[Depends(require_roles(["OrgAdmin", "SuperAdmin"]))])
async def create_school(
    org_id: str,
    req: CreateSchoolRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    target_org_id = uuid.UUID(org_id)
    # Validate tenant boundary unless SuperAdmin
    user_roles = [ur.role.name for ur in current_user.roles]
    if "SuperAdmin" not in user_roles and current_user.organization_id != target_org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Cannot create school in foreign organization."
        )

    school = await SchoolService.create_school(
        session=session,
        organization_id=target_org_id,
        name=req.name,
        code=req.code
    )

    return {
        "data": {
            "id": str(school.id),
            "organization_id": str(school.organization_id),
            "name": school.name,
            "code": school.code,
            "created_at": school.created_at.isoformat()
        },
        "error": None,
        "meta": {}
    }

@router.get("/{org_id}/schools", response_model=dict, dependencies=[Depends(require_roles(["OrgAdmin", "SchoolAdmin", "Teacher", "SuperAdmin"]))])
async def list_schools(
    org_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    target_org_id = uuid.UUID(org_id)
    user_roles = [ur.role.name for ur in current_user.roles]
    if "SuperAdmin" not in user_roles and current_user.organization_id != target_org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Cannot access foreign organization schools."
        )

    schools = await SchoolService.list_schools(session, target_org_id)
    return {
        "data": [
            {
                "id": str(s.id),
                "organization_id": str(s.organization_id),
                "name": s.name,
                "code": s.code,
                "created_at": s.created_at.isoformat()
            } for s in schools
        ],
        "error": None,
        "meta": {"count": len(schools)}
    }
