"""
test_bess_optimizer.py

Hermetic unit and integration tests for the Battery Energy Storage System (BESS)
24-Hour Battery Arbitrage and Time-of-Use Peak Shaving Optimizer (Issue #18, ENERGY-06).

Validates:
1. Optimization feasibility and solver convergence using scipy.optimize.linprog(method='highs').
2. Economic superiority: verifies >15% cost savings vs unmanaged baseline.
3. State of Charge (SoC) operating boundaries: 20% <= SoC <= 90% across all 24 hours.
4. C-rate degradation limits: charging <= 0.5C (1000 kW), discharging <= 1.0C (2000 kW).
5. Round-trip efficiency losses: eta_ch = eta_dis = sqrt(0.885) (~0.940744).
6. Tariff arbitrage: charging during off-peak/solar hours and discharging during evening peak (INR 11.80, 18:00-22:00).
7. Peak shaving: grid import strictly respects contract demand ceiling (e.g. 3500 kW).
8. REST API endpoint contracts: POST /api/v1/energy/optimize-bess and GET /api/v1/energy/bess/schedule.
"""

import math
from typing import Any, Dict, List
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.bess_optimizer import (
    BessOptimizer,
    bess_optimizer,
    BessOptimizationRequest,
    BessOptimizationResult,
    HourlyScheduleItem,
)

client = TestClient(app)


def test_bess_optimizer_instantiation_and_defaults():
    """
    Verifies default parameters and electrical engineering constants
    of the BessOptimizer service.
    """
    opt = BessOptimizer()
    assert opt.DEFAULT_CAPACITY_KWH == 2000.0
    assert opt.DEFAULT_SOC_MIN == 0.20
    assert opt.DEFAULT_SOC_MAX == 0.90
    assert opt.DEFAULT_C_RATE_CHARGE == 0.5
    assert opt.DEFAULT_C_RATE_DISCHARGE == 1.0
    assert opt.ROUND_TRIP_EFFICIENCY == 0.885
    assert abs(opt.ONE_WAY_EFFICIENCY - math.sqrt(0.885)) < 1e-9

    load = opt.get_default_load_profile()
    assert len(load) == 24
    assert all(p >= 950.0 and p <= 3100.0 for p in load)

    solar = opt.get_default_solar_profile()
    assert len(solar) == 24
    assert solar[0] == 0.0
    assert solar[12] == 1000.0

    tariffs = opt.get_default_tariff_profile()
    assert len(tariffs) == 24
    assert tariffs[0] == 4.5
    assert tariffs[12] == 7.2
    assert tariffs[19] == 11.8


def test_optimization_feasibility_and_convergence():
    """
    Verifies optimization feasibility and solver convergence across standard
    and varied boundary initial SoC conditions (20%, 50%, 80%).
    """
    opt = BessOptimizer()

    for initial_soc in [20.0, 50.0, 80.0]:
        res = opt.optimize_24h_schedule(
            facility_id=f"urn:ngsi-ld:Building:TEST-FEASIBILITY-{int(initial_soc)}",
            initial_soc_pct=initial_soc,
        )
        assert res is not None
        assert "hourlySchedule" in res
        assert len(res["hourlySchedule"]) == 24
        assert res["projectedCostSavingsInr"] > 0.0
        assert res["costSavingsPct"] > 0.0
        assert res["provenance"]["qualityStatus"] == "VERIFIED"
        assert res["provenance"]["sourceMode"] == "PREDICTED"
        assert "scipy.optimize.linprog(method='highs')" in res["provenance"]["solver"]


def test_economic_superiority_exceeds_fifteen_percent_savings():
    """
    Verifies economic superiority: the optimized dispatch schedule must deliver
    strictly greater than 15% cost savings compared to the unmanaged baseline
    on the standard commercial facility load and solar profile.
    """
    opt = BessOptimizer()
    res = opt.optimize_24h_schedule(
        facility_id="urn:ngsi-ld:Building:TEST-SAVINGS",
        initial_soc_pct=50.0,
    )

    cost_savings_pct = res["costSavingsPct"]
    projected_savings_inr = res["projectedCostSavingsInr"]
    unmanaged_cost = res["unmanagedCostInr"]
    optimized_cost = res["optimizedCostInr"]

    # Invariant: >15% cost savings
    assert cost_savings_pct > 15.0, (
        f"Expected costSavingsPct > 15.0%, but obtained {cost_savings_pct}%"
    )
    assert projected_savings_inr > 0.0
    assert optimized_cost < unmanaged_cost
    assert abs((unmanaged_cost - optimized_cost) - projected_savings_inr) < 1.0


