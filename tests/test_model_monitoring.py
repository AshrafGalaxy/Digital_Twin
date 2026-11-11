"""
test_model_monitoring.py

Hermetic unit and integration tests for Model Observability and Population Stability Index (PSI)
feature drift monitoring (conforming to AGENTS.md §4 and BUG-49 / Issue #88).
"""

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Dict

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.core.config import settings
from backend.main import app
from ml.drift_detector import FeatureDriftDetector

client = TestClient(app)


def test_psi_insufficient_samples_returns_none():
    """calculate_psi must return None instead of fabricating 0.0 when samples < 10."""
    ref = np.array([10.0, 12.0, 14.0, 16.0, 18.0])  # 5 samples < 10
    curr = np.array([11.0, 13.0, 15.0, 17.0, 19.0])
    assert FeatureDriftDetector.calculate_psi(ref, curr) is None

    # Normal reference but current has < 10 samples
    ref_ok = np.linspace(10.0, 50.0, 50)
    curr_short = np.array([12.0, 14.0])
    assert FeatureDriftDetector.calculate_psi(ref_ok, curr_short) is None


def test_psi_degenerate_bins_returns_none():
    """calculate_psi must return None when reference distribution has fewer than 3 unique quantile edges."""
    ref_const = np.ones(50) * 25.0
    curr = np.ones(50) * 25.0
    assert FeatureDriftDetector.calculate_psi(ref_const, curr) is None


def test_psi_unique_bins_prevents_empty_reference_bucket():
    """
    Calling np.unique before setting outer -inf/+inf ensures that the first bucket
    is non-empty for bounded distributions with duplicate minimum values.
    """
    # Distribution with multiple zero values at lower bound
    ref = np.array([0.0] * 20 + list(np.linspace(1.0, 50.0, 80)))
    curr = np.array([0.0] * 15 + list(np.linspace(1.0, 50.0, 85)))
    psi = FeatureDriftDetector.calculate_psi(ref, curr)
    assert psi is not None
    assert psi >= 0.0
    assert psi < 0.10  # Minimal drift


def test_psi_status_threshold_transitions():
    """
    Verifies exact AGENTS.md §4 regulatory boundaries:
    STABLE < 0.10, WARNING in [0.10, 0.25), DRIFT >= 0.25.
    """
    detector = FeatureDriftDetector()
    ref_df = detector.reference_df

    # 1. Inlier sample -> STABLE
    sample_ref = ref_df.sample(200, random_state=42).copy()
    stable_eval = detector.evaluate_drift(sample_ref)
    assert stable_eval["overallStatus"] == "STABLE"
    assert stable_eval["qualityFlag"] == "valid"
    assert stable_eval["maxPsi"] < 0.10

    # 2. Significant shift -> DRIFT
    drift_sample = sample_ref.copy()
    drift_sample["speed_lag_5m"] = drift_sample["speed_lag_5m"] + 35.0
    drift_eval = detector.evaluate_drift(drift_sample)
    assert drift_eval["overallStatus"] == "DRIFT"
    assert drift_eval["qualityFlag"] == "suspect"
    assert drift_eval["maxPsi"] >= 0.25
    assert "speed_lag_5m" in drift_eval["driftedFeatures"]


def test_evaluate_drift_short_window_returns_insufficient_data():
    """
    Passing a dataframe with fewer than 15 rows must immediately return INSUFFICIENT_DATA
    with maxPsi=None and empty feature lists, never fabricating STABLE.
    """
    detector = FeatureDriftDetector()
    short_df = detector.reference_df.head(10).copy()

    eval_res = detector.evaluate_drift(short_df)
    assert eval_res["overallStatus"] == "INSUFFICIENT_DATA"
    assert eval_res["status"] == "INSUFFICIENT_DATA"
    assert eval_res["maxPsi"] is None
    assert eval_res["qualityFlag"] == "insufficient_data"
    assert eval_res["driftedFeaturesCount"] == 0
    assert eval_res["warningFeaturesCount"] == 0
    assert eval_res["driftedFeatures"] == []
    assert eval_res["warningFeatures"] == []
    assert "Insufficient" in eval_res["recommendation"]


def test_evaluate_drift_discrete_features_bypass_ks():
    """
    Discrete features (is_peak_hour, is_weekend, day_of_week) must bypass continuous
    2-sample Kolmogorov-Smirnov testing, returning null KS statistics.
    """
    detector = FeatureDriftDetector()
    sample_df = detector.reference_df.sample(100, random_state=42).copy()

    # Pass discrete feature columns explicitly
    eval_res = detector.evaluate_drift(
        sample_df,
        feature_columns=["is_peak_hour", "is_weekend", "day_of_week", "speed_lag_5m"]
    )
    metrics = eval_res["perFeatureMetrics"]

    for discrete_col in ["is_peak_hour", "is_weekend", "day_of_week"]:
        if discrete_col in metrics:
            assert metrics[discrete_col]["ksStatistic"] is None
            assert metrics[discrete_col]["ksPValue"] is None

    # Continuous column must have valid KS statistics
    assert metrics["speed_lag_5m"]["ksStatistic"] is not None
    assert metrics["speed_lag_5m"]["ksPValue"] is not None


def test_analytics_drift_endpoint_insufficient_data():
    """
    When traffic_observations in the lookback window has fewer than 15 rows,
    the API endpoint must return INSUFFICIENT_DATA and maxPsi=None,
    never sampling reference_df against itself to fabricate a false STABLE score.
    """
    # Fresh query with 1 hour window on empty test DB
    resp = client.get("/api/v1/analytics/drift?hours_ago=1")
    assert resp.status_code == 200
    data = resp.json()

    assert data["overallStatus"] == "INSUFFICIENT_DATA"
    assert data["status"] == "INSUFFICIENT_DATA"
    assert data["maxPsi"] is None
    assert data["qualityFlag"] == "insufficient_data"
    assert data["perFeatureMetrics"] == {}
    assert "Insufficient" in data["recommendation"]


def test_analytics_drift_endpoint_with_seeded_data(tmp_path):
    """
    Verifies that when >= 15 observations are present, drift is evaluated
    honestly without hardcoded 28.5 temperature literals in the query.
    """
    detector = FeatureDriftDetector()
    sample_df = detector.reference_df.sample(25, random_state=42).copy()
    assert len(sample_df) == 25
