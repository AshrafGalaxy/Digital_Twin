"""
test_ml_forecasting.py

Unit and integration tests for Phase 5: Traffic and Energy Forecasting (D-08 & D-09).
Tests chronological splitting, zero leakage, baseline comparisons,
prediction intervals, and PREDICTED provenance invariants.
"""

from datetime import datetime, timedelta, timezone
import math
from pathlib import Path
import sys
import joblib
import numpy as np
import pandas as pd
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ml.features.traffic_features import (
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    generate_corridor_traffic_history,
    build_traffic_features,
    extract_traffic_features_row,
    chronological_split
)
from ml.features.energy_features import (
    ENERGY_FEATURE_COLUMNS,
    ENERGY_TARGET_COLUMN,
    generate_building_energy_history,
    build_energy_features,
    extract_energy_features_row,
    chronological_energy_split
)
from ml.inference.forecaster import CorridorForecaster
from ml.conformal_calibrator import ConformalPredictionCalibrator
from backend.services.forecast_service import ForecastService


def test_traffic_chronological_split_no_leakage():
    """Verifies that traffic data is split strictly chronologically on an 80/10/10 split with embargo purge gap."""
    raw_df = generate_corridor_traffic_history(days=7, seed=42)
    featured_df = build_traffic_features(raw_df)

    train_df, val_df, test_df = chronological_split(featured_df)

    n = len(featured_df)
    assert len(train_df) == int(n * 0.80) - 3
    assert len(val_df) == int(n * 0.90) - int(n * 0.80) - 3
    assert len(test_df) == n - int(n * 0.90)

    # Strict chronological index and timestamp monotonicity
    assert train_df.index.max() < val_df.index.min()
    assert val_df.index.max() < test_df.index.min()
    assert train_df["timestamp"].max() < val_df["timestamp"].min()
    assert val_df["timestamp"].max() < test_df["timestamp"].min()

    # Embargo verification: last training label (shifted by 15m) strictly prior to first validation feature
    assert train_df["timestamp"].max() + pd.Timedelta(minutes=15) < val_df["timestamp"].min()
    assert val_df["timestamp"].max() + pd.Timedelta(minutes=15) < test_df["timestamp"].min()


def test_energy_chronological_split_no_leakage():
    """Verifies that building energy data is split strictly chronologically on an 80/10/10 split with embargo purge gap."""
    raw_df = generate_building_energy_history(days=10, seed=42)
    featured_df = build_energy_features(raw_df)

    train_df, val_df, test_df = chronological_energy_split(featured_df)

    n = len(featured_df)
    assert len(train_df) == int(n * 0.80) - 4
    assert len(val_df) == int(n * 0.90) - int(n * 0.80) - 4
    assert len(test_df) == n - int(n * 0.90)

    assert train_df.index.max() < val_df.index.min()
    assert val_df.index.max() < test_df.index.min()
    assert train_df["timestamp"].max() < val_df["timestamp"].min()
    assert val_df["timestamp"].max() < test_df["timestamp"].min()

    # Embargo verification: last training label (shifted by 60m) strictly prior to first validation feature
    assert train_df["timestamp"].max() + pd.Timedelta(minutes=60) < val_df["timestamp"].min()
    assert val_df["timestamp"].max() + pd.Timedelta(minutes=60) < test_df["timestamp"].min()


def test_saved_artifacts_reflect_consistent_booster_counts():
    """Verifies BUG-52: fitted booster count matches logged n_estimators (150 traffic, 160 energy)."""
    forecaster = CorridorForecaster()
    if forecaster.traffic_artifact is not None:
        assert forecaster.traffic_artifact["model"].n_estimators == 150
        assert len(forecaster.traffic_artifact["model"].get_booster().get_dump()) == 150
    if forecaster.energy_artifact is not None:
        assert forecaster.energy_artifact["model"].n_estimators == 160
        assert len(forecaster.energy_artifact["model"].get_booster().get_dump()) == 160

    energy_src = (BASE_DIR / "ml" / "training" / "train_energy_model.py").read_text(encoding="utf-8")
    assert '"n_estimators": 160' in energy_src
    assert '"n_estimators": 140' not in energy_src


