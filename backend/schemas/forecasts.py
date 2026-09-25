"""
forecasts.py

Pydantic schemas for traffic and building energy forecasts,
confidence intervals, baseline comparisons, and model registry records.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class BaselineComparison(BaseModel):
    persistenceValue: Optional[float] = None
    modelTestMae: Optional[float] = None
    persistenceMae: Optional[float] = None
    sameHourMae: Optional[float] = None
    accuracyGainPct: Optional[float] = None


class TrafficForecastResponse(BaseModel):
    entityId: str
    targetMetric: str = "averageSpeedKmh"
    sourceMode: str = "PREDICTED"
    generatedAt: str
    targetTimestamp: str
    horizonMinutes: int = 15
    predictedValue: float
    confidenceLower: float
    confidenceUpper: float
    conformalIntervals: Optional[Dict[str, Any]] = None
    explanation: Optional[Dict[str, Any]] = None
    unit: str = "km/h"
    modelVersion: str
    inputQualityStatus: str = "VALID"
    baselineComparison: BaselineComparison
    localityNotice: str


class EnergyForecastResponse(BaseModel):
    entityId: str
    targetMetric: str = "activePowerKw"
    sourceMode: str = "PREDICTED"
    generatedAt: str
    targetTimestamp: str
    horizonMinutes: int = 60
    predictedValue: float
    confidenceLower: float
    confidenceUpper: float
    conformalIntervals: Optional[Dict[str, Any]] = None
    explanation: Optional[Dict[str, Any]] = None
    unit: str = "kW"
    modelVersion: str
    inputQualityStatus: str = "VALID"
    contractDemandKw: Optional[float] = 6800.0
    isPeakDemandAlert: bool = False
    peakThresholdKw: float = 4800.0
    baselineComparison: BaselineComparison
    sourceLimitation: str


class ModelVersionInfo(BaseModel):
    modelId: str
    domain: str
    targetMetric: str
    horizonMinutes: int
    unit: str
    status: str
    testMae: float
    testRmse: float
    improvementVsPersistencePct: float
    trainedAt: str
    localityCaveat: Optional[str] = None
