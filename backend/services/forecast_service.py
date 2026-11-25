"""
forecast_service.py

Service layer managing traffic and building energy forecasts.
Ensures PREDICTED provenance, state isolation, and baseline comparisons.
"""

from typing import Any, Dict, List, Optional
from ml.inference.forecaster import CorridorForecaster


class ForecastService:
    """Manages model inference, cache, and baseline comparisons."""

    def __init__(self):
        self.forecaster = CorridorForecaster()

    def get_traffic_forecast(
        self,
        segment_id: str,
        current_speed: Optional[float] = None
    ) -> Dict[str, Any]:
        """Generates 15-minute ahead speed forecast for a road segment."""
        return self.forecaster.predict_traffic_speed(
            segment_id=segment_id,
            current_speed=current_speed
        )

    DEFAULT_FACILITY_BASELINES: Dict[str, float] = {
        "urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01": 4200.0,
        "urn:ngsi-ld:BuildingZone:PUNE:BLD-PHOENIX-01": 4200.0,
        "urn:ngsi-ld:BuildingZone:PUNE:PHOENIX-01": 4200.0,
        "BLD-PHOENIX-01": 4200.0,
        "urn:ngsi-ld:Building:PUNE:BLD-SOLITAIRE-01": 4800.0,
        "urn:ngsi-ld:BuildingZone:PUNE:BLD-SOLITAIRE-01": 4800.0,
        "BLD-SOLITAIRE-01": 4800.0,
        "urn:ngsi-ld:Building:PUNE:BLD-HYATT-01": 3100.0,
        "urn:ngsi-ld:BuildingZone:PUNE:BLD-HYATT-01": 3100.0,
        "BLD-HYATT-01": 3100.0,
        "urn:ngsi-ld:Building:PUNE:BLD-SOLITAIRE-03": 1950.0,
        "urn:ngsi-ld:BuildingZone:PUNE:BLD-SOLITAIRE-03": 1950.0,
        "BLD-SOLITAIRE-03": 1950.0,
    }

    def get_energy_forecast(
        self,
        building_id: str,
        current_kw: Optional[float] = None
    ) -> Dict[str, Any]:
        """Generates 60-minute ahead active power forecast for commercial building."""
        return self.forecaster.predict_building_energy(
            building_id=building_id,
            current_kw=current_kw
        )

    def get_multi_horizon_load_forecast(
        self,
        building_id: str,
        capacity_kw: float,
        current_kw: Optional[float] = None,
        kw_history: Optional[List[float]] = None,
        ambient_temp_c: float = 30.5,
        relative_humidity_pct: float = 55.0,
        solar_irradiance_wm2: Optional[float] = None,
        is_holiday_flag: int = 0,
        quality_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generates 15m, 60m, 240m, and 1440m quantile load forecasts (p10/p50/p90) with conformal bounds."""
        from ml.inference.quantile_load_service import quantile_load_forecaster

        predict_fn = getattr(
            quantile_load_forecaster,
            "predict_multi_horizon_load",
            getattr(quantile_load_forecaster, "predict", None),
        )
        if predict_fn is None:
            raise RuntimeError("quantile_load_forecaster does not expose a prediction method")

        return predict_fn(
            building_id=building_id,
            capacity_kw=float(capacity_kw),
            current_kw=float(current_kw) if current_kw is not None else None,
            kw_history=[float(val) for val in kw_history] if kw_history is not None else None,
            ambient_temp_c=float(ambient_temp_c),
            relative_humidity_pct=float(relative_humidity_pct),
            solar_irradiance_wm2=(
                float(solar_irradiance_wm2) if solar_irradiance_wm2 is not None else None
            ),
            is_holiday_flag=int(is_holiday_flag),
            quality_override=quality_override,
        )

    def _get_quantile_model_metadata(self) -> Dict[str, Any]:
        """Returns metadata for the multi-horizon quantile load forecaster."""
        try:
            from ml.inference.quantile_load_service import quantile_load_forecaster

            meta_fn = getattr(quantile_load_forecaster, "get_model_metadata", None)
            if callable(meta_fn):
                meta = meta_fn()
                if isinstance(meta, dict) and meta.get("modelId"):
                    return meta

            art = getattr(quantile_load_forecaster, "artifact", None)
            if isinstance(art, dict):
                raw_metrics = art.get("metrics")
                metrics: Dict[str, Any] = raw_metrics if isinstance(raw_metrics, dict) else {}
                raw_horizons = metrics.get("horizons")
                source_metrics: Dict[str, Any] = metrics
                if isinstance(raw_horizons, dict):
                    h60 = raw_horizons.get(60)
                    if not isinstance(h60, dict):
                        h60 = raw_horizons.get("60")
                    if isinstance(h60, dict):
                        source_metrics = h60

                test_mae = source_metrics.get("test_mae")
                test_rmse = source_metrics.get("test_rmse")
                imp_pct = source_metrics.get("improvement_vs_persistence_pct")

                return {
                    "modelId": str(art.get("model_id", "energy-quantile-xgb-v2")),
                    "domain": str(art.get("domain", "ENERGY")),
                    "targetMetric": str(art.get("target_metric", "activePowerKw")),
                    "horizonMinutes": int(art.get("horizon_minutes", 1440)),
                    "unit": str(art.get("unit", "kW")),
                    "status": str(art.get("status", "APPROVED_FOR_DEMO")),
                    "testMae": float(test_mae) if isinstance(test_mae, (int, float)) else None,
                    "testRmse": float(test_rmse) if isinstance(test_rmse, (int, float)) else None,
                    "improvementVsPersistencePct": (
                        float(imp_pct) if isinstance(imp_pct, (int, float)) else None
                    ),
                    "trainedAt": str(art.get("trained_at", "")),
                    "localityCaveat": str(
                        art.get(
                            "source_limitation",
                            "Normalized multi-horizon quantile load forecaster (15m, 60m, 240m, 1440m).",
                        )
                    ),
                }
        except Exception:
            pass

        return {
            "modelId": "energy-quantile-xgb-v2",
            "domain": "ENERGY",
            "targetMetric": "activePowerKw",
            "horizonMinutes": 1440,
            "unit": "kW",
            "status": "FALLBACK",
            "testMae": None,
            "testRmse": None,
            "improvementVsPersistencePct": None,
            "trainedAt": "",
            "localityCaveat": "Heuristic fallback: quantile model artifact unavailable. No holdout metrics computed.",
        }

    def list_models(self) -> List[Dict[str, Any]]:
        """Lists active models and evaluation metrics."""
        models = []
        if self.forecaster.traffic_artifact:
            art = self.forecaster.traffic_artifact
            models.append({
                "modelId": art.get("model_id", "traffic-xgb-v1"),
                "domain": art.get("domain", "TRAFFIC"),
                "targetMetric": art.get("target_metric", "averageSpeedKmh"),
                "horizonMinutes": art.get("horizon_minutes", 15),
                "unit": art.get("unit", "km/h"),
                "status": art.get("status", "APPROVED_FOR_DEMO"),
                "testMae": art["metrics"]["test_mae"],
                "testRmse": art["metrics"]["test_rmse"],
                "improvementVsPersistencePct": art["metrics"]["improvement_vs_persistence_pct"],
                "trainedAt": art.get("trained_at", ""),
                "localityCaveat": art.get("locality_caveat", "")
            })
        else:
            models.append({
                "modelId": "traffic-heuristic-v1",
                "domain": "TRAFFIC",
                "targetMetric": "averageSpeedKmh",
                "horizonMinutes": 15,
                "unit": "km/h",
                "status": "FALLBACK",
                "testMae": None,
                "testRmse": None,
                "improvementVsPersistencePct": None,
                "trainedAt": "",
                "localityCaveat": "Heuristic fallback: model artifact unavailable. No holdout metrics computed."
            })

        if self.forecaster.energy_artifact:
            art = self.forecaster.energy_artifact
            models.append({
                "modelId": art.get("model_id", "energy-xgb-v1"),
                "domain": art.get("domain", "ENERGY"),
                "targetMetric": art.get("target_metric", "activePowerKw"),
                "horizonMinutes": art.get("horizon_minutes", 60),
                "unit": art.get("unit", "kW"),
                "status": art.get("status", "APPROVED_FOR_DEMO"),
                "testMae": art["metrics"]["test_mae"],
                "testRmse": art["metrics"]["test_rmse"],
                "improvementVsPersistencePct": art["metrics"]["improvement_vs_persistence_pct"],
                "trainedAt": art.get("trained_at", ""),
                "localityCaveat": art.get("source_limitation", "")
            })
        else:
            models.append({
                "modelId": "energy-heuristic-v1",
                "domain": "ENERGY",
                "targetMetric": "activePowerKw",
                "horizonMinutes": 60,
                "unit": "kW",
                "status": "FALLBACK",
                "testMae": None,
                "testRmse": None,
                "improvementVsPersistencePct": None,
                "trainedAt": "",
                "localityCaveat": "Heuristic fallback: model artifact unavailable. No holdout metrics computed."
            })

        if self.forecaster.traffic_artifact is not None or self.forecaster.energy_artifact is not None:
            models.append(self._get_quantile_model_metadata())

        return models


# Global singleton forecast service instance
forecast_service = ForecastService()