def test_traffic_features_entity_isolation():
    """
    Verifies that build_traffic_features groups by segment_id so that multiple entities
    sharing identical timestamps do not interleave or exchange lag values.
    """
    timestamps = pd.date_range("2026-09-20 08:00", periods=20, freq="5min")
    records_a = [
        {"timestamp": ts, "segment_id": "SEG-01", "speed_kmh": 20.0 + i, "ambient_temp_c": 28.0}
        for i, ts in enumerate(timestamps)
    ]
    records_b = [
        {"timestamp": ts, "segment_id": "SEG-02", "speed_kmh": 50.0 + i, "ambient_temp_c": 28.0}
        for i, ts in enumerate(timestamps)
    ]
    interleaved_df = pd.DataFrame(records_a + records_b).sort_values("timestamp").reset_index(drop=True)

    featured = build_traffic_features(interleaved_df)
    assert len(featured) > 0

    # Filter for SEG-02 rows: speed_lag_5m must reflect SEG-02 speeds (>= 50), never SEG-01 speeds
    seg_b_featured = featured[featured["segment_id"] == "SEG-02"]
    assert len(seg_b_featured) > 0
    assert (seg_b_featured["speed_lag_5m"] >= 50.0).all()

    # Filter for SEG-01 rows: speed_lag_5m must reflect SEG-01 speeds (<= 40), never SEG-02 speeds
    seg_a_featured = featured[featured["segment_id"] == "SEG-01"]
    assert len(seg_a_featured) > 0
    assert (seg_a_featured["speed_lag_5m"] <= 40.0).all()


def test_traffic_features_time_gap_handling():
    """
    Verifies that time gaps (e.g. 2 hours) drop invalid bridged lags rather than
    assigning hours-old values to speed_lag_5m.
    """
    # 20 observations before gap, 2-hour gap, then 20 observations after gap
    ts_pre = pd.date_range("2026-09-20 08:00", periods=20, freq="5min")
    ts_post = pd.date_range("2026-09-20 12:00", periods=20, freq="5min")

    records_pre = [{"timestamp": ts, "segment_id": "SEG-01", "speed_kmh": 25.0, "ambient_temp_c": 28.0} for ts in ts_pre]
    records_post = [{"timestamp": ts, "segment_id": "SEG-01", "speed_kmh": 45.0, "ambient_temp_c": 28.0} for ts in ts_post]
    gap_df = pd.DataFrame(records_pre + records_post)

    featured = build_traffic_features(gap_df)
    # The first row at 12:00 must NOT have speed_lag_5m == 25.0 (which was from 09:35, 2h25m prior)
    post_rows = featured[featured["timestamp"] >= pd.Timestamp("2026-09-20 12:00")]
    assert len(post_rows) > 0
    # All valid post-gap rows must only have lags formed from post-gap speeds (45.0)
    assert (post_rows["speed_lag_5m"] == 45.0).all()


def test_traffic_forecaster_inference_and_provenance():
    """Verifies that CorridorForecaster serves 15-min speed forecasts with saved 80%/90% conformal bounds."""
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

    conformal = result["conformalIntervals"]
    assert conformal["available"] is True
    assert conformal["calibrationSplit"] == "validation"
    assert conformal["testSplit"] == "test"
    assert conformal["calibrationSamples"] > 0
    assert conformal["testSamples"] > 0
    for key, target in (("interval80", 0.80), ("interval90", 0.90)):
        band = conformal[key]
        assert band is not None
        assert band["coverageTarget"] == target
        assert band["lower"] <= result["predictedValue"] <= band["upper"]
        assert band["margin"] > 0.0
        assert band["coverageSplit"] == "test"
        assert 0.0 <= band["empiricalTestCoverage"] <= 1.0
    assert conformal["interval90"]["margin"] >= conformal["interval80"]["margin"]


