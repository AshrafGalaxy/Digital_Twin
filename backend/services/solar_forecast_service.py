"""
solar_forecast_service.py

Physical Solar PV Generation, Sandia Cell Temperature Derating, and
Performance Ratio (PR) Underperformance Anomaly Detection Engine (TASK-05 / ENERGY-05).

Preserves state separation by storing predicted yields in solar_pv_forecasts
without mutating measured inverter telemetry in energy_observations.
"""

from datetime import datetime, timedelta, timezone
import math
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.database import get_active_backend


# Default King / Sandia thermal coefficients for rooftop open-rack PV modules
DEFAULT_SANDIA_A: float = 3.56
DEFAULT_SANDIA_B: float = 0.075


class SolarPVArrayConfig(BaseModel):
    arrayId: str
    facilityId: str
    inverterId: str
    collectorAreaSqm: float = Field(..., gt=0.0)
    nominalEfficiency: float = Field(0.185, gt=0.0, le=0.45)
    thermalDeratingCoeff: float = Field(0.004, ge=0.0, le=0.02)
    tiltDegrees: float = Field(18.0, ge=0.0, le=90.0)
    azimuthDegrees: float = Field(180.0, ge=0.0, le=360.0)
    ratedPeakPowerKw: float = Field(..., gt=0.0)


class SolarForecastPoint(BaseModel):
    horizonMinutes: int
    targetTimestamp: str
    localHour: float
    ghiWPerSqm: float
    poaIrradianceWPerSqm: float
    ambientTemperatureC: float
    cellTemperatureC: float
    thermalDeratingFactor: float
    thermalDeratingLossPct: float
    expectedPowerKw: float
    isDaylight: bool


class SolarPVForecastResult(BaseModel):
    arrayId: str
    facilityId: str
    inverterId: str
    forecastGeneratedAt: str
    sourceMode: str = "PREDICTED"
    qualityStatus: str = "VALID"
    ratedPeakPowerKw: float
    collectorAreaSqm: float
    nominalEfficiency: float
    thermalDeratingCoeff: float
    dailyExpectedEnergyKwh: float
    peakExpectedPowerKw: float
    horizons: List[SolarForecastPoint]
    curve24h: List[SolarForecastPoint]
    advisoryNotice: str


class SolarPerformanceEvaluationRequest(BaseModel):
    measuredKw: float = Field(..., ge=0.0)
    ghiWPerSqm: float = Field(..., ge=0.0, le=1500.0)
    ambientTempC: float = Field(30.0, ge=-20.0, le=60.0)
    windSpeedMs: float = Field(2.0, ge=0.0, le=40.0)
    collectorAreaSqm: Optional[float] = Field(None, gt=0.0)
    nominalEfficiency: Optional[float] = Field(None, gt=0.0, le=0.45)
    thermalDeratingCoeff: Optional[float] = Field(None, ge=0.0, le=0.02)
    ratedPeakPowerKw: Optional[float] = Field(None, gt=0.0)
    observedAt: Optional[str] = None


class SolarPerformanceEvaluationResult(BaseModel):
    arrayId: str
    facilityId: str
    inverterId: str
    evaluatedAt: str
    measuredPowerKw: float
    expectedPhysicalPowerKw: float
    ghiWPerSqm: float
    ambientTemperatureC: float
    windSpeedMs: float
    cellTemperatureC: float
    thermalDeratingFactor: float
    thermalDeratingLossPct: float
    performanceRatio: Optional[float]
    diagnosticStatus: str
    advisoryAction: str
    sourceMode: str = "PREDICTED"
    nonActuationDisclaimer: str


