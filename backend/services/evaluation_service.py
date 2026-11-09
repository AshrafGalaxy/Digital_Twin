"""
evaluation_service.py

Benchmark service for the horizons a saved model was actually trained to predict.
Scores use a generated series with the same length and seed as that fit.
The holdout split starts after the training split of that series.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from ml.features.traffic_features import (
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    generate_corridor_traffic_history,
    build_traffic_features,
    chronological_split
)
from ml.features.energy_features import (
    ENERGY_FEATURE_COLUMNS,
    ENERGY_TARGET_COLUMN,
    generate_building_energy_history,
    build_energy_features,
    chronological_energy_split
)
from ml.inference.forecaster import CorridorForecaster
from ml.conformal_calibrator import ConformalPredictionCalibrator

# These match the saved artifacts. A later training change owns the 80/10/10 contract.
_SPEED_SERIES_DAYS = 21
_LOAD_SERIES_DAYS = 35
_FIT_TRAIN_PCT = 0.70
_FIT_VAL_PCT = 0.15
_SERIES_SEED = 42


def score_forecast_holdout(y_true, y_pred, y_persistence) -> Dict[str, Any]:
    """MAE, RMSE, and R-squared on one holdout. R-squared is not floored at zero."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    y_persistence = np.asarray(y_persistence, dtype=float)
    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    mape = float(np.mean(np.abs((y_true - y_pred) / np.maximum(y_true, 1e-5))) * 100.0)
    pers_mae = float(np.mean(np.abs(y_true - y_persistence)))
    pers_rmse = float(np.sqrt(np.mean((y_true - y_persistence) ** 2)))
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    r2 = float(1.0 - (ss_res / max(ss_tot, 1e-5)))
    skill_score = float(max(-1.0, 1.0 - (mae / max(pers_mae, 1e-5))))
    improvement_pct = float(((pers_mae - mae) / max(pers_mae, 1e-5)) * 100.0)
    return {
        "status": "SCORED",
        "modelMae": round(mae, 2),
        "modelRmse": round(rmse, 2),
        "modelMape": round(mape, 2),
        "r2Score": round(r2, 3),
        "persistenceMae": round(pers_mae, 2),
        "persistenceRmse": round(pers_rmse, 2),
        "skillScore": round(skill_score, 3),
        "improvementPct": round(improvement_pct, 1),
    }


def unavailable_model_score(y_true, y_persistence) -> Dict[str, Any]:
    """Persistence only. No invented model error."""
    y_true = np.asarray(y_true, dtype=float)
    y_persistence = np.asarray(y_persistence, dtype=float)
    pers_mae = float(np.mean(np.abs(y_true - y_persistence)))
    pers_rmse = float(np.sqrt(np.mean((y_true - y_persistence) ** 2)))
    return {
        "status": "MODEL_UNAVAILABLE",
        "modelMae": None,
        "modelRmse": None,
        "modelMape": None,
        "r2Score": None,
        "persistenceMae": round(pers_mae, 2),
        "persistenceRmse": round(pers_rmse, 2),
        "skillScore": None,
        "improvementPct": None,
    }