def test_energy_forecaster_inference_and_provenance():
    """Verifies that CorridorForecaster serves 60-min energy forecasts with saved 80%/90% conformal bounds."""
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

    conformal = result["conformalIntervals"]
    assert conformal["available"] is True
    assert conformal["calibrationSplit"] == "validation"
    assert conformal["testSplit"] == "test"
    assert conformal["calibrationSamples"] > 0
    assert conformal["testSamples"] > 0
    for key, target in (("interval80", 0.80), ("interval90", 0.90)):
        band = conformal[key]
        assert band is not None
        assert band["coverageTarget"] == target
        assert band["lower"] <= result["predictedValue"] <= band["upper"]
        assert band["margin"] > 0.0
        assert band["coverageSplit"] == "test"
        assert 0.0 <= band["empiricalTestCoverage"] <= 1.0
    assert conformal["interval90"]["margin"] >= conformal["interval80"]["margin"]


def test_calibration_quantile_is_not_scored_on_its_own_sample():
    """Finite-sample rank uses discrete order statistics on calibration split; coverage uses later test split."""
    calibration = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
    later = np.array([12.0, 12.0, 12.0, 12.0, 12.0])
    n = len(calibration)
    rank_80 = math.ceil((n + 1) * 0.80)
    rank_90 = math.ceil((n + 1) * 0.90)
    expected_80 = float(np.sort(np.abs(calibration))[rank_80 - 1])
    expected_90 = float(np.sort(np.abs(calibration))[rank_90 - 1])

    fitted_80 = ConformalPredictionCalibrator.calibrate_from_residuals(calibration, alpha=0.20)
    fitted_90 = ConformalPredictionCalibrator.calibrate_from_residuals(calibration, alpha=0.10)
    assert fitted_80 == expected_80 == 9.0
    assert fitted_90 == expected_90 == 10.0

    same_sample = float(np.mean(np.abs(calibration) <= fitted_90))
    intervals = ConformalPredictionCalibrator.get_traffic_intervals(
        30.0,
        calibration_residuals=calibration,
        test_residuals=later,
    )
    reported = intervals["interval90"]["empiricalTestCoverage"]
    assert intervals["available"] is True
    assert intervals["calibrationSplit"] == "calibration"
    assert intervals["testSplit"] == "test"
    assert intervals["calibrationSamples"] == 10
    assert intervals["testSamples"] == 5
    assert intervals["interval80"]["margin"] == round(expected_80, 2)
    assert intervals["interval90"]["margin"] == round(expected_90, 2)
    assert reported == 0.0
    assert reported != same_sample

    missing = ConformalPredictionCalibrator.get_traffic_intervals(30.0)
    assert missing["available"] is False
    assert missing["interval80"] is None
    assert missing["interval90"] is None


def test_conformal_discrete_order_statistic_and_small_sample_unavailability():
    """Verifies discrete order statistics (no interpolation) and ceil((n+1)*(1-alpha)) > n rejection."""
    # n = 8: ceil((8 + 1) * 0.90) = ceil(8.1) = 9 > 8 -> 90% level invalid -> unavailable
    small_cal = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
    assert ConformalPredictionCalibrator.calibrate_from_residuals(small_cal, alpha=0.20) == 8.0
    with pytest.raises(ValueError, match="Insufficient calibration samples"):
        ConformalPredictionCalibrator.calibrate_from_residuals(small_cal, alpha=0.10)

    unavailable = ConformalPredictionCalibrator.get_traffic_intervals(
        28.0,
        calibration_residuals=small_cal,
        test_residuals=np.array([1.0, 2.0]),
    )
    assert unavailable["available"] is False
    assert unavailable["interval80"] is None
    assert unavailable["interval90"] is None
    assert "ceil((n+1)*(1-alpha))" in unavailable["reason"]


