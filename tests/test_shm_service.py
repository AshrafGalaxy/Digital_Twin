"""
test_shm_service.py

Hermetic unit and integration tests for the Critical Infrastructure Structural Health
Monitoring (SHM) Telemetry Pipeline (TASK-07 / Section 10.1).
Tests sensor telemetry bounds validation, resonant frequency drift fatigue alerts,
fiber-optic microstrain yield warnings, Weigh-in-Motion axle overloads, and REST API endpoints.
"""

from datetime import datetime, timedelta, timezone
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.core.database import AsyncSessionLocal
from backend.main import app
from backend.schemas.shm import SHMReadingValue, ResonantFreqReading, SHMTelemetryPayload
from backend.services.shm_service import SHMTelemetryService, shm_service

client = TestClient(app)


def _auth_header() -> dict:
    res = client.post("/api/v1/auth/login", json={
        "username_or_email": "analyst@pmc.gov.in",
        "password": "analyst123",
    })
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['token']}"}


def test_shm_integrity_status_classification():
    """
    Verifies mathematical classification of structural health status:
    - NOMINAL: normal strain, normal frequency, legal axle loads
    - ADVISORY_FATIGUE: resonant drift > 5% or strain in (600, 800]
    - ALERT_OVERLOAD: strain > 800 microstrain or HCV axle load > 10.2 tonnes
    """
    service = SHMTelemetryService()

    # 1. Nominal operating state
    status, alerts = service.evaluate_integrity_status(
        strain_val=520.0,
        resonant_drift_pct=-1.2,
        hcv_axle_load=8.5,
        vibration_ppv=3.2,
    )
    assert status == "NOMINAL"
    assert len(alerts) == 0

    # 2. Resonant frequency drift fatigue advisory (> 5.0% stiffness degradation)
    status, alerts = service.evaluate_integrity_status(
        strain_val=540.0,
        resonant_drift_pct=-5.8,
        hcv_axle_load=9.0,
        vibration_ppv=3.8,
    )
    assert status == "ADVISORY_FATIGUE"
    assert any("resonant frequency drift" in a for a in alerts)

    # 3. Flange microstrain elevated warning (600 to 800 uE)
    status, alerts = service.evaluate_integrity_status(
        strain_val=680.0,
        resonant_drift_pct=-2.0,
        hcv_axle_load=9.5,
        vibration_ppv=4.0,
    )
    assert status == "ADVISORY_FATIGUE"
    assert any("Elevated microstrain" in a for a in alerts)

    # 4. Elastic yield strain overload alert (> 800 uE)
    status, alerts = service.evaluate_integrity_status(
        strain_val=845.0,
        resonant_drift_pct=-2.0,
        hcv_axle_load=9.8,
        vibration_ppv=4.5,
    )
    assert status == "ALERT_OVERLOAD"
    assert any("Elastic yield advisory alert" in a for a in alerts)

    # 5. Weigh-in-Motion axle weight overload (> 10.2 tonnes)
    status, alerts = service.evaluate_integrity_status(
        strain_val=500.0,
        resonant_drift_pct=-1.0,
        hcv_axle_load=12.4,
        vibration_ppv=4.2,
    )
    assert status == "ALERT_OVERLOAD"
    assert any("Weigh-in-Motion overload alert" in a for a in alerts)