class EvaluationService:
    """Computes and caches multi-horizon empirical benchmark metrics."""

    def __init__(self):
        self._cached_benchmarks: Optional[Dict[str, Any]] = None
        self._cache_timestamp: Optional[datetime] = None

    def get_multi_horizon_benchmarks(self, force_recompute: bool = False) -> Dict[str, Any]:
        """Returns multi-horizon forecasting benchmarks with persistence baseline comparisons."""
        now_dt = datetime.now(timezone.utc)
        # Cache for 1 hour unless explicitly forced
        if (
            self._cached_benchmarks
            and not force_recompute
            and self._cache_timestamp
            and (now_dt - self._cache_timestamp).total_seconds() < 3600
        ):
            return self._cached_benchmarks

        now_iso = now_dt.isoformat()
        forecaster = CorridorForecaster()

        raw_df = generate_corridor_traffic_history(days=_SPEED_SERIES_DAYS, seed=_SERIES_SEED)
        feat_df = build_traffic_features(raw_df)
        train_df, val_df, test_df = chronological_split(
            feat_df, train_pct=_FIT_TRAIN_PCT, val_pct=_FIT_VAL_PCT
        )
        y_test_15m = test_df[TARGET_COLUMN].values
        y_pers = test_df["speed_kmh"].values
        speed_model = (
            forecaster.traffic_artifact.get("model")
            if forecaster.traffic_artifact and "model" in forecaster.traffic_artifact
            else None
        )
        if speed_model is not None:
            traffic_15m = score_forecast_holdout(
                y_test_15m,
                speed_model.predict(test_df[FEATURE_COLUMNS]),
                y_pers,
            )
            calibration_residuals = np.abs(
                val_df[TARGET_COLUMN].values - speed_model.predict(val_df[FEATURE_COLUMNS])
            )
            test_residuals = np.abs(
                y_test_15m - speed_model.predict(test_df[FEATURE_COLUMNS])
            )
            q90 = ConformalPredictionCalibrator.calibrate_from_residuals(calibration_residuals, alpha=0.10)
            q95 = ConformalPredictionCalibrator.calibrate_from_residuals(calibration_residuals, alpha=0.05)
            cov_90 = round(ConformalPredictionCalibrator.empirical_coverage(test_residuals, q90) * 100.0, 1)
            cov_95 = round(ConformalPredictionCalibrator.empirical_coverage(test_residuals, q95) * 100.0, 1)
            conformal_coverage = {
                "status": "SCORED",
                "calibrationSplit": "validation",
                "testSplit": "holdout",
                "calibrationSamples": int(calibration_residuals.size),
                "testSamples": int(test_residuals.size),
                "target90": {
                    "nominalConfidence": 0.90,
                    "empiricalCoveragePct": cov_90,
                    "halfWidthKmh": round(q90, 2),
                    "valid": cov_90 >= 90.0,
                },
                "target95": {
                    "nominalConfidence": 0.95,
                    "empiricalCoveragePct": cov_95,
                    "halfWidthKmh": round(q95, 2),
                    "valid": cov_95 >= 95.0,
                },
            }
        else:
            traffic_15m = unavailable_model_score(y_test_15m, y_pers)
            conformal_coverage = {
                "status": "MODEL_UNAVAILABLE",
                "calibrationSplit": None,
                "testSplit": None,
                "calibrationSamples": 0,
                "testSamples": 0,
                "target90": None,
                "target95": None,
            }

        raw_energy_df = generate_building_energy_history(days=_LOAD_SERIES_DAYS, seed=_SERIES_SEED)
        feat_energy_df = build_energy_features(raw_energy_df)
        _train_e, _val_e, test_e_df = chronological_energy_split(
            feat_energy_df, train_pct=_FIT_TRAIN_PCT, val_pct=_FIT_VAL_PCT
        )
        y_energy_test = test_e_df[ENERGY_TARGET_COLUMN].values
        y_energy_pers = test_e_df["active_power_kw"].values
        load_model = (
            forecaster.energy_artifact.get("model")
            if forecaster.energy_artifact and "model" in forecaster.energy_artifact
            else None
        )
        if load_model is not None:
            energy_score = score_forecast_holdout(
                y_energy_test,
                load_model.predict(test_e_df[ENERGY_FEATURE_COLUMNS]),
                y_energy_pers,
            )
        else:
            energy_score = unavailable_model_score(y_energy_test, y_energy_pers)
        energy_metrics = {
            "horizonMinutes": 60,
            "targetMetric": "commercialActivePowerKw",
            "unit": "kW",
            **energy_score,
            "facilityId": "urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01",
            "facilityName": "Phoenix Marketcity Commercial Complex",
        }

        benchmarks = {
            "evaluatedAt": now_iso,
            "seriesProvenance": "GENERATED",
            "generatorSeed": _SERIES_SEED,
            "testSetSamples": len(test_df),
            "holdoutStartsAfter": pd.Timestamp(train_df["timestamp"].max()).isoformat(),
            "testSplitStartsAt": pd.Timestamp(test_df["timestamp"].min()).isoformat(),
            "splitRatio": "70% Train / 15% Val / 15% Holdout (Chronological, matching the saved fit)",
            "splitRatioPct": "70/15/15",
            "governanceNotice": (
                "BENCHMARK INTEGRITY: Scores use a generated series with the same seed and length "
                "as the saved fit. They are not observed measurements. The holdout starts after "
                "the training split of that series. Only a horizon the model was trained to predict is listed."
            ),
            "horizons": {
                "15m": {
                    "horizonMinutes": 15,
                    "targetMetric": "averageSpeedKmh",
                    "unit": "km/h",
                    "trainedHorizon": True,
                    **traffic_15m,
                }
            },
            "buildingEnergy": energy_metrics,
            "conformalCoverage": conformal_coverage,
        }

        self._cached_benchmarks = benchmarks
        self._cache_timestamp = now_dt
        return benchmarks


# Global singleton evaluation service
evaluation_service = EvaluationService()