def test_forecaster_returns_unavailable_when_artifact_lacks_calibration():
    """Artifacts without stored conformal calibration must return available=False with null bands."""
    forecaster = CorridorForecaster()
    assert forecaster.traffic_artifact is not None
    assert forecaster.energy_artifact is not None

    forecaster.traffic_artifact = {k: v for k, v in forecaster.traffic_artifact.items() if k != "conformal_calibration"}
    forecaster.energy_artifact = {k: v for k, v in forecaster.energy_artifact.items() if k != "conformal_calibration"}

    t_res = forecaster.predict_traffic_speed("urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01", 25.0)
    e_res = forecaster.predict_building_energy("urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01", 4000.0)

    assert t_res["conformalIntervals"]["available"] is False
    assert t_res["conformalIntervals"]["interval80"] is None
    assert t_res["conformalIntervals"]["interval90"] is None
    assert e_res["conformalIntervals"]["available"] is False
    assert e_res["conformalIntervals"]["interval80"] is None
    assert e_res["conformalIntervals"]["interval90"] is None


def test_saved_model_artifacts_persist_calibration_quantiles_and_test_coverage():
    """Saved joblib artifacts persist validation 80%/90% quantiles and chronological test coverage."""
    models_dir = BASE_DIR / "artifacts" / "models"
    for filename in ("traffic_xgb_v1.joblib", "energy_xgb_v1.joblib"):
        artifact = joblib.load(models_dir / filename)
        cal = artifact.get("conformal_calibration")
        assert isinstance(cal, dict)
        assert cal["available"] is True
        assert cal["calibrationSplit"] == "validation"
        assert cal["testSplit"] == "test"
        assert cal["calibrationSamples"] > 0
        assert cal["testSamples"] > 0
        assert cal["quantiles"]["80"]["alpha"] == 0.20
        assert cal["quantiles"]["90"]["alpha"] == 0.10
        assert cal["quantiles"]["90"]["quantile"] >= cal["quantiles"]["80"]["quantile"] > 0.0
        for level in ("80", "90"):
            cov = cal["empiricalCoverage"][level]
            assert cov["coverageSplit"] == "test"
            assert cov["testSamples"] == cal["testSamples"]
            assert 0.0 <= cov["empiricalTestCoverage"] <= 1.0


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


def test_traffic_baseline_fallback_uses_train_mean_not_test_labels():
    """
    Verifies BUG-51: evaluate_baselines must fall back to the training target mean
    when an hour is absent from the historical map, never leaking test labels.
    """
    from ml.training.train_traffic_model import evaluate_baselines

    # Train dataset covering only hour 8 on weekday (mean = 25.0)
    train_df = pd.DataFrame({
        "timestamp": pd.date_range("2026-09-21 08:00", periods=5, freq="5min"),  # Monday
        "is_weekend": [0, 0, 0, 0, 0],
        TARGET_COLUMN: [20.0, 25.0, 30.0, 25.0, 25.0],  # Mean = 25.0
        "speed_kmh": [20.0, 25.0, 30.0, 25.0, 25.0]
    })

    # Test dataset has hour 14 (missing from train_df historical map)
    # Test case 1: test targets are 100.0
    test_df_1 = pd.DataFrame({
        "timestamp": pd.date_range("2026-09-21 14:00", periods=3, freq="5min"),
        "is_weekend": [0, 0, 0],
        TARGET_COLUMN: [100.0, 100.0, 100.0],
        "speed_kmh": [100.0, 100.0, 100.0]
    })
    res_1 = evaluate_baselines(train_df, test_df_1)

    # Test case 2: test targets are 0.0
    test_df_2 = pd.DataFrame({
        "timestamp": pd.date_range("2026-09-21 14:00", periods=3, freq="5min"),
        "is_weekend": [0, 0, 0],
        TARGET_COLUMN: [0.0, 0.0, 0.0],
        "speed_kmh": [0.0, 0.0, 0.0]
    })
    res_2 = evaluate_baselines(train_df, test_df_2)

    # Historical average prediction for missing hour 14 must equal train_mean (25.0) in both cases
    # For test_df_1: true=100.0, pred=25.0 -> MAE = 75.0
    assert res_1["historical_average"]["mae"] == 75.0

    # For test_df_2: true=0.0, pred=25.0 -> MAE = 25.0
    assert res_2["historical_average"]["mae"] == 25.0


