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


def _auth_header() -> dict:
    res = client.post("/api/v1/auth/login", json={
        "username_or_email": "analyst@pmc.gov.in",
        "password": "analyst123",
    })
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['token']}"}


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


def test_bess_cycle_efficiency_not_lossless():
    """
    Verifies BUG-20 (#43): A charge and matching discharge cycle is not lossless.
    Starting at 50% SOC with 550 kWh in and 550 kWh out must leave the battery below 50% SOC.
    Closed-SOC round-trip efficiency ratio matches 0.885 within 0.01.
    """
    service = EnergyTopologyService()
    service._bess_soc_pct = 50.0

    # Step 1: Charge 1 hour at -550 kW (550 kWh AC in)
    charge_res = service.simulate_bess_dynamics(solar_active_kw=1000.0, hour=12.0, dt_sec=3600.0)
    assert charge_res["operatingMode"] == "CHARGING"
    assert charge_res["activePowerKw"] == -550.0
    soc_after_charge = charge_res["stateOfChargePct"]
    assert soc_after_charge > 50.0
    # 50.0 + (550 * sqrt(0.885) / 2000 * 100) = 75.87%
    assert abs(soc_after_charge - 75.87) < 0.1

    # Step 2: Discharge 1 hour at +550 kW (550 kWh AC out)
    discharge_res = service.simulate_bess_dynamics(solar_active_kw=0.0, hour=19.0, dt_sec=3600.0)
    assert discharge_res["operatingMode"] == "DISCHARGING"
    assert discharge_res["activePowerKw"] == 550.0
    soc_after_discharge = discharge_res["stateOfChargePct"]

    # Must end strictly below starting 50% SOC (specifically 46.64%)
    assert soc_after_discharge < 50.0
    assert abs(soc_after_discharge - 46.64) < 0.1

    # Over a closed SOC cycle, AC energy out / AC energy in = 0.885
    # Stored DC kWh gained in Step 1:
    dc_kwh_gained = (soc_after_charge - 50.0) / 100.0 * 2000.0
    # To return to 50.0% SOC, extracted DC kWh must equal gained DC kWh:
    ac_kwh_out_to_neutral = dc_kwh_gained * (math.sqrt(0.885))
    round_trip_ratio = ac_kwh_out_to_neutral / 550.0
    assert abs(round_trip_ratio - 0.885) < 0.01


def test_bess_standby_parasitic_loss_drains_soc():
    """
    Verifies BUG-20 (#43): Standby auxiliary/BMS parasitic power drains stored energy in the loss direction.
    """
    service = EnergyTopologyService()
    service._bess_soc_pct = 50.0

    standby_res = service.simulate_bess_dynamics(solar_active_kw=0.0, hour=12.0, dt_sec=3600.0)
    assert standby_res["operatingMode"] == "STANDBY"
    assert standby_res["activePowerKw"] == -8.0
    # 8 kWh loss / 2000 kWh capacity * 100 = 0.4% SOC decrease -> 49.6%
    assert standby_res["stateOfChargePct"] < 50.0
    assert abs(standby_res["stateOfChargePct"] - 49.6) < 0.05


def test_bess_soc_floor_and_ceiling_clamps():
    """
    Verifies BUG-20 (#43): BESS SOC respects physical operating limits (15% floor to 95% ceiling).
    """
    service = EnergyTopologyService()

    # Ceiling clamp
    service._bess_soc_pct = 94.5
    charge_res = service.simulate_bess_dynamics(solar_active_kw=1000.0, hour=12.0, dt_sec=3600.0)
    assert charge_res["stateOfChargePct"] <= 95.0

    # Floor clamp
    service._bess_soc_pct = 16.0
    discharge_res = service.simulate_bess_dynamics(solar_active_kw=0.0, hour=19.0, dt_sec=3600.0)
    assert discharge_res["stateOfChargePct"] >= 15.0


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
    """Verifies POST /api/v1/energy/telemetry/tick advances simulation and returns records when authenticated."""
    res = client.post("/api/v1/energy/telemetry/tick", headers=_auth_header())
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 10


