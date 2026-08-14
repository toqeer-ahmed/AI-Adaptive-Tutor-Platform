import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.config.logging import setup_logging
from backend.api.middleware.observability import ObservabilityMiddleware
from backend.api.routers import (
    auth,
    organizations,
    users,
    classes,
    parents,
    audit,
    health,
    curriculum,
    documents,
    ai_curriculum,
    rag,
    assessment,
    mastery,
    adaptive,
    tutor,
    misconceptions,
    evaluations,
    analytics,
    notifications,
    ai_evaluation,
    observability
)

setup_logging()
logger = logging.getLogger("api")

from backend.db.session import engine, is_sqlite
from backend.models import Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting AI Adaptive Education Platform API (Env: {settings.ENVIRONMENT})")
    if is_sqlite:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Local SQLite database schema verified & ready.")
    yield
    logger.info("Shutting down API service.")

app = FastAPI(
    title="AI Adaptive Education Platform API",
    description="Production-grade multi-tenant adaptive education API for Grades 4-8",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Custom Observability Middleware (Request-ID, Correlation-ID & Latency Headers)
app.add_middleware(ObservabilityMiddleware)

# Explicit CORS setup for localhost frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler formatting consistent envelope
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "data": None,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": str(exc) if settings.DEBUG else "An unexpected error occurred."
            },
            "meta": {}
        }
    )

# Include Routers under /api/v1
app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(organizations.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(classes.router, prefix="/api/v1")
app.include_router(parents.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(curriculum.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(ai_curriculum.router, prefix="/api/v1")
app.include_router(rag.router, prefix="/api/v1")
app.include_router(assessment.router)
app.include_router(mastery.router, prefix="/api/v1")
app.include_router(adaptive.router, prefix="/api/v1")
app.include_router(tutor.router, prefix="/api/v1")
app.include_router(misconceptions.router, prefix="/api/v1")
app.include_router(evaluations.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(ai_evaluation.router, prefix="/api/v1")
app.include_router(observability.router, prefix="/api/v1")

# Root health endpoint
@app.get("/health", tags=["Health"])
async def root_health():
    return {
        "status": "healthy",
        "service": "api",
        "version": "1.0.0"
    }
