"""
test_building_thermal.py

Hermetic unit and integration tests for the 2R-2C Equivalent Thermal Parameter (ETP)
Building Thermal Network & Dynamic Occupancy Setback Engine (Issue #15, ENERGY-03).

Validates:
1. Runge-Kutta 4th-Order (RK4) numerical stability, bounded derivatives, and convergence.
2. Building envelope thermal inertia lag (concrete mass temperature lags indoor air).
3. ASHRAE 55 statutory comfort envelope evaluation (23.0 to 25.0 deg C).
4. Automated dynamic setback policy triggered by occupancy density (< 0.10 pax/m2).
5. Diurnal 24-hour pre-cooling simulation (peak demand reduction and cost savings).
6. REST API contracts for all 4 endpoints:
   - GET /api/v1/energy/zones
   - GET /api/v1/energy/zones/{zone_id}/thermal-state
   - POST /api/v1/energy/zones/{zone_id}/step
   - POST /api/v1/energy/zones/{zone_id}/simulate-precooling
7. Non-actuation architectural governance disclaimer verification.
8. Strictly zero emojis and zero em dashes across services, endpoints, and schemas.
"""

from datetime import datetime, timezone
import pathlib
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.building_thermal_service import (
    NON_ACTUATION_DISCLAIMER,
    BuildingThermalService,
    PrecoolingSimulationRequest,
    SimulationStepRequest,
    ThermalZoneConfig,
    building_thermal_service,
)

client = TestClient(app)


# =============================================================================
# Unit Tests: 2R-2C RK4 Physical Dynamics
# =============================================================================

def test_rk4_numerical_stability() -> None:
    """
    Verifies that Runge-Kutta 4th-order (RK4) integration remains numerically stable
    and non-divergent across varying time step durations (60s to 3600s).
    """
    svc = BuildingThermalService()
    zone = svc._default_zones["ZONE-PHOENIX-RETAIL-01"]

    # Test small, medium, and large step sizes
    step_sizes = [60.0, 300.0, 900.0, 3600.0]
    t_in = 26.0
    t_env = 27.0
    t_amb = 35.0
    q_internal = 100.0
    q_hvac = 250.0

    for dt in step_sizes:
        next_tin, next_tenv = svc.integrate_rk4(
            t_in_init=t_in,
            t_env_init=t_env,
            t_amb=t_amb,
            q_internal=q_internal,
            q_hvac=q_hvac,
            r1=zone.thermal_resistance_r1,
            r2=zone.thermal_resistance_r2,
            c_in=zone.thermal_capacitance_cin,
            c_env=zone.thermal_capacitance_cenv,
            dt_seconds=dt,
        )

        # Temperatures must stay within realistic physical bounds (10.0 to 50.0 deg C)
        assert 10.0 <= next_tin <= 50.0, f"RK4 divergence for dt={dt}: next_tin={next_tin}"
        assert 10.0 <= next_tenv <= 50.0, f"RK4 divergence for dt={dt}: next_tenv={next_tenv}"


def test_thermal_inertia_lag() -> None:
    """
    Verifies that structural envelope mass temperature lags indoor air temperature
    due to large concrete thermal capacitance (C_env >> C_in).
    """
    svc = BuildingThermalService()
    zone = svc._default_zones["ZONE-SOLITAIRE-OFFICE-01"]

    # Initial thermal equilibrium at 24.0 deg C
    t_in = 24.0
    t_env = 24.0
    t_amb = 38.0  # Sudden hot outdoor ambient
    q_internal = 50.0
    q_hvac = 0.0  # Chiller off, letting zone heat up

    dt = 900.0  # 15 minutes
    next_tin, next_tenv = svc.integrate_rk4(
        t_in_init=t_in,
        t_env_init=t_env,
        t_amb=t_amb,
        q_internal=q_internal,
        q_hvac=q_hvac,
        r1=zone.thermal_resistance_r1,
        r2=zone.thermal_resistance_r2,
        c_in=zone.thermal_capacitance_cin,
        c_env=zone.thermal_capacitance_cenv,
        dt_seconds=dt,
    )

    # Indoor air heats up faster than the heavy structural envelope
    delta_tin = next_tin - t_in
    delta_tenv = next_tenv - t_env

    assert delta_tin > delta_tenv, (
        f"Indoor air delta ({delta_tin:.4f}) should exceed envelope delta ({delta_tenv:.4f}) "
        "due to thermal inertia lag."
    )


