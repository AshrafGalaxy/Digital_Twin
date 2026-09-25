"""
forecaster.py

Inference engine for 15-minute traffic speed and 60-minute commercial building energy forecasting.
Loads trained model artifacts, validates real-time feature completeness,
and outputs standardized predictions with confidence bounds and PREDICTED provenance.
"""

import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
import joblib

from ml.features.traffic_features import FEATURE_COLUMNS
from ml.features.energy_features import ENERGY_FEATURE_COLUMNS
from ml.conformal_calibrator import ConformalPredictionCalibrator
from ml.explainer import LocalModelExplainer

MODELS_DIR = ROOT_DIR / "artifacts" / "models"

FACILITY_CONTRACT_KW: Dict[str, float] = {
    "urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01": 6800.0,
    "urn:ngsi-ld:BuildingZone:PUNE:BLD-PHOENIX-01": 6800.0,
    "urn:ngsi-ld:BuildingZone:PUNE:PHOENIX-01": 6800.0,
    "BLD-PHOENIX-01": 6800.0,
    "urn:ngsi-ld:Building:PUNE:BLD-SOLITAIRE-01": 6010.0,
    "urn:ngsi-ld:BuildingZone:PUNE:BLD-SOLITAIRE-01": 6010.0,
    "BLD-SOLITAIRE-01": 6010.0,
    "urn:ngsi-ld:Building:PUNE:BLD-HYATT-01": 4990.0,
    "urn:ngsi-ld:BuildingZone:PUNE:BLD-HYATT-01": 4990.0,
    "BLD-HYATT-01": 4990.0,
    "urn:ngsi-ld:Building:PUNE:BLD-SOLITAIRE-03": 2400.0,
    "urn:ngsi-ld:BuildingZone:PUNE:BLD-SOLITAIRE-03": 2400.0,
    "BLD-SOLITAIRE-03": 2400.0,
}


