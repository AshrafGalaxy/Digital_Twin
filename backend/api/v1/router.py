"""
router.py

Aggregates all API v1 routers into a single root router.
"""

from fastapi import APIRouter
from .endpoints import assets, forecasts, health, recommendations, scenarios, state, stream, study_area

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(health.router)
api_v1_router.include_router(study_area.router)
api_v1_router.include_router(assets.router)
api_v1_router.include_router(state.router)
api_v1_router.include_router(stream.router)
api_v1_router.include_router(scenarios.router)
api_v1_router.include_router(forecasts.router)
api_v1_router.include_router(recommendations.router)

