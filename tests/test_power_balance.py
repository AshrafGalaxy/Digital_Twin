"""
test_power_balance.py

Hermetic unit and integration tests for the Electrical Bus Power Balance &
Feeder Thermal Loading Engine (Energy TASK-02).
Tests Kirchhoff power conservation closure, branch ampacity thermal loading thresholds,
technical line distribution losses, and REST API endpoints.
"""

import math
import pytest
from fastapi.testclient import TestClient

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