# =============================================================================
# Unit Tests: ASHRAE 55 Comfort Envelope & Internal Heat Gains
# =============================================================================

def test_ashrae55_comfort_boundaries() -> None:
    """
    Verifies ASHRAE 55 statutory comfort compliance evaluation:
    Nominal setpoint 24.0 deg C allows +/- 1.0 deg C (23.0 to 25.0 deg C).
    """
    svc = BuildingThermalService()

    # In-band comfort temperatures
    compliant_24, dev_24 = svc.evaluate_ashrae55_comfort(24.0, occupant_count=100)
    assert compliant_24 is True
    assert dev_24 == 0.0

    compliant_23, dev_23 = svc.evaluate_ashrae55_comfort(23.0, occupant_count=100)
    assert compliant_23 is True
    assert dev_23 == 0.0

    compliant_25, dev_25 = svc.evaluate_ashrae55_comfort(25.0, occupant_count=100)
    assert compliant_25 is True
    assert dev_25 == 0.0

    # Overheating violation
    compliant_hot, dev_hot = svc.evaluate_ashrae55_comfort(25.8, occupant_count=100)
    assert compliant_hot is False
    assert dev_hot == 0.8

    # Overcooling violation
    compliant_cold, dev_cold = svc.evaluate_ashrae55_comfort(22.4, occupant_count=100)
    assert compliant_cold is False
    assert dev_cold == 0.6

    # Unoccupied setback exemption (0 occupants)
    compliant_unocc, dev_unocc = svc.evaluate_ashrae55_comfort(27.5, occupant_count=0)
    assert compliant_unocc is True
    assert dev_unocc == 0.0


def test_internal_sensible_heat_gains() -> None:
    """
    Verifies sensible heat gain calculation from occupancy (100 W/person),
    lighting, and plug loads.
    """
    svc = BuildingThermalService()
    # 50 occupants * 0.10 kW = 5.0 kW
    # 1000 m2 floor * 0.008 = 8.0 kW lighting
    # 1000 m2 floor * 0.010 = 10.0 kW plug
    # Total = 23.0 kW
    q_gain = svc.calculate_internal_heat_gain(
        occupant_count=50,
        floor_area_sqm=1000.0,
    )
    assert q_gain == 23.0


# =============================================================================
# Unit Tests: Dynamic Occupancy Setback
# =============================================================================

def test_dynamic_occupancy_setback_trigger() -> None:
    """
    Verifies dynamic setback trigger:
    When occupancy density < 0.10 pax/m2, setpoint expands by +2.5 deg C (to 26.5 deg C).
    When occupancy density >= 0.10 pax/m2, setpoint returns to nominal 24.0 deg C.
    """
    svc = BuildingThermalService()
    floor_area = 1000.0

    # Sparse occupancy: 40 occupants / 1000 m2 = 0.04 pax/m2 (< 0.10)
    mode_sparse, sp_sparse = svc.determine_hvac_mode_and_setpoint(
        occupant_count=40,
        floor_area_sqm=floor_area,
        nominal_setpoint_c=24.0,
        enable_dynamic_setback=True,
    )
    assert mode_sparse == "DYNAMIC_SETBACK"
    assert sp_sparse == 26.5

    # Dense occupancy: 150 occupants / 1000 m2 = 0.15 pax/m2 (>= 0.10)
    mode_dense, sp_dense = svc.determine_hvac_mode_and_setpoint(
        occupant_count=150,
        floor_area_sqm=floor_area,
        nominal_setpoint_c=24.0,
        enable_dynamic_setback=True,
    )
    assert mode_dense == "COMFORT"
    assert sp_dense == 24.0

    # Unoccupied (0 occupants)
    mode_empty, sp_empty = svc.determine_hvac_mode_and_setpoint(
        occupant_count=0,
        floor_area_sqm=floor_area,
        nominal_setpoint_c=24.0,
    )
    assert mode_empty == "UNOCCUPIED"
    assert sp_empty == 28.0


