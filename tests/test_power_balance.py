"""
test_power_balance.py

Hermetic unit and integration tests for the Electrical Bus Power Balance &
Feeder Thermal Loading Engine (Energy TASK-02).
Tests Kirchhoff power conservation closure, branch ampacity thermal loading thresholds,
technical line distribution losses, and REST API endpoints.
"""

import math
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.core.database import AsyncSessionLocal
from backend.main import app
from backend.services.power_balance_service import PowerBalanceService, power_balance_service

client = TestClient(app)


def test_feeder_thermal_loading_thresholds():
    """
    Verifies that branch thermal loading ratio maps accurately to operational status:
    - ratio < 0.75: NOMINAL
    - 0.75 <= ratio < 0.90: WARNING
    - ratio >= 0.90: CRITICAL_OVERLOAD_RISK
    """
    service = PowerBalanceService()

    # Nominal range
    assert service.evaluate_feeder_thermal_status(0.50) == "NOMINAL"
    assert service.evaluate_feeder_thermal_status(0.749) == "NOMINAL"

    # Warning range
    assert service.evaluate_feeder_thermal_status(0.75) == "WARNING"
    assert service.evaluate_feeder_thermal_status(0.85) == "WARNING"
    assert service.evaluate_feeder_thermal_status(0.899) == "WARNING"

    # Critical overload risk
    assert service.evaluate_feeder_thermal_status(0.90) == "CRITICAL_OVERLOAD_RISK"
    assert service.evaluate_feeder_thermal_status(0.98) == "CRITICAL_OVERLOAD_RISK"
    assert service.evaluate_feeder_thermal_status(1.15) == "CRITICAL_OVERLOAD_RISK"


def test_branch_technical_loss_and_headroom_math():
    """
    Verifies 3-phase technical line loss (3 * I^2 * R / 1000)
    and available active power headroom (sqrt(3) * V * (I_rated - I) * PF / 1000).
    """
    service = PowerBalanceService()

    # 1. Test technical loss for 1000A through 0.05 Ohm conductor
    # P_loss = 3 * (1000^2) * 0.05 / 1000 = 150.0 kW
    loss_kw = service.calculate_branch_loss_kw(current_amps=1000.0, resistance_ohm=0.05)
    assert abs(loss_kw - 150.0) < 0.01

    # 2. Test headroom for 2200A rated bus loaded at 1800A at 415V, PF 0.95
    # Headroom = sqrt(3) * 415 * (2200 - 1800) * 0.95 / 1000 = ~273.1 kW
    expected_headroom = (math.sqrt(3.0) * 415.0 * 400.0 * 0.95) / 1000.0
    calc_headroom = service.calculate_headroom_kw(
        rated_current_amps=2200.0,
        actual_current_amps=1800.0,
        line_voltage_v=415.0,
        power_factor=0.95
    )
    assert abs(calc_headroom - expected_headroom) < 0.2

    # Zero headroom when overloaded
    zero_headroom = service.calculate_headroom_kw(
        rated_current_amps=1000.0,
        actual_current_amps=1200.0,
        line_voltage_v=415.0,
        power_factor=0.95
    )
    assert zero_headroom == 0.0


@pytest.mark.asyncio
async def test_power_balance_calculation():
    """
    Verifies that calculate_power_balance executes successfully,
    returns valid physical quantities, and includes feeder thermal margins.
    """
    res = await power_balance_service.calculate_power_balance()

    assert "substationId" in res
    assert "timestamp" in res
    assert "pccGridImportKw" in res
    assert res["pccGridImportKw"] >= 0.0
    assert "solarGenerationKw" in res
    assert "bessNetPowerKw" in res
    assert "facilityTotalLoadKw" in res
    assert "technicalLossesKw" in res
    assert res["technicalLossesKw"] >= 0.0
    assert "powerBalanceResidualKw" in res
    assert "feeders" in res
    assert len(res["feeders"]) >= 1

    # Validate feeder item attributes
    feeder = res["feeders"][0]
    assert "feederId" in feeder
    assert "thermalLoadingRatio" in feeder
    assert "thermalLoadingPct" in feeder
    assert "status" in feeder
    assert feeder["status"] in ("NOMINAL", "WARNING", "CRITICAL_OVERLOAD_RISK")
    assert "availableHeadroomKw" in feeder


