"""
test_solar_forecast.py

Hermetic unit and integration test suite for Issue #16 ([ENERGY-05]):
Solar PV Generation & Irradiance Physical Forecasting Engine.

Covers:
1. Nighttime zero generation invariant (GHI == 0 -> P_pv == 0.0 kW).
2. King / Sandia cell temperature physics and wind cooling effects.
3. Thermal derating under elevated ambient heat ([1 - gamma * (T_cell - 25)]).
4. Inverter clipping ceiling enforcement (P_pv <= rated_peak_power_kw).
5. Performance Ratio (PR) anomaly detector thresholds and low-light standby guard.
6. REST API endpoints (/solar/arrays, /solar/{array_id}/forecast, /evaluate-performance),
   404 unknown array guard, portable geometry overrides, and segregated persistence.
7. Zero emojis and zero em/en dashes across all Issue #16 files.
"""

from datetime import datetime, timezone
import asyncio
from pathlib import Path
import re
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.core.database import persistence_manager
from backend.core.schema_migrator import init_db_schema
from backend.main import app
from backend.services.solar_forecast_service import (
    SolarPVArrayConfig,
    solar_forecast_service,
)


ROOT_DIR = Path(__file__).resolve().parent.parent


def _default_array() -> SolarPVArrayConfig:
    return SolarPVArrayConfig(
        arrayId="AST-PV-PHOENIX-01",
        facilityId="urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01",
        inverterId="INV-PHOENIX-ROOF-01",
        collectorAreaSqm=6486.49,
        nominalEfficiency=0.185,
        thermalDeratingCoeff=0.004,
        tiltDegrees=18.0,
        azimuthDegrees=180.0,
        ratedPeakPowerKw=1200.0,
    )


def test_nighttime_zero_irradiance_yields_zero_generation():
    """Asserts GHI == 0.0 during local nighttime and output strictly == 0.0 kW."""
    # 20:00 UTC is 01:30 IST (nighttime)
    night_utc = datetime(2026, 9, 26, 20, 0, tzinfo=timezone.utc)
    ghi_night = solar_forecast_service.compute_clear_sky_ghi_wm2(night_utc, tz_name="Asia/Kolkata")
    assert ghi_night == 0.0

    res = solar_forecast_service.compute_pv_output_kw(
        collector_area_sqm=6486.49,
        nominal_efficiency=0.185,
        thermal_derating_coeff=0.004,
        rated_peak_power_kw=1200.0,
        ghi_wm2=0.0,
        cell_temperature_c=28.0,
    )
    assert res["expectedPowerKw"] == 0.0
    assert res["thermalDeratingLossPct"] == 0.0


def test_sandia_cell_temperature_and_wind_cooling():
    """Higher irradiance elevates T_cell above T_amb; higher wind lowers T_cell."""
    t_amb = 32.0
    ghi = 900.0
    t_cell_calm = solar_forecast_service.compute_cell_temperature_c(t_amb, ghi, wind_speed_ms=0.5)
    t_cell_windy = solar_forecast_service.compute_cell_temperature_c(t_amb, ghi, wind_speed_ms=6.0)
    t_cell_dark = solar_forecast_service.compute_cell_temperature_c(t_amb, 0.0, wind_speed_ms=2.0)

    assert t_cell_calm > t_amb + 15.0
    assert t_cell_windy < t_cell_calm
    assert t_cell_dark == t_amb


def test_thermal_derating_reduces_yield_under_high_ambient_heat():
    """Asserts ambient heat increases cell temperature and reduces AC yield via gamma."""
    cfg = _default_array()
    ghi = 850.0

    t_cell_cool = solar_forecast_service.compute_cell_temperature_c(20.0, ghi, wind_speed_ms=2.0)
    t_cell_hot = solar_forecast_service.compute_cell_temperature_c(42.0, ghi, wind_speed_ms=2.0)

    out_cool = solar_forecast_service.compute_pv_output_kw(
        cfg.collectorAreaSqm,
        cfg.nominalEfficiency,
        cfg.thermalDeratingCoeff,
        cfg.ratedPeakPowerKw,
        ghi,
        t_cell_cool,
    )
    out_hot = solar_forecast_service.compute_pv_output_kw(
        cfg.collectorAreaSqm,
        cfg.nominalEfficiency,
        cfg.thermalDeratingCoeff,
        cfg.ratedPeakPowerKw,
        ghi,
        t_cell_hot,
    )

    assert t_cell_hot > t_cell_cool
    assert out_hot["expectedPowerKw"] < out_cool["expectedPowerKw"]
    assert out_hot["thermalDeratingFactor"] < out_cool["thermalDeratingFactor"]
    assert out_hot["thermalDeratingLossPct"] > out_cool["thermalDeratingLossPct"]


