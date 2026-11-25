"""
quantile_load_service.py

Multi-horizon normalized quantile load inference service (15m, 60m, 240m, 1440m).
Loads trained P10/P50/P90 XGBoost quantile models and calibrated conformal bounds,
scales dimensionless predictions linearly to any facility capacity_kw, computes
TreeSHAP local feature attributions, and returns PREDICTED provenance payloads.
"""

import math
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import joblib
import numpy as np
import pandas as pd

from ml.explainer import LocalModelExplainer
from ml.features.civil_time import (
    ensure_utc_datetime,
    get_corridor_utc_offset_minutes,
    to_civil_datetime,
)
from ml.features.quantile_load_features import (
    QUANTILE_HORIZONS_MINUTES,
    QUANTILE_LOAD_FEATURE_COLUMNS,
    extract_quantile_load_features_row,
)

MODELS_DIR = ROOT_DIR / "artifacts" / "models"
DEFAULT_ARTIFACT_FILENAME = "quantile_load_xgb_v2.joblib"
ADVISORY_NOTICE = (
    "Advisory forecast only (non-actuating). "
    "Requires authorized facility engineering review before operational dispatch."
)


class QuantileLoadForecaster:
    """
    Capacity-portable multi-horizon commercial load forecaster producing P10, P50, P90
    quantiles, 90% split-conformal intervals, and TreeSHAP attributions.
    """

    def __init__(self, artifact_path: Optional[Path] = None) -> None:
        self._artifact_path = artifact_path if artifact_path is not None else (MODELS_DIR / DEFAULT_ARTIFACT_FILENAME)
        self.artifact: Optional[Dict[str, Any]] = self._load_artifact(self._artifact_path)

    def _load_artifact(self, path: Path) -> Optional[Dict[str, Any]]:
        if not path.exists():
            return None
        try:
            loaded = joblib.load(path)
            if isinstance(loaded, dict):
                return loaded
            return None
        except Exception as exc:
            print(f"[!] Warning: failed loading {path.name}: {exc}")
            return None

    def get_model_metadata(self) -> Dict[str, Any]:
        """Returns model registry metadata compatible with ForecastService.list_models()."""
        if not isinstance(self.artifact, dict):
            return {
                "modelId": "energy-quantile-heuristic-fallback",
                "domain": "ENERGY",
                "targetMetric": "activePowerKw",
                "horizonMinutes": 1440,
                "unit": "kW",
                "status": "FALLBACK",
                "testMae": None,
                "testRmse": None,
                "improvementVsPersistencePct": None,
                "trainedAt": "",
                "localityCaveat": (
                    "Heuristic fallback: quantile model artifact unavailable. "
                    "No holdout metrics computed."
                ),
            }

        raw_metrics = self.artifact.get("metrics")
        metrics_map: Dict[Any, Any] = raw_metrics if isinstance(raw_metrics, dict) else {}
        ref_horizon = metrics_map.get(60)
        if not isinstance(ref_horizon, dict):
            ref_horizon = metrics_map.get("60")
        if not isinstance(ref_horizon, dict) and metrics_map:
            first_val = next(iter(metrics_map.values()))
            ref_horizon = first_val if isinstance(first_val, dict) else {}
        if not isinstance(ref_horizon, dict):
            ref_horizon = {}

        raw_mae = ref_horizon.get("testMaeKw")
        raw_rmse = ref_horizon.get("testRmseKw")
        raw_gain = ref_horizon.get("improvementVsPersistencePct")

        return {
            "modelId": str(self.artifact.get("model_id", "energy-quantile-xgb-v2")),
            "domain": str(self.artifact.get("domain", "ENERGY")),
            "targetMetric": str(self.artifact.get("target_metric", "activePowerKw")),
            "horizonMinutes": 1440,
            "unit": str(self.artifact.get("unit", "kW")),
            "status": str(self.artifact.get("status", "APPROVED_FOR_DEMO")),
            "testMae": float(raw_mae) if isinstance(raw_mae, (int, float)) else None,
            "testRmse": float(raw_rmse) if isinstance(raw_rmse, (int, float)) else None,
            "improvementVsPersistencePct": (
                float(raw_gain) if isinstance(raw_gain, (int, float)) else None
            ),
            "trainedAt": str(self.artifact.get("trained_at", "")),
            "localityCaveat": str(
                self.artifact.get(
                    "source_limitation",
                    "Multi-facility normalized quantile load forecaster (15m, 60m, 240m, 1440m).",
                )
            ),
        }

    @staticmethod
    def _diurnal_shape(dt: datetime, offset_minutes: int) -> float:
        """Smooth normalized diurnal activity factor evaluated in local civil time."""
        civil_dt = to_civil_datetime(dt, offset_minutes)
        hour_float = float(civil_dt.hour) + (float(civil_dt.minute) / 60.0)
        if 7.0 <= hour_float <= 22.0:
            phase = (hour_float - 7.0) / 15.0
            return 0.45 + 0.55 * math.sin(math.pi * phase)
        return 0.35

    @classmethod
    def _prepare_normalized_history(
        cls,
        capacity_kw: float,
        effective_kw: float,
        kw_history: Optional[List[float]],
        now_utc: datetime,
        offset_minutes: int,
    ) -> List[float]:
        """
        Normalizes kw_history by capacity_kw. When fewer than 673 steps (168h + 1)
        are supplied, synthesizes a smooth diurnal prior-week prefix anchored to
        current_kw / capacity_kw (or the earliest provided observation).
        """
        required_len = 673
        norm_tail: List[float] = []
        if kw_history is not None and len(kw_history) > 0:
            norm_tail = [float(np.clip(float(val) / capacity_kw, 0.05, 1.35)) for val in kw_history]

        if len(norm_tail) >= required_len:
            return norm_tail[-required_len:]

        if norm_tail:
            anchor_idx = required_len - len(norm_tail)
            anchor_dt = now_utc - timedelta(minutes=15 * (len(norm_tail) - 1))
            anchor_norm = norm_tail[0]
            anchor_shape = max(cls._diurnal_shape(anchor_dt, offset_minutes), 1e-6)
            scale = anchor_norm / anchor_shape
            prefix: List[float] = []
            for idx in range(anchor_idx):
                step_dt = now_utc - timedelta(minutes=15 * (required_len - 1 - idx))
                val = float(np.clip(cls._diurnal_shape(step_dt, offset_minutes) * scale, 0.05, 1.35))
                prefix.append(val)
            return prefix + norm_tail

        anchor_norm = float(np.clip(effective_kw / capacity_kw, 0.05, 1.35))
        anchor_shape = max(cls._diurnal_shape(now_utc, offset_minutes), 1e-6)
        scale = anchor_norm / anchor_shape
        synth: List[float] = []
        for idx in range(required_len):
            step_dt = now_utc - timedelta(minutes=15 * (required_len - 1 - idx))
            val = float(np.clip(cls._diurnal_shape(step_dt, offset_minutes) * scale, 0.05, 1.35))
            synth.append(val)
        synth[-1] = anchor_norm
        return synth

    @staticmethod
    def _extract_conformal_q90_norm(
        conformal_calibrations: Mapping[Any, Any],
        horizon_min: int,
    ) -> float:
        """Extracts calibrated 90% conformal residual quantile in normalized load units."""
        entry = conformal_calibrations.get(horizon_min)
        if not isinstance(entry, Mapping):
            entry = conformal_calibrations.get(str(horizon_min))
        if isinstance(entry, Mapping) and entry.get("available"):
            quantiles = entry.get("quantiles")
            if isinstance(quantiles, Mapping):
                q90_entry = quantiles.get("90")
                if isinstance(q90_entry, Mapping):
                    q_val = q90_entry.get("quantile")
                    if isinstance(q_val, (int, float)) and math.isfinite(float(q_val)):
                        return max(0.0, float(q_val))
        return 0.15

    @staticmethod
    def _serialize_baseline_metrics(artifact: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
        """Formats per-horizon baseline and model test metrics with JSON-safe string keys."""
        raw_baselines = artifact.get("baselineMetrics")
        raw_metrics = artifact.get("metrics")
        if not isinstance(raw_baselines, Mapping):
            return None

        formatted: Dict[str, Any] = {}
        for horizon_min in QUANTILE_HORIZONS_MINUTES:
            b_entry = raw_baselines.get(horizon_min)
            if not isinstance(b_entry, Mapping):
                b_entry = raw_baselines.get(str(horizon_min))
            m_entry = None
            if isinstance(raw_metrics, Mapping):
                m_entry = raw_metrics.get(horizon_min)
                if not isinstance(m_entry, Mapping):
                    m_entry = raw_metrics.get(str(horizon_min))

            horizon_payload: Dict[str, Any] = {}
            if isinstance(b_entry, Mapping):
                for k, v in b_entry.items():
                    horizon_payload[str(k)] = v
            if isinstance(m_entry, Mapping):
                horizon_payload["modelP50"] = {
                    "maeNorm": m_entry.get("testMaeNorm"),
                    "rmseNorm": m_entry.get("testRmseNorm"),
                    "maeKw": m_entry.get("testMaeKw"),
                    "rmseKw": m_entry.get("testRmseKw"),
                    "improvementVsPersistencePct": m_entry.get("improvementVsPersistencePct"),
                }
            if horizon_payload:
                formatted[f"{horizon_min}m"] = horizon_payload
        return formatted if formatted else None

    def _predict_fallback(
        self,
        building_id: str,
        cap_kw: float,
        effective_kw: float,
        now_utc: datetime,
        offset_minutes: int,
        quality_status: str,
    ) -> Dict[str, Any]:
        """Deterministic heuristic fallback when the trained quantile artifact is unavailable."""
        min_kw = 0.05 * cap_kw
        max_kw = 1.35 * cap_kw
        now_shape = max(self._diurnal_shape(now_utc, offset_minutes), 1e-6)
        horizons_out: List[Dict[str, Any]] = []

        for horizon_min in QUANTILE_HORIZONS_MINUTES:
            target_dt = now_utc + timedelta(minutes=int(horizon_min))
            target_shape = self._diurnal_shape(target_dt, offset_minutes)
            ratio = target_shape / now_shape
            blend_weight = min(1.0, float(horizon_min) / 240.0)
            projected_kw = effective_kw * ((1.0 - blend_weight) + blend_weight * ratio)

            p50_kw = float(np.clip(projected_kw, min_kw, max_kw))
            spread_factor = 0.06 + 0.04 * min(1.0, float(horizon_min) / 240.0)
            p10_kw = float(np.clip(p50_kw * (1.0 - spread_factor), min_kw, max_kw))
            p90_kw = float(np.clip(p50_kw * (1.0 + spread_factor), min_kw, max_kw))

            p50_round = round(p50_kw, 1)
            p10_round = min(round(p10_kw, 1), p50_round)
            p90_round = max(round(p90_kw, 1), p50_round)

            margin_kw = 0.15 * cap_kw
            lower_kw = max(0.0, p50_kw - margin_kw)
            upper_kw = p50_kw + margin_kw

            horizons_out.append({
                "horizonMinutes": int(horizon_min),
                "targetTimestamp": target_dt.isoformat(),
                "p10Kw": p10_round,
                "p50Kw": p50_round,
                "p90Kw": p90_round,
                "conformalInterval90": [round(lower_kw, 1), round(upper_kw, 1)],
            })

        return {
            "buildingId": building_id,
            "forecastGeneratedAt": now_utc.isoformat(),
            "capacityKw": round(cap_kw, 2),
            "horizons": horizons_out,
            "topFeatures": [],
            "provenance": {
                "sourceMode": "PREDICTED",
                "modelVersion": "energy-quantile-heuristic-fallback",
                "qualityStatus": quality_status,
            },
            "baselineMetrics": None,
            "advisoryNotice": ADVISORY_NOTICE,
        }

    def predict_multi_horizon_load(
        self,
        building_id: str,
        capacity_kw: float,
        current_kw: Optional[float] = None,
        kw_history: Optional[List[float]] = None,
        ambient_temp_c: float = 30.5,
        relative_humidity_pct: float = 55.0,
        solar_irradiance_wm2: Optional[float] = None,
        is_holiday_flag: int = 0,
        now_utc: Optional[datetime] = None,
        utc_offset_minutes: Optional[int] = None,
        quality_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generates multi-horizon (15m, 60m, 240m, 1440m) P10/P50/P90 load forecasts
        with 90% conformal intervals and TreeSHAP attributions scaled to capacity_kw.
        """
        now_dt = ensure_utc_datetime(now_utc)
        offset_minutes = get_corridor_utc_offset_minutes(utc_offset_minutes)
        cap_kw = max(float(capacity_kw), 1e-6)

        input_omitted = current_kw is None
        if current_kw is not None:
            effective_kw = float(current_kw)
        elif kw_history is not None and len(kw_history) > 0:
            effective_kw = float(kw_history[-1])
        else:
            effective_kw = cap_kw * 0.45

        if not isinstance(self.artifact, dict):
            fallback_quality = str(quality_override) if quality_override is not None else "DEGRADED"
            return self._predict_fallback(
                building_id=building_id,
                cap_kw=cap_kw,
                effective_kw=effective_kw,
                now_utc=now_dt,
                offset_minutes=offset_minutes,
                quality_status=fallback_quality,
            )

        norm_hist = self._prepare_normalized_history(
            capacity_kw=cap_kw,
            effective_kw=effective_kw,
            kw_history=kw_history,
            now_utc=now_dt,
            offset_minutes=offset_minutes,
        )
        if current_kw is not None:
            norm_hist[-1] = float(np.clip(float(current_kw) / cap_kw, 0.05, 1.35))

        feature_cols_raw = self.artifact.get("features")
        feature_cols: List[str] = (
            [str(col) for col in feature_cols_raw]
            if isinstance(feature_cols_raw, list)
            else list(QUANTILE_LOAD_FEATURE_COLUMNS)
        )

        row_dict = extract_quantile_load_features_row(
            norm_hist=norm_hist,
            dt=now_dt,
            ambient_temp_c=float(ambient_temp_c),
            relative_humidity_pct=float(relative_humidity_pct),
            solar_irradiance_wm2=(
                float(solar_irradiance_wm2) if solar_irradiance_wm2 is not None else None
            ),
            is_holiday_flag=int(is_holiday_flag),
            utc_offset_minutes=offset_minutes,
        )
        X_input = pd.DataFrame([row_dict])[feature_cols]

        models_raw = self.artifact.get("models")
        models_map: Mapping[Any, Any] = models_raw if isinstance(models_raw, Mapping) else {}
        conformal_raw = self.artifact.get("conformal_calibrations")
        conformal_map: Mapping[Any, Any] = conformal_raw if isinstance(conformal_raw, Mapping) else {}

        min_kw = 0.05 * cap_kw
        max_kw = 1.35 * cap_kw
        horizons_out: List[Dict[str, Any]] = []
        p50_60m_model: Any = None

        for horizon_min in QUANTILE_HORIZONS_MINUTES:
            h_models = models_map.get(horizon_min)
            if not isinstance(h_models, Mapping):
                h_models = models_map.get(str(horizon_min))
            if not isinstance(h_models, Mapping):
                fallback_quality = str(quality_override) if quality_override is not None else "DEGRADED"
                return self._predict_fallback(
                    building_id=building_id,
                    cap_kw=cap_kw,
                    effective_kw=effective_kw,
                    now_utc=now_dt,
                    offset_minutes=offset_minutes,
                    quality_status=fallback_quality,
                )

            m_p10 = h_models.get("p10")
            m_p50 = h_models.get("p50")
            m_p90 = h_models.get("p90")
            if m_p10 is None or m_p50 is None or m_p90 is None:
                fallback_quality = str(quality_override) if quality_override is not None else "DEGRADED"
                return self._predict_fallback(
                    building_id=building_id,
                    cap_kw=cap_kw,
                    effective_kw=effective_kw,
                    now_utc=now_dt,
                    offset_minutes=offset_minutes,
                    quality_status=fallback_quality,
                )

            if int(horizon_min) == 60:
                p50_60m_model = m_p50

            raw_p10_norm = float(m_p10.predict(X_input)[0])
            raw_p50_norm = float(m_p50.predict(X_input)[0])
            raw_p90_norm = float(m_p90.predict(X_input)[0])

            p10_kw = float(np.clip(raw_p10_norm * cap_kw, min_kw, max_kw))
            p50_kw = float(np.clip(raw_p50_norm * cap_kw, min_kw, max_kw))
            p90_kw = float(np.clip(raw_p90_norm * cap_kw, min_kw, max_kw))

            # Enforce strict quantile monotonicity: p10Kw <= p50Kw <= p90Kw
            p10_kw = min(p10_kw, p50_kw)
            p90_kw = max(p90_kw, p50_kw)

            p50_round = round(p50_kw, 1)
            p10_round = min(round(p10_kw, 1), p50_round)
            p90_round = max(round(p90_kw, 1), p50_round)

            q90_norm = self._extract_conformal_q90_norm(conformal_map, int(horizon_min))
            margin_kw = q90_norm * cap_kw
            lower_kw = max(0.0, p50_kw - margin_kw)
            upper_kw = p50_kw + margin_kw

            target_ts = (now_dt + timedelta(minutes=int(horizon_min))).isoformat()
            horizons_out.append({
                "horizonMinutes": int(horizon_min),
                "targetTimestamp": target_ts,
                "p10Kw": p10_round,
                "p50Kw": p50_round,
                "p90Kw": p90_round,
                "conformalInterval90": [round(lower_kw, 1), round(upper_kw, 1)],
            })

        top_features: List[Dict[str, Any]] = []
        explainer_ok = True
        if p50_60m_model is not None:
            explanation = LocalModelExplainer.explain_prediction(
                p50_60m_model,
                X_input,
                feature_cols,
                top_k=5,
            )
            explainer_ok = bool(explanation.get("available", False)) and not explanation.get("error")
            raw_contribs = explanation.get("topContributors")
            if isinstance(raw_contribs, list):
                for item in raw_contribs:
                    if not isinstance(item, Mapping):
                        continue
                    contrib_raw = item.get("contribution", 0.0)
                    contrib_val = float(contrib_raw) if isinstance(contrib_raw, (int, float)) else 0.0
                    shap_kw = round(contrib_val * cap_kw, 2)
                    fname = str(item.get("feature", ""))
                    dname = str(item.get("displayName", fname))
                    impact = str(
                        item.get("impact", "INCREASES" if contrib_val >= 0.0 else "DECREASES")
                    )
                    top_features.append({
                        "feature": fname,
                        "shapValue": shap_kw,
                        "displayName": dname,
                        "impact": impact,
                    })
                top_features.sort(key=lambda x: abs(float(x["shapValue"])), reverse=True)
                top_features = top_features[:5]
        else:
            explainer_ok = False

        if quality_override is not None:
            quality_status = str(quality_override)
        elif input_omitted and (kw_history is None or len(kw_history) == 0):
            quality_status = "DEGRADED"
        elif not explainer_ok:
            quality_status = "DEGRADED"
        else:
            quality_status = "VALID"

        model_version = str(self.artifact.get("model_id", "energy-quantile-xgb-v2"))
        baseline_metrics = self._serialize_baseline_metrics(self.artifact)

        return {
            "buildingId": building_id,
            "forecastGeneratedAt": now_dt.isoformat(),
            "capacityKw": round(cap_kw, 2),
            "horizons": horizons_out,
            "topFeatures": top_features,
            "provenance": {
                "sourceMode": "PREDICTED",
                "modelVersion": model_version,
                "qualityStatus": quality_status,
            },
            "baselineMetrics": baseline_metrics,
            "advisoryNotice": ADVISORY_NOTICE,
        }


quantile_load_forecaster = QuantileLoadForecaster()