def test_energy_baseline_fallback_uses_train_mean_not_test_labels():
    """
    Verifies BUG-51: evaluate_energy_baselines must fall back to the training target mean
    when an hour is absent from the same-hour map, never leaking test labels.
    """
    from ml.training.train_energy_model import evaluate_energy_baselines

    # Train dataset covering only hour 9 on weekday (mean = 3000.0 kW)
    train_df = pd.DataFrame({
        "timestamp": pd.date_range("2026-09-21 09:00", periods=4, freq="15min"),  # Monday
        "is_weekend": [0, 0, 0, 0],
        ENERGY_TARGET_COLUMN: [2800.0, 3000.0, 3200.0, 3000.0],  # Mean = 3000.0
        "active_power_kw": [2800.0, 3000.0, 3200.0, 3000.0]
    })

    # Test dataset has hour 15 (missing from train_df map)
    # Test case 1: test targets are 5000.0 kW
    test_df_1 = pd.DataFrame({
        "timestamp": pd.date_range("2026-09-21 15:00", periods=4, freq="15min"),
        "is_weekend": [0, 0, 0, 0],
        ENERGY_TARGET_COLUMN: [5000.0, 5000.0, 5000.0, 5000.0],
        "active_power_kw": [5000.0, 5000.0, 5000.0, 5000.0]
    })
    res_1 = evaluate_energy_baselines(train_df, test_df_1)

    # Test case 2: test targets are 1000.0 kW
    test_df_2 = pd.DataFrame({
        "timestamp": pd.date_range("2026-09-21 15:00", periods=4, freq="15min"),
        "is_weekend": [0, 0, 0, 0],
        ENERGY_TARGET_COLUMN: [1000.0, 1000.0, 1000.0, 1000.0],
        "active_power_kw": [1000.0, 1000.0, 1000.0, 1000.0]
    })
    res_2 = evaluate_energy_baselines(train_df, test_df_2)

    # Pred is train_mean (3000.0 kW) in both cases
    # For test_df_1: true=5000.0, pred=3000.0 -> MAE = 2000.0
    assert res_1["same_hour_average"]["mae"] == 2000.0

    # For test_df_2: true=1000.0, pred=3000.0 -> MAE = 2000.0
    assert res_2["same_hour_average"]["mae"] == 2000.0


def test_hour_features_respect_configured_civil_offset(monkeypatch):
    """
    Verifies BUG-54: sin_hour, cos_hour, is_peak_hour, and is_mall_open evaluate
    relative to the configured corridor civil UTC offset across traffic and energy pipelines.
    """
    from backend.core.config import settings

    hist_traffic = [32.0] * 13
    hist_energy = [3500.0] * 97

    # Default pilot reference: UTC+05:30 (+330 min)
    # 08:30 UTC == 14:00 local civil time -> midday off-peak (NOT morning rush)
    dt_midday_civil_utc = datetime(2026, 9, 21, 8, 30, tzinfo=timezone.utc)
    t_midday = extract_traffic_features_row(hist_traffic, dt_midday_civil_utc, ambient_temp_c=32.0)
    assert t_midday["is_peak_hour"] == 0
    assert abs(t_midday["sin_hour"] - math.sin(2 * math.pi * 14.0 / 24.0)) < 1e-6
    assert abs(t_midday["cos_hour"] - math.cos(2 * math.pi * 14.0 / 24.0)) < 1e-6

    # 03:00 UTC == 08:30 local civil time -> morning rush peak
    dt_morning_civil_utc = datetime(2026, 9, 21, 3, 0, tzinfo=timezone.utc)
    t_morning = extract_traffic_features_row(hist_traffic, dt_morning_civil_utc, ambient_temp_c=27.0)
    assert t_morning["is_peak_hour"] == 1
    assert abs(t_morning["sin_hour"] - math.sin(2 * math.pi * 8.5 / 24.0)) < 1e-6

    # 18:00 UTC == 23:30 local civil time -> commercial facility closed (0), even though 18:00 UTC is afternoon
    dt_late_night_civil_utc = datetime(2026, 9, 21, 18, 0, tzinfo=timezone.utc)
    e_night = extract_energy_features_row(hist_energy, dt_late_night_civil_utc, ambient_temp_c=25.0)
    assert e_night["is_mall_open"] == 0
    assert abs(e_night["sin_hour"] - math.sin(2 * math.pi * 23.5 / 24.0)) < 1e-6

    # Dynamically changing central config offset must shift hour features accordingly (08:30 UTC -> 08:30 under UTC+0)
    monkeypatch.setattr(settings, "CORRIDOR_UTC_OFFSET_MINUTES", 0)
    t_utc0 = extract_traffic_features_row(hist_traffic, dt_midday_civil_utc, ambient_temp_c=32.0)
    assert t_utc0["is_peak_hour"] == 1
    assert abs(t_utc0["sin_hour"] - math.sin(2 * math.pi * 8.5 / 24.0)) < 1e-6


