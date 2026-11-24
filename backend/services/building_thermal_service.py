"""
building_thermal_service.py

2R-2C Equivalent Thermal Parameter (ETP) Building Thermal Network
and Dynamic Occupancy Setback Engine (ENERGY-03 / TASK-03).

Models lumped-capacitance indoor air and structural envelope thermal dynamics
via coupled first-order ordinary differential equations integrated via Runge-Kutta
4th-order (RK4) numerical integration.
Integrates sensible internal heat gains from occupant metabolic rate (100 W/person),
plug loads, and lighting, enforces ASHRAE 55 statutory comfort envelopes (23.0 to 25.0 deg C),
and commands dynamic setbacks (+2.5 deg C) in under-utilized zones (rho_occ < 0.10 pax/m2).
Simulates 24-hour diurnal pre-cooling strategies to quantify peak chiller demand reduction
and electricity tariff cost savings under Time-of-Use tariffs.

Mathematical Formulation:
Coupled Differential Equations:
    dT_in / dt = (1 / (R1 * C_in)) * (T_amb - T_in) + (1 / (R2 * C_in)) * (T_env - T_in) + (Q_internal - Q_hvac) / C_in
    dT_env / dt = (1 / (R2 * C_env)) * (T_in - T_env)

Where:
    T_in(t): Indoor zone air temperature in degrees Celsius.
    T_amb(t): Ambient outdoor dry-bulb temperature in degrees Celsius.
    T_env(t): Internal building envelope structural mass temperature in degrees Celsius.
    C_in: Thermal capacitance of zone indoor air volume (kJ/deg C).
    C_env: Thermal capacitance of building structural envelope mass (kJ/deg C).
    R1: Thermal resistance of window glazing and air infiltration (deg C/kW).
    R2: Thermal resistance between indoor air and building envelope boundary (deg C/kW).
    Q_internal: Dynamic sensible heat gains in kW (q_occ * N_occ + P_lighting + P_plug).
    Q_hvac: Thermal cooling extraction rate delivered by chiller/fan-coil (kW_th).
    P_hvac_elec: Electrical chiller compressor power (Q_hvac / chiller_cooling_cop).
"""

from datetime import datetime, timezone
import logging
import math
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("digital_twin.energy.building_thermal")

# Non-actuation architectural governance disclaimer
NON_ACTUATION_DISCLAIMER = (
    "Advisory Only (Non-Actuating). Dynamic setbacks and pre-cooling schedules "
    "are simulation projections requiring authorized facility BMS dispatch."
)


class ThermalZoneConfig(BaseModel):
    """
    Physical structural parameters and 2R-2C thermal parameters of a building zone.
    """
    model_config = ConfigDict(populate_by_name=True)

    zone_id: str = Field(..., alias="zoneId", description="Unique thermal zone identifier")
    building_id: str = Field(..., alias="buildingId", description="Parent building canonical entity URN")
    zone_name: str = Field(..., alias="zoneName", description="Human-readable zone name")
    floor_number: int = Field(..., alias="floorNumber", description="Floor level number")
    floor_area_sqm: float = Field(..., alias="floorAreaSqm", description="Gross floor area in square meters")
    thermal_capacitance_cin: float = Field(..., alias="thermalCapacitanceCin", description="Air capacitance in kJ/deg C")
    thermal_capacitance_cenv: float = Field(..., alias="thermalCapacitanceCenv", description="Envelope capacitance in kJ/deg C")
    thermal_resistance_r1: float = Field(..., alias="thermalResistanceR1", description="Infiltration resistance in deg C/kW")
    thermal_resistance_r2: float = Field(..., alias="thermalResistanceR2", description="Envelope boundary resistance in deg C/kW")
    chiller_cooling_cop: float = Field(default=4.2, alias="chillerCoolingCop", description="Chiller coefficient of performance")
    nominal_setpoint_c: float = Field(default=24.0, alias="nominalSetpointC", description="Nominal comfort setpoint in deg C")


class ThermalState(BaseModel):
    """
    Instantaneous thermal state, occupancy, and chiller power metrics for a zone.
    """
    model_config = ConfigDict(populate_by_name=True)

    zone_id: str = Field(..., alias="zoneId")
    zone_name: str = Field(..., alias="zoneName")
    observed_at: str = Field(..., alias="observedAt")
    temp_indoor_c: float = Field(..., alias="tempIndoorC")
    temp_envelope_c: float = Field(..., alias="tempEnvelopeC")
    temp_ambient_c: float = Field(..., alias="tempAmbientC")
    occupant_count: int = Field(..., alias="occupantCount")
    occupancy_density_pax_sqm: float = Field(..., alias="occupancyDensityPaxSqm")
    co2_ppm: float = Field(..., alias="co2Ppm")
    internal_heat_gain_kw: float = Field(..., alias="internalHeatGainKw")
    cooling_demand_kw_th: float = Field(..., alias="coolingDemandKwTh")
    chiller_electrical_kw: float = Field(..., alias="chillerElectricalKw")
    hvac_mode: str = Field(..., alias="hvacMode")
    target_setpoint_c: float = Field(..., alias="targetSetpointC")
    ashrae55_compliant: bool = Field(..., alias="ashrae55Compliant")
    comfort_deviation_c: float = Field(..., alias="comfortDeviationC")
    source_mode: str = Field(default="SIMULATION", alias="sourceMode")
    quality_status: str = Field(default="VALID", alias="qualityStatus")
    non_actuation_disclaimer: str = Field(default=NON_ACTUATION_DISCLAIMER, alias="nonActuationDisclaimer")


