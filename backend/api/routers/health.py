import logging
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as aioredis

from backend.api.deps import get_db
from backend.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("", response_model=dict)
async def check_health(session: AsyncSession = Depends(get_db)):
    db_healthy = False
    redis_healthy = False
    
    # 1. Test PostgreSQL connection
    try:
        result = await session.execute(text("SELECT 1"))
        if result.scalar() == 1:
            db_healthy = True
    except Exception as e:
        logger.error(f"PostgreSQL Health Check Failed: {e}")

    # 2. Test Redis connection
    try:
        r = aioredis.from_url(settings.REDIS_URL)
        ping_res = await r.ping()
        if ping_res:
            redis_healthy = True
        await r.aclose()
    except Exception as e:
        logger.error(f"Redis Health Check Failed: {e}")

    is_all_healthy = db_healthy and redis_healthy
    status_code = status.HTTP_200_OK

    return JSONResponse(
        status_code=status_code,
        content={
            "data": {
                "status": "healthy" if is_all_healthy else "degraded",
                "version": "1.0.0",
                "environment": settings.ENVIRONMENT,
                "services": {
                    "postgresql": "reachable" if db_healthy else "unreachable",
                    "redis": "reachable" if redis_healthy else "unreachable"
                }
            },
            "error": None if is_all_healthy else {"code": "HEALTH_CHECK_FAILED", "message": "One or more infrastructure dependencies are unreachable."},
            "meta": {}
        }
    )
