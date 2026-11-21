from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.errors import setup_exception_handlers
from app.db.session import init_db
from app.schemas.health import HealthResponse

# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description="AdaptLearn - Adaptive Education Platform API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Initialize database schema (NFR-07, NFR-08)
init_db()

# Configure Cross-Origin Resource Sharing (CORS)
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Register custom exception handlers
setup_exception_handlers(app)


# Root health check endpoint (GET /health)
@app.get("/health", response_model=HealthResponse, tags=["Health"], summary="Root Health Check")
def root_health() -> HealthResponse:
    """Convenience health check endpoint returning API operational status."""
    return HealthResponse(
        status="healthy",
        project=settings.PROJECT_NAME,
        version="0.1.0",
        environment=settings.ENVIRONMENT,
    )


# Root welcome endpoint (GET /)
@app.get("/", tags=["Root"], summary="API Root")
def root():
    """Root endpoint welcoming users to the AdaptLearn API."""
    return {
        "project": settings.PROJECT_NAME,
        "status": "operational",
        "docs_url": "/docs",
        "health_check": "/health",
        "api_v1_health": f"{settings.API_V1_PREFIX}/health",
        "version": "0.1.0",
    }


# Include V1 API Router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

