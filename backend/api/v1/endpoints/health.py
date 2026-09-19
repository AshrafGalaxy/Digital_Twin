"""
health.py

Health check and readiness endpoints for the digital twin platform.
"""

from fastapi import APIRouter
from pydantic import BaseModel

try:
    from core.config import settings
    from core.database import check_db_health
except ImportError:
    from backend.core.config import settings
    from backend.core.database import check_db_health

router = APIRouter(tags=["Health"])

class HealthResponse(BaseModel):
    status: str
    environment: str
    databaseConnected: bool
    version: str

@router.get("/health", response_model=HealthResponse)
async def get_health():
    db_ok = await check_db_health()
    return HealthResponse(
        status="HEALTHY" if db_ok else "DEGRADED",
        environment=settings.ENVIRONMENT,
        databaseConnected=db_ok,
        version="1.0.0"
    )
