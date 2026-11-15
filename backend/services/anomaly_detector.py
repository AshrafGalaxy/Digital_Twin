"""
anomaly_detector.py

Environmental Anomaly Detection Engine for Corridor Air Quality and Thermal Sensors.
Combines dynamic statistical Z-score thresholds with a trained Isolation Forest model
to detect acute pollution surges, sensor malfunctions, and thermal anomalies.
"""

from typing import Any, Dict, List, Optional
import numpy as np
from sklearn.ensemble import IsolationForest


class EnvironmentalAnomalyDetector:
    """
    Evaluates environmental sensor telemetry (PM2.5, PM10, AQI, Temp)
    to detect abnormal spikes or hazardous atmospheric conditions.
    """

    # National Ambient Air Quality Standards (NAAQS) India / WHO reference thresholds
    PM25_MODERATE: float = 60.0    # 24h standard ug/m3
    PM25_POOR: float = 90.0
    PM25_SEVERE: float = 150.0

    AQI_POOR: float = 200.0
    AQI_SEVERE: float = 300.0

    def __init__(
        self,
        empirical_observations: Optional[np.ndarray] = None,
        baseline_stats: Optional[Dict[str, float]] = None,
    ):
        """
        Initializes the Environmental Anomaly Detector.
        If empirical_observations is provided (shape (N, 4): pm25, pm10, aqi, temp),
        the Isolation Forest and baseline parameters are fitted to empirical telemetry
        with source_mode='CALIBRATED'.
        Otherwise, a synthetic Gaussian distribution generator is used, explicitly labeled
        with source_mode='SIMULATION'.
        """
        stats = baseline_stats or {}
        if empirical_observations is not None and len(empirical_observations) >= 10:
            self.source_mode = "CALIBRATED"
            self.baseline_source = "EMPIRICAL_OBSERVATIONS"
            self.is_synthetic_baseline = False
            X_train = np.asarray(empirical_observations, dtype=float)
            self.pm25_mean = float(stats.get("pm25_mean", np.mean(X_train[:, 0])))
            self.pm25_std = float(stats.get("pm25_std", max(1.0, np.std(X_train[:, 0], ddof=1) if len(X_train) > 1 else 12.0)))
            self.pm10_mean = float(stats.get("pm10_mean", np.mean(X_train[:, 1])))
            self.aqi_mean = float(stats.get("aqi_mean", np.mean(X_train[:, 2])))
            self.temp_mean = float(stats.get("temp_mean", np.mean(X_train[:, 3])))
        else:
            self.source_mode = "SIMULATION"
            self.baseline_source = "SYNTHETIC_GENERATOR"
            self.is_synthetic_baseline = True
            self.pm25_mean = float(stats.get("pm25_mean", 45.0))
            self.pm25_std = float(stats.get("pm25_std", 12.0))
            self.pm10_mean = float(stats.get("pm10_mean", 85.0))
            self.aqi_mean = float(stats.get("aqi_mean", 110.0))
            self.temp_mean = float(stats.get("temp_mean", 28.5))

            np.random.seed(42)
            normal_pm25 = np.random.normal(loc=self.pm25_mean, scale=self.pm25_std, size=500)
            normal_pm10 = np.random.normal(loc=self.pm10_mean, scale=20.0, size=500)
            normal_aqi = np.random.normal(loc=self.aqi_mean, scale=25.0, size=500)
            normal_temp = np.random.normal(loc=self.temp_mean, scale=4.0, size=500)
            X_train = np.column_stack([normal_pm25, normal_pm10, normal_aqi, normal_temp])

        self.iso_forest = IsolationForest(contamination=0.03, random_state=42)
        self.iso_forest.fit(X_train)

    def evaluate_reading(
        self,
        sensor_id: str,
        pm25: float,
        pm10: Optional[float] = None,
        aqi: Optional[float] = None,
        ambient_temp_c: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Evaluates an environmental sensor observation for acute anomalies.
        Returns anomaly status, severity level, Z-score, provenance, and transparent rationale.
        Identifies and flags missing physical dimensions without silent imputation.
        """
        imputed_fields: List[str] = []
        if pm10 is None:
            imputed_fields.append("pm10")
            pm10_val = self.pm10_mean
        else:
            pm10_val = float(pm10)

        if aqi is None:
            imputed_fields.append("aqi")
            aqi_val = self.aqi_mean
        else:
            aqi_val = float(aqi)

        if ambient_temp_c is None:
            imputed_fields.append("ambientTempC")
            temp_val = self.temp_mean
        else:
            temp_val = float(ambient_temp_c)

        has_imputed = len(imputed_fields) > 0
        quality_status = "DEGRADED" if has_imputed else "VALID"

        # 1. Statistical Z-score evaluation against calibrated baseline
        z_score = (pm25 - self.pm25_mean) / self.pm25_std

        # 2. Multivariate Isolation Forest prediction
        X_sample = np.array([[pm25, pm10_val, aqi_val, temp_val]])
        iso_pred = int(self.iso_forest.predict(X_sample)[0])  # -1 for anomaly, 1 for inlier
        iso_score = float(self.iso_forest.score_samples(X_sample)[0])

        is_anomaly = False
        severity = "NORMAL"
        reasons = []

        if pm25 >= self.PM25_SEVERE or aqi_val >= self.AQI_SEVERE or z_score >= 4.0:
            is_anomaly = True
            severity = "CRITICAL"
            reasons.append(f"Severe particulate surge: PM2.5={pm25:.1f} ug/m3 (Z={z_score:+.2f})")
        elif pm25 >= self.PM25_POOR or aqi_val >= self.AQI_POOR or z_score >= 3.0 or iso_pred == -1:
            is_anomaly = True
            severity = "HIGH"
            reasons.append(f"Elevated atmospheric pollution: PM2.5={pm25:.1f} ug/m3, AQI={aqi_val:.0f}")
        elif z_score >= 2.2:
            is_anomaly = True
            severity = "MEDIUM"
            reasons.append(f"Statistically abnormal PM2.5 deviation: Z={z_score:+.2f}")

        return {
            "sensorId": sensor_id,
            "sourceMode": self.source_mode,
            "isSyntheticBaseline": self.is_synthetic_baseline,
            "baselineSource": self.baseline_source,
            "inputQualityStatus": quality_status,
            "hasImputedFeatures": has_imputed,
            "imputedFeatures": imputed_fields,
            "isAnomaly": is_anomaly,
            "severity": severity,
            "zScore": round(float(z_score), 2),
            "isolationScore": round(iso_score, 3),
            "reasons": reasons,
            "baselineStats": {
                "pm25Mean": round(self.pm25_mean, 2),
                "pm25Std": round(self.pm25_std, 2)
            },
            "telemetrySnapshot": {
                "pm25": pm25,
                "pm10": round(pm10_val, 1),
                "aqi": round(aqi_val, 1),
                "ambientTempC": round(temp_val, 1)
            }
        }