def test_api_power_balance_endpoints():
    """
    Tests REST API endpoints:
    - GET /api/v1/energy/power-balance
    - POST /api/v1/energy/power-balance/snapshot
    - GET /api/v1/energy/feeders/thermal-margins
    - GET /api/v1/energy/power-balance/history
    """
    # 1. GET /power-balance
    resp = client.get("/api/v1/energy/power-balance")
    assert resp.status_code == 200
    data = resp.json()
    assert "pccGridImportKw" in data
    assert "feeders" in data
    assert len(data["feeders"]) >= 1

    # 2. POST /power-balance/snapshot
    resp_snap = client.post("/api/v1/energy/power-balance/snapshot")
    assert resp_snap.status_code == 200
    snap_data = resp_snap.json()
    assert "powerBalanceResidualKw" in snap_data

    # 3. GET /feeders/thermal-margins
    resp_feeders = client.get("/api/v1/energy/feeders/thermal-margins")
    assert resp_feeders.status_code == 200
    feeders = resp_feeders.json()
    assert isinstance(feeders, list)
    assert len(feeders) >= 1
    assert "thermalLoadingRatio" in feeders[0]
    assert "availableHeadroomKw" in feeders[0]

    # 4. GET /power-balance/history
    resp_hist = client.get("/api/v1/energy/power-balance/history?limit=10")
    assert resp_hist.status_code == 200
    hist = resp_hist.json()
    assert isinstance(hist, list)
    assert len(hist) >= 1


async def _insert_bus(nodes, readings):
    observed = datetime.now(timezone.utc).isoformat()
    async with AsyncSessionLocal() as session:
        for node in nodes:
            await session.execute(text("""
                INSERT INTO energy_network_nodes (
                    node_id, study_area_id, name, node_type, parent_node_id,
                    nominal_voltage_kv, rated_capacity_kva, rated_current_amps,
                    phase_count, coordinates, properties
                ) VALUES (
                    :node_id, NULL, :name, :node_type, :parent_node_id,
                    :nominal_voltage_kv, :rated_capacity_kva, :rated_current_amps,
                    3, NULL, '{}'
                )
            """), node)
        for reading in readings:
            await session.execute(text("""
                INSERT INTO energy_asset_telemetry (
                    asset_id, observed_at, source_mode, active_power_kw,
                    reactive_power_kvar, apparent_power_kva, power_factor,
                    voltage_v, current_a, frequency_hz, voltage_unbalance_pct,
                    current_unbalance_pct, device_metrics_json, quality_status
                ) VALUES (
                    :asset_id, :observed_at, 'SIMULATION', :p, 0, :p, 1,
                    :voltage_v, :current_a, 50.0, 0.4, 1.1, '{}', 'VALID'
                )
            """), {**reading, "observed_at": observed})
        await session.commit()


async def _delete_bus(node_ids):
    async with AsyncSessionLocal() as session:
        for node_id in node_ids:
            await session.execute(
                text("DELETE FROM energy_asset_telemetry WHERE asset_id = :id"),
                {"id": node_id},
            )
        for node_id in reversed(node_ids):
            await session.execute(
                text("DELETE FROM energy_network_nodes WHERE node_id = :id"),
                {"id": node_id},
            )
        await session.commit()


def test_unknown_substation_is_not_replaced():
    """An unknown substation id is rejected and does not return another substation."""
    resp = client.get("/api/v1/energy/power-balance?substation_id=SUB-DOES-NOT-EXIST")
    assert resp.status_code == 404
    assert "SUB-NR-22KV" not in resp.text


