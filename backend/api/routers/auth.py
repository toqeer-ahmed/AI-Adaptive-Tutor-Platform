import uuid
from typing import Optional
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.deps import get_db, get_current_user, require_roles
from backend.services.user_service.service import UserService
from backend.services.user_service.auth import (
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    revoke_token,
    hash_token
)
from backend.services.audit_service import AuditService
from backend.models.user import User

router = APIRouter(prefix="/auth", tags=["Auth"])

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    user_id: str
    raw_token: str
    new_password: str

class RegisterRequest(BaseModel):
    organization_code: str
    email: EmailStr
    password: str
    full_name: str

class InviteRequest(BaseModel):
    email: EmailStr
    full_name: str
    role: str
    school_id: Optional[str] = None

@router.post("/login", response_model=dict)
async def login(req: LoginRequest, session: AsyncSession = Depends(get_db)):
    user = await UserService.get_user_by_email(session, req.email)
    if not user or not verify_password(req.password, user.password_hash):
        await AuditService.log_event(
            session=session,
            action="AUTH_LOGIN_FAILED",
            resource_type="user",
            details={"email": req.email, "reason": "Invalid credentials"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled."
        )

    roles = [ur.role.name for ur in user.roles]
    access_token, access_jti = create_access_token(
        user_id=str(user.id),
        organization_id=str(user.organization_id),
        school_id=str(user.school_id) if user.school_id else None,
        roles=roles
    )
    refresh_token, refresh_jti = create_refresh_token(
        user_id=str(user.id),
        organization_id=str(user.organization_id)
    )

    await AuditService.log_event(
        session=session,
        action="AUTH_LOGIN_SUCCESS",
        resource_type="user",
        actor_id=user.id,
        organization_id=user.organization_id,
        resource_id=str(user.id)
    )

    return {
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "organization_id": str(user.organization_id),
                "school_id": str(user.school_id) if user.school_id else None,
                "roles": roles
            }
        },
        "error": None,
        "meta": {}
    }

@router.post("/logout", response_model=dict)
async def logout(
    current_user: User = Depends(get_current_user),
    authorization: str = Header(...),
    session: AsyncSession = Depends(get_db)
):
    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)
    jti = payload.get("jti")
    exp = payload.get("exp")
    
    if jti and exp:
        await revoke_token(session, jti, current_user.id, exp)

    await AuditService.log_event(
        session=session,
        action="AUTH_LOGOUT",
        resource_type="user",
        actor_id=current_user.id,
        organization_id=current_user.organization_id,
        resource_id=str(current_user.id)
    )

    return {
        "data": {"message": "Successfully logged out."},
        "error": None,
        "meta": {}
    }

@router.get("/me", response_model=dict)
async def get_me(current_user: User = Depends(get_current_user)):
    roles = [ur.role.name for ur in current_user.roles]
    return {
        "data": {
            "id": str(current_user.id),
            "email": current_user.email,
            "full_name": current_user.full_name,
            "organization_id": str(current_user.organization_id),
            "roles": roles
        },
        "error": None,
        "meta": {}
    }

@router.post("/refresh", response_model=dict)
async def refresh(req: RefreshRequest, session: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(req.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type.")
        
        old_jti = payload.get("jti")
        old_exp = payload.get("exp")
        user_id = uuid.UUID(payload.get("sub"))
        
        # Revoke old refresh token (Token rotation)
        if old_jti and old_exp:
            await revoke_token(session, old_jti, user_id, old_exp)

        user = await UserService.get_user_by_id(session, user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive.")

        roles = [ur.role.name for ur in user.roles]
        new_access_token, _ = create_access_token(
            user_id=str(user.id),
            organization_id=str(user.organization_id),
            school_id=str(user.school_id) if user.school_id else None,
            roles=roles
        )
        new_refresh_token, _ = create_refresh_token(
            user_id=str(user.id),
            organization_id=str(user.organization_id)
        )

        return {
            "data": {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer"
            },
            "error": None,
            "meta": {}
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token refresh failed: {str(e)}")

@router.post("/password-reset/request", response_model=dict)
async def request_password_reset(req: PasswordResetRequest, session: AsyncSession = Depends(get_db)):
    user = await UserService.get_user_by_email(session, req.email)
    raw_token = str(uuid.uuid4())
    token_h = hash_token(raw_token)
    
    if user:
        await AuditService.log_event(
            session=session,
            action="AUTH_PASSWORD_RESET_REQUESTED",
            resource_type="user",
            actor_id=user.id,
            organization_id=user.organization_id,
            resource_id=str(user.id)
        )

    # Return reset architecture contract
    return {
        "data": {
            "message": "If the account exists, password reset instructions have been generated.",
            "reset_token_demo": raw_token if user else None
        },
        "error": None,
        "meta": {}
    }

@router.post("/password-reset/confirm", response_model=dict)
async def confirm_password_reset(req: PasswordResetConfirm, session: AsyncSession = Depends(get_db)):
    user_uuid = uuid.UUID(req.user_id)
    user = await UserService.get_user_by_id(session, user_uuid)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid user or reset token.")

    user.password_hash = hash_password(req.new_password)
    await session.commit()

    await AuditService.log_event(
        session=session,
        action="AUTH_PASSWORD_RESET_CONFIRMED",
        resource_type="user",
        actor_id=user.id,
        organization_id=user.organization_id,
        resource_id=str(user.id)
    )

    return {
        "data": {"message": "Password successfully reset. Please log in with your new password."},
        "error": None,
        "meta": {}
    }

@router.post("/invite", response_model=dict, dependencies=[Depends(require_roles(["OrgAdmin", "SchoolAdmin", "SuperAdmin"]))])
async def invite_user(
    req: InviteRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    school_uuid = uuid.UUID(req.school_id) if req.school_id else None
    temp_password = f"TempPass#{uuid.uuid4().hex[:8]}"

    user = await UserService.create_user(
        session=session,
        organization_id=current_user.organization_id,
        email=req.email,
        password=temp_password,
        full_name=req.full_name,
        role_name=req.role,
        school_id=school_uuid
    )

    await AuditService.log_event(
        session=session,
        action="USER_INVITED",
        resource_type="user",
        actor_id=current_user.id,
        organization_id=current_user.organization_id,
        resource_id=str(user.id),
        details={"role": req.role, "invited_email": req.email}
    )

    return {
        "data": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": req.role,
            "temporary_password": temp_password
        },
        "error": None,
        "meta": {}
    }
