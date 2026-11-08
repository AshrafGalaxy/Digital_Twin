"""
conformal_calibrator.py

Conformal Prediction Uncertainty Calibration for Corridor Traffic and Building Energy Forecasters.
Computes distribution-free prediction intervals with guaranteed finite-sample coverage
using non-conformity scores calculated on held-out validation data.
"""

from typing import Any, Dict, Optional
import numpy as np


class ConformalPredictionCalibrator:
    """
    Computes distribution-free conformal prediction intervals for point forecasts.
    Quantiles are fit on a calibration split. Coverage is scored on a later test split.
    """

    @classmethod
    def calibrate_from_residuals(
        cls,
        residuals: np.ndarray,
        alpha: float = 0.10
    ) -> float:
        """
        Finite-sample conformal quantile:
        q_alpha = Quantile(|residuals|, ceil((n+1)(1-alpha)) / n)
        """
        values = np.abs(np.asarray(residuals, dtype=float))
        n = int(values.size)
        if n == 0:
            raise ValueError("Calibration split is empty.")
        level = min(1.0, float(np.ceil((n + 1) * (1.0 - alpha)) / n))
        return float(np.quantile(values, level))

    @classmethod
    def empirical_coverage(cls, test_residuals: np.ndarray, quantile: float) -> float:
        """Fraction of a later test split whose absolute residual is within the calibration quantile."""
        values = np.abs(np.asarray(test_residuals, dtype=float))
        if values.size == 0:
            raise ValueError("Test split is empty.")
        return float(np.mean(values <= quantile))

    @classmethod
    def _unavailable(cls, reason: str) -> Dict[str, Any]:
        return {
            "available": False,
            "reason": reason,
            "calibrationSplit": None,
            "testSplit": None,
            "calibrationSamples": 0,
            "testSamples": 0,
            "interval90": None,
            "interval95": None,
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
        if calibration_residuals is None or np.asarray(calibration_residuals).size == 0:
            return cls._unavailable("Interval unavailable: calibration split is missing.")
        calibration = np.abs(np.asarray(calibration_residuals, dtype=float))
        q90 = cls.calibrate_from_residuals(calibration, alpha=0.10)
        q95 = cls.calibrate_from_residuals(calibration, alpha=0.05)
        coverage_90 = None
        coverage_95 = None
        test_count = 0
        if test_residuals is not None and np.asarray(test_residuals).size > 0:
            coverage_90 = round(cls.empirical_coverage(test_residuals, q90), 4)
            coverage_95 = round(cls.empirical_coverage(test_residuals, q95), 4)
            test_count = int(np.asarray(test_residuals).size)

        def band(quantile: float, coverage: Optional[float], target: float) -> Dict[str, Any]:
            return {
                "lower": round(max(lower_bound, predicted - quantile), decimals),
                "upper": round(min(upper_bound, predicted + quantile), decimals),
                "margin": round(quantile, decimals),
                "coverageTarget": target,
                "empiricalTestCoverage": coverage,
                "coverageSplit": "test" if coverage is not None else None,
                "calibrationSamples": int(calibration.size),
                "testSamples": test_count,
            }

        return {
            "available": True,
            "reason": None,
            "calibrationSplit": "calibration",
            "testSplit": "test" if test_count else None,
            "calibrationSamples": int(calibration.size),
            "testSamples": test_count,
            "interval90": band(q90, coverage_90, 0.90),
            "interval95": band(q95, coverage_95, 0.95),
        }

    @classmethod
    def get_traffic_intervals(
        cls,
        predicted_speed: float,
        min_speed: float = 5.0,
        max_speed: float = 55.0,
        calibration_residuals: Optional[np.ndarray] = None,
        test_residuals: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:
        """90% and 95% intervals for a speed forecast. Missing calibration returns no interval."""
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
    ) -> Dict[str, Any]:
        """90% and 95% intervals for a load forecast. Missing calibration returns no interval."""
        return cls._intervals_from_splits(
            predicted_kw,
            calibration_residuals,
            test_residuals,
            min_kw,
            max_kw,
            1,
        )
