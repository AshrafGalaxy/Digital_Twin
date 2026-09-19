"""
test_validation.py

Unit tests for IngestionValidator and state-separation invariants.
"""

from datetime import datetime, timedelta, timezone
from backend.core.constants import QualityStatus, SourceMode
from backend.ingestion.validator import IngestionValidator

def test_ingestion_validator_valid_event():
    now_utc = datetime.now(timezone.utc)
    payload = {
        "observedAt": now_utc.isoformat(),
        "sensorId": "urn:ngsi-ld:TrafficSensor:PUNE:DS-VN-EB-01",
        "segmentId": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01",
        "sourceMode": "REPLAY",
        "averageSpeedKmh": 25.0,
        "vehicleFlowPerHour": 1800.0,
        "occupancyPercent": 60.0
    }
    is_valid, error, event = IngestionValidator.validate_traffic_event(payload)
    assert is_valid is True
    assert error is None
    assert event is not None
    assert event.congestionIndex == 0.5  # 1.0 - (25.0 / 50.0)

def test_ingestion_validator_future_timestamp_rejected():
    future_time = datetime.now(timezone.utc) + timedelta(minutes=15)
    payload = {
        "observedAt": future_time.isoformat(),
        "sensorId": "urn:ngsi-ld:TrafficSensor:PUNE:DS-VN-EB-01",
        "segmentId": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01",
        "sourceMode": "LIVE",
        "averageSpeedKmh": 45.0,
        "vehicleFlowPerHour": 800.0
    }
    is_valid, error, event = IngestionValidator.validate_traffic_event(payload)
    assert is_valid is False
    assert "in future" in error

def test_ingestion_validator_stale_detection():
    old_time = datetime.now(timezone.utc) - timedelta(seconds=250)
    payload = {
        "observedAt": old_time.isoformat(),
        "sensorId": "urn:ngsi-ld:TrafficSensor:PUNE:DS-VN-EB-01",
        "segmentId": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01",
        "sourceMode": "LIVE",
        "averageSpeedKmh": 35.0,
        "vehicleFlowPerHour": 1200.0
    }
    is_valid, error, event = IngestionValidator.validate_traffic_event(payload)
    assert is_valid is True
    assert event.qualityFlag == QualityStatus.STALE