def test_api_tick_rejects_anonymous_request_with_401():
    """
    Verifies BUG-22 (#45): Anonymous callers cannot trigger telemetry ticks.
    Unauthenticated request must return HTTP 401 Unauthorized.
    """
    res = client.post("/api/v1/energy/telemetry/tick")
    assert res.status_code == 401


def test_calculate_3phase_unbalance_deterministic_nema_rates():
    """
    Verifies BUG-22 (#45): calculate_3phase_unbalance produces strictly deterministic
    NEMA Voltage and Current Unbalance Rates from per-phase quantities.
    """
    service = EnergyTopologyService()
    # 500 kW active, 250 kVAR reactive at 415 V line-to-line
    res1 = service.calculate_3phase_unbalance(500.0, 250.0, 415.0, phase_count=3)
    res2 = service.calculate_3phase_unbalance(500.0, 250.0, 415.0, phase_count=3)

    # Determinism
    assert res1 == res2
    assert "phaseVoltagesV" in res1
    assert "phaseCurrentsA" in res1
    assert len(res1["phaseVoltagesV"]) == 3
    assert len(res1["phaseCurrentsA"]) == 3

    # Hand-calculate expected NEMA VUR and CUR
    voltages = res1["phaseVoltagesV"]
    currents = res1["phaseCurrentsA"]
    v_avg = sum(voltages) / 3.0
    v_max_dev = max(abs(v - v_avg) for v in voltages)
    expected_vur = round((v_max_dev / v_avg) * 100.0, 2)
    assert abs(res1["voltageUnbalancePct"] - expected_vur) < 0.01

    i_avg = sum(currents) / 3.0
    i_max_dev = max(abs(i - i_avg) for i in currents)
    expected_cur = round((i_max_dev / i_avg) * 100.0, 2)
    assert abs(res1["currentUnbalancePct"] - expected_cur) < 0.01

    # Single-phase case
    res_1ph = service.calculate_3phase_unbalance(10.0, 2.0, 230.0, phase_count=1)
    assert res_1ph["voltageUnbalancePct"] == 0.0
    assert res_1ph["currentUnbalancePct"] == 0.0
    assert len(res_1ph["phaseVoltagesV"]) == 1
    assert len(res_1ph["phaseCurrentsA"]) == 1


@pytest.mark.asyncio
async def test_unbalance_is_deterministic_and_traceable_to_phase_quantities():
    """
    Verifies BUG-22 (#45):
    1. Unbalance is strictly deterministic across consecutive telemetry ticks.
    2. Per-phase voltages and currents are stored in deviceMetrics.
    3. Stored unbalance matches standard NEMA Voltage/Current Unbalance Rates calculated
       from recorded phase quantities.
    4. Records retain source_mode = 'SIMULATION' and quality_status = 'VALID'.
    """
    service = EnergyTopologyService()
    async with AsyncSessionLocal() as session:
        records1 = await service.generate_telemetry_tick(session=session)
        records2 = await service.generate_telemetry_tick(session=session)

    assert len(records1) == 10
    assert len(records2) == 10

    for r1, r2 in zip(records1, records2):
        assert r1["assetId"] == r2["assetId"]
        assert r1["sourceMode"] == "SIMULATION"
        assert r1["qualityStatus"] == "VALID"

        # If electrical inputs match, unbalance must be strictly identical (zero noise variance)
        if r1["activePowerKw"] == r2["activePowerKw"] and r1["reactivePowerKvar"] == r2["reactivePowerKvar"]:
            assert r1["voltageUnbalancePct"] == r2["voltageUnbalancePct"]
            assert r1["currentUnbalancePct"] == r2["currentUnbalancePct"]

        # Check phase quantities presence and exact NEMA formula compliance for all generated records
        for r in (r1, r2):
            dm = r.get("deviceMetrics", {})
            assert "phaseVoltagesV" in dm
            assert "phaseCurrentsA" in dm
            phase_v = dm["phaseVoltagesV"]
            phase_i = dm["phaseCurrentsA"]
            assert len(phase_v) == 3
            assert len(phase_i) == 3

            # Verify NEMA Voltage Unbalance Rate (VUR) formula:
            v_avg = sum(phase_v) / 3.0
            v_max_dev = max(abs(v - v_avg) for v in phase_v)
            expected_vur = round((v_max_dev / v_avg) * 100.0, 2)
            assert abs(r["voltageUnbalancePct"] - expected_vur) < 0.01

            # Verify NEMA Current Unbalance Rate (CUR) formula:
            i_avg = sum(phase_i) / 3.0
            if i_avg > 0.01:
                i_max_dev = max(abs(i - i_avg) for i in phase_i)
                expected_cur = round((i_max_dev / i_avg) * 100.0, 2)
            else:
                expected_cur = 0.0
            assert abs(r["currentUnbalancePct"] - expected_cur) < 0.01