def test_inverter_clipping_bounds():
    """Solar yield must never exceed ratedPeakPowerKw under extreme peak irradiance."""
    cfg = _default_array()
    out = solar_forecast_service.compute_pv_output_kw(
        cfg.collectorAreaSqm,
        cfg.nominalEfficiency,
        cfg.thermalDeratingCoeff,
        cfg.ratedPeakPowerKw,
        ghi_wm2=1250.0,
        cell_temperature_c=20.0,
    )
    assert out["expectedPowerKw"] == cfg.ratedPeakPowerKw


def test_performance_ratio_underperformance_classifications():
    """Verifies NOMINAL, SOILING_OR_DEGRADATION_WARNING, INVERTER_OR_STRING_FAULT, and LOW_IRRADIANCE_STANDBY."""
    cfg = _default_array()
    ghi = 800.0
    t_amb = 30.0
    t_cell = solar_forecast_service.compute_cell_temperature_c(t_amb, ghi, wind_speed_ms=2.0)
    expected = solar_forecast_service.compute_pv_output_kw(
        cfg.collectorAreaSqm,
        cfg.nominalEfficiency,
        cfg.thermalDeratingCoeff,
        cfg.ratedPeakPowerKw,
        ghi,
        t_cell,
    )["expectedPowerKw"]

    nominal_res = solar_forecast_service.evaluate_performance_ratio(
        cfg, measured_kw=expected * 0.94, ghi_wm2=ghi, ambient_temp_c=t_amb
    )
    assert nominal_res.diagnosticStatus == "NOMINAL"
    assert nominal_res.performanceRatio is not None and nominal_res.performanceRatio >= 0.85

    soiling_res = solar_forecast_service.evaluate_performance_ratio(
        cfg, measured_kw=expected * 0.74, ghi_wm2=ghi, ambient_temp_c=t_amb
    )
    assert soiling_res.diagnosticStatus == "SOILING_OR_DEGRADATION_WARNING"
    assert soiling_res.performanceRatio is not None and 0.65 <= soiling_res.performanceRatio < 0.85

    fault_res = solar_forecast_service.evaluate_performance_ratio(
        cfg, measured_kw=expected * 0.42, ghi_wm2=ghi, ambient_temp_c=t_amb
    )
    assert fault_res.diagnosticStatus == "INVERTER_OR_STRING_FAULT"
    assert fault_res.performanceRatio is not None and fault_res.performanceRatio < 0.65

    night_res = solar_forecast_service.evaluate_performance_ratio(
        cfg, measured_kw=0.0, ghi_wm2=0.0, ambient_temp_c=24.0
    )
    assert night_res.diagnosticStatus == "LOW_IRRADIANCE_STANDBY"
    assert night_res.performanceRatio is None


def test_multi_horizon_curve_contains_night_and_day():
    """24-hour curve includes both zero nighttime generation and positive midday generation."""
    cfg = _default_array()
    start_utc = datetime(2026, 9, 26, 0, 0, tzinfo=timezone.utc)
    res = solar_forecast_service.generate_multi_horizon_forecast(
        array_cfg=cfg,
        horizon_hours=24,
        step_minutes=15,
        now_utc=start_utc,
        tz_name="Asia/Kolkata",
    )
    assert len(res.curve24h) == 96
    assert any(not pt.isDaylight and pt.expectedPowerKw == 0.0 for pt in res.curve24h)
    assert any(pt.isDaylight and pt.expectedPowerKw > 400.0 for pt in res.curve24h)
    assert res.peakExpectedPowerKw <= cfg.ratedPeakPowerKw
    assert res.dailyExpectedEnergyKwh > 0.0


