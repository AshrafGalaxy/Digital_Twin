"""
test_quarantine.py

Comprehensive tests for the data quarantine table and dead-letter queue (P3-B).
Validates AGENTS.md §7.5 (Data Quality & Rejection Invariants) and DATA_AND_ML_PLAN.md §3.
"""

from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.ingestion.validator import IngestionValidator
from backend.ingestion.quarantine import quarantine_manager

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_quarantine_before_each():
    """Ensures each test starts with a known quarantine state."""
    quarantine_manager.clear_quarantine()
    yield


def test_quarantine_speed_out_of_bounds():
    """Verifies that an event with speed exceeding physical corridor bounds is quarantined."""
    now_utc = datetime.now(timezone.utc)
    raw_event = {
        "observedAt": now_utc.isoformat(),
        "sensorId": "urn:ngsi-ld:TrafficSensor:PUNE:DET-NR-EB-01",
        "segmentId": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01",
        "sourceMode": "LIVE",
        "averageSpeedKmh": 185.0,  # Physically impossible on corridor (>120 km/h)
        "vehicleFlowPerHour": 1800.0,
        "occupancyPercent": 25.0
    }

    is_valid, error, event = IngestionValidator.validate_traffic_event(raw_event)
    assert not is_valid
    assert event is None
    assert "Speed metric failed validation" in (error or "")

    # Check that the record was written to quarantine
    records = quarantine_manager.get_quarantined_records(limit=10)
    assert len(records) == 1
    q_record = records[0]
    assert q_record["rejectionReason"] == "SPEED_OUT_OF_BOUNDS"
    assert q_record["entityId"] == "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01"
    assert q_record["rawPayload"]["averageSpeedKmh"] == 185.0


def test_quarantine_negative_speed():
    """Verifies that an event with negative speed is quarantined."""
    now_utc = datetime.now(timezone.utc)
    raw_event = {
        "observedAt": now_utc.isoformat(),
        "sensorId": "urn:ngsi-ld:TrafficSensor:PUNE:DET-NR-EB-01",
        "segmentId": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01",
        "sourceMode": "LIVE",
        "averageSpeedKmh": -10.0,
        "vehicleFlowPerHour": 500.0
    }

    is_valid, error, event = IngestionValidator.validate_traffic_event(raw_event)
    assert not is_valid
    assert event is None

    records = quarantine_manager.get_quarantined_records(limit=10)
    assert len(records) == 1
    assert records[0]["rejectionReason"] == "SPEED_OUT_OF_BOUNDS"


def test_quarantine_future_timestamp():
    """Verifies that an event timestamped in the distant future is quarantined."""
    future_time = datetime.now(timezone.utc) + timedelta(hours=3)
    raw_event = {
        "observedAt": future_time.isoformat(),
        "sensorId": "urn:ngsi-ld:TrafficSensor:PUNE:DET-NR-EB-01",
        "segmentId": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01",
        "sourceMode": "LIVE",
        "averageSpeedKmh": 45.0,
        "vehicleFlowPerHour": 1200.0,
        "occupancyPercent": 15.0
    }

    is_valid, error, event = IngestionValidator.validate_traffic_event(raw_event)
    assert not is_valid
    assert event is None
    assert "timestamp is in future" in (error or "")

    records = quarantine_manager.get_quarantined_records(limit=10)
    assert len(records) == 1
    assert records[0]["rejectionReason"] == "FUTURE_TIMESTAMP_REJECTED"
    assert records[0]["entityId"] == "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01"


def test_quarantine_missing_schema_fields():
    """Verifies that malformed payloads missing mandatory fields are quarantined."""
    raw_event = {
        "sensorId": "urn:ngsi-ld:TrafficSensor:PUNE:DET-NR-EB-01",
        "averageSpeedKmh": 35.0
        # Missing observedAt, segmentId, sourceMode, vehicleFlowPerHour
    }

    is_valid, error, event = IngestionValidator.validate_traffic_event(raw_event)
    assert not is_valid
    assert event is None

    records = quarantine_manager.get_quarantined_records(limit=10)
    assert len(records) == 1
    assert records[0]["rejectionReason"] == "SCHEMA_VALIDATION_FAILED"


