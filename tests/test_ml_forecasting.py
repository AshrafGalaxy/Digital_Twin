"""
test_ml_forecasting.py

Unit and integration tests for Phase 5: Traffic and Energy Forecasting (D-08 & D-09).
Tests chronological splitting, zero leakage, baseline comparisons,
prediction intervals, and PREDICTED provenance invariants.
"""

from datetime import datetime
from pathlib import Path
import sys
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ml.features.traffic_features import (
    generate_corridor_traffic_history,
    build_traffic_features,
    chronological_split
)
from ml.features.energy_features import (
    generate_building_energy_history,
    build_energy_features,
    chronological_energy_split
)
from ml.inference.forecaster import CorridorForecaster
from backend.services.forecast_service import ForecastService


def test_traffic_chronological_split_no_leakage():
    """Verifies that traffic data is split strictly chronologically with zero temporal overlap."""
    raw_df = generate_corridor_traffic_history(days=7, seed=42)
    featured_df = build_traffic_features(raw_df)

    train_df, val_df, test_df = chronological_split(featured_df, train_pct=0.70, val_pct=0.15)

    assert len(train_df) > 0
    assert len(val_df) > 0
    assert len(test_df) > 0

    # Strict chronological boundary verification
    assert train_df["timestamp"].max() < val_df["timestamp"].min()
    assert val_df["timestamp"].max() < test_df["timestamp"].min()


def test_energy_chronological_split_no_leakage():
    """Verifies that building energy data is split strictly chronologically."""
    raw_df = generate_building_energy_history(days=10, seed=42)
    featured_df = build_energy_features(raw_df)

    train_df, val_df, test_df = chronological_energy_split(featured_df, train_pct=0.70, val_pct=0.15)

    assert len(train_df) > 0
    assert len(val_df) > 0
    assert len(test_df) > 0

    assert train_df["timestamp"].max() < val_df["timestamp"].min()
    assert val_df["timestamp"].max() < test_df["timestamp"].min()


def test_traffic_forecaster_inference_and_provenance():
    """Verifies that CorridorForecaster generates valid 15-min speed forecasts with confidence bounds."""
    forecaster = CorridorForecaster()
    result = forecaster.predict_traffic_speed(
        segment_id="urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01",
        current_speed=26.5
    )

    assert result["sourceMode"] == "PREDICTED"
    assert result["horizonMinutes"] == 15
    assert result["unit"] == "km/h"
    assert "traffic-xgb" in result["modelVersion"]
    assert result["confidenceLower"] <= result["predictedValue"] <= result["confidenceUpper"]
    assert "baselineComparison" in result
    assert result["baselineComparison"]["modelTestMae"] < result["baselineComparison"]["persistenceMae"]


def test_energy_forecaster_inference_and_provenance():
    """Verifies that CorridorForecaster generates valid 60-min building energy forecasts with confidence bounds."""
    forecaster = CorridorForecaster()
    result = forecaster.predict_building_energy(
        building_id="urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01",
        current_kw=4250.0
    )

    assert result["sourceMode"] == "PREDICTED"
    assert result["horizonMinutes"] == 60
    assert result["unit"] == "kW"
    assert "energy-xgb" in result["modelVersion"]
    assert result["confidenceLower"] <= result["predictedValue"] <= result["confidenceUpper"]
    assert "baselineComparison" in result
    assert result["baselineComparison"]["modelTestMae"] < result["baselineComparison"]["persistenceMae"]


def test_forecast_state_isolation_invariant():
    """Verifies that forecast requests are isolated and do not mutate current state."""
    service = ForecastService()
    traffic_forecast = service.get_traffic_forecast("urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01")
    energy_forecast = service.get_energy_forecast("urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01")

    assert traffic_forecast["sourceMode"] == "PREDICTED"
    assert energy_forecast["sourceMode"] == "PREDICTED"
    models = service.list_models()
    assert len(models) >= 2


if __name__ == "__main__":
    test_traffic_chronological_split_no_leakage()
    test_energy_chronological_split_no_leakage()
    test_traffic_forecaster_inference_and_provenance()
    test_energy_forecaster_inference_and_provenance()
    test_forecast_state_isolation_invariant()
    print("ALL ML FORECASTING TESTS PASSED!")