class SimulationStepRequest(BaseModel):
    """
    Input parameters to advance a zone 2R-2C thermal simulation by delta_t seconds.
    """
    model_config = ConfigDict(populate_by_name=True)

    dt_seconds: float = Field(default=900.0, ge=1.0, le=86400.0, alias="dtSeconds", description="Time step in seconds (default 15m)")
    temp_ambient_c: Optional[float] = Field(default=None, alias="tempAmbientC", description="Outdoor ambient dry-bulb temperature")
    occupant_count: Optional[int] = Field(default=None, ge=0, alias="occupantCount", description="Live occupant count")
    q_hvac_kw_th: Optional[float] = Field(default=None, ge=0.0, alias="qHvacKwTh", description="Forced chiller thermal extraction rate")
    lighting_kw: Optional[float] = Field(default=None, ge=0.0, alias="lightingKw", description="Lighting electrical power")
    plug_kw: Optional[float] = Field(default=None, ge=0.0, alias="plugKw", description="Plug load electrical power")
    enable_dynamic_setback: bool = Field(default=True, alias="enableDynamicSetback", description="Enable occupancy-triggered setback")


class PrecoolingSimulationRequest(BaseModel):
    """
    Parameters for 24-hour diurnal pre-cooling simulation vs baseline operation.
    """
    model_config = ConfigDict(populate_by_name=True)

    target_precool_temp_c: float = Field(default=22.0, ge=18.0, le=24.0, alias="targetPrecoolTempC")
    precool_start_hour: int = Field(default=2, ge=0, le=23, alias="precoolStartHour")
    precool_end_hour: int = Field(default=6, ge=0, le=23, alias="precoolEndHour")
    peak_start_hour: int = Field(default=18, ge=0, le=23, alias="peakStartHour")
    peak_end_hour: int = Field(default=22, ge=0, le=23, alias="peakEndHour")
    off_peak_tariff_inr_kwh: float = Field(default=4.50, ge=0.0, alias="offPeakTariffInrKwh")
    peak_tariff_inr_kwh: float = Field(default=11.50, ge=0.0, alias="peakTariffInrKwh")
    normal_tariff_inr_kwh: float = Field(default=7.50, ge=0.0, alias="normalTariffInrKwh")


class DiurnalProfileHour(BaseModel):
    """
    Hourly profile data item in a 24-hour diurnal thermal simulation.
    """
    model_config = ConfigDict(populate_by_name=True)

    hour: int = Field(..., ge=0, le=23)
    timestamp: str = Field(...)
    temp_ambient_c: float = Field(..., alias="tempAmbientC")
    occupant_count: int = Field(..., alias="occupantCount")
    occupancy_density_pax_sqm: float = Field(..., alias="occupancyDensityPaxSqm")
    hvac_mode: str = Field(..., alias="hvacMode")
    temp_indoor_c: float = Field(..., alias="tempIndoorC")
    temp_envelope_c: float = Field(..., alias="tempEnvelopeC")
    cooling_demand_kw_th: float = Field(..., alias="coolingDemandKwTh")
    chiller_electrical_kw: float = Field(..., alias="chillerElectricalKw")
    electricity_tariff_inr_kwh: float = Field(..., alias="electricityTariffInrKwh")
    hourly_cost_inr: float = Field(..., alias="hourlyCostInr")
    ashrae55_compliant: bool = Field(..., alias="ashrae55Compliant")


class PrecoolingSimulationResult(BaseModel):
    """
    Comparative 24-hour simulation results between baseline and pre-cooling strategies.
    """
    model_config = ConfigDict(populate_by_name=True)

    zone_id: str = Field(..., alias="zoneId")
    zone_name: str = Field(..., alias="zoneName")
    generated_at: str = Field(..., alias="generatedAt")
    source_mode: str = Field(default="SIMULATION", alias="sourceMode")
    baseline_profile: List[DiurnalProfileHour] = Field(..., alias="baselineProfile")
    precooling_profile: List[DiurnalProfileHour] = Field(..., alias="precoolingProfile")
    baseline_total_energy_kwh: float = Field(..., alias="baselineTotalEnergyKwh")
    precooling_total_energy_kwh: float = Field(..., alias="precoolingTotalEnergyKwh")
    baseline_total_cost_inr: float = Field(..., alias="baselineTotalCostInr")
    precooling_total_cost_inr: float = Field(..., alias="precoolingTotalCostInr")
    cost_savings_inr: float = Field(..., alias="costSavingsInr")
    cost_savings_pct: float = Field(..., alias="costSavingsPct")
    peak_demand_reduction_kw: float = Field(..., alias="peakDemandReductionKw")
    peak_demand_reduction_pct: float = Field(..., alias="peakDemandReductionPct")
    ashrae55_violations_baseline: int = Field(..., alias="ashrae55ViolationsBaseline")
    ashrae55_violations_precooling: int = Field(..., alias="ashrae55ViolationsPrecooling")
    non_actuation_disclaimer: str = Field(default=NON_ACTUATION_DISCLAIMER, alias="nonActuationDisclaimer")


