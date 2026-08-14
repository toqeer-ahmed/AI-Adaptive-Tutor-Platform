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

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    session: Optional[AsyncSession] = Depends(get_db)
) -> User:
    if not token or not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type.")
        
        jti = payload.get("jti")
        if jti and await is_token_revoked(session, jti):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked.")

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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or not found.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Authentication error: {str(e)}")

def require_roles(allowed_roles: List[str]) -> Callable:
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_roles = [ur.role.name for ur in current_user.roles]
        if "SuperAdmin" in user_roles:
            return current_user
        if not any(role in allowed_roles for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Requires one of roles {allowed_roles}."
            )
        return current_user

    return role_checker
