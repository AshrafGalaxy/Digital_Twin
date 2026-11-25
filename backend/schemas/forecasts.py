"""
forecasts.py

Pydantic schemas for traffic and building energy forecasts,
confidence intervals, baseline comparisons, and model registry records.
"""

from typing import Any, Dict, List, Optional
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
    contractDemandKw: Optional[float] = None
    isPeakDemandAlert: bool = False
    peakThresholdKw: Optional[float] = None
    baselineComparison: BaselineComparison
    sourceLimitation: str


class ModelVersionInfo(BaseModel):
    modelId: str
    domain: str
    targetMetric: str
    horizonMinutes: int
    unit: str
    status: str
    testMae: Optional[float] = None
    testRmse: Optional[float] = None
    improvementVsPersistencePct: Optional[float] = None
    trainedAt: str
    localityCaveat: Optional[str] = None


class QuantileHorizonForecast(BaseModel):
    horizonMinutes: int
    targetTimestamp: str
    p10Kw: float
    p50Kw: float
    p90Kw: float
    conformalInterval90: List[float]


class QuantileTopFeature(BaseModel):
    feature: str
    shapValue: float
    displayName: Optional[str] = None
    impact: Optional[str] = None


class QuantileForecastProvenance(BaseModel):
    sourceMode: str = "PREDICTED"
    modelVersion: str = "energy-quantile-xgb-v2"
    qualityStatus: str = "VALID"


class MultiHorizonLoadForecastResponse(BaseModel):
    buildingId: str
    forecastGeneratedAt: str
    capacityKw: float
    horizons: List[QuantileHorizonForecast]
    topFeatures: List[QuantileTopFeature]
    provenance: QuantileForecastProvenance
    baselineMetrics: Optional[Dict[str, Any]] = None
    advisoryNotice: str
