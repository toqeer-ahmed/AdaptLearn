from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Schema representing the health status response."""

    status: str
    project: str
    version: str
    environment: str

