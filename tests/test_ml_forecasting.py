"""
test_ml_forecasting.py

Unit and integration tests for Phase 5: Traffic and Energy Forecasting (D-08 & D-09).
Tests chronological splitting, zero leakage, baseline comparisons,
prediction intervals, and PREDICTED provenance invariants.
"""

from datetime import datetime
from pathlib import Path
import sys
import numpy as np
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ml.features.traffic_features import (
    FEATURE_COLUMNS,
    generate_corridor_traffic_history,
    build_traffic_features,
    extract_traffic_features_row,
    chronological_split
)
from ml.features.energy_features import (
    ENERGY_FEATURE_COLUMNS,
    generate_building_energy_history,
    build_energy_features,
    extract_energy_features_row,
    chronological_energy_split
)
from ml.inference.forecaster import CorridorForecaster
from ml.conformal_calibrator import ConformalPredictionCalibrator
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
    assert result["conformalIntervals"]["available"] is False
    assert result["conformalIntervals"]["interval90"] is None


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
    assert result["conformalIntervals"]["available"] is False
    assert result["conformalIntervals"]["interval90"] is None


def test_calibration_quantile_is_not_scored_on_its_own_sample():
    """Finite-sample rank uses the calibration split. Reported coverage uses the later test split."""
    calibration = np.array([1.0, 1.0, 1.0, 1.0])
    later = np.array([10.0, 10.0, 10.0, 10.0])
    n = len(calibration)
    level = min(1.0, float(np.ceil((n + 1) * 0.90) / n))
    expected = float(np.quantile(np.abs(calibration), level))
    fitted = ConformalPredictionCalibrator.calibrate_from_residuals(calibration, alpha=0.10)
    assert fitted == expected

    same_sample = float(np.mean(np.abs(calibration) <= fitted))
    intervals = ConformalPredictionCalibrator.get_traffic_intervals(
        30.0,
        calibration_residuals=calibration,
        test_residuals=later,
    )
    reported = intervals["interval90"]["empiricalTestCoverage"]
    assert intervals["available"] is True
    assert intervals["calibrationSplit"] == "calibration"
    assert intervals["testSplit"] == "test"
    assert intervals["calibrationSamples"] == 4
    assert intervals["testSamples"] == 4
    assert intervals["interval90"]["margin"] == round(expected, 2)
    assert reported == 0.0
    assert reported != same_sample

    missing = ConformalPredictionCalibrator.get_traffic_intervals(30.0)
    assert missing["available"] is False
    assert missing["interval90"] is None


def test_forecast_state_isolation_invariant():
    """Verifies that forecast requests are isolated and do not mutate current state."""
    service = ForecastService()
    traffic_forecast = service.get_traffic_forecast("urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01")
    energy_forecast = service.get_energy_forecast("urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01")

    assert traffic_forecast["sourceMode"] == "PREDICTED"
    assert energy_forecast["sourceMode"] == "PREDICTED"
    models = service.list_models()
    assert len(models) >= 2


def test_traffic_feature_parity_with_training():
    """
    Verifies that extract_traffic_features_row produces feature values that
    match build_traffic_features exactly for any given time step t.
    """
    raw_df = generate_corridor_traffic_history(days=4, seed=123)
    featured_df = build_traffic_features(raw_df)

    test_dt = raw_df["timestamp"].iloc[50]
    matched = featured_df[featured_df["timestamp"] == test_dt]
    assert len(matched) == 1
    target_row = matched.iloc[0]

    # History ending at time t (raw_df row 50)
    hist = raw_df["speed_kmh"].iloc[:51].tolist()
    extracted = extract_traffic_features_row(
        hist=hist,
        dt=test_dt,
        ambient_temp_c=raw_df["ambient_temp_c"].iloc[50]
    )

    for col in FEATURE_COLUMNS:
        expected = float(target_row[col])
        actual = float(extracted[col])
        assert abs(actual - expected) < 1e-4, f"Mismatch in {col}: actual={actual}, expected={expected}"


