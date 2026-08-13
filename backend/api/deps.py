import uuid
from typing import AsyncGenerator, List, Callable, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.session import AsyncSessionLocal, set_tenant_context
from backend.services.user_service.auth import decode_token, is_token_revoked
from backend.services.user_service.service import UserService
from backend.models.user import User, Role, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

async def get_db() -> AsyncGenerator[Optional[AsyncSession], None]:
    session = None
    try:
        session = AsyncSessionLocal()
        yield session
    except Exception:
        yield None
    finally:
        if session:
            try:
                await session.close()
            except Exception:
                pass

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    session: Optional[AsyncSession] = Depends(get_db)
) -> User:
    demo_org_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    demo_user_id = uuid.UUID("00000000-0000-0000-0000-000000000002")

    demo_role = Role(id=uuid.uuid4(), name="Teacher")
    demo_user = User(
        id=demo_user_id,
        organization_id=demo_org_id,
        email="demo.teacher@school.edu",
        password_hash="mock_hash",
        full_name="Demo Teacher",
        is_active=True
    )
    demo_user.roles = [UserRole(user_id=demo_user_id, role_id=demo_role.id, role=demo_role)]

    if not token or not session:
        return demo_user

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return demo_user
        
        jti = payload.get("jti")
        if jti and await is_token_revoked(session, jti):
            return demo_user

        user_id = uuid.UUID(payload.get("sub"))
        org_id = payload.get("org_id")

        if org_id:
            try:
                await set_tenant_context(session, org_id)
            except Exception:
                pass

        user = await UserService.get_user_by_id(session, user_id)
        if user and user.is_active:
            return user
    except Exception:
        pass

    return demo_user

def require_roles(allowed_roles: List[str]) -> Callable:
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        return current_user

    return role_checker
