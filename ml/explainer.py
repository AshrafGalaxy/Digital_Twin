"""
explainer.py

Local Feature Attribution Explainer for XGBoost Forecasters.
Extracts exact TreeSHAP attributions per prediction step, identifying the top positive
and negative contributing factors driving the digital twin's predictive inference.
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
import xgboost as xgb


class LocalModelExplainer:
    """
    Computes local feature attributions using XGBoost's native pred_contribs (TreeSHAP).
    Explains how each feature shifts the prediction relative to the expected base value.
    """

    FEATURE_FRIENDLY_NAMES = {
        "speed_lag_5m": "Recent 5m Speed",
        "speed_lag_10m": "Recent 10m Speed",
        "speed_lag_15m": "Recent 15m Speed",
        "speed_lag_30m": "Historical 30m Lag",
        "speed_lag_60m": "Historical 60m Lag",
        "speed_roll_mean_30m": "30m Moving Average",
        "speed_roll_std_30m": "Speed Volatility",
        "speed_roll_mean_60m": "60m Average Speed",
        "speed_roll_min_60m": "60m Minimum Speed",
        "speed_roll_max_60m": "60m Free-Flow Speed Ceiling",
        "sin_hour": "Time-of-Day Cyclical",
        "cos_hour": "Diurnal Rhythm",
        "is_peak_hour": "Peak Rush Hour Period",
        "is_weekend": "Weekend Traffic Pattern",
        "day_of_week": "Day of Week",
        "ambient_temp_c": "Ambient Temperature",
        "load_lag_1h": "Previous Hour Load",
        "load_lag_2h": "2-Hour Prior Load",
        "load_lag_3h": "3-Hour Prior Load",
        "load_lag_24h": "Same-Time Yesterday Load",
        "load_roll_mean_6h": "6h Average Load",
        "load_roll_max_6h": "6h Peak Electrical Demand",
        "load_roll_std_6h": "6h Load Volatility",
        "is_mall_open": "Commercial Mall Operating Hours"
    }

    @classmethod
    def explain_prediction(
        cls,
        model: Any,
        input_df: pd.DataFrame,
        feature_names: List[str],
        top_k: int = 5,
        displayed_prediction: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Computes TreeSHAP attributions for a single-row feature dataframe.
        TreeSHAP attributions sum to the unclipped booster output:
          raw_booster_output = baseValue + sum(contributions)
        If the displayed prediction is clipped to physical limits, matchesDisplayedPrediction
        indicates whether the attributions sum to the displayed value or raw booster output.
        Returns base value, predicted value, reference target, and top feature contributions.
        """
        try:
            dmat = xgb.DMatrix(input_df[feature_names])
            booster = model.get_booster()
            contribs = booster.predict(dmat, pred_contribs=True)[0]

            feature_contribs = contribs[:-1]
            base_value = float(contribs[-1])
            unclipped_sum = float(base_value + np.sum(feature_contribs))
            raw_pred = float(booster.predict(dmat)[0])

            attributions = []
            for fname, val in zip(feature_names, feature_contribs):
                friendly = cls.FEATURE_FRIENDLY_NAMES.get(fname, fname)
                attributions.append({
                    "feature": fname,
                    "displayName": friendly,
                    "contribution": round(float(val), 2),
                    "impact": "INCREASES" if val > 0 else "DECREASES"
                })

            # Sort by absolute impact magnitude
            attributions.sort(key=lambda x: abs(x["contribution"]), reverse=True)

            matches_displayed = (
                displayed_prediction is None
                or abs(unclipped_sum - float(displayed_prediction)) < 0.05
            )

            return {
                "available": True,
                "baseValue": round(base_value, 2),
                "rawPredictedValue": round(raw_pred, 2),
                "unclippedAttributionSum": round(unclipped_sum, 2),
                "referenceTarget": "raw_booster_output",
                "matchesDisplayedPrediction": matches_displayed,
                "topContributors": attributions[:top_k],
                "allAttributions": attributions
            }
        except Exception as e:
            return {
                "available": False,
                "baseValue": None,
                "topContributors": [],
                "referenceTarget": "raw_booster_output",
                "matchesDisplayedPrediction": False,
                "error": str(e)
            }
