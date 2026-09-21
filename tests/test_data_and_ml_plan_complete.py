"""
test_data_and_ml_plan_complete.py

Comprehensive test suite verifying full implementation of all DATA_AND_ML_PLAN.md requirements:
1. Medallion Lakehouse directory structure and raw sample fixtures.
2. Offline Gold Feature Store tables (Parquet & CSV) and SHA-256 manifests.
3. Local MLflow experiment tracking and model registry runs.
4. Open-Meteo live weather ingestion and diurnal curve fallback.
5. Population Stability Index (PSI) feature distribution drift detection.
6. Traffic feature ablation study results (Experiment E-03).
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app
from backend.ingestion.weather_client import OpenMeteoWeatherClient
from ml.drift_detector import FeatureDriftDetector
from ml.features.feature_pipeline import compute_file_sha256
from ml.training.mlflow_tracker import MLflowTracker

ROOT_DIR = Path(__file__).resolve().parent.parent


def test_lakehouse_directory_structure_and_samples():
    """Verifies that all medallion storage directories and raw sample fixtures exist."""
    required_dirs = [
        ROOT_DIR / "data" / "raw" / "traffic",
        ROOT_DIR / "data" / "raw" / "energy",
        ROOT_DIR / "data" / "raw" / "weather",
        ROOT_DIR / "data" / "raw" / "environment",
        ROOT_DIR / "data" / "gold" / "features",
        ROOT_DIR / "data" / "gold" / "aggregates",
        ROOT_DIR / "artifacts" / "mlflow",
        ROOT_DIR / "artifacts" / "models"
    ]
    for d in required_dirs:
        assert d.exists() and d.is_dir(), f"Missing required Lakehouse directory: {d}"

    # Verify sample fixtures
    traffic_sample = ROOT_DIR / "data" / "raw" / "traffic" / "pune_traffic_sample.csv"
    assert traffic_sample.exists()
    df_traffic = pd.read_csv(traffic_sample)
    assert "avg_speed_kmh" in df_traffic.columns
    assert len(df_traffic) > 0

    energy_sample = ROOT_DIR / "data" / "raw" / "energy" / "uci_electricity_sample.csv"
    assert energy_sample.exists()
    df_energy = pd.read_csv(energy_sample)
    assert "active_power_kw" in df_energy.columns
    assert len(df_energy) > 0

    weather_sample = ROOT_DIR / "data" / "raw" / "weather" / "openmeteo_pune_sample.json"
    assert weather_sample.exists()
    with open(weather_sample, "r", encoding="utf-8") as f:
        weather_json = json.load(f)
    assert "current_weather" in weather_json

    readme_file = ROOT_DIR / "data" / "README.md"
    assert readme_file.exists()
    assert "Medallion Data Lakehouse Storage Architecture" in readme_file.read_text(encoding="utf-8")


def test_gold_feature_store_integrity():
    """Verifies that Gold Parquet tables and feature manifest exist with valid checksums."""
    gold_dir = ROOT_DIR / "data" / "gold" / "features"
    traffic_parquet = gold_dir / "traffic_features_v1.parquet"
    energy_parquet = gold_dir / "energy_features_v1.parquet"
    manifest_file = gold_dir / "feature_manifest.json"

    assert traffic_parquet.exists(), "Missing traffic_features_v1.parquet"
    assert energy_parquet.exists(), "Missing energy_features_v1.parquet"
    assert manifest_file.exists(), "Missing feature_manifest.json"

    # Read Parquet
    df_traffic = pd.read_parquet(traffic_parquet)
    assert len(df_traffic) >= 5000
    assert "speed_lag_5m" in df_traffic.columns
    assert "target_speed_15m" in df_traffic.columns

    df_energy = pd.read_parquet(energy_parquet)
    assert len(df_energy) >= 2000
    assert "load_lag_1h" in df_energy.columns
    assert "target_load_60m" in df_energy.columns

    # Verify manifest integrity
    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["storage_tier"] == "GOLD"
    assert manifest["datasets"]["traffic"]["rows"] == len(df_traffic)
    assert manifest["datasets"]["energy"]["rows"] == len(df_energy)

    # Checksum verification
    actual_traffic_sha = compute_file_sha256(traffic_parquet)
    assert manifest["datasets"]["traffic"]["sha256_parquet"] == actual_traffic_sha


def test_mlflow_local_tracking():
    """Verifies that MLflowTracker logs parameters, metrics, tags, and run IDs."""
    tracker = MLflowTracker(experiment_name="Test_Verification_Suite")
    run_id = tracker.log_training_run(
        run_name="unit-test-run",
        parameters={"n_estimators": 50, "max_depth": 3},
        metrics={"test_mae": 2.85, "test_rmse": 3.42},
        tags={"domain": "TEST", "status": "VERIFIED"},
        feature_names=["feat_a", "feat_b"]
    )
    assert isinstance(run_id, str) and len(run_id) > 10
    db_path = ROOT_DIR / "artifacts" / "mlflow" / "mlflow.db"
    assert db_path.exists(), "MLflow SQLite database should exist in artifacts/mlflow/"


@pytest.mark.asyncio
async def test_weather_client_live_and_fallback():
    """Verifies that OpenMeteoWeatherClient fetches or falls back gracefully."""
    client = OpenMeteoWeatherClient(timeout_seconds=3.0)
    weather = await client.get_current_weather()

    assert "temperature_c" in weather
    assert "humidity_pct" in weather
    assert weather["source_mode"] in ["LIVE", "SIMULATION"]
    assert 10.0 <= weather["temperature_c"] <= 50.0
    assert 0.0 <= weather["humidity_pct"] <= 100.0

    # Test diurnal fallback explicitly
    from datetime import datetime, timezone
    fallback = client._compute_diurnal_fallback(datetime(2026, 9, 20, 14, 0, tzinfo=timezone.utc))
    assert fallback["source_mode"] == "SIMULATION"
    assert fallback["source_id"] == "diurnal-model:pune-viman-nagar"
    assert 20.0 <= fallback["temperature_c"] <= 40.0


def test_feature_drift_detector():
    """Verifies that FeatureDriftDetector calculates PSI and classifies drift correctly."""
    detector = FeatureDriftDetector()
    assert len(detector.reference_df) > 0

    # Inlier sample from reference distribution -> STABLE
    sample_ref = detector.reference_df.sample(200, random_state=42)
    stable_eval = detector.evaluate_drift(sample_ref)
    assert stable_eval["overallStatus"] == "STABLE"
    assert stable_eval["qualityFlag"] == "valid"
    assert stable_eval["maxPsi"] < 0.15

    # Artificially shifted sample -> DRIFT_DETECTED
    shifted_sample = sample_ref.copy()
    shifted_sample["speed_lag_5m"] = shifted_sample["speed_lag_5m"] + 30.0
    drift_eval = detector.evaluate_drift(shifted_sample)
    assert drift_eval["overallStatus"] == "DRIFT_DETECTED"
    assert drift_eval["qualityFlag"] == "suspect"
    assert drift_eval["maxPsi"] >= 0.25
    assert "speed_lag_5m" in drift_eval["driftedFeatures"]


def test_ablation_study_artifacts():
    """Verifies that Experiment E-03 benchmark results exist and have valid configuration scores."""
    benchmarks_file = ROOT_DIR / "artifacts" / "evaluation_benchmarks.json"
    assert benchmarks_file.exists()
    with open(benchmarks_file, "r", encoding="utf-8") as f:
        benchmarks = json.load(f)

    assert "E-03" in benchmarks
    e03 = benchmarks["E-03"]
    assert "Config-1 (Lags Only)" in e03["configurations"]
    assert "Config-4 (Full Features + Ambient Temp)" in e03["configurations"]
    assert e03["configurations"]["Config-1 (Lags Only)"]["testMaeKmh"] > 0


@pytest.mark.asyncio
async def test_analytics_drift_api_endpoint():
    """Tests the GET /api/v1/analytics/drift endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/analytics/drift?hours_ago=6")
        assert resp.status_code == 200
        data = resp.json()
        assert "overallStatus" in data
        assert "maxPsi" in data
        assert "qualityFlag" in data
        assert "perFeatureMetrics" in data
        assert data["overallStatus"] in ["STABLE", "EARLY_WARNING", "DRIFT_DETECTED"]