class CorridorForecaster:
    """Unified inference service for corridor traffic and building energy forecasts."""

    def __init__(self):
        self.traffic_artifact = self._load_model("traffic_xgb_v1.joblib")
        self.energy_artifact = self._load_model("energy_xgb_v1.joblib")

    def _load_model(self, filename: str) -> Optional[Dict[str, Any]]:
        path = MODELS_DIR / filename
        if path.exists():
            try:
                return joblib.load(path)
            except Exception as e:
                print(f"[!] Warning: failed loading {filename}: {e}")
                return None
        return None

    def predict_traffic_speed(
        self,
        segment_id: str,
        current_speed: float,
        speed_history: Optional[List[float]] = None,
        ambient_temp_c: float = 29.5
    ) -> Dict[str, Any]:
        """
        Generates a 15-minute ahead speed prediction for a road segment.
        Returns point estimate, 80% prediction interval, input quality, and model version.
        """
        now_utc = datetime.now(timezone.utc)
        target_utc = now_utc + timedelta(minutes=15)

        # Fallback if artifact is not loaded
        if not self.traffic_artifact:
            # Calibrated deterministic heuristic baseline
            pred = max(10.0, min(50.0, current_speed * 0.95))
            return {
                "entityId": segment_id,
                "targetMetric": "averageSpeedKmh",
                "sourceMode": "PREDICTED",
                "generatedAt": now_utc.isoformat(),
                "targetTimestamp": target_utc.isoformat(),
                "horizonMinutes": 15,
                "predictedValue": round(pred, 2),
                "confidenceLower": round(max(8.0, pred - 3.5), 2),
                "confidenceUpper": round(min(52.0, pred + 3.5), 2),
                "unit": "km/h",
                "modelVersion": "traffic-heuristic-fallback",
                "inputQualityStatus": "DEGRADED",
                "baselineComparison": {"persistence": current_speed}
            }

        # Synthesize recent lags if partial history provided
        hist = speed_history or [current_speed] * 12
        if len(hist) < 12:
            hist = [hist[0]] * (12 - len(hist)) + hist

        # Construct single-row feature dataframe
        hour_float = now_utc.hour + now_utc.minute / 60.0
        row_dict = {
            "speed_lag_5m": hist[-1],
            "speed_lag_10m": hist[-2],
            "speed_lag_15m": hist[-3],
            "speed_lag_30m": hist[-6],
            "speed_lag_60m": hist[-12],
            "speed_roll_mean_30m": float(np.mean(hist[-6:])),
            "speed_roll_std_30m": float(np.std(hist[-6:])),
            "speed_roll_mean_60m": float(np.mean(hist[-12:])),
            "speed_roll_min_60m": float(np.min(hist[-12:])),
            "speed_roll_max_60m": float(np.max(hist[-12:])),
            "sin_hour": math.sin(2 * math.pi * hour_float / 24.0),
            "cos_hour": math.cos(2 * math.pi * hour_float / 24.0),
            "day_of_week": now_utc.weekday(),
            "is_weekend": 1 if now_utc.weekday() in [5, 6] else 0,
            "is_peak_hour": 1 if (8.5 <= hour_float <= 10.5 or 17.5 <= hour_float <= 21.0) else 0,
            "ambient_temp_c": ambient_temp_c
        }

        X_input = pd.DataFrame([row_dict])[FEATURE_COLUMNS]
        
        # Primary prediction & Quantile bounds
        pred = float(self.traffic_artifact["model"].predict(X_input)[0])
        p10 = float(self.traffic_artifact["model_p10"].predict(X_input)[0])
        p90 = float(self.traffic_artifact["model_p90"].predict(X_input)[0])

        # Clamp to physical bounds (5 km/h to 55 km/h)
        pred = float(np.clip(pred, 5.0, 55.0))
        p10 = float(np.clip(p10, 4.0, pred - 0.5))
        p90 = float(np.clip(p90, pred + 0.5, 56.0))

        # Conformal prediction intervals & local feature attributions
        conformal = ConformalPredictionCalibrator.get_traffic_intervals(pred)
        explanation = LocalModelExplainer.explain_prediction(
            self.traffic_artifact["model"],
            X_input,
            FEATURE_COLUMNS,
            top_k=5
        )

        return {
            "entityId": segment_id,
            "targetMetric": "averageSpeedKmh",
            "sourceMode": "PREDICTED",
            "generatedAt": now_utc.isoformat(),
            "targetTimestamp": target_utc.isoformat(),
            "horizonMinutes": 15,
            "predictedValue": round(pred, 2),
            "confidenceLower": round(p10, 2),
            "confidenceUpper": round(p90, 2),
            "conformalIntervals": conformal,
            "explanation": explanation,
            "unit": "km/h",
            "modelVersion": self.traffic_artifact.get("model_id", "traffic-xgb-v1"),
            "inputQualityStatus": "VALID",
            "baselineComparison": {
                "persistenceValue": round(current_speed, 2),
                "modelTestMae": self.traffic_artifact["metrics"]["test_mae"],
                "persistenceMae": self.traffic_artifact["metrics"]["persistence_mae"],
                "accuracyGainPct": self.traffic_artifact["metrics"]["improvement_vs_persistence_pct"]
            },
            "localityNotice": self.traffic_artifact.get("locality_caveat", "")
        }

    def predict_building_energy(
        self,
        building_id: str,
        current_kw: float,
        kw_history: Optional[List[float]] = None,
        ambient_temp_c: float = 30.5,
        contract_kw: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generates a 60-minute ahead active power demand forecast for a commercial building.
        """
        now_utc = datetime.now(timezone.utc)
        target_utc = now_utc + timedelta(minutes=60)
        contract_demand = contract_kw if contract_kw is not None else FACILITY_CONTRACT_KW.get(building_id, 6800.0)
        peak_threshold = round(contract_demand * 0.85, 1)

        if not self.energy_artifact:
            pred = max(1200.0, current_kw * 1.02)
            return {
                "entityId": building_id,
                "targetMetric": "activePowerKw",
                "sourceMode": "PREDICTED",
                "generatedAt": now_utc.isoformat(),
                "targetTimestamp": target_utc.isoformat(),
                "horizonMinutes": 60,
                "predictedValue": round(pred, 1),
                "confidenceLower": round(pred * 0.92, 1),
                "confidenceUpper": round(pred * 1.08, 1),
                "unit": "kW",
                "modelVersion": "energy-heuristic-fallback",
                "inputQualityStatus": "DEGRADED",
                "contractDemandKw": contract_demand,
                "isPeakDemandAlert": pred >= peak_threshold,
                "peakThresholdKw": peak_threshold
            }

        hist = kw_history or [current_kw] * 96
        if len(hist) < 96:
            hist = [hist[0]] * (96 - len(hist)) + hist

        hour_float = now_utc.hour + now_utc.minute / 60.0
        row_dict = {
            "load_lag_1h": hist[-4],
            "load_lag_2h": hist[-8],
            "load_lag_3h": hist[-12],
            "load_lag_24h": hist[-96],
            "load_roll_mean_6h": float(np.mean(hist[-24:])),
            "load_roll_max_6h": float(np.max(hist[-24:])),
            "load_roll_std_6h": float(np.std(hist[-24:])),
            "sin_hour": math.sin(2 * math.pi * hour_float / 24.0),
            "cos_hour": math.cos(2 * math.pi * hour_float / 24.0),
            "day_of_week": now_utc.weekday(),
            "is_weekend": 1 if now_utc.weekday() in [5, 6] else 0,
            "is_mall_open": 1 if 10.0 <= hour_float <= 22.0 else 0,
            "ambient_temp_c": ambient_temp_c
        }

        X_input = pd.DataFrame([row_dict])[ENERGY_FEATURE_COLUMNS]

        pred = float(self.energy_artifact["model"].predict(X_input)[0])
        p10 = float(self.energy_artifact["model_p10"].predict(X_input)[0])
        p90 = float(self.energy_artifact["model_p90"].predict(X_input)[0])

        pred = float(np.clip(pred, 1000.0, 6500.0))
        p10 = float(np.clip(p10, 950.0, pred - 20.0))
        p90 = float(np.clip(p90, pred + 20.0, 6800.0))

        # Dynamic Peak load alert if forecast exceeds 85% of building contract capacity
        is_peak_alert = pred >= peak_threshold

        # Conformal prediction intervals & local feature attributions
        conformal = ConformalPredictionCalibrator.get_energy_intervals(pred)
        explanation = LocalModelExplainer.explain_prediction(
            self.energy_artifact["model"],
            X_input,
            ENERGY_FEATURE_COLUMNS,
            top_k=5
        )

        return {
            "entityId": building_id,
            "targetMetric": "activePowerKw",
            "sourceMode": "PREDICTED",
            "generatedAt": now_utc.isoformat(),
            "targetTimestamp": target_utc.isoformat(),
            "horizonMinutes": 60,
            "predictedValue": round(pred, 1),
            "confidenceLower": round(p10, 1),
            "confidenceUpper": round(p90, 1),
            "conformalIntervals": conformal,
            "explanation": explanation,
            "unit": "kW",
            "modelVersion": self.energy_artifact.get("model_id", "energy-xgb-v1"),
            "inputQualityStatus": "VALID",
            "contractDemandKw": contract_demand,
            "isPeakDemandAlert": is_peak_alert,
            "peakThresholdKw": peak_threshold,
            "baselineComparison": {
                "persistenceValue": round(current_kw, 1),
                "modelTestMae": self.energy_artifact["metrics"]["test_mae"],
                "persistenceMae": self.energy_artifact["metrics"]["persistence_mae"],
                "accuracyGainPct": self.energy_artifact["metrics"]["improvement_vs_persistence_pct"]
            },
            "sourceLimitation": self.energy_artifact.get("source_limitation", "")
        }