def test_soc_boundaries_strictly_respected_all_hours():
    """
    Verifies that battery State of Charge stays strictly within the safe operating
    envelope of 20% <= SoC <= 90% across every single hour of the 24-hour horizon.
    Also verifies end-of-horizon replenishment constraint.
    """
    opt = BessOptimizer()
    capacity = 2000.0
    min_energy = 0.20 * capacity  # 400 kWh
    max_energy = 0.90 * capacity  # 1800 kWh

    res = opt.optimize_24h_schedule(
        facility_id="urn:ngsi-ld:Building:TEST-SOC",
        initial_soc_pct=50.0,
    )

    for item in res["hourlySchedule"]:
        soc = item["targetSoCPct"]
        stored_kwh = item["storedEnergyKwh"]

        # 20% <= SoC <= 90%
        assert 20.0 - 1e-4 <= soc <= 90.0 + 1e-4, (
            f"Hour {item['hour']}: SoC {soc}% violated bounds [20.0%, 90.0%]"
        )
        assert min_energy - 1e-3 <= stored_kwh <= max_energy + 1e-3, (
            f"Hour {item['hour']}: Stored energy {stored_kwh} kWh violated bounds [{min_energy}, {max_energy}]"
        )

    # End-of-horizon replenishment check: SoC(23) >= SoC_init - 5%
    final_soc = res["hourlySchedule"][23]["targetSoCPct"]
    assert final_soc >= 50.0 - 5.0 - 1e-4, (
        f"Final SoC {final_soc}% violated replenishment threshold (>= 45.0%)"
    )


def test_c_rate_compliance_and_power_limits():
    """
    Verifies C-rate limits:
    - Charging power <= 0.5C (1000 kW for 2000 kWh pack)
    - Discharging power <= 1.0C (2000 kW for 2000 kWh pack)
    - Zero simultaneous charging and discharging
    """
    opt = BessOptimizer()
    res = opt.optimize_24h_schedule(
        facility_id="urn:ngsi-ld:Building:TEST-C-RATE",
        initial_soc_pct=50.0,
    )

    max_charge_kw = 0.5 * opt.DEFAULT_CAPACITY_KWH  # 1000 kW
    max_discharge_kw = 1.0 * opt.DEFAULT_CAPACITY_KWH  # 2000 kW

    for item in res["hourlySchedule"]:
        action = item["action"]
        power_kw = item["powerKw"]
        net_power_kw = item["netPowerKw"]

        if action == "CHARGE":
            assert power_kw <= max_charge_kw + 1e-3, (
                f"Hour {item['hour']}: Charge power {power_kw} kW exceeded 0.5C limit ({max_charge_kw} kW)"
            )
            assert abs(net_power_kw - (-power_kw)) < 1e-3
        elif action == "DISCHARGE":
            assert power_kw <= max_discharge_kw + 1e-3, (
                f"Hour {item['hour']}: Discharge power {power_kw} kW exceeded 1.0C limit ({max_discharge_kw} kW)"
            )
            assert abs(net_power_kw - power_kw) < 1e-3
        else:
            assert action == "STANDBY"
            assert power_kw == 0.0
            assert net_power_kw == 0.0


def test_round_trip_efficiency_modeling():
    """
    Verifies that electrochemical storage losses are modeled with square-root symmetric
    one-way efficiencies: eta_ch = eta_dis = sqrt(0.885) (~0.940744).
    Checks exact energy continuity between hour t-1 and hour t.
    """
    opt = BessOptimizer()
    initial_soc_pct = 50.0
    res = opt.optimize_24h_schedule(
        facility_id="urn:ngsi-ld:Building:TEST-EFFICIENCY",
        initial_soc_pct=initial_soc_pct,
    )

    eta = math.sqrt(0.885)
    e_prev = (initial_soc_pct / 100.0) * opt.DEFAULT_CAPACITY_KWH

    for item in res["hourlySchedule"]:
        action = item["action"]
        power_kw = item["powerKw"]
        stored_kwh = item["storedEnergyKwh"]

        if action == "CHARGE":
            delta_e = power_kw * eta * 1.0  # 1 hour dt
        elif action == "DISCHARGE":
            delta_e = -(power_kw / eta) * 1.0
        else:
            delta_e = 0.0

        expected_stored = e_prev + delta_e
        assert abs(stored_kwh - expected_stored) < 0.1, (
            f"Hour {item['hour']}: Stored energy {stored_kwh} differs from expected {expected_stored} "
            f"under eta={eta}"
        )
        e_prev = stored_kwh