def test_localized_and_utc_equivalents_produce_identical_features_and_forecasts():
    """
    Verifies BUG-54: 18:00 local civil time evaluates identically whether passed as
    localized UTC+05:30 or UTC equivalent (12:30 UTC), including across midnight boundaries.
    """
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    instant_utc = datetime(2026, 9, 21, 12, 30, tzinfo=timezone.utc)
    instant_ist = datetime(2026, 9, 21, 18, 0, tzinfo=ist_tz)

    hist_t = [22.0] * 13
    t_from_utc = extract_traffic_features_row(hist_t, instant_utc, ambient_temp_c=30.0)
    t_from_ist = extract_traffic_features_row(hist_t, instant_ist, ambient_temp_c=30.0)
    assert t_from_utc["is_peak_hour"] == 1
    assert t_from_utc == t_from_ist

    hist_e = [4300.0] * 97
    e_from_utc = extract_energy_features_row(hist_e, instant_utc, ambient_temp_c=30.0)
    e_from_ist = extract_energy_features_row(hist_e, instant_ist, ambient_temp_c=30.0)
    assert e_from_utc["is_mall_open"] == 1
    assert e_from_utc == e_from_ist

    # Across UTC Friday -> IST Saturday midnight rollover (2026-09-18 20:00 UTC == 2026-09-19 01:30+05:30)
    rollover_utc = datetime(2026, 9, 18, 20, 0, tzinfo=timezone.utc)
    rollover_ist = datetime(2026, 9, 19, 1, 30, tzinfo=ist_tz)
    r_utc = extract_traffic_features_row(hist_t, rollover_utc, ambient_temp_c=24.0)
    r_ist = extract_traffic_features_row(hist_t, rollover_ist, ambient_temp_c=24.0)
    assert r_utc == r_ist
    assert r_utc["day_of_week"] == 5  # Saturday in corridor civil time
    assert r_utc["is_weekend"] == 1

    # Forecaster end-to-end equivalence
    forecaster = CorridorForecaster()
    f_utc = forecaster.predict_traffic_speed("urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01", 22.0, now_utc=instant_utc)
    f_ist = forecaster.predict_traffic_speed("urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01", 22.0, now_utc=instant_ist)
    assert f_utc["predictedValue"] == f_ist["predictedValue"]
    assert f_utc["generatedAt"] == f_ist["generatedAt"]


