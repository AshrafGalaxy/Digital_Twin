"""
test_schemas.py

Unit tests for canonical NGSI-LD inspired schemas.
"""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from backend.core.constants import QualityStatus, SourceMode
from backend.schemas.canonical import (
    EnergyObservationEvent,
    ForecastRecord,
    TrafficObservationEvent
)

def test_valid_traffic_observation():
    now = datetime.now(timezone.utc)
    event = TrafficObservationEvent(
        observedAt=now,
        sensorId="urn:ngsi-ld:TrafficSensor:PUNE:DS-VN-EB-01",
        segmentId="urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01",
        sourceMode=SourceMode.REPLAY,
        averageSpeedKmh=38.5,
        vehicleFlowPerHour=1420.0,
        occupancyPercent=45.2,
        queueLengthMeters=65.0
    )
    assert event.averageSpeedKmh == 38.5
    assert event.sourceMode == SourceMode.REPLAY
    assert event.qualityFlag == QualityStatus.VALID
    assert event.observedAt.tzinfo is not None

def test_invalid_traffic_speed_out_of_bounds():
    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError):
        # Speed cannot exceed 120 km/h sanity boundary
        TrafficObservationEvent(
            observedAt=now,
            sensorId="urn:ngsi-ld:TrafficSensor:PUNE:DS-VN-EB-01",
            segmentId="urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01",
            sourceMode=SourceMode.LIVE,
            averageSpeedKmh=210.0,
            vehicleFlowPerHour=100.0
        )

def test_valid_energy_observation():
    now = datetime.now(timezone.utc)
    event = EnergyObservationEvent(
        observedAt=now,
        buildingId="urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01",
        sourceMode=SourceMode.SIMULATION,
        activePowerKw=4250.0,
        reactivePowerKvar=620.0,
        powerFactor=0.98
    )
    assert event.activePowerKw == 4250.0
    assert event.sourceMode == SourceMode.SIMULATION

def test_forecast_record_provenance_invariant():
    now = datetime.now(timezone.utc)
    record = ForecastRecord(
        targetTimestamp=now,
        entityId="urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01",
        domain="TRAFFIC",
        modelVersionId="XGBoost_Traffic_v1.0",
        horizonMinutes=15,
        predictedValue=32.4,
        unit="km/h"
    )
    # Invariant: Forecast sourceMode must default to PREDICTED
    assert record.sourceMode == SourceMode.PREDICTED