def test_tariff_arbitrage_behavior():
    """
    Verifies tariff arbitrage:
    - BESS charges during off-peak nocturnal hours (00:00 to 06:00, INR 4.50)
      or high-solar midday hours (INR 7.20 with solar surplus).
    - BESS discharges during peak evening hours (18:00 to 22:00, INR 11.80).
    """
    opt = BessOptimizer()
    res = opt.optimize_24h_schedule(
        facility_id="urn:ngsi-ld:Building:TEST-ARBITRAGE",
        initial_soc_pct=50.0,
    )

    schedule = res["hourlySchedule"]

    # Peak evening hours: 18, 19, 20, 21
    peak_hours = [18, 19, 20, 21]
    peak_discharge_energy = sum(
        schedule[h]["powerKw"]
        for h in peak_hours
        if schedule[h]["action"] == "DISCHARGE"
    )
    assert peak_discharge_energy > 500.0, (
        f"Expected significant discharge during evening peak hours (18-22), but got {peak_discharge_energy} kWh"
    )

    # Off-peak nocturnal hours: 0, 1, 2, 3, 4, 5 (INR 4.50)
    off_peak_charge_energy = sum(
        schedule[h]["powerKw"]
        for h in range(6)
        if schedule[h]["action"] == "CHARGE"
    )
    assert off_peak_charge_energy > 0.0, (
        f"Expected BESS charging during cheap off-peak night hours, got {off_peak_charge_energy} kWh"
    )


def test_peak_shaving_and_contract_demand_ceiling():
    """
    Verifies that grid import strictly respects the contract demand ceiling across all hours:
    P_grid(t) <= P_contract_limit.
    Also verifies peak shaving reduction metric: optimizedPeakKw < unmanagedPeakKw.
    """
    opt = BessOptimizer()
    custom_ceiling = 2700.0  # Lower than unmanaged peak (~3100 kW)

    res = opt.optimize_24h_schedule(
        facility_id="urn:ngsi-ld:Building:TEST-PEAK-SHAVING",
        initial_soc_pct=70.0,
        contract_demand_ceiling_kw=custom_ceiling,
    )

    unmanaged_peak = res["unmanagedPeakKw"]
    optimized_peak = res["optimizedPeakKw"]
    peak_reduction = res["peakShavingReductionKw"]

    assert optimized_peak <= custom_ceiling + 1e-3, (
        f"Optimized peak {optimized_peak} kW exceeded contract ceiling {custom_ceiling} kW"
    )
    assert optimized_peak < unmanaged_peak
    assert peak_reduction > 0.0
    assert abs((unmanaged_peak - optimized_peak) - peak_reduction) < 0.1

    for item in res["hourlySchedule"]:
        assert item["gridImportKw"] <= custom_ceiling + 1e-3, (
            f"Hour {item['hour']}: Grid import {item['gridImportKw']} kW exceeded ceiling {custom_ceiling} kW"
        )


def test_power_balance_equality_constraint():
    """
    Verifies that the physical active power balance holds for every hour t in 0..23:
    P_grid(t) - P_feedin(t) - P_ch(t) + P_dis(t) = P_load(t) - P_solar(t)
    """
    opt = BessOptimizer()
    res = opt.optimize_24h_schedule(
        facility_id="urn:ngsi-ld:Building:TEST-POWER-BALANCE",
        initial_soc_pct=50.0,
    )

    for item in res["hourlySchedule"]:
        p_grid = item["gridImportKw"]
        p_feedin = item["feedinKw"]
        action = item["action"]
        power = item["powerKw"]
        p_ch = power if action == "CHARGE" else 0.0
        p_dis = power if action == "DISCHARGE" else 0.0
        p_load = item["loadKw"]
        p_solar = item["solarKw"]

        lhs = p_grid - p_feedin - p_ch + p_dis
        rhs = p_load - p_solar
        assert abs(lhs - rhs) < 0.1, (
            f"Hour {item['hour']}: Power balance violated: LHS={lhs:.2f} kW, RHS={rhs:.2f} kW"
        )


