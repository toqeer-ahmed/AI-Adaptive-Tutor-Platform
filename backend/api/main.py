import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.config.logging import setup_logging
from backend.api.routers import auth, organizations, users, classes, parents, audit, health, curriculum, documents, ai_curriculum, rag, assessment, mastery

setup_logging()
logger = logging.getLogger("api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting AI Adaptive Education Platform API (Env: {settings.ENVIRONMENT})")
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

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

# Root health endpoint
@app.get("/health", tags=["Health"])
async def root_health():
    return {
        "status": "healthy",
        "service": "api",
        "version": "1.0.0"
    }
