from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.errors import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
)
from app.db.session import init_db, engine
import structlog

setup_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("starting_application", env=settings.APP_ENV)
    await init_db()
    yield
    # Shutdown
    logger.info("shutting_down_application")
    await engine.dispose()


app = FastAPI(
    title="Company Brain API",
    description="Evidence-backed knowledge extraction and safe skill execution",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", "")
    if not correlation_id:
        import uuid
        correlation_id = str(uuid.uuid4())

    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "company-brain-api"}


@app.get("/api/v1/health")
async def api_health():
    return {
        "status": "healthy",
        "service": "company-brain-api",
        "version": "0.1.0",
    }


# Exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(PydanticValidationError, validation_exception_handler)

# Global exception handler for unexpected errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    correlation_id = getattr(request.state, "correlation_id", "")
    logger.error("unhandled_exception", error=str(exc), path=request.url.path, correlation_id=correlation_id)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Internal server error"
            },
            "correlation_id": correlation_id
        },
    )


# Import and include routers
from app.api.v1 import sources, health, auth, audit
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(sources.router, prefix="/api/v1/sources", tags=["sources"])
app.include_router(audit.router, prefix="/api/v1/audit", tags=["audit"])
# app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["knowledge"])
# app.include_router(skills.router, prefix="/api/v1/skills", tags=["skills"])
# app.include_router(runs.router, prefix="/api/v1/runs", tags=["runs"])
# app.include_router(ask.router, prefix="/api/v1", tags=["ask"])