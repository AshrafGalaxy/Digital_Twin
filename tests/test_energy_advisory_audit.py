"""
test_energy_advisory_audit.py

Hermetic unit and integration tests for Human-in-the-Loop Demand-Response Advisory Dossiers,
Physical Safety Interlocks, and Dual-Key Operator Dispatch Authorization (TASK-10 / GitHub #22).
Tests dossier generation, interlock compliance, SHA-256 tamper-evident hash signing,
and Table 29 (advisory_audit_log) database persistence.
"""

import hashlib
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.core.database import AsyncSessionLocal
from backend.main import app
from backend.schemas.energy_advisory import (
    AdvisoryStatus,
    AuthorizeEnergyAdvisoryRequest,
    EnergyOfficerCredentials,
    SafetyInterlocks,
)
from backend.services.energy_advisory_service import (
    EnergyAdvisoryService,
    energy_advisory_service,
    interlock_status_mask,
)

client = TestClient(app)


def _get_energy_auth_header():
    """Helper to retrieve authenticated Bearer token for Energy Grid Manager."""
    res = client.post("/api/v1/auth/login", json={
        "username_or_email": "grid.manager@pmc.gov.in",
        "password": "energy123"
    })
    assert res.status_code == 200
    token = res.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_energy_advisory_service_initialization():
    """
    Verifies that the EnergyAdvisoryService seeds baseline demand response dossiers
    with realistic physical, economic, and safety constraints.
    """
    service = EnergyAdvisoryService()
    advisories = service.list_advisories()
    assert len(advisories) >= 1

    phoenix_adv = advisories[0]
    assert phoenix_adv.advisoryId == "ADVISORY-DR-20261023-001"
    assert phoenix_adv.status == AdvisoryStatus.PENDING_REVIEW
    assert phoenix_adv.projectedSavingsInr == 18450.0
    assert phoenix_adv.peakReductionKw == 840.0
    assert phoenix_adv.batteryWearCycles == 0.082
    assert phoenix_adv.avoidedCarbonKg == 620.0
    assert len(phoenix_adv.schedule) == 5


def test_physical_safety_interlock_verification():
    """
    Verifies that all 4 physical safety interlocks are compliant:
    1. Feeder line voltage within 415V +/- 6% (390.1V - 439.9V).
    2. Inverter slew rate throttled <= 10%/min.
    3. Battery SoC bounded >= 20% floor.
    4. Occupant thermal comfort preserves ASHRAE 55 <= 25.5 deg C.
    """
    service = EnergyAdvisoryService()
    adv = service.get_advisory("ADVISORY-DR-20261023-001")
    assert adv is not None

    checks = adv.safetyChecks
    assert checks.voltageCompliant is True
    assert 390.1 <= checks.voltageValueV <= 439.9

    assert checks.rampRateCompliant is True
    assert checks.rampRatePctPerMin <= 10.0

    assert checks.socBounded is True
    assert checks.currentSocPct >= 20.0

    assert checks.comfortPreserved is True
    assert checks.projectedIndoorTempC <= 25.5


def test_api_list_and_get_energy_advisories():
    """
    Verifies REST API endpoints:
    - GET /api/v1/energy/advisories
    - GET /api/v1/energy/advisories/{id}
    """
    # List advisories
    res = client.get("/api/v1/energy/advisories")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["advisoryId"] == "ADVISORY-DR-20261023-001"

    # Detail view
    res_detail = client.get("/api/v1/energy/advisories/ADVISORY-DR-20261023-001")
    assert res_detail.status_code == 200
    dossier = res_detail.json()
    assert dossier["facilityId"] == "urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01"
    assert dossier["peakReductionKw"] == 840.0
    assert dossier["safetyChecks"]["voltageCompliant"] is True
    assert len(dossier["schedule"]) == 5

    # Not found
    res_404 = client.get("/api/v1/energy/advisories/NONEXISTENT-ADV-999")
    assert res_404.status_code == 404