# =============================================================================
# Unit Tests: 24-Hour Diurnal Pre-cooling Simulator
# =============================================================================

def test_precooling_simulation_demand_and_cost_savings() -> None:
    """
    Verifies that 24-hour diurnal pre-cooling reduces peak period chiller electrical demand
    and delivers positive electricity cost savings.
    """
    svc = BuildingThermalService()
    zone = svc._default_zones["ZONE-PHOENIX-RETAIL-01"]

    req = PrecoolingSimulationRequest(
        target_precool_temp_c=22.0,
        precool_start_hour=2,
        precool_end_hour=6,
        peak_start_hour=18,
        peak_end_hour=22,
        off_peak_tariff_inr_kwh=4.50,
        peak_tariff_inr_kwh=11.50,
        normal_tariff_inr_kwh=7.50,
    )

    res = svc.simulate_precooling_comparison(zone, req)

    assert len(res.baseline_profile) == 24
    assert len(res.precooling_profile) == 24
    assert res.baseline_total_cost_inr > 0.0
    assert res.precooling_total_cost_inr > 0.0

    # Pre-cooling must achieve cost savings or peak demand reduction
    assert res.cost_savings_inr > 0.0, f"Expected cost savings > 0, got {res.cost_savings_inr}"
    assert res.cost_savings_pct > 0.0, f"Expected cost savings pct > 0, got {res.cost_savings_pct}"
    assert res.peak_demand_reduction_kw >= 0.0
    assert res.source_mode == "SIMULATION"
    assert res.non_actuation_disclaimer == NON_ACTUATION_DISCLAIMER


# =============================================================================
# Integration Tests: REST API Endpoints
# =============================================================================

def test_api_list_thermal_zones() -> None:
    """
    GET /api/v1/energy/zones
    Returns 200 OK with list of configured thermal zones and current states.
    """
    response = client.get("/api/v1/energy/zones")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    first = data[0]
    assert "zoneId" in first
    assert "zoneName" in first
    assert "floorAreaSqm" in first
    assert "currentTempC" in first
    assert "hvacMode" in first
    assert "sourceMode" in first
    assert first["sourceMode"] == "SIMULATION"


def test_api_get_zone_thermal_state() -> None:
    """
    GET /api/v1/energy/zones/{zone_id}/thermal-state
    Returns 200 OK with detailed 2R-2C thermal parameters and current state.
    """
    response = client.get("/api/v1/energy/zones/ZONE-PHOENIX-RETAIL-01/thermal-state")
    assert response.status_code == 200
    data = response.json()

    assert data["zoneId"] == "ZONE-PHOENIX-RETAIL-01"
    assert "tempIndoorC" in data
    assert "tempEnvelopeC" in data
    assert "ashrae55Compliant" in data
    assert "nonActuationDisclaimer" in data
    assert data["sourceMode"] == "SIMULATION"


def test_api_get_zone_not_found() -> None:
    """
    GET /api/v1/energy/zones/NON-EXISTENT-ZONE/thermal-state
    Returns 404 Not Found.
    """
    response = client.get("/api/v1/energy/zones/NON-EXISTENT-ZONE/thermal-state")
    assert response.status_code == 404