@pytest.mark.asyncio
async def test_signed_residual_above_share_is_not_valid():
    """A supply surplus near 1554.09 kW keeps its sign and is not labeled VALID."""
    substation_id = "SUB-PROOF-SURPLUS"
    node_ids = [
        substation_id,
        "FDR-PROOF-A",
        "FDR-PROOF-B",
        "FDR-PROOF-C",
        "AST-PROOF-PV",
        "AST-PROOF-BESS",
        "AST-PROOF-LOAD",
    ]
    nodes = [
        {"node_id": substation_id, "name": "Proof substation", "node_type": "SUBSTATION", "parent_node_id": None, "nominal_voltage_kv": 22.0, "rated_capacity_kva": 15000.0, "rated_current_amps": 400.0},
        {"node_id": "FDR-PROOF-A", "name": "Proof feeder A", "node_type": "FEEDER", "parent_node_id": substation_id, "nominal_voltage_kv": 11.0, "rated_capacity_kva": 5000.0, "rated_current_amps": 262.43},
        {"node_id": "FDR-PROOF-B", "name": "Proof feeder B", "node_type": "FEEDER", "parent_node_id": substation_id, "nominal_voltage_kv": 11.0, "rated_capacity_kva": 5000.0, "rated_current_amps": 262.43},
        {"node_id": "FDR-PROOF-C", "name": "Proof feeder C", "node_type": "FEEDER", "parent_node_id": substation_id, "nominal_voltage_kv": 11.0, "rated_capacity_kva": 5000.0, "rated_current_amps": 262.43},
        {"node_id": "AST-PROOF-PV", "name": "Proof solar", "node_type": "SOLAR_PV", "parent_node_id": substation_id, "nominal_voltage_kv": 0.415, "rated_capacity_kva": 1200.0, "rated_current_amps": 100.0},
        {"node_id": "AST-PROOF-BESS", "name": "Proof storage", "node_type": "BESS", "parent_node_id": substation_id, "nominal_voltage_kv": 0.415, "rated_capacity_kva": 1250.0, "rated_current_amps": 100.0},
        {"node_id": "AST-PROOF-LOAD", "name": "Proof load", "node_type": "BUILDING_LOAD", "parent_node_id": substation_id, "nominal_voltage_kv": 0.415, "rated_capacity_kva": 3000.0, "rated_current_amps": 100.0},
    ]
    readings = [
        {"asset_id": substation_id, "p": 6250.0, "voltage_v": 22000.0, "current_a": 164.0},
        {"asset_id": "FDR-PROOF-A", "p": 2180.0, "voltage_v": 11000.0, "current_a": 119.86},
        {"asset_id": "FDR-PROOF-B", "p": 2450.0, "voltage_v": 11000.0, "current_a": 134.03},
        {"asset_id": "FDR-PROOF-C", "p": 1620.0, "voltage_v": 11000.0, "current_a": 89.79},
        {"asset_id": "AST-PROOF-PV", "p": 780.0, "voltage_v": 415.0, "current_a": 10.0},
        {"asset_id": "AST-PROOF-BESS", "p": -250.0, "voltage_v": 415.0, "current_a": 5.0},
        {"asset_id": "AST-PROOF-LOAD", "p": 5220.0, "voltage_v": 415.0, "current_a": 20.0},
    ]
    try:
        await _insert_bus(nodes, readings)
        resp = client.get(f"/api/v1/energy/power-balance?substation_id={substation_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["substationId"] == substation_id
        assert data["pccGridImportKw"] == 6250.0
        assert data["solarGenerationKw"] == 780.0
        assert data["bessNetPowerKw"] == -250.0
        assert data["facilityTotalLoadKw"] == 5220.0
        assert data["technicalLossesKw"] == 5.91
        assert data["powerBalanceResidualKw"] == 1554.09
        assert data["powerBalanceResidualKw"] > 0
        assert data["residualShare"] > data["residualShareThreshold"]
        assert data["provenance"]["qualityStatus"] != "VALID"
        assert data["gridMeterStatus"] == "MEASURED"
    finally:
        await _delete_bus(node_ids)


@pytest.mark.asyncio
async def test_zero_grid_meter_is_not_back_solved():
    """A measured zero import stays zero and the deficit keeps a negative sign."""
    substation_id = "SUB-PROOF-ZERO"
    node_ids = [substation_id, "AST-PROOF-ZERO-PV", "AST-PROOF-ZERO-LOAD"]
    nodes = [
        {"node_id": substation_id, "name": "Zero meter substation", "node_type": "SUBSTATION", "parent_node_id": None, "nominal_voltage_kv": 22.0, "rated_capacity_kva": 15000.0, "rated_current_amps": 400.0},
        {"node_id": "AST-PROOF-ZERO-PV", "name": "Zero meter solar", "node_type": "SOLAR_PV", "parent_node_id": substation_id, "nominal_voltage_kv": 0.415, "rated_capacity_kva": 200.0, "rated_current_amps": 100.0},
        {"node_id": "AST-PROOF-ZERO-LOAD", "name": "Zero meter load", "node_type": "BUILDING_LOAD", "parent_node_id": substation_id, "nominal_voltage_kv": 0.415, "rated_capacity_kva": 500.0, "rated_current_amps": 100.0},
    ]
    readings = [
        {"asset_id": substation_id, "p": 0.0, "voltage_v": 22000.0, "current_a": 0.0},
        {"asset_id": "AST-PROOF-ZERO-PV", "p": 100.0, "voltage_v": 415.0, "current_a": 1.0},
        {"asset_id": "AST-PROOF-ZERO-LOAD", "p": 400.0, "voltage_v": 415.0, "current_a": 2.0},
    ]
    try:
        await _insert_bus(nodes, readings)
        resp = client.get(f"/api/v1/energy/power-balance?substation_id={substation_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["substationId"] == substation_id
        assert data["gridMeterStatus"] == "MEASURED"
        assert data["pccGridImportKw"] == 0.0
        assert data["powerBalanceResidualKw"] == -300.0
        assert data["provenance"]["qualityStatus"] != "VALID"
    finally:
        await _delete_bus(node_ids)


@pytest.mark.asyncio
async def test_missing_grid_meter_is_not_invented():
    """A substation with no grid meter is reported missing and is not back-solved."""
    substation_id = "SUB-PROOF-MISSING"
    node_ids = [substation_id, "AST-PROOF-MISS-PV", "AST-PROOF-MISS-LOAD"]
    nodes = [
        {"node_id": substation_id, "name": "Missing meter substation", "node_type": "SUBSTATION", "parent_node_id": None, "nominal_voltage_kv": 22.0, "rated_capacity_kva": 15000.0, "rated_current_amps": 400.0},
        {"node_id": "AST-PROOF-MISS-PV", "name": "Missing meter solar", "node_type": "SOLAR_PV", "parent_node_id": substation_id, "nominal_voltage_kv": 0.415, "rated_capacity_kva": 200.0, "rated_current_amps": 100.0},
        {"node_id": "AST-PROOF-MISS-LOAD", "name": "Missing meter load", "node_type": "BUILDING_LOAD", "parent_node_id": substation_id, "nominal_voltage_kv": 0.415, "rated_capacity_kva": 500.0, "rated_current_amps": 100.0},
    ]
    readings = [
        {"asset_id": "AST-PROOF-MISS-PV", "p": 100.0, "voltage_v": 415.0, "current_a": 1.0},
        {"asset_id": "AST-PROOF-MISS-LOAD", "p": 400.0, "voltage_v": 415.0, "current_a": 2.0},
    ]
    try:
        await _insert_bus(nodes, readings)
        resp = client.get(f"/api/v1/energy/power-balance?substation_id={substation_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["substationId"] == substation_id
        assert data["gridMeterStatus"] == "MISSING"
        assert data["pccGridImportKw"] is None
        assert data["powerBalanceResidualKw"] == -300.0
        assert data["provenance"]["qualityStatus"] != "VALID"
    finally:
        await _delete_bus(node_ids)


def test_headroom_uses_explicit_voltage_over_registry():
    """calculate_headroom_kw uses line_voltage_v when explicitly provided."""
    svc = PowerBalanceService()
    rated = 262.43
    actual = 130.0
    # With telemetry voltage 11 kV explicitly supplied
    headroom_11kv = svc.calculate_headroom_kw(
        rated_current_amps=rated,
        actual_current_amps=actual,
        line_voltage_v=11000.0,
        power_factor=0.95,
    )
    # With low-voltage fallback 415 V (no telemetry, no registry hint)
    headroom_415v = svc.calculate_headroom_kw(
        rated_current_amps=rated,
        actual_current_amps=actual,
        line_voltage_v=None,
        power_factor=0.95,
    )
    assert headroom_11kv > 0.0
    assert headroom_415v > 0.0
    # 11 kV feeder must report far greater headroom than 415 V LV circuit
    ratio = headroom_11kv / headroom_415v
    assert ratio > 20.0, f"Expected 11kV/415V headroom ratio > 20, got {ratio:.2f}"


def test_headroom_registry_fallback_matches_explicit_voltage():
    """calculate_headroom_kw nominal_voltage_kv fallback matches explicit line_voltage_v."""
    svc = PowerBalanceService()
    rated = 262.43
    actual = 130.0
    nominal_kv = 11.0
    # Explicit voltage passed as line_voltage_v
    h_explicit = svc.calculate_headroom_kw(
        rated_current_amps=rated,
        actual_current_amps=actual,
        line_voltage_v=nominal_kv * 1000.0,
        power_factor=0.95,
    )
    # Same voltage passed via nominal_voltage_kv fallback (no line_voltage_v)
    h_registry = svc.calculate_headroom_kw(
        rated_current_amps=rated,
        actual_current_amps=actual,
        line_voltage_v=None,
        power_factor=0.95,
        nominal_voltage_kv=nominal_kv,
    )
    assert h_explicit == h_registry, (
        f"Registry fallback headroom {h_registry} kW must equal explicit {h_explicit} kW"
    )
