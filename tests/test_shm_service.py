"""
test_shm_service.py

Hermetic unit and integration tests for the Critical Infrastructure Structural Health
Monitoring (SHM) Telemetry Pipeline (TASK-07 / Section 10.1).
Tests sensor telemetry bounds validation, resonant frequency drift fatigue alerts,
fiber-optic microstrain yield warnings, Weigh-in-Motion axle overloads, and REST API endpoints.
"""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.core.database import AsyncSessionLocal
from backend.main import app
from backend.schemas.shm import SHMReadingValue, ResonantFreqReading, SHMTelemetryPayload
from backend.services.shm_service import SHMTelemetryService, shm_service

client = TestClient(app)


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
    # 1. List structures
    resp = client.get("/api/v1/shm/structures")
    assert resp.status_code == 200
    structures = resp.json()
    assert isinstance(structures, list)
    assert len(structures) >= 1

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
    post_resp = client.post("/api/v1/shm/telemetry", json=sample_payload)
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
    bad_resp = client.post("/api/v1/shm/telemetry", json=bad_payload)
    assert bad_resp.status_code == 422