def test_quarantine_energy_power_out_of_bounds():
    """Verifies that negative energy load is rejected and quarantined."""
    now_utc = datetime.now(timezone.utc)
    raw_event = {
        "observedAt": now_utc.isoformat(),
        "buildingId": "urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01",
        "sourceMode": "SIMULATION",
        "activePowerKw": -120.0  # Invalid negative load
    }

    is_valid, error, event = IngestionValidator.validate_energy_event(raw_event)
    assert not is_valid
    assert event is None

    records = quarantine_manager.get_quarantined_records(limit=10)
    assert len(records) == 1
    assert records[0]["rejectionReason"] == "POWER_OUT_OF_BOUNDS"
    assert records[0]["entityId"] == "urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01"


def test_quarantine_api_endpoint_and_filtering():
    """Verifies the GET /api/v1/health/quarantine endpoint with reason filtering and summary."""
    now_utc = datetime.now(timezone.utc)

    # 1. Generate 3 speed out-of-bounds events
    for speed in [140.0, 160.0, 190.0]:
        IngestionValidator.validate_traffic_event({
            "observedAt": now_utc.isoformat(),
            "sensorId": "urn:ngsi-ld:TrafficSensor:PUNE:DET-NR-EB-01",
            "segmentId": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01",
            "sourceMode": "LIVE",
            "averageSpeedKmh": speed,
            "vehicleFlowPerHour": 1000.0
        })

    # 2. Generate 2 future timestamp events
    future_time = now_utc + timedelta(hours=2)
    for _ in range(2):
        IngestionValidator.validate_traffic_event({
            "observedAt": future_time.isoformat(),
            "sensorId": "urn:ngsi-ld:TrafficSensor:PUNE:DET-NR-EB-01",
            "segmentId": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01",
            "sourceMode": "LIVE",
            "averageSpeedKmh": 40.0,
            "vehicleFlowPerHour": 1000.0
        })

    # Query full quarantine queue via API
    res = client.get("/api/v1/health/quarantine")
    assert res.status_code == 200
    data = res.json()

    assert data["totalQuarantined"] == 5
    assert data["reasonsBreakdown"]["SPEED_OUT_OF_BOUNDS"] == 3
    assert data["reasonsBreakdown"]["FUTURE_TIMESTAMP_REJECTED"] == 2
    assert len(data["records"]) == 5

    # Query filtered by reason
    res_filtered = client.get("/api/v1/health/quarantine?reason=SPEED_OUT_OF_BOUNDS")
    assert res_filtered.status_code == 200
    filtered_data = res_filtered.json()
    assert len(filtered_data["records"]) == 3
    for r in filtered_data["records"]:
        assert r["rejectionReason"] == "SPEED_OUT_OF_BOUNDS"

    # Query with pagination limit
    res_paginated = client.get("/api/v1/health/quarantine?limit=2&offset=0")
    assert res_paginated.status_code == 200
    assert len(res_paginated.json()["records"]) == 2


def test_quarantined_event_state_isolation_invariant():
    """
    State Isolation Invariant:
    Rejected events must NEVER appear in current twin state or update authoritative observations.
    """
    now_utc = datetime.now(timezone.utc)
    raw_event = {
        "observedAt": now_utc.isoformat(),
        "sensorId": "urn:ngsi-ld:TrafficSensor:PUNE:DET-NR-EB-01",
        "segmentId": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01",
        "sourceMode": "LIVE",
        "averageSpeedKmh": 250.0,  # Absurd speed
        "vehicleFlowPerHour": 1000.0
    }

    is_valid, _, _ = IngestionValidator.validate_traffic_event(raw_event)
    assert not is_valid

    # Query current state to ensure the absurd speed was not projected
    state_res = client.get("/api/v1/state/current")
    assert state_res.status_code == 200
    state_records = state_res.json()

    for rec in state_records:
        if rec["entityId"] == "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01":
            speed = rec.get("metrics", {}).get("averageSpeedKmh")
            if speed is not None:
                assert speed < 120.0
                assert speed != 250.0