@pytest.mark.asyncio
async def test_shm_ingestion_and_database_persistence():
    """
    Verifies that valid SHM telemetry packets persist to shm_telemetry table
    and update entity_current_state with StructuralAsset type.
    """
    now_utc = datetime.now(timezone.utc)
    payload = SHMTelemetryPayload(
        structureId="STR-VN-FLY-01",
        structureName="Viman Nagar Corridor Flyover",
        spanId="SPAN-03-EB",
        sensorId="SENSOR-SHM-EB-03",
        observedAt=now_utc,
        vibrationPPV=SHMReadingValue(value=3.45, unit="mm/s", qualityScore=0.99),
        strain=SHMReadingValue(value=515.0, unit="microstrain", qualityScore=0.98),
        resonantFreqHz=ResonantFreqReading(value=4.20, baselineHz=4.25, driftPct=-1.18),
        ambientTempC=29.2,
        hcvAxleLoadTonnes=9.4,
        provenance={"sourceMode": "LIVE", "sensorType": "FBG_OPTICAL_PIEZO"},
    )

    async with AsyncSessionLocal() as session:
        record = await shm_service.ingest_shm_payload(session, payload)
        assert record.structureId == "STR-VN-FLY-01"
        assert record.spanId == "SPAN-03-EB"
        assert record.integrityStatus == "NOMINAL"
        assert record.strainMicrostrain == 515.0

        # Verify record in shm_telemetry table
        res = await session.execute(
            text("SELECT structure_id, span_id, integrity_status FROM shm_telemetry WHERE structure_id = :id ORDER BY observed_at DESC LIMIT 1"),
            {"id": "STR-VN-FLY-01"},
        )
        row = res.fetchone()
        assert row is not None
        assert row[0] == "STR-VN-FLY-01"
        assert row[1] == "SPAN-03-EB"
        assert row[2] == "NOMINAL"

        # Verify entity_current_state cache update
        res_state = await session.execute(
            text("SELECT entity_type, source_mode, quality_status FROM entity_current_state WHERE entity_id = :id"),
            {"id": "STR-VN-FLY-01"},
        )
        row_state = res_state.fetchone()
        assert row_state is not None
        assert row_state[0] == "StructuralAsset"
        assert row_state[1] == "LIVE"
        assert row_state[2] == "VALID"


def test_shm_physical_bounds_validation():
    """
    Verifies that impossible physical measurements are rejected by the Pydantic schema firewall:
    - PPV < 0 or PPV > 100 mm/s
    - Strain < -2000 or Strain > 3000 microstrain
    """
    now_utc = datetime.now(timezone.utc)

    # Rejection of excessive PPV (> 100 mm/s)
    with pytest.raises(ValueError, match="Peak Particle Velocity"):
        SHMTelemetryPayload(
            structureId="STR-VN-FLY-01",
            spanId="SPAN-01",
            observedAt=now_utc,
            vibrationPPV=SHMReadingValue(value=150.0, unit="mm/s"),
            strain=SHMReadingValue(value=500.0, unit="microstrain"),
            resonantFreqHz=ResonantFreqReading(value=4.25, baselineHz=4.25, driftPct=0.0),
            ambientTempC=25.0,
        )

    # Rejection of negative PPV (< 0 mm/s)
    with pytest.raises(ValueError, match="Peak Particle Velocity"):
        SHMTelemetryPayload(
            structureId="STR-VN-FLY-01",
            spanId="SPAN-01",
            observedAt=now_utc,
            vibrationPPV=SHMReadingValue(value=-5.0, unit="mm/s"),
            strain=SHMReadingValue(value=500.0, unit="microstrain"),
            resonantFreqHz=ResonantFreqReading(value=4.25, baselineHz=4.25, driftPct=0.0),
            ambientTempC=25.0,
        )

    # Rejection of impossible strain (> 3000 uE)
    with pytest.raises(ValueError, match="Strain reading"):
        SHMTelemetryPayload(
            structureId="STR-VN-FLY-01",
            spanId="SPAN-01",
            observedAt=now_utc,
            vibrationPPV=SHMReadingValue(value=5.0, unit="mm/s"),
            strain=SHMReadingValue(value=4500.0, unit="microstrain"),
            resonantFreqHz=ResonantFreqReading(value=4.25, baselineHz=4.25, driftPct=0.0),
            ambientTempC=25.0,
        )


