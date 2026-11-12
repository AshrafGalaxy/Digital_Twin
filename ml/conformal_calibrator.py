"""
conformal_calibrator.py

Conformal Prediction Uncertainty Calibration for Corridor Traffic and Building Energy Forecasters.
Computes distribution-free marginal prediction intervals with finite-sample discrete order
statistics using nonconformity scores calculated on held-out validation data.
"""

import math
from typing import Any, Dict, Mapping, Optional, Tuple
import numpy as np


_TARGET_LEVELS: Tuple[Tuple[str, float, float], ...] = (
    ("80", 0.20, 0.80),
    ("90", 0.10, 0.90),
)


class ConformalPredictionCalibrator:
    """
    Computes distribution-free marginal conformal prediction intervals for point forecasts.
    Quantiles are fit on a validation/calibration split using discrete order statistics.
    Empirical coverage is scored strictly on a subsequent chronological test split.
    """

    @staticmethod
    def _is_sample_size_valid(n: int, alpha: float) -> bool:
        """Returns True iff ceil((n + 1) * (1 - alpha)) <= n for finite-sample validity."""
        if n <= 0 or not (0.0 < alpha < 1.0):
            return False
        rank = math.ceil((n + 1) * (1.0 - alpha))
        return 1 <= rank <= n

    @classmethod
    def calibrate_from_residuals(
        cls,
        residuals: np.ndarray,
        alpha: float = 0.10
    ) -> float:
        """
        Finite-sample discrete conformal order statistic:
        k = ceil((n + 1) * (1 - alpha)), q_alpha = sorted(|residuals|)[k - 1]
        Raises ValueError when n == 0 or ceil((n + 1) * (1 - alpha)) > n.
        """
        values = np.abs(np.asarray(residuals, dtype=float))
        n = int(values.size)
        if n == 0:
            raise ValueError("Calibration split is empty.")
        if not np.isfinite(values).all():
            raise ValueError("Calibration residuals contain non-finite values.")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must lie strictly in (0, 1); got {alpha}.")
        rank = math.ceil((n + 1) * (1.0 - alpha))
        if rank > n:
            raise ValueError(
                f"Insufficient calibration samples (n={n}) for nominal coverage "
                f"{1.0 - alpha:.2f}: ceil((n+1)*(1-alpha))={rank} > {n}."
            )
        rank = max(1, rank)
        sorted_values = np.sort(values)
        return float(sorted_values[rank - 1])

    @classmethod
    def empirical_coverage(cls, test_residuals: np.ndarray, quantile: float) -> float:
        """Fraction of a later test split whose absolute residual is within the calibration quantile."""
        values = np.abs(np.asarray(test_residuals, dtype=float))
        if values.size == 0:
            raise ValueError("Test split is empty.")
        return float(np.mean(values <= quantile))

    @classmethod
    def fit_calibration_summary(
        cls,
        calibration_residuals: Optional[np.ndarray],
        test_residuals: Optional[np.ndarray] = None,
        calibration_split: str = "validation",
        test_split: str = "test",
    ) -> Dict[str, Any]:
        """
        Fits 80% and 90% finite-sample conformal quantiles on calibration residuals
        and scores empirical coverage strictly on subsequent test residuals.
        """
        if calibration_residuals is None:
            return {
                "available": False,
                "reason": "Interval unavailable: calibration split is missing.",
                "method": "split_conformal_discrete_order_statistic",
                "calibrationSplit": None,
                "testSplit": None,
                "calibrationSamples": 0,
                "testSamples": 0,
                "quantiles": None,
                "empiricalCoverage": None,
            }

        cal_abs = np.abs(np.asarray(calibration_residuals, dtype=float))
        n_cal = int(cal_abs.size)
        test_abs = (
            np.abs(np.asarray(test_residuals, dtype=float))
            if test_residuals is not None
            else np.array([], dtype=float)
        )
        n_test = int(test_abs.size)

        if n_cal == 0:
            return {
                "available": False,
                "reason": "Interval unavailable: calibration split is empty.",
                "method": "split_conformal_discrete_order_statistic",
                "calibrationSplit": calibration_split,
                "testSplit": test_split if n_test > 0 else None,
                "calibrationSamples": 0,
                "testSamples": n_test,
                "quantiles": None,
                "empiricalCoverage": None,
            }

        for level_key, alpha, nominal in _TARGET_LEVELS:
            if not cls._is_sample_size_valid(n_cal, alpha):
                rank = math.ceil((n_cal + 1) * (1.0 - alpha))
                return {
                    "available": False,
                    "reason": (
                        f"Interval unavailable: insufficient calibration samples (n={n_cal}) "
                        f"for {level_key}% level (ceil((n+1)*(1-alpha))={rank} > {n_cal})."
                    ),
                    "method": "split_conformal_discrete_order_statistic",
                    "calibrationSplit": calibration_split,
                    "testSplit": test_split if n_test > 0 else None,
                    "calibrationSamples": n_cal,
                    "testSamples": n_test,
                    "quantiles": None,
                    "empiricalCoverage": None,
                }

        quantiles: Dict[str, Dict[str, Any]] = {}
        empirical: Dict[str, Dict[str, Any]] = {}
        for level_key, alpha, nominal in _TARGET_LEVELS:
            q_val = cls.calibrate_from_residuals(cal_abs, alpha=alpha)
            quantiles[level_key] = {
                "alpha": alpha,
                "nominalCoverage": nominal,
                "quantile": float(q_val),
            }
            cov_val: Optional[float] = None
            cov_pct: Optional[float] = None
            if n_test > 0:
                cov_val = round(cls.empirical_coverage(test_abs, q_val), 4)
                cov_pct = round(cov_val * 100.0, 2)
            empirical[level_key] = {
                "nominalCoverage": nominal,
                "empiricalTestCoverage": cov_val,
                "empiricalTestCoveragePct": cov_pct,
                "coverageSplit": test_split if cov_val is not None else None,
                "testSamples": n_test,
            }

        return {
            "available": True,
            "reason": None,
            "method": "split_conformal_discrete_order_statistic",
            "calibrationSplit": calibration_split,
            "testSplit": test_split if n_test > 0 else None,
            "calibrationSamples": n_cal,
            "testSamples": n_test,
            "quantiles": quantiles,
            "empiricalCoverage": empirical,
        }

    @classmethod
    def _unavailable(cls, reason: str) -> Dict[str, Any]:
        return {
            "available": False,
            "reason": reason,
            "calibrationSplit": None,
            "testSplit": None,
            "calibrationSamples": 0,
            "testSamples": 0,
            "interval80": None,
            "interval90": None,
        }

    @classmethod
    def _build_band(
        cls,
        predicted: float,
        quantile: float,
        coverage: Optional[float],
        target: float,
        lower_bound: float,
        upper_bound: float,
        decimals: int,
        cal_samples: int,
        test_samples: int,
        test_split: Optional[str],
    ) -> Dict[str, Any]:
        return {
            "lower": round(max(lower_bound, predicted - quantile), decimals),
            "upper": round(min(upper_bound, predicted + quantile), decimals),
            "margin": round(quantile, decimals),
            "coverageTarget": target,
            "empiricalTestCoverage": coverage,
            "empiricalTestCoveragePct": round(coverage * 100.0, 2) if coverage is not None else None,
            "coverageSplit": test_split if coverage is not None else None,
            "calibrationSamples": cal_samples,
            "testSamples": test_samples,
        }

    @classmethod
    def intervals_from_calibration(
        cls,
        predicted: float,
        calibration: Optional[Mapping[str, Any]],
        lower_bound: float,
        upper_bound: float,
        decimals: int,
    ) -> Dict[str, Any]:
        """Builds runtime 80% and 90% conformal intervals directly from a stored calibration dictionary."""
        if not isinstance(calibration, Mapping):
            return cls._unavailable("Interval unavailable: model artifact lacks conformal calibration data.")
        if not calibration.get("available"):
            reason = calibration.get("reason") or "Interval unavailable: artifact conformal calibration is disabled."
            return cls._unavailable(str(reason))

        quantiles = calibration.get("quantiles")
        if not isinstance(quantiles, Mapping):
            return cls._unavailable("Interval unavailable: artifact conformal quantiles are missing.")

        cal_samples = int(calibration.get("calibrationSamples") or 0)
        test_samples = int(calibration.get("testSamples") or 0)
        cal_split = calibration.get("calibrationSplit") or "validation"
        test_split = calibration.get("testSplit") if test_samples > 0 else None
        empirical = calibration.get("empiricalCoverage") or {}

        bands: Dict[str, Dict[str, Any]] = {}
        for level_key, alpha, nominal in _TARGET_LEVELS:
            if not cls._is_sample_size_valid(cal_samples, alpha):
                rank = math.ceil((cal_samples + 1) * (1.0 - alpha))
                return cls._unavailable(
                    f"Interval unavailable: calibration samples (n={cal_samples}) insufficient "
                    f"for {level_key}% level (ceil((n+1)*(1-alpha))={rank} > {cal_samples})."
                )
            q_entry = quantiles.get(level_key)
            q_val = q_entry.get("quantile") if isinstance(q_entry, Mapping) else None
            if not isinstance(q_val, (int, float)) or not math.isfinite(float(q_val)):
                return cls._unavailable(f"Interval unavailable: missing valid {level_key}% conformal quantile.")

            emp_entry = empirical.get(level_key) if isinstance(empirical, Mapping) else None
            cov = emp_entry.get("empiricalTestCoverage") if isinstance(emp_entry, Mapping) else None
            cov_val = float(cov) if isinstance(cov, (int, float)) and math.isfinite(float(cov)) else None
            entry_split = emp_entry.get("coverageSplit") if isinstance(emp_entry, Mapping) else test_split

            bands[level_key] = cls._build_band(
                predicted=predicted,
                quantile=float(q_val),
                coverage=cov_val,
                target=nominal,
                lower_bound=lower_bound,
                upper_bound=upper_bound,
                decimals=decimals,
                cal_samples=cal_samples,
                test_samples=test_samples,
                test_split=entry_split,
            )

        return {
            "available": True,
            "reason": None,
            "calibrationSplit": cal_split,
            "testSplit": test_split,
            "calibrationSamples": cal_samples,
            "testSamples": test_samples,
            "interval80": bands["80"],
            "interval90": bands["90"],
        }

    @classmethod
    def _intervals_from_splits(
        cls,
        predicted: float,
        calibration_residuals: Optional[np.ndarray],
        test_residuals: Optional[np.ndarray],
        lower_bound: float,
        upper_bound: float,
        decimals: int,
    ) -> Dict[str, Any]:
        summary = cls.fit_calibration_summary(
            calibration_residuals=calibration_residuals,
            test_residuals=test_residuals,
            calibration_split="calibration",
            test_split="test",
        )
        return cls.intervals_from_calibration(
            predicted=predicted,
            calibration=summary,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            decimals=decimals,
        )

    @classmethod
    def get_traffic_intervals(
        cls,
        predicted_speed: float,
        min_speed: float = 5.0,
        max_speed: float = 55.0,
        calibration_residuals: Optional[np.ndarray] = None,
        test_residuals: Optional[np.ndarray] = None,
        calibration: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        """80% and 90% conformal intervals for a speed forecast. Missing calibration returns unavailable."""
        if calibration is not None:
            return cls.intervals_from_calibration(
                predicted_speed,
                calibration,
                min_speed,
                max_speed,
                2,
            )
        return cls._intervals_from_splits(
            predicted_speed,
            calibration_residuals,
            test_residuals,
            min_speed,
            max_speed,
            2,
        )

    @classmethod
    def get_energy_intervals(
        cls,
        predicted_kw: float,
        min_kw: float = 800.0,
        max_kw: float = 7000.0,
        calibration_residuals: Optional[np.ndarray] = None,
        test_residuals: Optional[np.ndarray] = None,
        calibration: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        """80% and 90% conformal intervals for a load forecast. Missing calibration returns unavailable."""
        if calibration is not None:
            return cls.intervals_from_calibration(
                predicted_kw,
                calibration,
                min_kw,
                max_kw,
                1,
            )
        return cls._intervals_from_splits(
            predicted_kw,
            calibration_residuals,
            test_residuals,
            min_kw,
            max_kw,
            1,
        )