@pytest.mark.asyncio
async def test_dual_key_authorization_and_tamper_evident_audit():
    """
    Verifies the complete dual-key authorization workflow:
    - Authorizes advisory with authenticated dual-officer credentials and justification notes.
    - Computes SHA-256 cryptographic hash.
    - Generates OpenADR 2.0b and Modbus dispatch tickets.
    - Persists an immutable record to Table 29 (advisory_audit_log).
    """
    headers = _get_energy_auth_header()
    payload = {
        "primaryOfficer": {
            "officerName": "Chief Facility Energy Manager",
            "badgeId": "FAC-ENG-8021",
            "department": "Commercial Facility Microgrid Management"
        },
        "concurringOfficer": {
            "officerName": "Municipal Grid Interconnection Supervisor",
            "badgeId": "GRID-SUP-3044",
            "department": "Municipal Energy & Power Distribution Cell"
        },
        "shiftId": "SHIFT-EVENING-B",
        "decision": "AUTHORIZED",
        "notes": "Authorized 840 kW peak shaving for evening TOD tariff window."
    }

    res = client.post("/api/v1/energy/advisories/ADVISORY-DR-20261023-001/authorize", json=payload, headers=headers)
    assert res.status_code == 200
    work_order = res.json()

    assert work_order["advisoryId"] == "ADVISORY-DR-20261023-001"
    assert "Chief Facility Energy Manager" in work_order["authorizedBy"]
    assert "FAC-ENG-8021" in work_order["badgeId"]
    assert "GRID-SUP-3044" in work_order["badgeId"]
    assert work_order["decision"] == "AUTHORIZED"
    assert work_order["dispatchOrderId"].startswith("EDO-")

    # Verify SHA-256 hash length and format (64 hex characters)
    tamper_hash = work_order["tamperEvidentHash"]
    assert len(tamper_hash) == 64
    assert int(tamper_hash, 16) > 0  # Valid hex integer

    # Verify OpenADR 2.0b payload
    assert "eiEvent" in work_order["openAdrPayload"]
    event_desc = work_order["openAdrPayload"]["eiEvent"]["eventDescriptor"]
    assert event_desc["eventID"] == work_order["dispatchOrderId"]

    # Verify Modbus registers
    assert "40001_bess_power_setpoint_kw" in work_order["modbusRegisters"]
    assert work_order["modbusRegisters"]["40001_bess_power_setpoint_kw"] == 450
    assert work_order["modbusRegisters"]["40002_bess_inverter_mode"] == 2
    assert work_order["modbusRegisters"]["40004_interlock_status_flags"] == 15

    # Verify persistent audit trail record in Table 29 (advisory_audit_log)
    async with AsyncSessionLocal() as session:
        audit_res = await session.execute(
            text("SELECT audit_id, recommendation_id, action_type, authorized_by, badge_id, tamper_evident_hash FROM advisory_audit_log WHERE recommendation_id = :rec_id ORDER BY created_at DESC LIMIT 1"),
            {"rec_id": "ADVISORY-DR-20261023-001"}
        )
        row = audit_res.fetchone()
        assert row is not None
        assert row[1] == "ADVISORY-DR-20261023-001"
        assert row[2] == "ENERGY_DEMAND_RESPONSE_AUTHORIZATION"
        assert "Chief Facility Energy Manager" in row[3]
        assert "FAC-ENG-8021" in row[4]
        assert row[5] == tamper_hash

    # Retrieve dispatch ticket via endpoint
    ticket_res = client.get("/api/v1/energy/advisories/ADVISORY-DR-20261023-001/dispatch-ticket")
    assert ticket_res.status_code == 200
    ticket_data = ticket_res.json()
    assert ticket_data["dispatchOrderId"] == work_order["dispatchOrderId"]
    assert ticket_data["tamperEvidentHash"] == tamper_hash


def test_energy_authorize_unauthenticated_rejection():
    """Verifies that authorizing energy advisory without Bearer token returns 401."""
    payload = {
        "primaryOfficer": {
            "officerName": "Chief Facility Energy Manager",
            "badgeId": "FAC-ENG-8021"
        },
        "concurringOfficer": {
            "officerName": "Municipal Grid Interconnection Supervisor",
            "badgeId": "GRID-SUP-3044"
        },
        "shiftId": "SHIFT-A",
        "decision": "AUTHORIZED"
    }
    res = client.post("/api/v1/energy/advisories/ADVISORY-DR-20261023-001/authorize", json=payload)
    assert res.status_code == 401


def test_energy_authorize_identical_officer_rejection():
    """Verifies that initiating engineer and concurring supervisor cannot be identical (HTTP 400)."""
    headers = _get_energy_auth_header()
    payload = {
        "primaryOfficer": {
            "officerName": "Chief Facility Energy Manager",
            "badgeId": "FAC-ENG-8021"
        },
        "concurringOfficer": {
            "officerName": "Chief Facility Energy Manager",
            "badgeId": "FAC-ENG-8021"
        },
        "shiftId": "SHIFT-A",
        "decision": "AUTHORIZED"
    }
    res = client.post("/api/v1/energy/advisories/ADVISORY-DR-20261023-001/authorize", json=payload, headers=headers)
    assert res.status_code == 400
    assert "cannot be identical" in res.json()["detail"]


def test_interlock_mask_tracks_each_boolean():
    """Register 40004 is 15 only when every interlock passes."""
    passing = SafetyInterlocks()
    assert interlock_status_mask(passing) == 15
    failed = passing.model_copy(update={
        "voltageCompliant": False,
        "rampRateCompliant": False,
        "socBounded": False,
        "comfortPreserved": False,
    })
    assert interlock_status_mask(failed) == 0
    voltage_only = passing.model_copy(update={
        "rampRateCompliant": False,
        "socBounded": False,
        "comfortPreserved": False,
    })
    assert interlock_status_mask(voltage_only) == 1


def test_energy_authorize_rejects_failed_interlock():
    """A failed interlock returns 409 and does not serialize the all-pass mask."""
    headers = _get_energy_auth_header()
    dossier = energy_advisory_service.get_advisory("ADVISORY-DR-20261023-001")
    assert dossier is not None
    original = dossier.safetyChecks
    status_before = dossier.status
    order_before = dossier.dispatchOrderId
    dossier.safetyChecks = original.model_copy(update={
        "voltageCompliant": False,
        "rampRateCompliant": False,
        "socBounded": False,
        "comfortPreserved": False,
    })
    payload = {
        "primaryOfficer": {
            "officerName": "Chief Facility Energy Manager",
            "badgeId": "FAC-ENG-8021",
        },
        "concurringOfficer": {
            "officerName": "Municipal Grid Interconnection Supervisor",
            "badgeId": "GRID-SUP-3044",
        },
        "shiftId": "SHIFT-EVENING-B",
        "decision": "AUTHORIZED",
        "notes": "Must be refused.",
    }
    try:
        res = client.post(
            "/api/v1/energy/advisories/ADVISORY-DR-20261023-001/authorize",
            json=payload,
            headers=headers,
        )
        assert res.status_code == 409
        assert "40004_interlock_status_flags" not in res.text
        body = res.json()
        assert "interlock" in body["detail"]
        assert dossier.status == status_before
        assert dossier.dispatchOrderId == order_before
    finally:
        dossier.safetyChecks = original
