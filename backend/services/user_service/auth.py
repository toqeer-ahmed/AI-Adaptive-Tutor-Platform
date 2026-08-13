import uuid
import hashlib
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.config import settings
from backend.models.security import TokenRevocation, PasswordResetToken, EmailVerificationToken

pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()

def create_access_token(
    user_id: str,
    organization_id: str,
    roles: list[str],
    school_id: Optional[str] = None,
    expires_delta: Optional[timedelta] = None
) -> tuple[str, str]:
    jti = str(uuid.uuid4())
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload: Dict[str, Any] = {
        "jti": jti,
        "sub": str(user_id),
        "org_id": str(organization_id),
        "school_id": str(school_id) if school_id else None,
        "roles": roles,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti

def create_refresh_token(user_id: str, organization_id: str) -> tuple[str, str]:
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "jti": jti,
        "sub": str(user_id),
        "org_id": str(organization_id),
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti

def decode_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError as e:
        raise ValueError(f"Invalid token: {e}")

async def is_token_revoked(session: AsyncSession, jti: str) -> bool:
    if not jti:
        return False
    res = await session.execute(select(TokenRevocation).where(TokenRevocation.jti == jti))
    return res.scalars().first() is not None

async def revoke_token(session: AsyncSession, jti: str, user_id: uuid.UUID, exp_timestamp: int):
    expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
    rev = TokenRevocation(
        jti=jti,
        user_id=user_id,
        expires_at=expires_at
    )
    session.add(rev)
    await session.commit()