class SolarForecastService:
    """
    Physical PV yield forecaster and underperformance diagnostic engine.
    Parameterized by collector area, system efficiency, Sandia cell temperature
    coefficients, and configured local civil timezone.
    """

    def get_local_civil_datetime(
        self,
        dt: Optional[datetime] = None,
        tz_name: Optional[str] = None,
    ) -> datetime:
        base_dt = dt or datetime.now(timezone.utc)
        if base_dt.tzinfo is None:
            base_dt = base_dt.replace(tzinfo=timezone.utc)
        zone_str = tz_name or getattr(settings, "STUDY_AREA_TIMEZONE", "Asia/Kolkata")
        try:
            return base_dt.astimezone(ZoneInfo(zone_str))
        except Exception:
            offset_min = int(getattr(settings, "CORRIDOR_UTC_OFFSET_MINUTES", 330))
            return base_dt.astimezone(timezone(timedelta(minutes=offset_min)))

    def estimate_ambient_temperature_c(self, local_decimal_hour: float) -> float:
        """
        Smooth diurnal ambient temperature profile (minimum near 05:00, peak near 14:30)
        used when external weather forecast temperature is not supplied.
        """
        temp = 24.5 + 8.5 * math.sin((local_decimal_hour - 8.5) * math.pi / 12.0)
        return round(temp, 2)

    def compute_clear_sky_ghi_wm2(
        self,
        dt_utc: datetime,
        cloud_cover_pct: float = 0.0,
        tz_name: Optional[str] = None,
    ) -> float:
        """
        Computes clear-sky Global Horizontal Irradiance (W/m2) in local civil time.
        Strictly returns 0.0 W/m2 outside solar daylight window [06:12, 18:30].
        """
        local_dt = self.get_local_civil_datetime(dt_utc, tz_name)
        decimal_hour = local_dt.hour + (local_dt.minute / 60.0) + (local_dt.second / 3600.0)

        sunrise = 6.2
        sunset = 18.5
        if decimal_hour <= sunrise or decimal_hour >= sunset:
            return 0.0

        solar_duration = sunset - sunrise
        progress = (decimal_hour - sunrise) / solar_duration
        sin_elevation = max(0.0, math.sin(math.pi * progress))

        # Peak clear-sky solar constant attenuation (~980 W/m2 clear-sky horizontal peak)
        clear_sky_ghi = 980.0 * (sin_elevation ** 1.15)
        clamped_cloud = max(0.0, min(100.0, float(cloud_cover_pct)))
        # Kasten-Czeplak cloud attenuation approximation: GHI = GHI_clear * (1 - 0.75 * N^3.4)
        cloud_fraction = clamped_cloud / 100.0
        cloud_transmittance = max(0.15, 1.0 - 0.75 * (cloud_fraction ** 3.4))
        return round(max(0.0, clear_sky_ghi * cloud_transmittance), 2)

    def compute_poa_irradiance_wm2(
        self,
        ghi_wm2: float,
        tilt_degrees: float = 18.0,
        azimuth_degrees: float = 180.0,
    ) -> float:
        """
        Projects GHI onto tilted Plane-of-Array (POA) irradiance using optimal tilt
        transposition gain bounded to realistic commercial rooftop incidence geometry.
        """
        if ghi_wm2 <= 0.0:
            return 0.0
        tilt_rad = math.radians(max(0.0, min(60.0, float(tilt_degrees))))
        # Optimal low-latitude south-facing transposition boost (~1.00 - 1.06)
        azimuth_alignment = math.cos(math.radians(float(azimuth_degrees) - 180.0))
        transposition_factor = 1.0 + 0.06 * math.sin(tilt_rad) * max(0.0, azimuth_alignment)
        return round(ghi_wm2 * transposition_factor, 2)

    def compute_cell_temperature_c(
        self,
        ambient_temp_c: float,
        ghi_wm2: float,
        wind_speed_ms: float = 2.0,
        sandia_a: float = DEFAULT_SANDIA_A,
        sandia_b: float = DEFAULT_SANDIA_B,
    ) -> float:
        """
        King / Sandia PV module cell temperature formulation:
        T_cell(t) = T_amb(t) + GHI(t) * exp(-a - b * v_wind)
        When GHI == 0, T_cell equals T_amb exactly.
        """
        if ghi_wm2 <= 0.0:
            return round(float(ambient_temp_c), 2)
        v_wind = max(0.0, float(wind_speed_ms))
        delta_t = float(ghi_wm2) * math.exp(-float(sandia_a) - float(sandia_b) * v_wind)
        return round(float(ambient_temp_c) + delta_t, 2)

    def compute_pv_output_kw(
        self,
        collector_area_sqm: float,
        nominal_efficiency: float,
        thermal_derating_coeff: float,
        rated_peak_power_kw: float,
        ghi_wm2: float,
        cell_temperature_c: float,
    ) -> Dict[str, float]:
        """
        Physical Photovoltaic Power Output Model:
        P_pv(t) = eta_sys * A_pv * (GHI(t) / 1000.0) * [1 - gamma * (T_cell(t) - 25.0)]
        Bounded in [0.0, rated_peak_power_kw] accounting for nighttime zeroing and inverter clipping.
        """
        if ghi_wm2 <= 0.0:
            return {
                "expectedPowerKw": 0.0,
                "thermalDeratingFactor": 1.0,
                "thermalDeratingLossPct": 0.0,
            }

        derating_factor = max(0.50, 1.0 - float(thermal_derating_coeff) * (float(cell_temperature_c) - 25.0))
        raw_kw = (
            float(nominal_efficiency)
            * float(collector_area_sqm)
            * (float(ghi_wm2) / 1000.0)
            * derating_factor
        )
        clipped_kw = min(float(rated_peak_power_kw), max(0.0, raw_kw))
        loss_pct = max(0.0, (1.0 - derating_factor) * 100.0)

        return {
            "expectedPowerKw": round(clipped_kw, 2),
            "thermalDeratingFactor": round(derating_factor, 4),
            "thermalDeratingLossPct": round(loss_pct, 2),
        }

    def generate_multi_horizon_forecast(
        self,
        array_cfg: SolarPVArrayConfig,
        horizon_hours: int = 24,
        step_minutes: int = 15,
        ambient_temp_c: Optional[float] = None,
        wind_speed_ms: float = 2.0,
        cloud_cover_pct: float = 0.0,
        now_utc: Optional[datetime] = None,
        tz_name: Optional[str] = None,
    ) -> SolarPVForecastResult:
        """
        Generates a 15-minute resolution solar PV physical generation curve spanning 15m to 24h
        with King/Sandia cell temperature thermal derating and PREDICTED provenance.
        """
        gen_dt = now_utc or datetime.now(timezone.utc)
        if gen_dt.tzinfo is None:
            gen_dt = gen_dt.replace(tzinfo=timezone.utc)

        total_steps = max(1, (int(horizon_hours) * 60) // int(step_minutes))
        curve_points: List[SolarForecastPoint] = []
        total_energy_kwh = 0.0
        peak_kw = 0.0

        for idx in range(1, total_steps + 1):
            horizon_min = idx * int(step_minutes)
            target_dt = gen_dt + timedelta(minutes=horizon_min)
            local_dt = self.get_local_civil_datetime(target_dt, tz_name)
            local_hour = round(local_dt.hour + local_dt.minute / 60.0, 2)

            ghi_wm2 = self.compute_clear_sky_ghi_wm2(
                target_dt,
                cloud_cover_pct=cloud_cover_pct,
                tz_name=tz_name,
            )
            poa_wm2 = self.compute_poa_irradiance_wm2(
                ghi_wm2,
                tilt_degrees=array_cfg.tiltDegrees,
                azimuth_degrees=array_cfg.azimuthDegrees,
            )
            step_amb_c = (
                float(ambient_temp_c)
                if ambient_temp_c is not None
                else self.estimate_ambient_temperature_c(local_hour)
            )
            cell_temp_c = self.compute_cell_temperature_c(
                ambient_temp_c=step_amb_c,
                ghi_wm2=ghi_wm2,
                wind_speed_ms=wind_speed_ms,
            )
            pv_calc = self.compute_pv_output_kw(
                collector_area_sqm=array_cfg.collectorAreaSqm,
                nominal_efficiency=array_cfg.nominalEfficiency,
                thermal_derating_coeff=array_cfg.thermalDeratingCoeff,
                rated_peak_power_kw=array_cfg.ratedPeakPowerKw,
                ghi_wm2=ghi_wm2,
                cell_temperature_c=cell_temp_c,
            )

            expected_kw = pv_calc["expectedPowerKw"]
            total_energy_kwh += expected_kw * (float(step_minutes) / 60.0)
            if expected_kw > peak_kw:
                peak_kw = expected_kw

            curve_points.append(
                SolarForecastPoint(
                    horizonMinutes=horizon_min,
                    targetTimestamp=target_dt.isoformat(),
                    localHour=local_hour,
                    ghiWPerSqm=ghi_wm2,
                    poaIrradianceWPerSqm=poa_wm2,
                    ambientTemperatureC=round(step_amb_c, 2),
                    cellTemperatureC=cell_temp_c,
                    thermalDeratingFactor=pv_calc["thermalDeratingFactor"],
                    thermalDeratingLossPct=pv_calc["thermalDeratingLossPct"],
                    expectedPowerKw=expected_kw,
                    isDaylight=ghi_wm2 > 0.0,
                )
            )

        checkpoint_minutes = {15, 60, 240, 1440}
        horizons = [pt for pt in curve_points if pt.horizonMinutes in checkpoint_minutes]
        if not horizons and curve_points:
            horizons = [curve_points[0], curve_points[-1]] if len(curve_points) > 1 else [curve_points[0]]

        return SolarPVForecastResult(
            arrayId=array_cfg.arrayId,
            facilityId=array_cfg.facilityId,
            inverterId=array_cfg.inverterId,
            forecastGeneratedAt=gen_dt.isoformat(),
            sourceMode="PREDICTED",
            qualityStatus="VALID",
            ratedPeakPowerKw=array_cfg.ratedPeakPowerKw,
            collectorAreaSqm=array_cfg.collectorAreaSqm,
            nominalEfficiency=array_cfg.nominalEfficiency,
            thermalDeratingCoeff=array_cfg.thermalDeratingCoeff,
            dailyExpectedEnergyKwh=round(total_energy_kwh, 2),
            peakExpectedPowerKw=round(peak_kw, 2),
            horizons=horizons,
            curve24h=curve_points,
            advisoryNotice=(
                "Physical PV yield predictions use clear-sky/NWP irradiance profiles and Sandia "
                "cell thermal derating (PREDICTED provenance). Predictions do not measure physical inverter telemetry."
            ),
        )

    def evaluate_performance_ratio(
        self,
        array_cfg: SolarPVArrayConfig,
        measured_kw: float,
        ghi_wm2: float,
        ambient_temp_c: float = 30.0,
        wind_speed_ms: float = 2.0,
        observed_at: Optional[str] = None,
    ) -> SolarPerformanceEvaluationResult:
        """
        Compares measured inverter AC output against expected physical PV yield:
          PR(t) = P_measured(t) / P_expected(t)
        Classifications:
          - Expected <= 10 kW (nighttime/twilight): LOW_IRRADIANCE_STANDBY
          - PR >= 0.85: NOMINAL
          - 0.65 <= PR < 0.85: SOILING_OR_DEGRADATION_WARNING
          - PR < 0.65: INVERTER_OR_STRING_FAULT
        """
        eval_ts = observed_at or datetime.now(timezone.utc).isoformat()
        cell_temp_c = self.compute_cell_temperature_c(
            ambient_temp_c=ambient_temp_c,
            ghi_wm2=ghi_wm2,
            wind_speed_ms=wind_speed_ms,
        )
        pv_calc = self.compute_pv_output_kw(
            collector_area_sqm=array_cfg.collectorAreaSqm,
            nominal_efficiency=array_cfg.nominalEfficiency,
            thermal_derating_coeff=array_cfg.thermalDeratingCoeff,
            rated_peak_power_kw=array_cfg.ratedPeakPowerKw,
            ghi_wm2=ghi_wm2,
            cell_temperature_c=cell_temp_c,
        )
        expected_kw = pv_calc["expectedPowerKw"]

        if expected_kw < 10.0 or ghi_wm2 < 25.0:
            pr: Optional[float] = None
            diag_status = "LOW_IRRADIANCE_STANDBY"
            advisory = "Irradiance below 25 W/m2 operational threshold; Performance Ratio suppressed to prevent low-light division artifacts."
        else:
            pr_val = round(float(measured_kw) / expected_kw, 4)
            pr = pr_val
            if pr_val >= 0.85:
                diag_status = "NOMINAL"
                advisory = "Solar PV array operating within nominal physical thermal-derated performance envelope."
            elif pr_val >= 0.65:
                diag_status = "SOILING_OR_DEGRADATION_WARNING"
                advisory = "Advisory: Moderate yield deficit detected (65%-85% PR). Schedule panel surface washing and soiling inspection."
            else:
                diag_status = "INVERTER_OR_STRING_FAULT"
                advisory = "Advisory: Severe underperformance detected (<65% PR). Dispatch maintenance crew to inspect inverter clipping, DC strings, or breaker trip."

        return SolarPerformanceEvaluationResult(
            arrayId=array_cfg.arrayId,
            facilityId=array_cfg.facilityId,
            inverterId=array_cfg.inverterId,
            evaluatedAt=eval_ts,
            measuredPowerKw=round(float(measured_kw), 2),
            expectedPhysicalPowerKw=expected_kw,
            ghiWPerSqm=round(float(ghi_wm2), 2),
            ambientTemperatureC=round(float(ambient_temp_c), 2),
            windSpeedMs=round(float(wind_speed_ms), 2),
            cellTemperatureC=cell_temp_c,
            thermalDeratingFactor=pv_calc["thermalDeratingFactor"],
            thermalDeratingLossPct=pv_calc["thermalDeratingLossPct"],
            performanceRatio=pr,
            diagnosticStatus=diag_status,
            advisoryAction=advisory,
            sourceMode="PREDICTED",
            nonActuationDisclaimer=(
                "Advisory Only (Non-Actuating). Solar performance diagnostics require authorized "
                "O&M technician dispatch prior to inverter reset or field maintenance."
            ),
        )

    async def list_solar_arrays(self, session: AsyncSession) -> List[SolarPVArrayConfig]:
        stmt = text("""
            SELECT id, facility_id, inverter_id, collector_area_sqm, nominal_efficiency,
                   thermal_derating_coeff, tilt_degrees, azimuth_degrees, rated_peak_power_kw
            FROM solar_pv_arrays
            ORDER BY rated_peak_power_kw DESC
        """)
        res = await session.execute(stmt)
        rows = res.fetchall()
        arrays: List[SolarPVArrayConfig] = []
        for r in rows:
            arrays.append(
                SolarPVArrayConfig(
                    arrayId=str(r[0]),
                    facilityId=str(r[1]),
                    inverterId=str(r[2]),
                    collectorAreaSqm=float(r[3]),
                    nominalEfficiency=float(r[4]),
                    thermalDeratingCoeff=float(r[5]),
                    tiltDegrees=float(r[6]),
                    azimuthDegrees=float(r[7]),
                    ratedPeakPowerKw=float(r[8]),
                )
            )
        return arrays

    async def get_solar_array_config(
        self,
        array_id: str,
        session: AsyncSession,
    ) -> Optional[SolarPVArrayConfig]:
        norm_id = array_id.strip()
        stmt = text("""
            SELECT id, facility_id, inverter_id, collector_area_sqm, nominal_efficiency,
                   thermal_derating_coeff, tilt_degrees, azimuth_degrees, rated_peak_power_kw
            FROM solar_pv_arrays
            WHERE id = :exact_id OR facility_id = :exact_id OR inverter_id = :exact_id
            LIMIT 1
        """)
        res = await session.execute(stmt, {"exact_id": norm_id})
        r = res.fetchone()
        if r is None:
            return None
        return SolarPVArrayConfig(
            arrayId=str(r[0]),
            facilityId=str(r[1]),
            inverterId=str(r[2]),
            collectorAreaSqm=float(r[3]),
            nominalEfficiency=float(r[4]),
            thermalDeratingCoeff=float(r[5]),
            tiltDegrees=float(r[6]),
            azimuthDegrees=float(r[7]),
            ratedPeakPowerKw=float(r[8]),
        )

    async def persist_solar_forecasts(
        self,
        forecast_result: SolarPVForecastResult,
        session: AsyncSession,
    ) -> int:
        """
        Persists forecast curve rows exclusively into solar_pv_forecasts tagged PREDICTED.
        Never inserts into energy_observations.
        """
        is_pg = get_active_backend() == "postgresql"
        gen_ts: Any = (
            datetime.fromisoformat(forecast_result.forecastGeneratedAt.replace("Z", "+00:00"))
            if is_pg
            else forecast_result.forecastGeneratedAt
        )

        # Ensure array_id exists or pass NULL if custom ephemeral override array
        exists_stmt = text("SELECT 1 FROM solar_pv_arrays WHERE id = :array_id LIMIT 1")
        exists_res = await session.execute(exists_stmt, {"array_id": forecast_result.arrayId})
        fk_array_id: Optional[str] = forecast_result.arrayId if exists_res.fetchone() is not None else None

        insert_stmt = text("""
            INSERT INTO solar_pv_forecasts (
                array_id, forecast_generated_at, target_timestamp,
                expected_power_kw, ghi_w_per_sqm, cell_temperature_c, source_mode
            ) VALUES (
                :array_id, :forecast_generated_at, :target_timestamp,
                :expected_power_kw, :ghi_w_per_sqm, :cell_temperature_c, 'PREDICTED'
            );
        """)

        written = 0
        for pt in forecast_result.curve24h:
            target_ts: Any = (
                datetime.fromisoformat(pt.targetTimestamp.replace("Z", "+00:00"))
                if is_pg
                else pt.targetTimestamp
            )
            await session.execute(
                insert_stmt,
                {
                    "array_id": fk_array_id,
                    "forecast_generated_at": gen_ts,
                    "target_timestamp": target_ts,
                    "expected_power_kw": float(pt.expectedPowerKw),
                    "ghi_w_per_sqm": float(pt.ghiWPerSqm),
                    "cell_temperature_c": float(pt.cellTemperatureC),
                },
            )
            written += 1
        await session.commit()
        return written


# Global singleton solar forecast service
solar_forecast_service = SolarForecastService()
