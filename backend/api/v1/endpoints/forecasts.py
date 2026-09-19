"""
forecasts.py

API endpoints for querying real-time traffic and energy forecasts,
prediction intervals, model versions, and baseline accuracy comparisons.
All outputs are strictly tagged as PREDICTED provenance.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

try:
    from services.forecast_service import ForecastService
    from schemas.forecasts import (
        TrafficForecastResponse,
        EnergyForecastResponse,
        ModelVersionInfo
    )
except ImportError:
    from backend.services.forecast_service import ForecastService
    from backend.schemas.forecasts import (
        TrafficForecastResponse,
        EnergyForecastResponse,
        ModelVersionInfo
    )

router = APIRouter(prefix="/forecasts", tags=["Forecasts & Predictive ML"])
forecast_service = ForecastService()


@router.get("/traffic/{segment_id}", response_model=TrafficForecastResponse)
def get_traffic_forecast(
    segment_id: str,
    current_speed: Optional[float] = Query(None, description="Optional current observed speed in km/h")
):
    """
    Returns a 15-minute ahead vehicle speed forecast for a corridor road segment.
    Includes 80% prediction interval (p10 to p90), baseline comparison, and model version.
    """
    try:
        forecast = forecast_service.get_traffic_forecast(segment_id, current_speed=current_speed)
        return forecast
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Traffic forecast generation failed: {str(e)}")


@router.get("/energy/{building_id}", response_model=EnergyForecastResponse)
def get_energy_forecast(
    building_id: str,
    current_kw: Optional[float] = Query(None, description="Optional current observed load in kW")
):
    """
    Returns a 60-minute ahead active power demand forecast for a commercial building.
    Includes 80% prediction interval, peak load advisory threshold flag, and baseline comparison.
    """
    try:
        forecast = forecast_service.get_energy_forecast(building_id, current_kw=current_kw)
        return forecast
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Energy forecast generation failed: {str(e)}")


@router.get("/models", response_model=List[ModelVersionInfo])
def list_forecast_models():
    """Lists all active forecasting models and test evaluation metrics."""
    return forecast_service.list_models()