def test_rest_api_optimize_bess_contract_and_aliases():
    """
    Verifies REST endpoint contracts:
    - POST /api/v1/energy/optimize-bess
    - POST /api/v1/energy/bess/optimize
    Validates input parsing (both snake_case and camelCase), governance advisory notices,
    data provenance format, and 24-step schedule schema.
    """
    payload = {
        "facilityId": "urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01",
        "targetScheduleDate": "2026-11-23",
        "initialSocPct": 55.0,
        "contractDemandCeilingKw": 3500.0,
        "demandPenaltyRateInr": 650.0,
        "capacityKwh": 2000.0
    }

    # Test primary POST endpoint
    res1 = client.post("/api/v1/energy/optimize-bess", json=payload)
    assert res1.status_code == 200
    data1 = res1.json()

    assert data1["facilityId"] == payload["facilityId"]
    assert data1["targetScheduleDate"] == payload["targetScheduleDate"]
    assert data1["projectedCostSavingsInr"] > 0.0
    assert data1["costSavingsPct"] > 15.0
    assert len(data1["hourlySchedule"]) == 24
    assert data1["governanceNotice"] == "Advisory only. Requires human verification before central dispatch."
    assert data1["provenance"]["sourceMode"] == "PREDICTED"
    assert data1["provenance"]["qualityScore"] == 1.0
    assert data1["provenance"]["qualityStatus"] == "VERIFIED"

    # Test alias POST endpoint
    res2 = client.post("/api/v1/energy/bess/optimize", json=payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["facilityId"] == payload["facilityId"]


def test_rest_api_optimize_bess_rejects_invalid_profile_lengths():
    """
    Verifies that the API enforces validation guards:
    Rejects custom load, solar, or tariff profiles whose length is not exactly 24.
    """
    # 23 items instead of 24
    invalid_load = [1000.0] * 23
    res = client.post(
        "/api/v1/energy/optimize-bess",
        json={"customLoadProfileKw": invalid_load}
    )
    assert res.status_code == 400
    assert "must contain exactly 24" in res.json()["detail"]

    # Invalid solar profile length
    invalid_solar = [0.0] * 25
    res_solar = client.post(
        "/api/v1/energy/optimize-bess",
        json={"customSolarProfileKw": invalid_solar}
    )
    assert res_solar.status_code == 400
    assert "must contain exactly 24" in res_solar.json()["detail"]


def test_rest_api_get_active_bess_schedule():
    """
    Verifies REST endpoint contracts:
    - GET /api/v1/energy/bess/schedule
    - GET /api/v1/energy/bess-schedule
    Verifies retrieving active cached schedule or automatic generation.
    """
    facility_id = "urn:ngsi-ld:Building:TEST-ACTIVE-CACHE"

    # First optimize schedule to populate cache
    post_res = client.post(
        "/api/v1/energy/optimize-bess",
        json={"facilityId": facility_id, "initialSocPct": 40.0}
    )
    assert post_res.status_code == 200
    post_data = post_res.json()

    # GET active schedule via query parameter
    get_res1 = client.get(f"/api/v1/energy/bess/schedule?facility_id={facility_id}")
    assert get_res1.status_code == 200
    get_data1 = get_res1.json()
    assert get_data1["recommendationId"] == post_data["recommendationId"]
    assert get_data1["facilityId"] == facility_id
    assert len(get_data1["hourlySchedule"]) == 24

    # GET active schedule via camelCase query parameter and alias
    get_res2 = client.get(f"/api/v1/energy/bess-schedule?facilityId={facility_id}")
    assert get_res2.status_code == 200
    get_data2 = get_res2.json()
    assert get_data2["recommendationId"] == post_data["recommendationId"]

    # GET active schedule with default facility ID when omitted
    get_res_default = client.get("/api/v1/energy/bess/schedule")
    assert get_res_default.status_code == 200
    assert len(get_res_default.json()["hourlySchedule"]) == 24


def test_custom_profiles_and_parameter_scenarios():
    """
    Verifies optimization behavior under customized load, solar, and tariff profiles.
    """
    opt = BessOptimizer()
    custom_load = [1500.0] * 24
    custom_solar = [0.0] * 6 + [500.0] * 12 + [0.0] * 6
    custom_tariff = [5.0] * 12 + [12.0] * 12

    res = opt.optimize_24h_schedule(
        facility_id="urn:ngsi-ld:Building:TEST-CUSTOM-PROFILES",
        initial_soc_pct=45.0,
        custom_load_profile_kw=custom_load,
        custom_solar_profile_kw=custom_solar,
        custom_tariff_profile_inr=custom_tariff,
        contract_demand_ceiling_kw=2500.0,
        demand_penalty_rate_inr=700.0,
        capacity_kwh=3000.0,
    )

    assert res["facilityId"] == "urn:ngsi-ld:Building:TEST-CUSTOM-PROFILES"
    assert len(res["hourlySchedule"]) == 24
    assert res["projectedCostSavingsInr"] >= 0.0
    assert res["costSavingsPct"] >= 0.0
    for item in res["hourlySchedule"]:
        assert item["gridImportKw"] <= 2500.0 + 1e-3


def test_bess_optimizer_cache_management():
    """
    Verifies thread-safe cache storage, retrieval, and cache clearing.
    """
    opt = BessOptimizer()
    test_facility = "urn:ngsi-ld:Building:TEST-CACHE-MGMT"

    opt.clear_cache()
    sched = opt.optimize_24h_schedule(facility_id=test_facility)
    assert opt.get_active_schedule(test_facility, auto_generate=False) is not None

    opt.clear_cache()
    assert opt.get_active_schedule(test_facility, auto_generate=False) is None
    # auto_generate should reconstruct
    reconstructed = opt.get_active_schedule(test_facility, auto_generate=True)
    assert reconstructed is not None
    assert reconstructed["facilityId"] == test_facility


def test_pydantic_model_contracts_and_serialization():
    """
    Verifies Pydantic model serialization, validation, and alias conversion.
    """
    req = BessOptimizationRequest(
        facilityId="urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01",
        initialSocPct=60.0,
        contractDemandCeilingKw=3500.0
    )
    req_dict = req.to_dict()
    assert req_dict["facilityId"] == "urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01"
    assert req.initial_soc_pct == 60.0

    item = HourlyScheduleItem(
        hour=18,
        tariffRateInr=11.8,
        action="DISCHARGE",
        powerKw=1000.0,
        targetSoCPct=50.0,
        loadKw=3100.0,
        solarKw=0.0,
        gridImportKw=2100.0,
        feedinKw=0.0,
        storedEnergyKwh=1000.0,
        netPowerKw=1000.0,
    )
    item_dict = item.to_dict()
    assert item_dict["hour"] == 18
    assert item_dict["tariffRateInr"] == 11.8
    assert item_dict["action"] == "DISCHARGE"


def test_source_code_contains_zero_emojis_and_no_em_dashes():
    """
    AGENTS.md invariant verification:
    Ensures backend/services/bess_optimizer.py and tests/test_bess_optimizer.py
    contain zero emojis and zero em dashes or en dashes.
    """
    files_to_check = [
        "backend/services/bess_optimizer.py",
        "tests/test_bess_optimizer.py"
    ]
    for path in files_to_check:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "\u2014" not in content, f"Em dash found in {path}"
        assert "\u2013" not in content, f"En dash found in {path}"
        # Assert no common emoji characters
        for char in content:
            code = ord(char)
            # Check emoji unicode blocks
            is_emoji = (
                0x1F600 <= code <= 0x1F64F or  # Emoticons
                0x1F300 <= code <= 0x1F5FF or  # Misc Symbols and Pictographs
                0x1F680 <= code <= 0x1F6FF or  # Transport and Map
                0x1F1E0 <= code <= 0x1F1FF or  # Flags
                0x2600 <= code <= 0x26FF or    # Misc symbols
                0x2700 <= code <= 0x27BF       # Dingbats
            )
            assert not is_emoji, f"Emoji character '{char}' (U+{code:04X}) found in {path}"

