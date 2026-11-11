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


# Discrete features where continuous 2-sample KS test assumptions do not hold
DISCRETE_FEATURES = {"is_peak_hour", "is_weekend", "day_of_week"}


class FeatureDriftDetector:
    """
    Evaluates covariate and concept drift by comparing streaming evaluation windows
    against the authoritative Gold feature baseline.
    """

    # PSI standard regulatory boundaries (§4 of AGENTS.md)
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
    ) -> Optional[float]:
        """
        Computes the Population Stability Index (PSI) between reference and current feature arrays.
        Returns None when arrays have fewer than 10 observations or quantile bins cannot partition into >= 3 edges.
        """
        ref_clean = reference[~np.isnan(reference)]
        curr_clean = current[~np.isnan(current)]

        if len(ref_clean) < 10 or len(curr_clean) < 10:
            return None

        # Create quantile bins on reference distribution
        percentiles = np.linspace(0, 100, num_buckets + 1)
        bins = np.percentile(ref_clean, percentiles)
        # Ensure unique bin edges on reference first to avoid empty buckets from duplicate percentiles
        bins = np.unique(bins)
        if len(bins) < 3:
            return None

        # Expand outer edges to capture out-of-range observations in current
        bins[0] = -np.inf
        bins[-1] = np.inf

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
        Returns detailed per-feature metrics and overall drift status conforming to AGENTS.md §4.
        """
        if len(current_df) < 15:
            return {
                "overallStatus": "INSUFFICIENT_DATA",
                "status": "INSUFFICIENT_DATA",
                "maxPsi": None,
                "qualityFlag": "insufficient_data",
                "driftedFeaturesCount": 0,
                "warningFeaturesCount": 0,
                "driftedFeatures": [],
                "warningFeatures": [],
                "recommendation": "Insufficient telemetry observations in lookback window (< 15 rows) to evaluate feature drift.",
                "perFeatureMetrics": {}
            }

        if feature_columns is None:
            feature_columns = [
                "speed_lag_5m", "speed_lag_15m", "speed_lag_60m",
                "speed_roll_mean_30m", "speed_roll_std_30m", "ambient_temp_c"
            ]

        feature_results = {}
        max_psi = 0.0
        drifted_features = []
        warning_features = []
        valid_evaluations_count = 0

        for col in feature_columns:
            if col not in self.reference_df.columns or col not in current_df.columns:
                continue

            ref_vals = self.reference_df[col].dropna().values
            curr_vals = current_df[col].dropna().values

            if len(curr_vals) == 0:
                continue

            psi = self.calculate_psi(ref_vals, curr_vals)

            # Continuous 2-sample KS test: skip on discrete flags or binary features
            is_discrete = col in DISCRETE_FEATURES or len(np.unique(ref_vals)) <= 2
            if not is_discrete and len(ref_vals) >= 5 and len(curr_vals) >= 5:
                ks_res = stats.ks_2samp(ref_vals, curr_vals)
                ks_stat: Optional[float] = round(float(ks_res.statistic), 4)
                ks_pval: Optional[float] = round(float(ks_res.pvalue), 6)
            else:
                ks_stat = None
                ks_pval = None

            if psi is None:
                status = "INSUFFICIENT_DATA"
            elif psi >= self.PSI_WARNING_THRESHOLD:
                status = "DRIFT"
                drifted_features.append(col)
                valid_evaluations_count += 1
                if psi > max_psi:
                    max_psi = psi
            elif psi >= self.PSI_STABLE_THRESHOLD:
                status = "WARNING"
                warning_features.append(col)
                valid_evaluations_count += 1
                if psi > max_psi:
                    max_psi = psi
            else:
                status = "STABLE"
                valid_evaluations_count += 1
                if psi > max_psi:
                    max_psi = psi

            feature_results[col] = {
                "psi": round(psi, 4) if psi is not None else None,
                "ksStatistic": ks_stat,
                "ksPValue": ks_pval,
                "status": status
            }

        if len(drifted_features) > 0:
            overall_status = "DRIFT"
            recommendation = (
                f"Significant distribution drift detected in {len(drifted_features)} features "
                f"({', '.join(drifted_features)}). Flag predictions as suspect and schedule model retraining."
            )
            quality_flag = "suspect"
        elif len(warning_features) > 0:
            overall_status = "WARNING"
            recommendation = (
                f"Moderate distribution drift in {len(warning_features)} features "
                f"({', '.join(warning_features)}). Continue monitoring."
            )
            quality_flag = "valid"
        elif valid_evaluations_count > 0:
            overall_status = "STABLE"
            recommendation = "Feature distributions match Gold baseline reference within standard stability thresholds (PSI < 0.10)."
            quality_flag = "valid"
        else:
            overall_status = "INSUFFICIENT_DATA"
            recommendation = "Insufficient valid feature data to evaluate distribution drift."
            quality_flag = "insufficient_data"

        return {
            "overallStatus": overall_status,
            "status": overall_status,
            "maxPsi": round(max_psi, 4) if valid_evaluations_count > 0 else None,
            "qualityFlag": quality_flag,
            "driftedFeaturesCount": len(drifted_features),
            "warningFeaturesCount": len(warning_features),
            "driftedFeatures": drifted_features,
            "warningFeatures": warning_features,
            "recommendation": recommendation,
            "perFeatureMetrics": feature_results
        }
