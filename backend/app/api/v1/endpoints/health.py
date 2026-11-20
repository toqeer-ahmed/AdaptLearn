from fastapi import APIRouter
from app.core.config import settings
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="API Health Check")
def get_health() -> HealthResponse:
    """Return application health status, version, and environment."""
    return HealthResponse(
        status="healthy",
        project=settings.PROJECT_NAME,
        version="0.1.0",
        environment=settings.ENVIRONMENT,
    )