def test_api_solar_endpoints_and_state_separation():
    """Verifies /solar/arrays, /solar/{array_id}/forecast, /evaluate-performance, 404, and DB isolation."""
    with TestClient(app) as client:
        arrays_resp = client.get("/api/v1/energy/solar/arrays")
        assert arrays_resp.status_code == 200
        arrays = arrays_resp.json()
        assert len(arrays) >= 3
        array_ids = {a["arrayId"] for a in arrays}
        assert "AST-PV-PHOENIX-01" in array_ids

        # Unknown array without overrides -> 404
        unk_resp = client.get("/api/v1/energy/solar/UNKNOWN-PV-99/forecast")
        assert unk_resp.status_code == 404

        # Portable custom array via query parameters
        port_resp = client.get(
            "/api/v1/energy/solar/PORTABLE-CITY-PV-01/forecast",
            params={"collector_area_sqm": 3000.0, "rated_peak_power_kw": 555.0},
        )
        assert port_resp.status_code == 200
        assert port_resp.json()["ratedPeakPowerKw"] == 555.0

        # Known array with persist=True -> writes to solar_pv_forecasts only
        fc_resp = client.get(
            "/api/v1/energy/solar/AST-PV-PHOENIX-01/forecast",
            params={"persist": "true", "cloud_cover_pct": 15.0},
        )
        assert fc_resp.status_code == 200
        payload = fc_resp.json()
        assert payload["sourceMode"] == "PREDICTED"
        assert len(payload["curve24h"]) == 96
        assert len(payload["horizons"]) == 4

        # Performance evaluation endpoint (soiling warning at PR ~ 0.76, fault at PR < 0.65)
        eval_resp = client.post(
            "/api/v1/energy/solar/AST-PV-PHOENIX-01/evaluate-performance",
            json={
                "measuredKw": 680.0,
                "ghiWPerSqm": 850.0,
                "ambientTempC": 34.0,
                "windSpeedMs": 1.8,
            },
        )
        assert eval_resp.status_code == 200
        eval_json = eval_resp.json()
        assert eval_json["diagnosticStatus"] == "SOILING_OR_DEGRADATION_WARNING"
        assert eval_json["sourceMode"] == "PREDICTED"

        fault_resp = client.post(
            "/api/v1/energy/solar/AST-PV-PHOENIX-01/evaluate-performance",
            json={
                "measuredKw": 450.0,
                "ghiWPerSqm": 850.0,
                "ambientTempC": 34.0,
                "windSpeedMs": 1.8,
            },
        )
        assert fault_resp.status_code == 200
        assert fault_resp.json()["diagnosticStatus"] == "INVERTER_OR_STRING_FAULT"


def test_solar_forecasts_persist_segregated_from_observations():
    """DB verification ensuring solar_pv_forecasts writes never touch energy_observations."""
    async def _run() -> None:
        await init_db_schema()
        async with persistence_manager.session_factory() as session:
            before_obs = (
                await session.execute(text("SELECT COUNT(*) FROM energy_observations"))
            ).scalar() or 0

            cfg = await solar_forecast_service.get_solar_array_config("AST-PV-PHOENIX-01", session)
            assert cfg is not None
            fc = solar_forecast_service.generate_multi_horizon_forecast(cfg)
            inserted = await solar_forecast_service.persist_solar_forecasts(fc, session)
            assert inserted == 96

            solar_fc_count = (
                await session.execute(
                    text("SELECT COUNT(*) FROM solar_pv_forecasts WHERE array_id = 'AST-PV-PHOENIX-01'")
                )
            ).scalar() or 0
            after_obs = (
                await session.execute(text("SELECT COUNT(*) FROM energy_observations"))
            ).scalar() or 0

            assert solar_fc_count >= 96
            assert after_obs == before_obs

    asyncio.run(_run())


def test_zero_emojis_and_zero_em_dashes_in_solar_files():
    """Enforces zero emojis and zero em/en dashes across all Issue #16 files."""
    files = [
        ROOT_DIR / "backend" / "services" / "solar_forecast_service.py",
        ROOT_DIR / "backend" / "api" / "v1" / "endpoints" / "energy.py",
        ROOT_DIR / "frontend" / "src" / "components" / "energy" / "SolarPVForecastPanel.tsx",
        ROOT_DIR / "frontend" / "src" / "components" / "views" / "EnergyAnalyticsView.tsx",
        ROOT_DIR / "tests" / "test_solar_forecast.py",
    ]
    emoji_re = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]")
    for fpath in files:
        content = fpath.read_text(encoding="utf-8")
        assert "\u2014" not in content, f"Em dash found in {fpath}"
        assert "\u2013" not in content, f"En dash found in {fpath}"
        assert not emoji_re.search(content), f"Emoji found in {fpath}"