def test_energy_feature_parity_with_training():
    """
    Verifies that extract_energy_features_row produces feature values that
    match build_energy_features exactly for any given time step t.
    """
    raw_df = generate_building_energy_history(days=14, seed=123)
    featured_df = build_energy_features(raw_df)

    test_dt = raw_df["timestamp"].iloc[150]
    matched = featured_df[featured_df["timestamp"] == test_dt]
    assert len(matched) == 1
    target_row = matched.iloc[0]

    # History ending at time t (raw_df row 150)
    hist = raw_df["active_power_kw"].iloc[:151].tolist()
    extracted = extract_energy_features_row(
        hist=hist,
        dt=test_dt,
        ambient_temp_c=raw_df["ambient_temp_c"].iloc[150]
    )

    for col in ENERGY_FEATURE_COLUMNS:
        expected = float(target_row[col])
        actual = float(extracted[col])
        assert abs(actual - expected) < 1e-4, f"Mismatch in {col}: actual={actual}, expected={expected}"


def test_traffic_inference_excludes_current_sample_from_lags_and_rolling():
    """
    Verifies that a history ending at the current observation excludes the current
    sample from the 5-minute lag and rolling window statistics.
    """
    # 12 prior steady samples at 50.0 km/h, followed by a sudden perturbation to 10.0 km/h at time t
    hist = [50.0] * 12 + [10.0]
    dt = datetime(2026, 9, 10, 10, 0)

    features = extract_traffic_features_row(hist=hist, dt=dt, ambient_temp_c=28.0)

    # 5m lag must be 50.0 km/h (prior observation), not 10.0 km/h (current)
    assert features["speed_lag_5m"] == 50.0
    # Rolling 30m window must only contain the prior 6 samples (all 50.0 km/h)
    assert features["speed_roll_mean_30m"] == 50.0
    assert features["speed_roll_std_30m"] == 0.0
    # Rolling 60m window must only contain the prior 12 samples (all 50.0 km/h)
    assert features["speed_roll_mean_60m"] == 50.0
    assert features["speed_roll_min_60m"] == 50.0


def test_energy_inference_hourly_lag_indices():
    """
    Verifies that building energy lags strictly match training hourly steps:
    1h lag is 4 steps prior (hist[-5]), 2h lag is 8 steps prior (hist[-9]),
    3h lag is 12 steps prior (hist[-13]), and 24h lag is 96 steps prior (hist[-97]).
    """
    # Create 100 sequential steps: [0.0, 1.0, 2.0, ..., 99.0]
    # Current sample S_t is 99.0 at hist[-1]
    hist = [float(i) for i in range(100)]
    dt = datetime(2026, 9, 10, 12, 0)

    features = extract_energy_features_row(hist=hist, dt=dt, ambient_temp_c=30.0)

    assert features["load_lag_1h"] == 95.0   # 99 - 4
    assert features["load_lag_2h"] == 91.0   # 99 - 8
    assert features["load_lag_3h"] == 87.0   # 99 - 12
    assert features["load_lag_24h"] == 3.0   # 99 - 96
    # 6h rolling window covers 24 prior steps: 75.0 to 98.0
    expected_mean = sum(range(75, 99)) / 24.0
    assert abs(features["load_roll_mean_6h"] - expected_mean) < 1e-4
    assert features["load_roll_max_6h"] == 98.0


def test_inference_rolling_std_uses_ddof_1():
    """
    Verifies that inference rolling standard deviation uses divisor N - 1 (ddof=1)
    to strictly match pandas rolling().std() in the training pipeline.
    """
    values = [10.0, 20.0, 10.0, 20.0, 10.0, 20.0]
    hist = values + [99.0]  # Current sample is 99.0
    dt = datetime(2026, 9, 10, 12, 0)

    features = extract_traffic_features_row(hist=hist, dt=dt, ambient_temp_c=25.0)

    expected_std_ddof_1 = float(np.std(values, ddof=1))
    assert abs(features["speed_roll_std_30m"] - expected_std_ddof_1) < 1e-4
    assert abs(features["speed_roll_std_30m"] - 5.4772) < 1e-3
    assert features["speed_roll_std_30m"] != 5.0


if __name__ == "__main__":
    test_traffic_chronological_split_no_leakage()
    test_energy_chronological_split_no_leakage()
    test_traffic_forecaster_inference_and_provenance()
    test_energy_forecaster_inference_and_provenance()
    test_forecast_state_isolation_invariant()
    print("ALL ML FORECASTING TESTS PASSED!")