def test_shm_rest_api_endpoints():
    """
    Verifies all SHM REST API routes:
    - GET /api/v1/shm/structures
    - POST /api/v1/shm/telemetry
    - GET /api/v1/shm/structures/{id}/status
    - GET /api/v1/shm/structures/{id}/telemetry
    """
    # 1. List structures. An empty table is an empty catalog, not a fabricated pair.
    resp = client.get("/api/v1/shm/structures")
    assert resp.status_code == 200
    structures = resp.json()
    assert isinstance(structures, list)
    for item in structures:
        assert not (
            item["peakStrainMicrostrain"] == 520.5
            and item["peakVibrationMms"] == 3.42
            and item["resonantDriftPct"] == -1.18
        )

    # 2. Ingest telemetry via POST
    sample_payload = {
        "structureId": "STR-SN-BRG-01",
        "structureName": "Somnath Nagar River Span Bridge",
        "spanId": "SPAN-01-CENTRAL",
        "sensorId": "SENSOR-SHM-SN-01",
        "observedAt": datetime.now(timezone.utc).isoformat(),
        "vibrationPPV": {"value": 2.85, "unit": "mm/s", "qualityScore": 0.99},
        "strain": {"value": 480.0, "unit": "microstrain", "qualityScore": 0.99},
        "resonantFreqHz": {"value": 3.75, "baselineHz": 3.80, "driftPct": -1.32},
        "ambientTempC": 27.8,
        "hcvAxleLoadTonnes": 9.1,
        "provenance": {"sourceMode": "LIVE", "sensorType": "FBG_OPTICAL_PIEZO"},
    }
    post_resp = client.post("/api/v1/shm/telemetry", json=sample_payload, headers=_auth_header())
    assert post_resp.status_code == 201
    created = post_resp.json()
    assert created["structureId"] == "STR-SN-BRG-01"
    assert created["integrityStatus"] == "NOMINAL"

    # 3. Check status
    status_resp = client.get("/api/v1/shm/structures/STR-SN-BRG-01/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["structureId"] == "STR-SN-BRG-01"
    assert status_data["integrityStatus"] == "NOMINAL"
    assert status_data["isFatigueAlert"] is False
    assert status_data["isOverloadAlert"] is False

    # 4. Check telemetry history
    hist_resp = client.get("/api/v1/shm/structures/STR-SN-BRG-01/telemetry?limit=10")
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    assert isinstance(hist_data, list)
    assert len(hist_data) >= 1
    assert hist_data[0]["structureId"] == "STR-SN-BRG-01"

    # 5. Verify invalid payload returns 422
    bad_payload = dict(sample_payload)
    bad_payload["vibrationPPV"] = {"value": 250.0, "unit": "mm/s"}
    bad_resp = client.post("/api/v1/shm/telemetry", json=bad_payload, headers=_auth_header())
    assert bad_resp.status_code == 422


def _nominal_packet(**overrides) -> dict:
    packet = {
        "structureId": "STR-VN-FLY-01",
        "structureName": "Viman Nagar Corridor Flyover",
        "spanId": "SPAN-01-EB",
        "sensorId": "SENSOR-SHM-EB-03",
        "observedAt": datetime.now(timezone.utc).isoformat(),
        "vibrationPPV": {"value": 3.2, "unit": "mm/s", "qualityScore": 0.99},
        "strain": {"value": 510.0, "unit": "microstrain", "qualityScore": 0.99},
        "resonantFreqHz": {"value": 3.40, "baselineHz": 4.25, "driftPct": 0.4},
        "ambientTempC": 28.0,
        "hcvAxleLoadTonnes": 8.5,
        "provenance": {"sourceMode": "LIVE", "sensorType": "FBG_OPTICAL_PIEZO"},
    }
    packet.update(overrides)
    return packet


def test_computed_drift_replaces_caller_drift_and_is_not_nominal():
    """3.40 Hz against a 4.25 Hz baseline is -20.0 percent, even if the caller sends 0.4."""
    response = client.post("/api/v1/shm/telemetry", json=_nominal_packet(), headers=_auth_header())
    assert response.status_code == 201
    body = response.json()
    assert body["resonantDriftPct"] == -20.0
    assert body["integrityStatus"] != "NOMINAL"
    assert body["integrityStatus"] == "ADVISORY_FATIGUE"


def test_future_shm_timestamp_is_rejected():
    future = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    response = client.post(
        "/api/v1/shm/telemetry",
        json=_nominal_packet(observedAt=future, structureId="STR-FUTURE-01"),
        headers=_auth_header(),
    )
    assert response.status_code == 422
    assert "INVALID" in response.json()["detail"]


def test_shm_ingest_requires_a_session():
    response = client.post("/api/v1/shm/telemetry", json=_nominal_packet())
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_shm_packet_does_not_replace_segment_metrics():
    segment_id = "urn:ngsi-ld:RoadSegment:PROOF:SEG-01"
    original_metrics = {"averageSpeedKmh": 18.0, "queueLengthMeters": 410.0}
    observed = datetime.now(timezone.utc).isoformat()

    async with AsyncSessionLocal() as session:
        await session.execute(
            text("""
                INSERT INTO entity_current_state (
                    entity_id, entity_type, source_mode, observed_at, updated_at,
                    metrics, quality_status, freshness_seconds
                ) VALUES (
                    :entity_id, :entity_type, :source_mode, :observed_at, :updated_at,
                    :metrics, 'VALID', 0.0
                )
                ON CONFLICT(entity_id) DO UPDATE SET
                    entity_type = excluded.entity_type,
                    source_mode = excluded.source_mode,
                    metrics = excluded.metrics
            """),
            {
                "entity_id": segment_id,
                "entity_type": "RoadSegment",
                "source_mode": "LIVE",
                "observed_at": observed,
                "updated_at": observed,
                "metrics": json.dumps(original_metrics),
            },
        )
        await session.commit()

    response = client.post(
        "/api/v1/shm/telemetry",
        json=_nominal_packet(structureId=segment_id),
        headers=_auth_header(),
    )
    assert response.status_code == 422

    async with AsyncSessionLocal() as session:
        row = (await session.execute(
            text("SELECT entity_type, source_mode, metrics FROM entity_current_state WHERE entity_id = :id"),
            {"id": segment_id},
        )).fetchone()

    assert row is not None
    assert row[0] == "RoadSegment"
    assert row[1] == "LIVE"
    stored = json.loads(row[2]) if isinstance(row[2], str) else row[2]
    assert stored["averageSpeedKmh"] == 18.0
    assert stored["queueLengthMeters"] == 410.0


def test_unregistered_sensor_cannot_store_live():
    response = client.post(
        "/api/v1/shm/telemetry",
        json=_nominal_packet(
            structureId="STR-UNREGISTERED-01",
            sensorId="SENSOR-SHM-UNKNOWN",
            resonantFreqHz={"value": 4.20, "baselineHz": 4.25, "driftPct": -1.18},
        ),
        headers=_auth_header(),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["sourceMode"] == "SIMULATION"
    assert body["integrityStatus"] == "NOMINAL"


def test_unknown_structure_status_is_not_a_fabricated_reading():
    response = client.get("/api/v1/shm/structures/STR-DOES-NOT-EXIST/status")
    assert response.status_code == 404
    body = response.text
    assert "480.0" not in body
    assert "2.85" not in body
    assert "28.5" not in body


@pytest.mark.asyncio
async def test_empty_telemetry_catalog_does_not_invent_readings():
    async with AsyncSessionLocal() as session:
        await session.execute(text("DELETE FROM shm_telemetry"))
        await session.commit()
        summaries = await shm_service.get_monitored_structures(session)
    assert summaries == []

    response = client.get("/api/v1/shm/structures")
    assert response.status_code == 200
    assert response.json() == []
    raw = response.text
    assert "520.5" not in raw
    assert "3.42" not in raw
    assert "-1.18" not in raw
