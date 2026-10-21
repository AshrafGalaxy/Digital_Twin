"""
test_energy_topology.py

Hermetic unit and integration tests for the Canonical Electrical Network Topology &
Multi-Asset Telemetry Engine (Energy TASK-01).
Tests AC electrical physics, diurnal solar curves, BESS dynamics, EV hub simulations,
network hierarchy graph traversal, and REST endpoints.
"""

import math
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.energy_topology_service import EnergyTopologyService, energy_topology_service
from backend.core.database import AsyncSessionLocal

client = TestClient(app)


def test_three_phase_ac_physics():
    """
    Verifies 3-phase AC power physics formulas:
    S = sqrt(P^2 + Q^2)
    PF = abs(P / S)
    I = (S * 1000) / (sqrt(3) * V)
    """
    service = EnergyTopologyService()
    # 400 kW active, 300 kVAR reactive at 415 V line-to-line
    res = service.calculate_ac_physics(
        active_power_kw=400.0,
        reactive_power_kvar=300.0,
        nominal_voltage_v=415.0,
        phase_count=3
    )

    expected_s = math.sqrt(400.0**2 + 300.0**2)  # 500.0 kVA
    expected_pf = 400.0 / 500.0  # 0.80
    expected_i = (expected_s * 1000.0) / (math.sqrt(3.0) * 415.0)  # ~695.6 A

    assert res["activePowerKw"] == 400.0
    assert res["reactivePowerKvar"] == 300.0
    assert abs(res["apparentPowerKva"] - expected_s) < 0.1
    assert abs(res["powerFactor"] - expected_pf) < 0.005
    assert abs(res["currentA"] - expected_i) < 0.5


def test_diurnal_solar_generation():
    """
    Verifies that solar generation accurately follows the diurnal sun curve:
    Zero generation at night, peak generation near solar noon.
    """
    service = EnergyTopologyService()
    rated_kwp = 1200.0

    # Midnight (01:00 UTC) -> Zero generation
    night_time = datetime(2026, 10, 21, 1, 0, 0, tzinfo=timezone.utc)
    night_res = service.simulate_diurnal_solar_kw(rated_kwp, night_time)
    assert night_res["activePowerKw"] == 0.0
    assert night_res["irradianceWm2"] == 0.0

    # Solar Noon (12:30 UTC) -> Peak generation (> 75% of rated capacity)
    noon_time = datetime(2026, 10, 21, 12, 30, 0, tzinfo=timezone.utc)
    noon_res = service.simulate_diurnal_solar_kw(rated_kwp, noon_time)
    assert noon_res["activePowerKw"] > 800.0
    assert noon_res["irradianceWm2"] > 800.0
    assert noon_res["inverterEfficiencyPct"] >= 95.0


def test_bess_charge_discharge_dynamics():
    """
    Verifies BESS charge absorption during high solar generation and
    discharge support during evening peak hours.
    """
    service = EnergyTopologyService()

    # High solar scenario (13:00, 800 kW solar) -> BESS charges (P < 0)
    charge_res = service.simulate_bess_dynamics(solar_active_kw=800.0, hour=13.0, dt_sec=10.0)
    assert charge_res["operatingMode"] == "CHARGING"
    assert charge_res["activePowerKw"] < 0.0

    # Evening peak scenario (19:30, 0 kW solar) -> BESS discharges (P > 0)
    service._bess_soc_pct = 75.0
    discharge_res = service.simulate_bess_dynamics(solar_active_kw=0.0, hour=19.5, dt_sec=10.0)
    assert discharge_res["operatingMode"] == "DISCHARGING"
    assert discharge_res["activePowerKw"] > 0.0


def test_ev_hub_charging_dynamics():
    """
    Verifies EV charging plaza vehicle arrivals and active plug power.
    """
    service = EnergyTopologyService()
    ev_res = service.simulate_ev_hub_dynamics(hour=18.0, total_plugs=12, plug_capacity_kw=60.0)
    assert 1 <= ev_res["activePlugs"] <= 12
    assert ev_res["activePowerKw"] > 0.0
    assert 0.0 < ev_res["utilizationRatePct"] <= 100.0


@pytest.mark.asyncio
async def test_topology_graph_hierarchy():
    """
    Verifies the electrical single-line hierarchy graph:
    Substation -> Feeders -> Connected Assets.
    """
    tree = await energy_topology_service.get_topology_tree()
    assert tree["totalNodes"] == 10
    sub = tree["substation"]
    assert sub is not None
    assert sub["nodeType"] == "SUBSTATION"
    assert sub["nominalVoltageKv"] == 22.0

    # Substation must have 3 11kV distribution feeders
    feeders = sub["children"]
    assert len(feeders) == 3
    for f in feeders:
        assert f["nodeType"] == "FEEDER"
        assert f["nominalVoltageKv"] == 11.0
        # Each feeder must have endpoint children
        assert len(f["children"]) > 0


@pytest.mark.asyncio
async def test_telemetry_tick_generation_and_persistence():
    """
    Verifies that generate_telemetry_tick() generates valid 3-phase readings
    for all 10 nodes and persists records to the database.
    """
    async with AsyncSessionLocal() as session:
        records = await energy_topology_service.generate_telemetry_tick(session=session)
        assert len(records) == 10
        for r in records:
            assert "assetId" in r
            assert "activePowerKw" in r
            assert "apparentPowerKva" in r
            assert "powerFactor" in r
            assert 0.0 <= r["powerFactor"] <= 1.0
            assert 49.5 <= r["frequencyHz"] <= 50.5
            assert r["sourceMode"] == "SIMULATION"
            assert r["qualityStatus"] == "VALID"


# ============================================================================
# API Endpoint Tests
# ============================================================================

def test_api_get_energy_topology():
    """Verifies GET /api/v1/energy/topology returns the full microgrid tree."""
    res = client.get("/api/v1/energy/topology")
    assert res.status_code == 200
    data = res.json()
    assert "substation" in data
    assert data["totalNodes"] == 10


def test_api_get_live_energy_telemetry():
    """Verifies GET /api/v1/energy/telemetry/live returns latest 3-phase telemetry."""
    res = client.get("/api/v1/energy/telemetry/live")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 10
    first = data[0]
    assert "assetId" in first
    assert "activePowerKw" in first
    assert "powerFactor" in first
    assert "currentA" in first


def test_api_get_microgrid_summary():
    """Verifies GET /api/v1/energy/summary computes corridor power balance."""
    res = client.get("/api/v1/energy/summary")
    assert res.status_code == 200
    data = res.json()
    assert "gridImportKw" in data
    assert "solarGenerationKw" in data
    assert "bessPowerKw" in data
    assert "bessStateOfChargePct" in data
    assert "netPowerFactor" in data
    assert 0.70 <= data["netPowerFactor"] <= 1.00


def test_api_get_telemetry_history():
    """Verifies GET /api/v1/energy/telemetry/history returns historical series for an asset."""
    res = client.get("/api/v1/energy/telemetry/history?asset_id=AST-PV-PHOENIX-01&limit=10")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["assetId"] == "AST-PV-PHOENIX-01"


def test_api_trigger_telemetry_tick():
    """Verifies POST /api/v1/energy/telemetry/tick advances simulation and returns records."""
    res = client.post("/api/v1/energy/telemetry/tick")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 10