def test_api_step_zone_simulation() -> None:
    """
    POST /api/v1/energy/zones/{zone_id}/step
    Advances simulation by dt_seconds, returns 200 OK with next state.
    """
    payload = {
        "dtSeconds": 900.0,
        "tempAmbientC": 34.5,
        "occupantCount": 450,
        "lightingKw": 30.0,
        "plugKw": 40.0,
        "enableDynamicSetback": True,
    }
    response = client.post("/api/v1/energy/zones/ZONE-PHOENIX-RETAIL-01/step", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["zoneId"] == "ZONE-PHOENIX-RETAIL-01"
    assert data["occupantCount"] == 450
    assert data["sourceMode"] == "SIMULATION"
    assert "coolingDemandKwTh" in data
    assert "chillerElectricalKw" in data


def test_api_simulate_precooling() -> None:
    """
    POST /api/v1/energy/zones/{zone_id}/simulate-precooling
    Returns 200 OK with comparative 24-hour diurnal profiles and cost savings.
    """
    payload = {
        "targetPrecoolTempC": 22.0,
        "precoolStartHour": 2,
        "precoolEndHour": 6,
        "peakStartHour": 18,
        "peakEndHour": 22,
        "offPeakTariffInrKwh": 4.50,
        "peakTariffInrKwh": 11.50,
        "normalTariffInrKwh": 7.50,
    }
    response = client.post("/api/v1/energy/zones/ZONE-PHOENIX-RETAIL-01/simulate-precooling", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["zoneId"] == "ZONE-PHOENIX-RETAIL-01"
    assert "baselineProfile" in data
    assert len(data["baselineProfile"]) == 24
    assert "precoolingProfile" in data
    assert len(data["precoolingProfile"]) == 24
    assert data["costSavingsInr"] > 0.0
    assert data["costSavingsPct"] > 0.0
    assert data["nonActuationDisclaimer"] == NON_ACTUATION_DISCLAIMER


# =============================================================================
# Code Hygiene & Invariant Tests
# =============================================================================

def test_zero_emojis_and_zero_em_dashes() -> None:
    """
    Verifies that building_thermal_service.py and energy.py strictly contain
    zero emojis and zero em dashes or en dashes.
    """
    files_to_check = [
        pathlib.Path("backend/services/building_thermal_service.py"),
        pathlib.Path("backend/api/v1/endpoints/energy.py"),
    ]

    em_dash = "\u2014"
    en_dash = "\u2013"

    for fpath in files_to_check:
        assert fpath.exists(), f"File {fpath} does not exist."
        content = fpath.read_text(encoding="utf-8")

        assert em_dash not in content, f"Em dash found in {fpath}"
        assert en_dash not in content, f"En dash found in {fpath}"

        # Emoji check: inspect characters outside ASCII and European standard ranges
        for char in content:
            code = ord(char)
            # Common emoji ranges
            is_emoji = (
                (0x1F600 <= code <= 0x1F64F)  # Emoticons
                or (0x1F300 <= code <= 0x1F5FF)  # Misc Symbols and Pictographs
                or (0x1F680 <= code <= 0x1F6FF)  # Transport and Map
                or (0x1F700 <= code <= 0x1F77F)  # Alchemical
                or (0x1F780 <= code <= 0x1F7FF)  # Geometric
                or (0x1F800 <= code <= 0x1F8FF)  # Supplemental Arrows-C
                or (0x1F900 <= code <= 0x1F9FF)  # Supplemental Symbols and Pictographs
                or (0x1FA00 <= code <= 0x1FA6F)  # Chess Symbols
                or (0x1FA70 <= code <= 0x1FAFF)  # Symbols and Pictographs Extended-A
                or (0x2600 <= code <= 0x26FF)    # Misc symbols (sun, zap, etc.)
                or (0x2700 <= code <= 0x27BF)    # Dingbats
            )
            assert not is_emoji, f"Emoji character {char!r} (U+{code:04X}) detected in {fpath}"