class BuildingThermalService:
    """
    Core numerical physics and control engine for building thermal zones.
    Provides 2R-2C Runge-Kutta 4th-order ODE integration, occupancy setback,
    and diurnal pre-cooling optimization.
    """

    def __init__(self) -> None:
        # Default in-memory cache of zones if DB is uninitialized
        self._default_zones: Dict[str, ThermalZoneConfig] = {
            "ZONE-PHOENIX-RETAIL-01": ThermalZoneConfig(
                zone_id="ZONE-PHOENIX-RETAIL-01",
                building_id="urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01",
                zone_name="Phoenix Retail Concourse",
                floor_number=1,
                floor_area_sqm=12500.0,
                thermal_capacitance_cin=150000.0,
                thermal_capacitance_cenv=850000.0,
                thermal_resistance_r1=0.008,
                thermal_resistance_r2=0.003,
                chiller_cooling_cop=4.2,
                nominal_setpoint_c=24.0,
            ),
            "ZONE-SOLITAIRE-OFFICE-01": ThermalZoneConfig(
                zone_id="ZONE-SOLITAIRE-OFFICE-01",
                building_id="urn:ngsi-ld:Building:PUNE:BLD-SOLITAIRE-01",
                zone_name="Solitaire Corporate Office Floor",
                floor_number=4,
                floor_area_sqm=4500.0,
                thermal_capacitance_cin=60000.0,
                thermal_capacitance_cenv=350000.0,
                thermal_resistance_r1=0.015,
                thermal_resistance_r2=0.006,
                chiller_cooling_cop=4.2,
                nominal_setpoint_c=24.0,
            ),
            "ZONE-HYATT-BALLROOM-01": ThermalZoneConfig(
                zone_id="ZONE-HYATT-BALLROOM-01",
                building_id="urn:ngsi-ld:Building:PUNE:BLD-HYATT-01",
                zone_name="Hyatt Regency Grand Ballroom",
                floor_number=2,
                floor_area_sqm=2800.0,
                thermal_capacitance_cin=40000.0,
                thermal_capacitance_cenv=220000.0,
                thermal_resistance_r1=0.020,
                thermal_resistance_r2=0.008,
                chiller_cooling_cop=4.2,
                nominal_setpoint_c=24.0,
            ),
        }

    # =========================================================================
    # Physical ODE Derivatives & Runge-Kutta 4th-Order Integration
    # =========================================================================

    @staticmethod
    def compute_derivatives(
        t_in: float,
        t_env: float,
        t_amb: float,
        q_internal: float,
        q_hvac: float,
        r1: float,
        r2: float,
        c_in: float,
        c_env: float,
    ) -> Tuple[float, float]:
        """
        Evaluates coupled 2R-2C state derivatives (deg C / second).
        
        dT_in / dt = (1 / (R1 * C_in)) * (T_amb - T_in) + (1 / (R2 * C_in)) * (T_env - T_in) + (Q_internal - Q_hvac) / C_in
        dT_env / dt = (1 / (R2 * C_env)) * (T_in - T_env)
        """
        dt_in_dt = (
            (1.0 / (r1 * c_in)) * (t_amb - t_in)
            + (1.0 / (r2 * c_in)) * (t_env - t_in)
            + (q_internal - q_hvac) / c_in
        )
        dt_env_dt = (1.0 / (r2 * c_env)) * (t_in - t_env)
        return dt_in_dt, dt_env_dt

    def integrate_rk4(
        self,
        t_in_init: float,
        t_env_init: float,
        t_amb: float,
        q_internal: float,
        q_hvac: float,
        r1: float,
        r2: float,
        c_in: float,
        c_env: float,
        dt_seconds: float,
        max_sub_dt_seconds: float = 60.0,
    ) -> Tuple[float, float]:
        """
        Advances the 2R-2C state vector [T_in, T_env] forward by dt_seconds
        using sub-stepped Runge-Kutta 4th-order (RK4) integration for unconditional numerical stability.
        """
        n_steps = max(1, int(math.ceil(dt_seconds / max_sub_dt_seconds)))
        sub_dt = dt_seconds / float(n_steps)

        tin = t_in_init
        tenv = t_env_init

        for _ in range(n_steps):
            # Stage 1
            k1_in, k1_env = self.compute_derivatives(
                tin, tenv, t_amb, q_internal, q_hvac, r1, r2, c_in, c_env
            )

            # Stage 2
            t_in_k2 = tin + 0.5 * sub_dt * k1_in
            t_env_k2 = tenv + 0.5 * sub_dt * k1_env
            k2_in, k2_env = self.compute_derivatives(
                t_in_k2, t_env_k2, t_amb, q_internal, q_hvac, r1, r2, c_in, c_env
            )

            # Stage 3
            t_in_k3 = tin + 0.5 * sub_dt * k2_in
            t_env_k3 = tenv + 0.5 * sub_dt * k2_env
            k3_in, k3_env = self.compute_derivatives(
                t_in_k3, t_env_k3, t_amb, q_internal, q_hvac, r1, r2, c_in, c_env
            )

            # Stage 4
            t_in_k4 = tin + sub_dt * k3_in
            t_env_k4 = tenv + sub_dt * k3_env
            k4_in, k4_env = self.compute_derivatives(
                t_in_k4, t_env_k4, t_amb, q_internal, q_hvac, r1, r2, c_in, c_env
            )

            # Weighted combination
            tin += (sub_dt / 6.0) * (k1_in + 2.0 * k2_in + 2.0 * k3_in + k4_in)
            tenv += (sub_dt / 6.0) * (k1_env + 2.0 * k2_env + 2.0 * k3_env + k4_env)

        return tin, tenv

    # =========================================================================
    # Internal Heat Gains & Thermostatic Chiller Calculation
    # =========================================================================

    @staticmethod
    def calculate_internal_heat_gain(
        occupant_count: int,
        floor_area_sqm: float,
        lighting_kw: Optional[float] = None,
        plug_kw: Optional[float] = None,
    ) -> float:
        """
        Sensible heat gain in kW:
        Q_internal = q_occupant * occupant_count + P_lighting + P_plug
        where q_occupant = 0.10 kW/person (100 W).
        Defaults lighting to 8 W/m2 and plug load to 10 W/m2.
        """
        q_occ = 0.10 * float(occupant_count)
        p_light = lighting_kw if lighting_kw is not None else (floor_area_sqm * 0.008)
        p_plug = plug_kw if plug_kw is not None else (floor_area_sqm * 0.010)
        return round(q_occ + p_light + p_plug, 3)

    @staticmethod
    def evaluate_ashrae55_comfort(
        temp_indoor_c: float,
        occupant_count: int,
        nominal_setpoint_c: float = 24.0,
    ) -> Tuple[bool, float]:
        """
        Evaluates ASHRAE 55 statutory comfort envelope:
        23.0 deg C <= T_in <= 25.0 deg C (setpoint 24.0 deg C).
        Unoccupied intervals (occupant_count == 0) permit setback without comfort violation.
        Returns: (ashrae55_compliant, comfort_deviation_c).
        """
        if occupant_count == 0:
            return True, 0.0

        min_comfort = nominal_setpoint_c - 1.0  # 23.0 deg C
        max_comfort = nominal_setpoint_c + 1.0  # 25.0 deg C

        if min_comfort <= temp_indoor_c <= max_comfort:
            return True, 0.0
        elif temp_indoor_c > max_comfort:
            return False, round(temp_indoor_c - max_comfort, 2)
        else:
            return False, round(min_comfort - temp_indoor_c, 2)

    def determine_hvac_mode_and_setpoint(
        self,
        occupant_count: int,
        floor_area_sqm: float,
        nominal_setpoint_c: float = 24.0,
        enable_dynamic_setback: bool = True,
        mode_override: Optional[str] = None,
    ) -> Tuple[str, float]:
        """
        Determines operating mode and target setpoint.
        When occupancy density rho_occ < 0.10 pax/m2 and dynamic setback is enabled:
        expands setpoint by +2.5 deg C (to 26.5 deg C) under DYNAMIC_SETBACK mode.
        """
        if mode_override:
            mode = mode_override.upper()
            if mode == "PRE_COOLING":
                return "PRE_COOLING", 22.0
            elif mode == "UNOCCUPIED":
                return "UNOCCUPIED", 28.0
            elif mode == "DYNAMIC_SETBACK":
                return "DYNAMIC_SETBACK", nominal_setpoint_c + 2.5
            else:
                return "COMFORT", nominal_setpoint_c

        if occupant_count == 0:
            return "UNOCCUPIED", 28.0

        density = occupant_count / floor_area_sqm if floor_area_sqm > 0 else 0.0
        if enable_dynamic_setback and density < 0.10:
            return "DYNAMIC_SETBACK", nominal_setpoint_c + 2.5
        return "COMFORT", nominal_setpoint_c

    def calculate_thermostatic_cooling(
        self,
        t_in: float,
        t_env: float,
        t_amb: float,
        q_internal: float,
        target_setpoint_c: float,
        r1: float,
        r2: float,
        c_in: float,
        dt_seconds: float,
        max_cooling_kw_th: float,
    ) -> float:
        """
        Computes closed-loop thermostatic cooling extraction rate (kW_th)
        required to drive zone indoor air toward target_setpoint_c over dt_seconds.
        """
        if t_in <= target_setpoint_c:
            return 0.0

        # Required extraction to balance heat flows and pull air temperature down to target
        q_steady = q_internal + (t_amb - t_in) / r1 + (t_env - t_in) / r2
        q_transient = c_in * (t_in - target_setpoint_c) / dt_seconds
        q_needed = q_steady + q_transient
        return max(0.0, min(max_cooling_kw_th, q_needed))

    # =========================================================================
    # Step Simulation & State Transition
    # =========================================================================

    def step_simulation(
        self,
        zone: ThermalZoneConfig,
        current_t_in: float,
        current_t_env: float,
        step_req: SimulationStepRequest,
    ) -> ThermalState:
        """
        Executes one discrete simulation step for a zone across dt_seconds.
        """
        dt = step_req.dt_seconds
        now_str = datetime.now(timezone.utc).isoformat()

        # Ambient temperature default: 32.0 deg C if unspecified
        t_amb = step_req.temp_ambient_c if step_req.temp_ambient_c is not None else 32.0

        # Occupant count default: 200 if unspecified
        occ_count = step_req.occupant_count if step_req.occupant_count is not None else 200
        density = occ_count / zone.floor_area_sqm if zone.floor_area_sqm > 0 else 0.0
        co2_ppm = round(420.0 + min(1200.0, occ_count * 1.5), 1)

        # Mode and setpoint determination
        hvac_mode, target_setpoint = self.determine_hvac_mode_and_setpoint(
            occupant_count=occ_count,
            floor_area_sqm=zone.floor_area_sqm,
            nominal_setpoint_c=zone.nominal_setpoint_c,
            enable_dynamic_setback=step_req.enable_dynamic_setback,
        )

        # Internal heat gains
        q_internal = self.calculate_internal_heat_gain(
            occupant_count=occ_count,
            floor_area_sqm=zone.floor_area_sqm,
            lighting_kw=step_req.lighting_kw,
            plug_kw=step_req.plug_kw,
        )

        # Cooling demand: explicit or thermostatic
        max_cooling_kw_th = zone.floor_area_sqm * 0.12  # 120 W/m2 chiller capacity
        if step_req.q_hvac_kw_th is not None:
            q_hvac = min(max_cooling_kw_th, step_req.q_hvac_kw_th)
        else:
            q_hvac = self.calculate_thermostatic_cooling(
                t_in=current_t_in,
                t_env=current_t_env,
                t_amb=t_amb,
                q_internal=q_internal,
                target_setpoint_c=target_setpoint,
                r1=zone.thermal_resistance_r1,
                r2=zone.thermal_resistance_r2,
                c_in=zone.thermal_capacitance_cin,
                dt_seconds=dt,
                max_cooling_kw_th=max_cooling_kw_th,
            )

        # RK4 ODE Integration
        next_t_in, next_t_env = self.integrate_rk4(
            t_in_init=current_t_in,
            t_env_init=current_t_env,
            t_amb=t_amb,
            q_internal=q_internal,
            q_hvac=q_hvac,
            r1=zone.thermal_resistance_r1,
            r2=zone.thermal_resistance_r2,
            c_in=zone.thermal_capacitance_cin,
            c_env=zone.thermal_capacitance_cenv,
            dt_seconds=dt,
        )

        # Chiller electrical power
        cop = zone.chiller_cooling_cop if zone.chiller_cooling_cop > 0 else 4.2
        chiller_elec_kw = round(q_hvac / cop, 2)

        # Comfort evaluation
        compliant, deviation = self.evaluate_ashrae55_comfort(
            temp_indoor_c=next_t_in,
            occupant_count=occ_count,
            nominal_setpoint_c=zone.nominal_setpoint_c,
        )

        return ThermalState(
            zone_id=zone.zone_id,
            zone_name=zone.zone_name,
            observed_at=now_str,
            temp_indoor_c=round(next_t_in, 2),
            temp_envelope_c=round(next_t_env, 2),
            temp_ambient_c=round(t_amb, 2),
            occupant_count=occ_count,
            occupancy_density_pax_sqm=round(density, 4),
            co2_ppm=co2_ppm,
            internal_heat_gain_kw=round(q_internal, 2),
            cooling_demand_kw_th=round(q_hvac, 2),
            chiller_electrical_kw=chiller_elec_kw,
            hvac_mode=hvac_mode,
            target_setpoint_c=round(target_setpoint, 2),
            ashrae55_compliant=compliant,
            comfort_deviation_c=deviation,
            source_mode="SIMULATION",
            quality_status="VALID",
            non_actuation_disclaimer=NON_ACTUATION_DISCLAIMER,
        )

    # =========================================================================
    # 24-Hour Diurnal Pre-cooling Strategy Simulator
    # =========================================================================

    @staticmethod
    def get_diurnal_ambient_temp(hour: int) -> float:
        """
        Diurnal outdoor ambient temperature profile for reference urban corridor.
        Daily low ~21.0 deg C at 04:00, peak ~36.0 deg C at 15:00.
        """
        t_min = 21.0
        t_max = 36.0
        t_mean = (t_max + t_min) / 2.0
        t_amp = (t_max - t_min) / 2.0
        return round(t_mean - t_amp * math.cos(math.pi * (hour - 3.5) / 12.0), 2)

    @staticmethod
    def get_diurnal_occupants(hour: int, floor_area_sqm: float) -> int:
        """
        Diurnal occupancy profile for typical commercial facility.
        """
        if 0 <= hour <= 6:
            fraction = 0.0
        elif hour in (7, 8):
            fraction = 0.02
        elif 9 <= hour <= 11:
            fraction = 0.06
        elif 12 <= hour <= 14:
            fraction = 0.12  # Peak density
        elif 15 <= hour <= 18:
            fraction = 0.08
        elif 19 <= hour <= 21:
            fraction = 0.05
        else:
            fraction = 0.01
        return int(round(fraction * floor_area_sqm))

    def get_electricity_tariff(
        self,
        hour: int,
        req: PrecoolingSimulationRequest,
    ) -> float:
        """
        Time-of-Use tariff mapping in INR/kWh.
        """
        if req.precool_start_hour <= hour <= req.precool_end_hour:
            return req.off_peak_tariff_inr_kwh
        elif req.peak_start_hour <= hour <= req.peak_end_hour:
            return req.peak_tariff_inr_kwh
        else:
            return req.normal_tariff_inr_kwh

    def simulate_precooling_comparison(
        self,
        zone: ThermalZoneConfig,
        req: PrecoolingSimulationRequest,
    ) -> PrecoolingSimulationResult:
        """
        Executes parallel 24-hour diurnal simulations:
        1. Baseline run: standard thermostat control (24.0 C during occupied hours, 28.0 C unoccupied).
        2. Pre-cooling run: pre-cools thermal mass to target_precool_temp_c during off-peak hours,
           enables dynamic setback, and floats setpoint during peak pricing hours to shave chiller load.
        """
        dt_hour = 3600.0  # 1 hour steps
        now_dt = datetime.now(timezone.utc)
        generated_at = now_dt.isoformat()

        baseline_profile: List[DiurnalProfileHour] = []
        precool_profile: List[DiurnalProfileHour] = []

        # Baseline simulation state
        base_t_in = 24.5
        base_t_env = 25.0

        # Pre-cooling simulation state
        prec_t_in = 24.5
        prec_t_env = 25.0

        max_cooling_kw_th = zone.floor_area_sqm * 0.12
        cop = zone.chiller_cooling_cop if zone.chiller_cooling_cop > 0 else 4.2

        base_total_kwh = 0.0
        base_total_cost = 0.0
        base_violations = 0

        prec_total_kwh = 0.0
        prec_total_cost = 0.0
        prec_violations = 0

        base_peak_kws: List[float] = []
        prec_peak_kws: List[float] = []

        for h in range(24):
            t_amb = self.get_diurnal_ambient_temp(h)
            occ_count = self.get_diurnal_occupants(h, zone.floor_area_sqm)
            density = occ_count / zone.floor_area_sqm if zone.floor_area_sqm > 0 else 0.0
            tariff = self.get_electricity_tariff(h, req)
            time_stamp = f"{h:02d}:00"

            q_internal = self.calculate_internal_heat_gain(
                occupant_count=occ_count,
                floor_area_sqm=zone.floor_area_sqm,
            )

            # -----------------------------------------------------------------
            # 1. Baseline Simulation Step
            # -----------------------------------------------------------------
            if occ_count > 0:
                base_mode = "COMFORT"
                base_target_sp = zone.nominal_setpoint_c
            else:
                base_mode = "UNOCCUPIED"
                base_target_sp = 28.0

            q_base = self.calculate_thermostatic_cooling(
                t_in=base_t_in,
                t_env=base_t_env,
                t_amb=t_amb,
                q_internal=q_internal,
                target_setpoint_c=base_target_sp,
                r1=zone.thermal_resistance_r1,
                r2=zone.thermal_resistance_r2,
                c_in=zone.thermal_capacitance_cin,
                dt_seconds=dt_hour,
                max_cooling_kw_th=max_cooling_kw_th,
            )

            next_base_tin, next_base_tenv = self.integrate_rk4(
                t_in_init=base_t_in,
                t_env_init=base_t_env,
                t_amb=t_amb,
                q_internal=q_internal,
                q_hvac=q_base,
                r1=zone.thermal_resistance_r1,
                r2=zone.thermal_resistance_r2,
                c_in=zone.thermal_capacitance_cin,
                c_env=zone.thermal_capacitance_cenv,
                dt_seconds=dt_hour,
            )
            base_t_in = next_base_tin
            base_t_env = next_base_tenv

            base_chiller_kw = round(q_base / cop, 2)
            base_cost_h = round(base_chiller_kw * tariff, 2)
            base_total_kwh += base_chiller_kw
            base_total_cost += base_cost_h

            base_comp, _ = self.evaluate_ashrae55_comfort(
                temp_indoor_c=base_t_in,
                occupant_count=occ_count,
                nominal_setpoint_c=zone.nominal_setpoint_c,
            )
            if not base_comp:
                base_violations += 1

            if req.peak_start_hour <= h <= req.peak_end_hour:
                base_peak_kws.append(base_chiller_kw)

            baseline_profile.append(
                DiurnalProfileHour(
                    hour=h,
                    timestamp=time_stamp,
                    temp_ambient_c=t_amb,
                    occupant_count=occ_count,
                    occupancy_density_pax_sqm=round(density, 4),
                    hvac_mode=base_mode,
                    temp_indoor_c=round(base_t_in, 2),
                    temp_envelope_c=round(base_t_env, 2),
                    cooling_demand_kw_th=round(q_base, 2),
                    chiller_electrical_kw=base_chiller_kw,
                    electricity_tariff_inr_kwh=tariff,
                    hourly_cost_inr=base_cost_h,
                    ashrae55_compliant=base_comp,
                )
            )

            # -----------------------------------------------------------------
            # 2. Pre-cooling Simulation Step
            # -----------------------------------------------------------------
            if req.precool_start_hour <= h <= req.precool_end_hour:
                # Active pre-cooling off-peak window: pull mass down to 22.0 C
                prec_mode = "PRE_COOLING"
                prec_target_sp = req.target_precool_temp_c
            elif req.peak_start_hour <= h <= req.peak_end_hour:
                # Peak tariff window: coast on envelope inertia, float setpoint to 25.0 C
                prec_mode = "PEAK_SHEDDING"
                prec_target_sp = zone.nominal_setpoint_c + 1.0  # 25.0 deg C (max comfort bound)
            elif occ_count == 0:
                prec_mode = "UNOCCUPIED"
                prec_target_sp = 28.0
            elif density < 0.10:
                prec_mode = "DYNAMIC_SETBACK"
                prec_target_sp = zone.nominal_setpoint_c + 2.5  # 26.5 deg C
            else:
                prec_mode = "COMFORT"
                prec_target_sp = zone.nominal_setpoint_c

            q_prec = self.calculate_thermostatic_cooling(
                t_in=prec_t_in,
                t_env=prec_t_env,
                t_amb=t_amb,
                q_internal=q_internal,
                target_setpoint_c=prec_target_sp,
                r1=zone.thermal_resistance_r1,
                r2=zone.thermal_resistance_r2,
                c_in=zone.thermal_capacitance_cin,
                dt_seconds=dt_hour,
                max_cooling_kw_th=max_cooling_kw_th,
            )

            next_prec_tin, next_prec_tenv = self.integrate_rk4(
                t_in_init=prec_t_in,
                t_env_init=prec_t_env,
                t_amb=t_amb,
                q_internal=q_internal,
                q_hvac=q_prec,
                r1=zone.thermal_resistance_r1,
                r2=zone.thermal_resistance_r2,
                c_in=zone.thermal_capacitance_cin,
                c_env=zone.thermal_capacitance_cenv,
                dt_seconds=dt_hour,
            )
            prec_t_in = next_prec_tin
            prec_t_env = next_prec_tenv

            prec_chiller_kw = round(q_prec / cop, 2)
            prec_cost_h = round(prec_chiller_kw * tariff, 2)
            prec_total_kwh += prec_chiller_kw
            prec_total_cost += prec_cost_h

            prec_comp, _ = self.evaluate_ashrae55_comfort(
                temp_indoor_c=prec_t_in,
                occupant_count=occ_count,
                nominal_setpoint_c=zone.nominal_setpoint_c,
            )
            if not prec_comp:
                prec_violations += 1

            if req.peak_start_hour <= h <= req.peak_end_hour:
                prec_peak_kws.append(prec_chiller_kw)

            precool_profile.append(
                DiurnalProfileHour(
                    hour=h,
                    timestamp=time_stamp,
                    temp_ambient_c=t_amb,
                    occupant_count=occ_count,
                    occupancy_density_pax_sqm=round(density, 4),
                    hvac_mode=prec_mode,
                    temp_indoor_c=round(prec_t_in, 2),
                    temp_envelope_c=round(prec_t_env, 2),
                    cooling_demand_kw_th=round(q_prec, 2),
                    chiller_electrical_kw=prec_chiller_kw,
                    electricity_tariff_inr_kwh=tariff,
                    hourly_cost_inr=prec_cost_h,
                    ashrae55_compliant=prec_comp,
                )
            )

        # Performance summary metrics
        cost_diff = base_total_cost - prec_total_cost
        cost_savings_pct = (cost_diff / base_total_cost * 100.0) if base_total_cost > 0 else 0.0

        max_base_peak = max(base_peak_kws) if base_peak_kws else 0.0
        max_prec_peak = max(prec_peak_kws) if prec_peak_kws else 0.0
        peak_reduction_kw = max(0.0, max_base_peak - max_prec_peak)
        peak_reduction_pct = (peak_reduction_kw / max_base_peak * 100.0) if max_base_peak > 0 else 0.0

        return PrecoolingSimulationResult(
            zone_id=zone.zone_id,
            zone_name=zone.zone_name,
            generated_at=generated_at,
            source_mode="SIMULATION",
            baseline_profile=baseline_profile,
            precooling_profile=precool_profile,
            baseline_total_energy_kwh=round(base_total_kwh, 2),
            precooling_total_energy_kwh=round(prec_total_kwh, 2),
            baseline_total_cost_inr=round(base_total_cost, 2),
            precooling_total_cost_inr=round(prec_total_cost, 2),
            cost_savings_inr=round(cost_diff, 2),
            cost_savings_pct=round(cost_savings_pct, 2),
            peak_demand_reduction_kw=round(peak_reduction_kw, 2),
            peak_demand_reduction_pct=round(peak_reduction_pct, 2),
            ashrae55_violations_baseline=base_violations,
            ashrae55_violations_precooling=prec_violations,
            non_actuation_disclaimer=NON_ACTUATION_DISCLAIMER,
        )

    # =========================================================================
    # Database Persistence & API Integration
    # =========================================================================

    async def get_all_thermal_zones(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """
        Retrieves all thermal zones with their physical configuration and latest telemetry state.
        """
        try:
            query = text("""
                SELECT 
                    z.id, z.building_id, z.zone_name, z.floor_number, z.floor_area_sqm,
                    z.thermal_capacitance_cin, z.thermal_capacitance_cenv,
                    z.thermal_resistance_r1, z.thermal_resistance_r2,
                    z.chiller_cooling_cop, z.nominal_setpoint_c,
                    t.observed_at, t.occupant_count, t.co2_ppm, t.occupancy_density_pax_sqm,
                    t.hvac_mode, t.current_temp_c, t.envelope_temp_c, t.cooling_kw_th,
                    t.chiller_electrical_kw, t.ashrae55_compliant
                FROM building_thermal_zones z
                LEFT JOIN zone_occupancy_telemetry t ON t.id = (
                    SELECT id FROM zone_occupancy_telemetry
                    WHERE zone_id = z.id
                    ORDER BY observed_at DESC
                    LIMIT 1
                )
                ORDER BY z.id ASC;
            """)
            res = await session.execute(query)
            rows = res.fetchall()

            if not rows:
                # Fallback to in-memory canonical defaults
                results = []
                for zone in self._default_zones.values():
                    results.append({
                        "zoneId": zone.zone_id,
                        "buildingId": zone.building_id,
                        "zoneName": zone.zone_name,
                        "floorNumber": zone.floor_number,
                        "floorAreaSqm": zone.floor_area_sqm,
                        "thermalCapacitanceCin": zone.thermal_capacitance_cin,
                        "thermalCapacitanceCenv": zone.thermal_capacitance_cenv,
                        "thermalResistanceR1": zone.thermal_resistance_r1,
                        "thermalResistanceR2": zone.thermal_resistance_r2,
                        "chillerCoolingCop": zone.chiller_cooling_cop,
                        "nominalSetpointC": zone.nominal_setpoint_c,
                        "currentTempC": 24.2,
                        "envelopeTempC": 24.5,
                        "occupantCount": 200,
                        "occupancyDensityPaxSqm": 0.044,
                        "co2Ppm": 620.0,
                        "hvacMode": "DYNAMIC_SETBACK",
                        "coolingKwTh": 120.0,
                        "chillerElectricalKw": 28.57,
                        "ashrae55Compliant": True,
                        "sourceMode": "SIMULATION",
                    })
                return results

            results = []
            for r in rows:
                t_in = float(r[16]) if r[16] is not None else float(r[10])
                occ = int(r[12]) if r[12] is not None else 0
                comp = bool(r[20]) if r[20] is not None else True
                results.append({
                    "zoneId": str(r[0]),
                    "buildingId": str(r[1]),
                    "zoneName": str(r[2]),
                    "floorNumber": int(r[3]),
                    "floorAreaSqm": float(r[4]),
                    "thermalCapacitanceCin": float(r[5]),
                    "thermalCapacitanceCenv": float(r[6]),
                    "thermalResistanceR1": float(r[7]),
                    "thermalResistanceR2": float(r[8]),
                    "chillerCoolingCop": float(r[9]),
                    "nominalSetpointC": float(r[10]),
                    "observedAt": str(r[11]) if r[11] is not None else datetime.now(timezone.utc).isoformat(),
                    "occupantCount": occ,
                    "co2Ppm": float(r[13]) if r[13] is not None else 450.0,
                    "occupancyDensityPaxSqm": float(r[14]) if r[14] is not None else 0.0,
                    "hvacMode": str(r[15]) if r[15] is not None else "COMFORT",
                    "currentTempC": t_in,
                    "envelopeTempC": float(r[17]) if r[17] is not None else (t_in + 0.3),
                    "coolingKwTh": float(r[18]) if r[18] is not None else 0.0,
                    "chillerElectricalKw": float(r[19]) if r[19] is not None else 0.0,
                    "ashrae55Compliant": comp,
                    "sourceMode": "SIMULATION",
                })
            return results
        except Exception as ex:
            logger.error("Failed to query thermal zones: %s", ex, exc_info=True)
            return []

    async def get_zone_config(self, zone_id: str, session: AsyncSession) -> Optional[ThermalZoneConfig]:
        """
        Retrieves the physical configuration for a specific thermal zone.
        """
        try:
            stmt = text("""
                SELECT 
                    id, building_id, zone_name, floor_number, floor_area_sqm,
                    thermal_capacitance_cin, thermal_capacitance_cenv,
                    thermal_resistance_r1, thermal_resistance_r2,
                    chiller_cooling_cop, nominal_setpoint_c
                FROM building_thermal_zones
                WHERE id = :zone_id
                LIMIT 1;
            """)
            res = await session.execute(stmt, {"zone_id": zone_id})
            row = res.fetchone()
            if row:
                return ThermalZoneConfig(
                    zone_id=str(row[0]),
                    building_id=str(row[1]),
                    zone_name=str(row[2]),
                    floor_number=int(row[3]),
                    floor_area_sqm=float(row[4]),
                    thermal_capacitance_cin=float(row[5]),
                    thermal_capacitance_cenv=float(row[6]),
                    thermal_resistance_r1=float(row[7]),
                    thermal_resistance_r2=float(row[8]),
                    chiller_cooling_cop=float(row[9]),
                    nominal_setpoint_c=float(row[10]),
                )
        except Exception as ex:
            logger.warning("DB query for zone %s failed: %s", zone_id, ex)

        return self._default_zones.get(zone_id)

    async def get_latest_zone_state(
        self,
        zone_id: str,
        session: AsyncSession,
    ) -> Optional[ThermalState]:
        """
        Fetches the latest recorded thermal state for a zone from database.
        """
        cfg = await self.get_zone_config(zone_id, session)
        if not cfg:
            return None

        try:
            stmt = text("""
                SELECT 
                    observed_at, occupant_count, co2_ppm, occupancy_density_pax_sqm,
                    hvac_mode, current_temp_c, envelope_temp_c, cooling_kw_th,
                    chiller_electrical_kw, ashrae55_compliant
                FROM zone_occupancy_telemetry
                WHERE zone_id = :zone_id
                ORDER BY observed_at DESC
                LIMIT 1;
            """)
            res = await session.execute(stmt, {"zone_id": zone_id})
            r = res.fetchone()
            if r:
                t_in = float(r[5])
                occ = int(r[1])
                comp, dev = self.evaluate_ashrae55_comfort(t_in, occ, cfg.nominal_setpoint_c)
                q_int = self.calculate_internal_heat_gain(occ, cfg.floor_area_sqm)
                _, sp = self.determine_hvac_mode_and_setpoint(occ, cfg.floor_area_sqm, cfg.nominal_setpoint_c)

                return ThermalState(
                    zone_id=cfg.zone_id,
                    zone_name=cfg.zone_name,
                    observed_at=str(r[0]),
                    temp_indoor_c=round(t_in, 2),
                    temp_envelope_c=round(float(r[6]), 2),
                    temp_ambient_c=31.5,
                    occupant_count=occ,
                    occupancy_density_pax_sqm=round(float(r[3]), 4),
                    co2_ppm=round(float(r[2]), 1),
                    internal_heat_gain_kw=q_int,
                    cooling_demand_kw_th=round(float(r[7]), 2),
                    chiller_electrical_kw=round(float(r[8]), 2),
                    hvac_mode=str(r[4]),
                    target_setpoint_c=sp,
                    ashrae55_compliant=comp,
                    comfort_deviation_c=dev,
                    source_mode="SIMULATION",
                    quality_status="VALID",
                    non_actuation_disclaimer=NON_ACTUATION_DISCLAIMER,
                )
        except Exception as ex:
            logger.warning("DB query for zone state %s failed: %s", zone_id, ex)

        # Fallback state if database has no records
        return ThermalState(
            zone_id=cfg.zone_id,
            zone_name=cfg.zone_name,
            observed_at=datetime.now(timezone.utc).isoformat(),
            temp_indoor_c=24.2,
            temp_envelope_c=24.5,
            temp_ambient_c=32.0,
            occupant_count=150,
            occupancy_density_pax_sqm=round(150 / cfg.floor_area_sqm, 4),
            co2_ppm=600.0,
            internal_heat_gain_kw=self.calculate_internal_heat_gain(150, cfg.floor_area_sqm),
            cooling_demand_kw_th=110.0,
            chiller_electrical_kw=round(110.0 / cfg.chiller_cooling_cop, 2),
            hvac_mode="DYNAMIC_SETBACK",
            target_setpoint_c=26.5,
            ashrae55_compliant=True,
            comfort_deviation_c=0.0,
            source_mode="SIMULATION",
            quality_status="VALID",
            non_actuation_disclaimer=NON_ACTUATION_DISCLAIMER,
        )

    async def advance_zone_step(
        self,
        zone_id: str,
        step_req: SimulationStepRequest,
        session: AsyncSession,
    ) -> Optional[ThermalState]:
        """
        Advances the 2R-2C simulation for a zone by dt_seconds, records the state
        to zone_occupancy_telemetry, and returns the updated ThermalState.
        """
        cfg = await self.get_zone_config(zone_id, session)
        if not cfg:
            return None

        latest_state = await self.get_latest_zone_state(zone_id, session)
        current_t_in = latest_state.temp_indoor_c if latest_state else 24.0
        current_t_env = latest_state.temp_envelope_c if latest_state else 24.5

        next_state = self.step_simulation(
            zone=cfg,
            current_t_in=current_t_in,
            current_t_env=current_t_env,
            step_req=step_req,
        )

        # Persist new state to database
        try:
            stmt = text("""
                INSERT INTO zone_occupancy_telemetry (
                    zone_id, observed_at, occupant_count, co2_ppm,
                    occupancy_density_pax_sqm, hvac_mode, current_temp_c,
                    envelope_temp_c, cooling_kw_th, chiller_electrical_kw,
                    ashrae55_compliant, source_mode
                ) VALUES (
                    :zone_id, :observed_at, :occupant_count, :co2_ppm,
                    :occupancy_density_pax_sqm, :hvac_mode, :current_temp_c,
                    :envelope_temp_c, :cooling_kw_th, :chiller_electrical_kw,
                    :ashrae55_compliant, :source_mode
                );
            """)
            await session.execute(stmt, {
                "zone_id": next_state.zone_id,
                "observed_at": next_state.observed_at,
                "occupant_count": next_state.occupant_count,
                "co2_ppm": next_state.co2_ppm,
                "occupancy_density_pax_sqm": next_state.occupancy_density_pax_sqm,
                "hvac_mode": next_state.hvac_mode,
                "current_temp_c": next_state.temp_indoor_c,
                "envelope_temp_c": next_state.temp_envelope_c,
                "cooling_kw_th": next_state.cooling_demand_kw_th,
                "chiller_electrical_kw": next_state.chiller_electrical_kw,
                "ashrae55_compliant": 1 if next_state.ashrae55_compliant else 0,
                "source_mode": "SIMULATION",
            })
            await session.commit()
        except Exception as ex:
            logger.warning("Failed to persist zone occupancy telemetry for %s: %s", zone_id, ex)
            await session.rollback()

        return next_state


# Canonical singleton export
building_thermal_service = BuildingThermalService()

__all__ = [
    "ThermalZoneConfig",
    "ThermalState",
    "SimulationStepRequest",
    "PrecoolingSimulationRequest",
    "DiurnalProfileHour",
    "PrecoolingSimulationResult",
    "BuildingThermalService",
    "building_thermal_service",
]