def test_morning_rush_boundary_harmonized_across_generator_and_features():
    """
    Verifies BUG-54: morning rush 08:30 - 11:00 local civil time matches between
    data generators, build_traffic_features, and extract_traffic_features_row.
    """
    # 10:45 IST (05:15 UTC) and 11:00 IST (05:30 UTC) are inside morning rush; 11:05 IST is off-peak
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    dt_1045 = datetime(2026, 9, 21, 10, 45, tzinfo=ist_tz)
    dt_1100 = datetime(2026, 9, 21, 11, 0, tzinfo=ist_tz)
    dt_1105 = datetime(2026, 9, 21, 11, 5, tzinfo=ist_tz)

    assert extract_traffic_features_row([30.0] * 13, dt_1045, 29.0)["is_peak_hour"] == 1
    assert extract_traffic_features_row([30.0] * 13, dt_1100, 29.0)["is_peak_hour"] == 1
    assert extract_traffic_features_row([30.0] * 13, dt_1105, 29.0)["is_peak_hour"] == 0

    raw_df = generate_corridor_traffic_history(days=7, seed=42)
    featured_df = build_traffic_features(raw_df)
    civil_ts = featured_df["timestamp"].dt.tz_convert(ist_tz)
    civil_hours = civil_ts.dt.hour + civil_ts.dt.minute / 60.0

    in_late_morning_rush = featured_df[(civil_hours >= 10.55) & (civil_hours <= 11.0)]
    assert len(in_late_morning_rush) > 0
    assert (in_late_morning_rush["is_peak_hour"] == 1).all()

    # Generated weekday speeds in 10:30-11:00 local civil window reflect morning rush (~28.5 km/h),
    # significantly lower than midday off-peak (12:00-14:00 local civil, ~37.0 km/h).
    weekday_rush = in_late_morning_rush[in_late_morning_rush["is_weekend"] == 0]["speed_kmh"].mean()
    weekday_midday = featured_df[
        (featured_df["is_weekend"] == 0) & (civil_hours >= 12.0) & (civil_hours <= 14.0)
    ]["speed_kmh"].mean()
    assert weekday_rush < 33.0
    assert weekday_midday > weekday_rush + 4.0


def test_training_and_inference_feature_parity_across_civil_transitions():
    """
    Verifies BUG-54: build_traffic_features and build_energy_features match online row extractors
    even when localized timestamps (+05:30) and UTC timestamps are queried across midnight.
    """
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    raw_t = generate_corridor_traffic_history(days=3, seed=99)
    feat_t = build_traffic_features(raw_t)

    # Check multiple steps including late-night UTC / early-morning civil rollover
    for idx in (40, 120, 240, 285):
        ts_utc = raw_t["timestamp"].iloc[idx]
        matched = feat_t[feat_t["timestamp"] == ts_utc]
        assert len(matched) == 1
        row = matched.iloc[0]
        hist = raw_t["speed_kmh"].iloc[: idx + 1].tolist()
        for dt_input in (ts_utc, ts_utc.to_pydatetime().astimezone(ist_tz)):
            extracted = extract_traffic_features_row(hist, dt_input, raw_t["ambient_temp_c"].iloc[idx])
            for col in FEATURE_COLUMNS:
                assert abs(float(extracted[col]) - float(row[col])) < 1e-4

    raw_e = generate_building_energy_history(days=6, seed=99)
    feat_e = build_energy_features(raw_e)
    for idx in (120, 180, 250):
        ts_utc = raw_e["timestamp"].iloc[idx]
        matched = feat_e[feat_e["timestamp"] == ts_utc]
        assert len(matched) == 1
        row = matched.iloc[0]
        hist = raw_e["active_power_kw"].iloc[: idx + 1].tolist()
        for dt_input in (ts_utc, ts_utc.to_pydatetime().astimezone(ist_tz)):
            extracted = extract_energy_features_row(hist, dt_input, raw_e["ambient_temp_c"].iloc[idx])
            for col in ENERGY_FEATURE_COLUMNS:
                assert abs(float(extracted[col]) - float(row[col])) < 1e-4


if __name__ == "__main__":
    test_traffic_chronological_split_no_leakage()
    test_energy_chronological_split_no_leakage()
    test_traffic_forecaster_inference_and_provenance()
    test_energy_forecaster_inference_and_provenance()
    test_forecast_state_isolation_invariant()
    print("ALL ML FORECASTING TESTS PASSED!")