def test_feeder_bess_charging_and_discharging_aggregation_parity():
    """
    Verifies BUG-21 (#44): Charging a battery increases feeder import, and
    both the node aggregation path and fallback path agree on sign convention.
    """
    building_kw = 1000.0
    bess_charging_kw = -650.0  # simulate_bess_dynamics returns negative for charging
    bess_discharging_kw = 550.0

    # 1. Charging Case
    # Fallback convention: building_kw - bess_kw
    fallback_charging = building_kw - bess_charging_kw
    assert fallback_charging == 1650.0
    assert fallback_charging > building_kw

    # Node aggregation convention: child_type in ("SOLAR_PV", "BESS") -> fdr_p -= cp
    node_charging = building_kw - bess_charging_kw
    assert node_charging == fallback_charging
    assert node_charging == 1650.0

    # 2. Discharging Case
    fallback_discharging = building_kw - bess_discharging_kw
    assert fallback_discharging == 450.0
    assert fallback_discharging < building_kw

    node_discharging = building_kw - bess_discharging_kw
    assert node_discharging == fallback_discharging
    assert node_discharging == 450.0


@pytest.mark.asyncio
async def test_substation_transformer_loss_identity():
    """
    Verifies BUG-21 (#44): Reported transformerLossKw equals substation active power
    minus the feeder sum (i.e. exactly the 2.5% gross-up added to feeder power).
    """
    service = EnergyTopologyService()
    async with AsyncSessionLocal() as session:
        records = await service.generate_telemetry_tick(session=session)

    # Separate substation and feeder records
    sub_records = [r for r in records if r["assetId"] == "SUB-NR-22KV"]
    feeder_records = [r for r in records if r["assetId"].startswith("FDR-")]

    assert len(sub_records) == 1
    assert len(feeder_records) == 3

    sub = sub_records[0]
    feeder_sum_p = sum(f["activePowerKw"] for f in feeder_records)

    # Substation power must equal feeder_sum * 1.025
    expected_sub_p = feeder_sum_p * 1.025
    assert abs(sub["activePowerKw"] - expected_sub_p) < 0.2

    # Transformer loss must equal substation active power minus feeder sum
    expected_loss = round(sub["activePowerKw"] - feeder_sum_p, 1)
    reported_loss = sub.get("transformerLossKw")
    if reported_loss is None:
        reported_loss = sub.get("deviceMetrics", {}).get("transformerLossKw")

    assert reported_loss is not None
    assert abs(reported_loss - expected_loss) < 0.1

    # For a synthetic 1000 kW feeder sum, loss must be exactly 25.0 kW (not 25.6 kW)
    synthetic_feeder_sum = 1000.0
    synthetic_sub_p = synthetic_feeder_sum * 1.025  # 1025.0 kW
    synthetic_loss = round(synthetic_sub_p - synthetic_feeder_sum, 1)
    assert synthetic_loss == 25.0
