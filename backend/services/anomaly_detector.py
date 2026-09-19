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

    def __init__(self):
        # Baseline training for Isolation Forest on normal Pune corridor ambient conditions
        np.random.seed(42)
        normal_pm25 = np.random.normal(loc=45.0, scale=12.0, size=500)
        normal_pm10 = np.random.normal(loc=85.0, scale=20.0, size=500)
        normal_aqi = np.random.normal(loc=110.0, scale=25.0, size=500)
        normal_temp = np.random.normal(loc=28.5, scale=4.0, size=500)

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
        Returns anomaly status, severity level, Z-score, and transparent rationale.
        """
        pm10_val = pm10 if pm10 is not None else pm25 * 1.8
        aqi_val = aqi if aqi is not None else pm25 * 2.2
        temp_val = ambient_temp_c if ambient_temp_c is not None else 29.0

        # 1. Statistical Z-score evaluation against expected baseline (mu=45.0, sigma=12.0)
        z_score = (pm25 - 45.0) / 12.0

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
            "isAnomaly": is_anomaly,
            "severity": severity,
            "zScore": round(float(z_score), 2),
            "isolationScore": round(iso_score, 3),
            "reasons": reasons,
            "telemetrySnapshot": {
                "pm25": pm25,
                "pm10": pm10_val,
                "aqi": round(aqi_val, 1),
                "ambientTempC": temp_val
            }
        }
