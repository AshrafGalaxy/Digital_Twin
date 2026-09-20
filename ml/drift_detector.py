"""
drift_detector.py

Feature Distribution Drift and Data Quality Detection Engine.
Computes Population Stability Index (PSI) and Kolmogorov-Smirnov (KS) tests
comparing incoming live/simulated feature windows against Gold baseline distributions (§9.1, §16.2).
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

ROOT_DIR = Path(__file__).resolve().parent.parent
GOLD_DIR = ROOT_DIR / "data" / "gold" / "features"


class FeatureDriftDetector:
    """
    Evaluates covariate and concept drift by comparing streaming evaluation windows
    against the authoritative Gold feature baseline.
    """

    # PSI standard regulatory boundaries
    PSI_STABLE_THRESHOLD: float = 0.10
    PSI_WARNING_THRESHOLD: float = 0.25

    def __init__(self, reference_df: Optional[pd.DataFrame] = None):
        if reference_df is not None:
            self.reference_df = reference_df
        else:
            self.reference_df = self._load_gold_reference()

    def _load_gold_reference(self) -> pd.DataFrame:
        """Loads the baseline Gold traffic feature store table."""
        parquet_file = GOLD_DIR / "traffic_features_v1.parquet"
        csv_file = GOLD_DIR / "traffic_features_v1.csv"

        if parquet_file.exists():
            return pd.read_parquet(parquet_file)
        elif csv_file.exists():
            return pd.read_csv(csv_file)
        else:
            raise FileNotFoundError(f"No Gold feature table found at {parquet_file} or {csv_file}")

    @staticmethod
    def calculate_psi(
        reference: np.ndarray,
        current: np.ndarray,
        num_buckets: int = 10,
        epsilon: float = 1e-4
    ) -> float:
        """
        Computes the Population Stability Index (PSI) between reference and current feature arrays.
        """
        ref_clean = reference[~np.isnan(reference)]
        curr_clean = current[~np.isnan(current)]

        if len(ref_clean) < 10 or len(curr_clean) < 10:
            return 0.0

        # Create quantile bins on reference distribution
        percentiles = np.linspace(0, 100, num_buckets + 1)
        bins = np.percentile(ref_clean, percentiles)
        bins[0] = -np.inf
        bins[-1] = np.inf
        # Ensure unique bin edges
        bins = np.unique(bins)
        if len(bins) < 3:
            return 0.0

        ref_counts, _ = np.histogram(ref_clean, bins=bins)
        curr_counts, _ = np.histogram(curr_clean, bins=bins)

        # Normalize to probabilities
        ref_pct = (ref_counts / len(ref_clean)) + epsilon
        curr_pct = (curr_counts / len(curr_clean)) + epsilon

        # Re-normalize
        ref_pct = ref_pct / ref_pct.sum()
        curr_pct = curr_pct / curr_pct.sum()

        psi_val = np.sum((curr_pct - ref_pct) * np.log(curr_pct / ref_pct))
        return float(np.clip(psi_val, 0.0, 10.0))

    def evaluate_drift(
        self,
        current_df: pd.DataFrame,
        feature_columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates PSI and KS 2-sample tests across all specified features.
        Returns detailed per-feature metrics and overall drift status.
        """
        if feature_columns is None:
            feature_columns = [
                "speed_lag_5m", "speed_lag_15m", "speed_lag_60m",
                "speed_roll_mean_30m", "speed_roll_std_30m", "ambient_temp_c"
            ]

        feature_results = {}
        max_psi = 0.0
        drifted_features = []
        warning_features = []

        for col in feature_columns:
            if col not in self.reference_df.columns or col not in current_df.columns:
                continue

            ref_vals = self.reference_df[col].dropna().values
            curr_vals = current_df[col].dropna().values

            if len(curr_vals) == 0:
                continue

            psi = self.calculate_psi(ref_vals, curr_vals)
            ks_res = stats.ks_2samp(ref_vals, curr_vals)

            if psi >= self.PSI_WARNING_THRESHOLD:
                status = "SIGNIFICANT_DRIFT"
                drifted_features.append(col)
            elif psi >= self.PSI_STABLE_THRESHOLD:
                status = "MODERATE_DRIFT"
                warning_features.append(col)
            else:
                status = "STABLE"

            if psi > max_psi:
                max_psi = psi

            feature_results[col] = {
                "psi": round(psi, 4),
                "ksStatistic": round(float(ks_res.statistic), 4),
                "ksPValue": round(float(ks_res.pvalue), 6),
                "status": status
            }

        if len(drifted_features) > 0:
            overall_status = "DRIFT_DETECTED"
            recommendation = f"Significant distribution drift detected in {len(drifted_features)} features ({', '.join(drifted_features)}). Flag predictions as suspect and schedule model retraining."
            quality_flag = "suspect"
        elif len(warning_features) > 0:
            overall_status = "EARLY_WARNING"
            recommendation = f"Moderate distribution drift in {len(warning_features)} features ({', '.join(warning_features)}). Continue monitoring."
            quality_flag = "valid"
        else:
            overall_status = "STABLE"
            recommendation = "Feature distributions match Gold baseline reference within standard stability thresholds (PSI < 0.10)."
            quality_flag = "valid"

        return {
            "overallStatus": overall_status,
            "maxPsi": round(max_psi, 4),
            "qualityFlag": quality_flag,
            "driftedFeaturesCount": len(drifted_features),
            "warningFeaturesCount": len(warning_features),
            "driftedFeatures": drifted_features,
            "warningFeatures": warning_features,
            "recommendation": recommendation,
            "perFeatureMetrics": feature_results
        }
