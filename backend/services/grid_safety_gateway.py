"""
grid_safety_gateway.py

Grid Safety Interlocks, Communication Watchdog, and OpenADR / Modbus Failsafe Dispatch Gateway (ENERGY-07).
Enforces physical grid interlocks before any demand response or battery energy storage dispatch:
1. Under/over-voltage lockout: 0.94 * V_nom <= V_line <= 1.06 * V_nom (390.1V to 439.9V for 415V nominal).
   Violations reject dispatch and revert to grid-following standby.
2. Ramp-rate slew throttling: |delta_P / delta_t| <= 0.10 * P_rated (kW/min) (e.g. max 200 kW/min for 2000 kW BESS).
   Excessive ramp steps are rejected or throttled to prevent feeder voltage fluctuations.
3. Dead-band thresholding: suppresses dispatch chattering if |delta_P_shave| < 15.0 kW.
4. Communication loss fallback: t_now - t_heartbeat > 60.0s triggers COMMUNICATION_LOST_FAILSAFE
   and reverts to local autonomous BMS.

Serializes approved dispatches into:
- OpenADR 2.0b distributeEvent XML and JSON payloads.
- Modbus TCP holding registers (40001-40005).

Adheres strictly to the Non-Actuation Invariant: dispatches are advisory decision support only.
Local BMS and physical protection relays remain authoritative.
"""

from datetime import datetime, timezone
import logging
import math
import threading
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid
import xml.etree.ElementTree as ET

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("digital_twin.energy.grid_safety_gateway")


class CandidateDispatchRequest(BaseModel):
    """
    Request payload schema for candidate dispatch safety validation.
    Supports both snake_case and camelCase field aliases.
    """
    model_config = ConfigDict(populate_by_name=True)

    facility_id: str = Field(
        default="urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01",
        alias="facilityId",
        description="Target facility or building entity identifier"
    )
    candidate_power_kw: float = Field(
        default=0.0,
        alias="candidatePowerKw",
        description="Requested dispatch active power magnitude in kW"
    )
    current_power_kw: Optional[float] = Field(
        default=None,
        alias="currentPowerKw",
        description="Current active battery power in kW before this step (None uses gateway state)"
    )
    line_voltage_v: float = Field(
        default=415.0,
        alias="lineVoltageV",
        ge=0.0,
        description="Measured 3-phase line-to-line AC voltage at point of common coupling in Volts"
    )
    nominal_voltage_v: float = Field(
        default=415.0,
        alias="nominalVoltageV",
        gt=0.0,
        description="Nominal line-to-line AC voltage in Volts (typically 415.0V)"
    )
    soc_pct: float = Field(
        default=50.0,
        alias="socPct",
        ge=0.0,
        le=100.0,
        description="Current battery State of Charge percentage"
    )
    rated_power_kw: float = Field(
        default=2000.0,
        alias="ratedPowerKw",
        gt=0.0,
        description="Rated BESS converter power in kW (used for ramp-rate calculation)"
    )
    delta_t_minutes: float = Field(
        default=1.0,
        alias="deltaTMinutes",
        gt=0.0,
        description="Time delta since previous setpoint adjustment in minutes"
    )
    action: Optional[str] = Field(
        default=None,
        description="Intended action: CHARGE, DISCHARGE, or STANDBY"
    )
    target_id: Optional[str] = Field(
        default=None,
        alias="targetId",
        description="OpenADR target identifier (defaults to facility_id)"
    )
    resource_id: Optional[str] = Field(
        default="BESS-PHOENIX-01",
        alias="resourceId",
        description="OpenADR resource identifier"
    )
    event_id: Optional[str] = Field(
        default=None,
        alias="eventId",
        description="Optional pre-assigned OpenADR event identifier"
    )
    duration: Optional[str] = Field(
        default="PT1H",
        description="Dispatch duration in ISO 8601 duration format"
    )

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True)


class HeartbeatPingRequest(BaseModel):
    """
    Keepalive heartbeat registration request schema.
    """
    model_config = ConfigDict(populate_by_name=True)

    sender_id: str = Field(
        default="BMS-LOCAL-ACTUATOR-01",
        alias="senderId",
        description="Identifier of the actuator, SCADA client, or BMS controller sending heartbeat"
    )
    timestamp: Optional[float] = Field(
        default=None,
        description="Optional Unix timestamp of ping in seconds (defaults to server time)"
    )

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True)


class ModbusRegisterMap(BaseModel):
    """
    Modbus TCP Holding Register Block for SCADA / BMS Inverter Controllers.
    Registers:
    - 40001: Setpoint High (high word of 32-bit active power setpoint in kW)
    - 40002: Setpoint Low (low word of 32-bit active power setpoint in kW)
    - 40003: Inverter Control Mode (0=Standby, 1=Charge, 2=Discharge, 3=Failsafe)
    - 40004: Interlock Status Bitmask (bit 0=voltage, bit 1=ramp, bit 2=soc, bit 3=heartbeat)
    - 40005: Watchdog Counter (monotonic tick counter)
    """
    model_config = ConfigDict(populate_by_name=True)

    setpoint_high: int = Field(..., alias="setpointHigh", ge=0, le=65535, description="Register 40001: Setpoint High Word")
    setpoint_low: int = Field(..., alias="setpointLow", ge=0, le=65535, description="Register 40002: Setpoint Low Word")
    control_mode: int = Field(..., alias="controlMode", ge=0, le=3, description="Register 40003: Control Mode (0=Standby, 1=Charge, 2=Discharge, 3=Failsafe)")
    interlock_bitmask: int = Field(..., alias="interlockBitmask", ge=0, le=15, description="Register 40004: Interlock Bitmask (bit 0=volt, 1=ramp, 2=soc, 3=heartbeat)")
    watchdog_counter: int = Field(..., alias="watchdogCounter", ge=0, le=65535, description="Register 40005: Watchdog Counter")

    @property
    def raw_registers(self) -> Dict[int, int]:
        return {
            40001: self.setpoint_high,
            40002: self.setpoint_low,
            40003: self.control_mode,
            40004: self.interlock_bitmask,
            40005: self.watchdog_counter,
        }

    @property
    def named_registers(self) -> Dict[str, int]:
        return {
            "40001_setpoint_high": self.setpoint_high,
            "40002_setpoint_low": self.setpoint_low,
            "40003_control_mode": self.control_mode,
            "40004_interlock_bitmask": self.interlock_bitmask,
            "40005_watchdog_counter": self.watchdog_counter,
        }

    def to_register_list(self) -> List[int]:
        return [
            self.setpoint_high,
            self.setpoint_low,
            self.control_mode,
            self.interlock_bitmask,
            self.watchdog_counter,
        ]

    def to_dict(self) -> Dict[str, Any]:
        d = self.model_dump(by_alias=True)
        d["rawRegisters"] = self.raw_registers
        d["namedRegisters"] = self.named_registers
        return d


class OpenADREventPayload(BaseModel):
    """
    OpenADR 2.0b distributeEvent Profile B serialization container.
    """
    model_config = ConfigDict(populate_by_name=True)

    event_id: str = Field(..., alias="eventId", description="Unique OpenADR Event identifier")
    vtn_id: str = Field(default="VTN-MUNICIPAL-SMARTGRID-01", alias="vtnId", description="Virtual Top Node identifier")
    target_id: str = Field(..., alias="targetId", description="Virtual End Node / facility identifier")
    resource_id: str = Field(default="BESS-PHOENIX-01", alias="resourceId", description="Target battery or inverter resource")
    status: str = Field(default="far", description="Event state: far, near, active, completed, or cancelled")
    priority: int = Field(default=1, description="Event dispatch priority level")
    market_context: str = Field(
        default="http://marketcontext.org/DR/PeakCurtailment",
        alias="marketContext",
        description="Standard market context URI"
    )
    start_time: str = Field(..., alias="startTime", description="Event activation ISO 8601 timestamp")
    duration: str = Field(default="PT1H", description="Event duration in ISO 8601 duration format")
    signal_name: str = Field(default="SIMPLE", alias="signalName", description="OpenADR signal name")
    signal_type: str = Field(default="level", alias="signalType", description="OpenADR signal type: level, setpoint, or delta")
    signal_id: str = Field(..., alias="signalId", description="Unique signal identifier")
    current_value: float = Field(..., alias="currentValue", description="Current power setpoint signal value in kW")
    approved_setpoint_kw: float = Field(..., alias="approvedSetpointKw", description="Approved battery active power in kW")
    control_mode: str = Field(..., alias="controlMode", description="Control mode string: STANDBY, CHARGE, DISCHARGE, or FAILSAFE")
    intervals: List[Dict[str, Any]] = Field(default_factory=list, description="OpenADR event signal interval schedule")
    ei_event: Dict[str, Any] = Field(default_factory=dict, alias="eiEvent", description="Canonical OpenADR 2.0b EiEvent dictionary")
    xml_payload: str = Field(..., alias="xmlPayload", description="Valid OpenADR 2.0b oadrDistributeEvent XML document")
    json_payload: Dict[str, Any] = Field(default_factory=dict, alias="jsonPayload", description="Complete OpenADR JSON structure")

    def to_xml(self) -> str:
        return self.xml_payload

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True)

    def to_json(self) -> Dict[str, Any]:
        return self.json_payload


class GridSafetyInterlockResult(BaseModel):
    """
    Evaluation result container for Grid Safety Gateway interlock checks.
    """
    model_config = ConfigDict(populate_by_name=True)

    is_safe: bool = Field(..., alias="isSafe", description="Overall interlock safety status: True if all active interlocks pass")
    voltage_compliant: bool = Field(..., alias="voltageCompliant", description="Interlock 1: Under/over-voltage compliance")
    ramp_rate_compliant: bool = Field(..., alias="rampRateCompliant", description="Interlock 2: Ramp-rate slew rate compliance")
    soc_bounded: bool = Field(..., alias="socBounded", description="Interlock 3: Battery SoC safe operating envelope compliance")
    heartbeat_compliant: bool = Field(..., alias="heartbeatCompliant", description="Interlock 4: Communication keepalive watchdog compliance")
    deadband_suppressed: bool = Field(..., alias="deadbandSuppressed", description="True if dispatch step was suppressed due to dead-band (<15 kW)")

    line_voltage_v: float = Field(..., alias="lineVoltageV", description="Measured line-to-line AC voltage in Volts")
    nominal_voltage_v: float = Field(default=415.0, alias="nominalVoltageV", description="Nominal line-to-line AC voltage in Volts")
    voltage_lower_bound_v: float = Field(..., alias="voltageLowerBoundV", description="0.94 * V_nom lower voltage threshold in Volts")
    voltage_upper_bound_v: float = Field(..., alias="voltageUpperBoundV", description="1.06 * V_nom upper voltage threshold in Volts")

    requested_power_kw: float = Field(..., alias="requestedPowerKw", description="Original candidate power setpoint in kW")
    approved_power_kw: float = Field(..., alias="approvedPowerKw", description="Approved dispatch power setpoint in kW after interlock logic")
    delta_power_kw: float = Field(..., alias="deltaPowerKw", description="Step change magnitude |P_cand - P_prev| in kW")
    ramp_rate_kw_per_min: float = Field(..., alias="rampRateKwPerMin", description="Evaluated ramp rate in kW/min")
    max_ramp_rate_kw_per_min: float = Field(..., alias="maxRampRateKwPerMin", description="Maximum allowable ramp rate in kW/min (0.10 * P_rated)")

    current_soc_pct: float = Field(..., alias="currentSocPct", description="Current battery State of Charge percentage")
    heartbeat_age_seconds: float = Field(..., alias="heartbeatAgeSeconds", description="Seconds elapsed since last actuator heartbeat")
    watchdog_timeout_seconds: float = Field(default=60.0, alias="watchdogTimeoutSeconds", description="Failsafe watchdog timeout limit in seconds")

    control_mode: int = Field(..., alias="controlMode", description="Resolved control mode integer: 0=Standby, 1=Charge, 2=Discharge, 3=Failsafe")
    control_mode_label: str = Field(..., alias="controlModeLabel", description="Resolved control mode label: STANDBY, CHARGE, DISCHARGE, or FAILSAFE")
    interlock_bitmask: int = Field(..., alias="interlockBitmask", description="Register 40004 bitmask (bit 0=volt, 1=ramp, 2=soc, 3=heartbeat)")

    violations: List[str] = Field(default_factory=list, description="List of physical safety constraint violations if any")
    rejection_reason: Optional[str] = Field(default=None, alias="rejectionReason", description="Primary rejection or fallback reason if unsafe")
    action_taken: str = Field(..., alias="actionTaken", description="Outcome: APPROVED, REJECTED_STANDBY, REJECTED_FAILSAFE, or SUPPRESSED_DEADBAND")
    timestamp: str = Field(..., description="Evaluation timestamp in ISO 8601 format")
    governance_notice: str = Field(
        default="Advisory decision support only. Requires human verification before central dispatch. Local BMS remains authoritative.",
        alias="governanceNotice",
        description="Mandatory non-actuation governance disclaimer"
    )
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Metadata provenance record conforming to AGENTS.md")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True)


class GridSafetyGateway:
    """
    Grid Safety Interlocks, Communication Watchdog, and OpenADR / Modbus Failsafe Dispatch Gateway.
    Enforces the 4 physical grid safety interlocks for municipal BESS and microgrid assets:
    1. Under/over-voltage lockout: [0.94 * V_nom, 1.06 * V_nom] (390.1V to 439.9V for 415V nominal).
    2. Ramp-rate slew throttling: |delta_P / delta_t| <= 0.10 * P_rated (kW/min).
    3. Dead-band thresholding: suppress dispatch if |delta_P_shave| < 15.0 kW.
    4. Communication loss fallback: t_now - t_heartbeat > 60.0s triggers COMMUNICATION_LOST_FAILSAFE.
    """

    # Physical Engineering Bounds
    NOMINAL_VOLTAGE_V: float = 415.0
    VOLTAGE_LOWER_RATIO: float = 0.94  # 390.1V for 415V nominal
    VOLTAGE_UPPER_RATIO: float = 1.06  # 439.9V for 415V nominal

    DEFAULT_BESS_RATED_KW: float = 2000.0
    RAMP_RATE_FRACTION_PER_MIN: float = 0.10  # 10% rated power per minute (200 kW/min for 2000 kW BESS)
    DEADBAND_THRESHOLD_KW: float = 15.0
    HEARTBEAT_TIMEOUT_SECONDS: float = 60.0

    SOC_MIN_PCT: float = 20.0
    SOC_MAX_PCT: float = 90.0

    # Control Modes
    CONTROL_MODE_STANDBY: int = 0
    CONTROL_MODE_CHARGE: int = 1
    CONTROL_MODE_DISCHARGE: int = 2
    CONTROL_MODE_FAILSAFE: int = 3

    # Bitmask flags
    BIT_VOLTAGE: int = 1     # Bit 0 (1 << 0)
    BIT_RAMP: int = 2        # Bit 1 (1 << 1)
    BIT_SOC: int = 4         # Bit 2 (1 << 2)
    BIT_HEARTBEAT: int = 8   # Bit 3 (1 << 3)
    ALL_PASS_BITMASK: int = 15

    def __init__(self) -> None:
        self._lock = threading.Lock()
        now_epoch = time.time()
        self._last_heartbeat_epoch: float = now_epoch
        self._last_heartbeat_iso: str = datetime.now(timezone.utc).isoformat()
        self._last_heartbeat_sender: str = "BMS-LOCAL-ACTUATOR-01"
        self._current_setpoint_kw: float = 0.0
        self._current_control_mode: int = self.CONTROL_MODE_STANDBY
        self._watchdog_counter: int = 0
        self._failsafe_active: bool = False
        self._total_validations: int = 0
        self._total_dispatches_approved: int = 0
        self._total_rejections: int = 0

    def reset_gateway_state(self, initial_setpoint_kw: float = 0.0) -> None:
        """
        Resets in-memory gateway telemetry state. Used for hermetic testing.
        """
        with self._lock:
            now_epoch = time.time()
            self._last_heartbeat_epoch = now_epoch
            self._last_heartbeat_iso = datetime.now(timezone.utc).isoformat()
            self._last_heartbeat_sender = "BMS-LOCAL-ACTUATOR-01"
            self._current_setpoint_kw = float(initial_setpoint_kw)
            self._current_control_mode = self.CONTROL_MODE_STANDBY
            self._watchdog_counter = 0
            self._failsafe_active = False
            self._total_validations = 0
            self._total_dispatches_approved = 0
            self._total_rejections = 0

    def record_heartbeat(
        self,
        sender_id: str = "BMS-LOCAL-ACTUATOR-01",
        timestamp: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Registers an actuator or SCADA keepalive ping to reset the 60-second fallback timer.
        """
        with self._lock:
            now_epoch = float(timestamp) if timestamp is not None else time.time()
            self._last_heartbeat_epoch = now_epoch
            self._last_heartbeat_iso = datetime.fromtimestamp(now_epoch, tz=timezone.utc).isoformat()
            self._last_heartbeat_sender = sender_id
            self._watchdog_counter = (self._watchdog_counter + 1) & 0xFFFF
            self._failsafe_active = False
            if self._current_control_mode == self.CONTROL_MODE_FAILSAFE:
                self._current_control_mode = self.CONTROL_MODE_STANDBY
            logger.info("Heartbeat recorded from %s at epoch %.3f (watchdog: %d)", sender_id, now_epoch, self._watchdog_counter)
            return {
                "status": "HEARTBEAT_ACKNOWLEDGED",
                "senderId": sender_id,
                "heartbeatTimestamp": self._last_heartbeat_iso,
                "watchdogCounter": self._watchdog_counter,
                "failsafeActive": self._failsafe_active,
                "timeoutLimitSeconds": self.HEARTBEAT_TIMEOUT_SECONDS,
            }

    def get_heartbeat_age(self, current_time: Optional[float] = None) -> float:
        """
        Returns the elapsed duration in seconds since the last registered heartbeat.
        """
        with self._lock:
            now_epoch = float(current_time) if current_time is not None else time.time()
            age = max(0.0, now_epoch - self._last_heartbeat_epoch)
            return round(age, 3)

    def is_heartbeat_valid(self, current_time: Optional[float] = None) -> bool:
        """
        Verifies whether the heartbeat age is within the 60.0s communication timeout limit.
        """
        return self.get_heartbeat_age(current_time) <= self.HEARTBEAT_TIMEOUT_SECONDS

    def check_watchdog(self, current_time: Optional[float] = None) -> Dict[str, Any]:
        """
        Evaluates communication loss watchdog status.
        If t_now - t_heartbeat > 60.0s, triggers COMMUNICATION_LOST_FAILSAFE and reverts to local BMS.
        """
        with self._lock:
            now_epoch = float(current_time) if current_time is not None else time.time()
            age = max(0.0, now_epoch - self._last_heartbeat_epoch)
            self._watchdog_counter = (self._watchdog_counter + 1) & 0xFFFF

            if age > self.HEARTBEAT_TIMEOUT_SECONDS:
                self._failsafe_active = True
                self._current_control_mode = self.CONTROL_MODE_FAILSAFE
                self._current_setpoint_kw = 0.0
                return {
                    "status": "COMMUNICATION_LOST_FAILSAFE",
                    "heartbeatAgeSeconds": round(age, 3),
                    "timeoutLimitSeconds": self.HEARTBEAT_TIMEOUT_SECONDS,
                    "failsafeActive": True,
                    "controlMode": self.CONTROL_MODE_FAILSAFE,
                    "controlModeLabel": "FAILSAFE",
                    "watchdogCounter": self._watchdog_counter,
                    "actionRequired": "Revert to local autonomous BMS. Central dispatch disabled.",
                }

            return {
                "status": "COMMUNICATION_HEALTHY",
                "heartbeatAgeSeconds": round(age, 3),
                "timeoutLimitSeconds": self.HEARTBEAT_TIMEOUT_SECONDS,
                "failsafeActive": False,
                "controlMode": self._current_control_mode,
                "controlModeLabel": self._get_mode_label(self._current_control_mode),
                "watchdogCounter": self._watchdog_counter,
                "actionRequired": "None. Central dispatch authorized.",
            }

    @staticmethod
    def _get_mode_label(mode: int) -> str:
        mapping = {
            0: "STANDBY",
            1: "CHARGE",
            2: "DISCHARGE",
            3: "FAILSAFE",
        }
        return mapping.get(mode, "STANDBY")

    def validate_safety(
        self,
        candidate_power_kw: Optional[float] = None,
        current_power_kw: Optional[float] = None,
        line_voltage_v: float = 415.0,
        nominal_voltage_v: float = 415.0,
        soc_pct: float = 50.0,
        rated_power_kw: float = 2000.0,
        delta_t_minutes: float = 1.0,
        current_time: Optional[float] = None,
        action: Optional[str] = None,
        facility_id: str = "urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01",
        request: Optional[CandidateDispatchRequest] = None,
    ) -> GridSafetyInterlockResult:
        """
        Validates candidate dispatch setpoint against the 4 physical grid safety interlocks:
        1. Under/over-voltage lockout: 0.94 * V_nom <= V_line <= 1.06 * V_nom
        2. Ramp-rate slew throttling: |delta_P / delta_t| <= 0.10 * P_rated
        3. Dead-band thresholding: suppress dispatch if |delta_P_shave| < 15.0 kW
        4. Communication loss fallback: t_now - t_heartbeat > 60.0s
        """
        if request is not None:
            c_power = request.candidate_power_kw
            p_power = request.current_power_kw
            l_volt = request.line_voltage_v
            n_volt = request.nominal_voltage_v
            s_pct = request.soc_pct
            r_power = request.rated_power_kw
            dt_m = request.delta_t_minutes
            act = request.action
            fac_id = request.facility_id
        else:
            c_power = 0.0 if candidate_power_kw is None else float(candidate_power_kw)
            p_power = current_power_kw
            l_volt = float(line_voltage_v)
            n_volt = float(nominal_voltage_v)
            s_pct = float(soc_pct)
            r_power = float(rated_power_kw)
            dt_m = float(delta_t_minutes)
            act = action
            fac_id = facility_id

        with self._lock:
            self._total_validations += 1
            now_epoch = float(current_time) if current_time is not None else time.time()
            now_iso = datetime.fromtimestamp(now_epoch, tz=timezone.utc).isoformat()

            # Baseline current setpoint
            prev_power = float(self._current_setpoint_kw) if p_power is None else float(p_power)
            candidate_p = float(c_power)
            nom_v = float(n_volt) if n_volt > 0.0 else self.NOMINAL_VOLTAGE_V
            meas_v = float(l_volt)
            rated_p = float(r_power) if r_power > 0.0 else self.DEFAULT_BESS_RATED_KW
            dt_min = max(0.001, float(dt_m))
            current_soc = float(s_pct)

            # 1. Under/over-voltage interlock check
            # Lower limit: 0.94 * V_nom (390.1V for 415V)
            # Upper limit: 1.06 * V_nom (439.9V for 415V)
            v_lower = round(self.VOLTAGE_LOWER_RATIO * nom_v, 1)
            v_upper = round(self.VOLTAGE_UPPER_RATIO * nom_v, 1)
            voltage_compliant = (v_lower <= round(meas_v, 1) <= v_upper)

            # 2. Ramp-rate slew rate check
            # Limit: 0.10 * P_rated (kW/min) (e.g. 200 kW/min for 2000 kW)
            delta_p = abs(candidate_p - prev_power)
            ramp_rate = delta_p / dt_min
            max_ramp = self.RAMP_RATE_FRACTION_PER_MIN * rated_p
            # Numerical tolerance of 1e-4 for floating-point comparisons
            ramp_rate_compliant = (ramp_rate <= max_ramp + 1e-4)

            # 3. Dead-band thresholding check
            # Suppress dispatch if step adjustment < 15.0 kW
            deadband_suppressed = (delta_p < self.DEADBAND_THRESHOLD_KW)

            # 4. Communication loss / heartbeat check
            heartbeat_age = max(0.0, now_epoch - self._last_heartbeat_epoch)
            heartbeat_compliant = (heartbeat_age <= self.HEARTBEAT_TIMEOUT_SECONDS)

            # Additional electrical protection: SoC boundary check
            # 20.0% <= SoC <= 90.0%
            soc_bounded = (self.SOC_MIN_PCT <= current_soc <= self.SOC_MAX_PCT)
            # If attempting to charge when already at or above max SoC
            if (act == "CHARGE" or candidate_p < 0.0) and current_soc >= self.SOC_MAX_PCT:
                soc_bounded = False
            # If attempting to discharge when already at or below min SoC
            if (act == "DISCHARGE" or candidate_p > 0.0) and current_soc <= self.SOC_MIN_PCT:
                soc_bounded = False

            # Compile interlock violations
            violations: List[str] = []
            if not voltage_compliant:
                if meas_v < v_lower:
                    violations.append(
                        f"Under-voltage lockout: line voltage {meas_v:.1f}V is below lower threshold {v_lower:.1f}V (0.94 * V_nom)."
                    )
                else:
                    violations.append(
                        f"Over-voltage lockout: line voltage {meas_v:.1f}V is above upper threshold {v_upper:.1f}V (1.06 * V_nom)."
                    )

            if not ramp_rate_compliant:
                violations.append(
                    f"Ramp-rate slew violation: step rate {ramp_rate:.1f} kW/min exceeds maximum {max_ramp:.1f} kW/min (10% rated power/min)."
                )

            if not soc_bounded:
                violations.append(
                    f"State-of-charge out of bounds: current SoC {current_soc:.1f}% violates safe envelope [{self.SOC_MIN_PCT:.1f}%, {self.SOC_MAX_PCT:.1f}%]."
                )

            if not heartbeat_compliant:
                violations.append(
                    f"Communication loss: heartbeat age {heartbeat_age:.1f}s exceeds timeout threshold {self.HEARTBEAT_TIMEOUT_SECONDS:.1f}s."
                )

            # Modbus Register 40004 Interlock Bitmask Calculation
            # bit 0 = voltage, bit 1 = ramp, bit 2 = soc, bit 3 = heartbeat
            interlock_bitmask = 0
            if voltage_compliant:
                interlock_bitmask |= self.BIT_VOLTAGE
            if ramp_rate_compliant:
                interlock_bitmask |= self.BIT_RAMP
            if soc_bounded:
                interlock_bitmask |= self.BIT_SOC
            if heartbeat_compliant:
                interlock_bitmask |= self.BIT_HEARTBEAT

            # Determine safety outcome, approved setpoint, and control mode
            # Priority 1: Communication loss failsafe
            if not heartbeat_compliant:
                self._failsafe_active = True
                self._total_rejections += 1
                approved_power = 0.0
                control_mode = self.CONTROL_MODE_FAILSAFE
                action_taken = "REJECTED_FAILSAFE"
                rejection_reason = "COMMUNICATION_LOST_FAILSAFE: Heartbeat age exceeds 60s. Reverting to local BMS."

            # Priority 2: Physical voltage lockout
            elif not voltage_compliant:
                self._total_rejections += 1
                approved_power = 0.0
                control_mode = self.CONTROL_MODE_STANDBY
                action_taken = "REJECTED_STANDBY"
                rejection_reason = "VOLTAGE_LOCKOUT: Grid voltage exceeds 0.94-1.06 V_nom. Reverting to grid-following standby."

            # Priority 3: Ramp-rate slew rate violation
            elif not ramp_rate_compliant:
                self._total_rejections += 1
                approved_power = prev_power
                control_mode = self._current_control_mode
                action_taken = "REJECTED_STANDBY"
                rejection_reason = "RAMP_RATE_SLEW_EXCEEDED: Step ramp exceeds 10% rated power/min. Dispatch rejected."

            # Priority 4: State of charge violation
            elif not soc_bounded:
                self._total_rejections += 1
                approved_power = 0.0
                control_mode = self.CONTROL_MODE_STANDBY
                action_taken = "REJECTED_STANDBY"
                rejection_reason = "SOC_ENVELOPE_VIOLATION: Battery SoC is outside safe operating window."

            # Priority 5: Dead-band suppression (healthy interlocks, but micro-fluctuation)
            elif deadband_suppressed:
                # Suppress dispatch: setpoint remains previous power to avoid unnecessary battery wear
                approved_power = prev_power
                control_mode = self._current_control_mode
                action_taken = "SUPPRESSED_DEADBAND"
                rejection_reason = None

            # All interlocks pass and outside dead-band: Approved!
            else:
                self._total_dispatches_approved += 1
                approved_power = candidate_p
                action_taken = "APPROVED"
                rejection_reason = None

                # Determine operational control mode
                if act == "CHARGE" or (act is None and candidate_p < 0.0):
                    control_mode = self.CONTROL_MODE_CHARGE
                elif act == "DISCHARGE" or (act is None and candidate_p > 0.0):
                    control_mode = self.CONTROL_MODE_DISCHARGE
                else:
                    control_mode = self.CONTROL_MODE_STANDBY

            is_safe = (
                voltage_compliant
                and ramp_rate_compliant
                and soc_bounded
                and heartbeat_compliant
            )

            result = GridSafetyInterlockResult(
                isSafe=is_safe,
                voltageCompliant=voltage_compliant,
                rampRateCompliant=ramp_rate_compliant,
                socBounded=soc_bounded,
                heartbeatCompliant=heartbeat_compliant,
                deadbandSuppressed=deadband_suppressed,
                lineVoltageV=meas_v,
                nominalVoltageV=nom_v,
                voltageLowerBoundV=v_lower,
                voltageUpperBoundV=v_upper,
                requestedPowerKw=candidate_p,
                approvedPowerKw=approved_power,
                deltaPowerKw=round(delta_p, 3),
                rampRateKwPerMin=round(ramp_rate, 3),
                maxRampRateKwPerMin=round(max_ramp, 3),
                currentSocPct=current_soc,
                heartbeatAgeSeconds=round(heartbeat_age, 3),
                watchdogTimeoutSeconds=self.HEARTBEAT_TIMEOUT_SECONDS,
                controlMode=control_mode,
                controlModeLabel=self._get_mode_label(control_mode),
                interlockBitmask=interlock_bitmask,
                violations=violations,
                rejectionReason=rejection_reason,
                actionTaken=action_taken,
                timestamp=now_iso,
                governanceNotice="Advisory decision support only. Requires human verification before central dispatch. Local BMS remains authoritative.",
                provenance={
                    "sourceMode": "PREDICTED",
                    "qualityScore": 1.0 if is_safe else 0.5,
                    "qualityStatus": "VERIFIED" if is_safe else "REJECTED",
                    "facilityId": fac_id,
                    "gatewayEvaluator": "GridSafetyGateway_v1.0",
                    "evaluationEpoch": round(now_epoch, 3),
                }
            )
            return result

    def apply_approved_dispatch(self, interlock_result: GridSafetyInterlockResult) -> None:
        """
        Updates gateway operational state with an approved or rejected dispatch outcome.
        """
        with self._lock:
            self._current_setpoint_kw = interlock_result.approved_power_kw
            self._current_control_mode = interlock_result.control_mode
            if interlock_result.control_mode == self.CONTROL_MODE_FAILSAFE:
                self._failsafe_active = True
            logger.info(
                "Updated gateway state: setpoint=%.1f kW, mode=%s, bitmask=%d",
                self._current_setpoint_kw,
                interlock_result.control_mode_label,
                interlock_result.interlock_bitmask,
            )

    def serialize_modbus(
        self,
        interlock_result: Union[GridSafetyInterlockResult, Dict[str, Any]],
        watchdog_counter: Optional[int] = None
    ) -> ModbusRegisterMap:
        """
        Packs holding registers 40001 to 40005 into standard 16-bit Modbus words:
        - 40001 (setpoint high): most significant 16-bit word of 32-bit integer setpoint
        - 40002 (setpoint low): least significant 16-bit word of 32-bit integer setpoint
        - 40003 (control mode): 0=Standby, 1=Charge, 2=Discharge, 3=Failsafe
        - 40004 (interlock status bitmask): bit 0=voltage, bit 1=ramp, bit 2=soc, bit 3=heartbeat
        - 40005 (watchdog counter): tick counter
        """
        if isinstance(interlock_result, dict):
            res = GridSafetyInterlockResult(**interlock_result)
        else:
            res = interlock_result

        with self._lock:
            wd_counter = self._watchdog_counter if watchdog_counter is None else int(watchdog_counter)

        # 32-bit integer power setpoint in kW magnitude (non-negative, mode conveys direction)
        power_mag = int(round(abs(res.approved_power_kw)))
        setpoint_high = (power_mag >> 16) & 0xFFFF
        setpoint_low = power_mag & 0xFFFF

        ctrl_mode = int(res.control_mode)
        bitmask = int(res.interlock_bitmask)

        return ModbusRegisterMap(
            setpointHigh=setpoint_high,
            setpointLow=setpoint_low,
            controlMode=ctrl_mode,
            interlockBitmask=bitmask,
            watchdogCounter=wd_counter & 0xFFFF,
        )

    def serialize_openadr(
        self,
        interlock_result: Union[GridSafetyInterlockResult, Dict[str, Any]],
        event_id: Optional[str] = None,
        target_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        duration: str = "PT1H",
        vtn_id: str = "VTN-MUNICIPAL-SMARTGRID-01",
    ) -> OpenADREventPayload:
        """
        Serializes approved or evaluated dispatch into standard OpenADR 2.0b distributeEvent XML and JSON.
        """
        if isinstance(interlock_result, dict):
            res = GridSafetyInterlockResult(**interlock_result)
        else:
            res = interlock_result

        now = datetime.now(timezone.utc)
        start_time_iso = now.isoformat()
        evt_id = event_id or f"EVT-GRID-{now.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        tgt_id = target_id or "urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01"
        res_id = resource_id or "BESS-PHOENIX-01"
        sig_id = f"SIG-{evt_id[:16]}"

        approved_kw = float(res.approved_power_kw)
        mode_label = res.control_mode_label
        event_status = "active" if res.is_safe and approved_kw > 0.0 else "far"

        # Canonical OpenADR 2.0b EiEvent dictionary structure
        intervals = [
            {
                "dtstart": {"date-time": start_time_iso},
                "duration": {"duration": duration},
                "signalPayload": {"payloadFloat": {"value": approved_kw}},
                "uid": {"text": "0"},
            }
        ]

        ei_event = {
            "eventDescriptor": {
                "eventID": evt_id,
                "modificationNumber": 0,
                "status": event_status,
                "priority": 1,
                "marketContext": "http://marketcontext.org/DR/PeakCurtailment",
                "createdDateTime": start_time_iso,
            },
            "eiActivePeriod": {
                "properties": {
                    "dtstart": {"date-time": start_time_iso},
                    "duration": {"duration": duration},
                    "tolerance": {"tolerate": {"startafter": "PT5M"}},
                    "x-eiNotification": {"duration": "PT15M"},
                }
            },
            "eiEventSignals": [
                {
                    "signalName": "SIMPLE",
                    "signalType": "level",
                    "signalID": sig_id,
                    "currentValue": {"payloadFloat": {"value": approved_kw}},
                    "intervals": intervals,
                }
            ],
            "eiTarget": {
                "targetID": tgt_id,
                "resourceID": res_id,
            },
        }

        json_payload = {
            "oadrDistributeEvent": {
                "requestID": f"REQ-{uuid.uuid4().hex[:10].upper()}",
                "vtnID": vtn_id,
                "oadrResponseRequired": "always",
                "oadrEvent": {
                    "eiEvent": ei_event,
                },
                "interlockVerification": {
                    "isSafe": res.is_safe,
                    "controlMode": mode_label,
                    "interlockBitmask": res.interlock_bitmask,
                    "actionTaken": res.action_taken,
                }
            }
        }

        # XML Serialization conforming to OpenADR 2.0b Profile B
        xml_root = ET.Element(
            "oadrDistributeEvent",
            attrib={
                "xmlns": "http://openadr.org/oadr-2.0b/2012/07",
                "xmlns:oadr": "http://openadr.org/oadr-2.0b/2012/07",
                "xmlns:ei": "http://docs.oasis-open.org/ns/energyinteroperation/201110",
                "xmlns:pyld": "http://docs.oasis-open.org/ns/energyinteroperation/201110/payloads",
            }
        )

        req_id_elem = ET.SubElement(xml_root, "ei:requestID")
        req_id_elem.text = json_payload["oadrDistributeEvent"]["requestID"]

        vtn_id_elem = ET.SubElement(xml_root, "oadr:vtnID")
        vtn_id_elem.text = vtn_id

        oadr_event_elem = ET.SubElement(xml_root, "oadr:oadrEvent")
        ei_event_elem = ET.SubElement(oadr_event_elem, "ei:eiEvent")

        desc_elem = ET.SubElement(ei_event_elem, "ei:eventDescriptor")
        ET.SubElement(desc_elem, "ei:eventID").text = evt_id
        ET.SubElement(desc_elem, "ei:modificationNumber").text = "0"
        ET.SubElement(desc_elem, "ei:status").text = event_status
        ET.SubElement(desc_elem, "ei:priority").text = "1"
        ET.SubElement(desc_elem, "ei:marketContext").text = "http://marketcontext.org/DR/PeakCurtailment"
        ET.SubElement(desc_elem, "ei:createdDateTime").text = start_time_iso

        active_period = ET.SubElement(ei_event_elem, "ei:eiActivePeriod")
        props = ET.SubElement(active_period, "properties")
        dtstart = ET.SubElement(props, "dtstart")
        ET.SubElement(dtstart, "date-time").text = start_time_iso
        ET.SubElement(props, "duration").text = duration

        signals_elem = ET.SubElement(ei_event_elem, "ei:eiEventSignals")
        sig_elem = ET.SubElement(signals_elem, "ei:eiEventSignal")
        ET.SubElement(sig_elem, "ei:signalName").text = "SIMPLE"
        ET.SubElement(sig_elem, "ei:signalType").text = "level"
        ET.SubElement(sig_elem, "ei:signalID").text = sig_id

        curr_val = ET.SubElement(sig_elem, "ei:currentValue")
        pyld_float = ET.SubElement(curr_val, "ei:payloadFloat")
        ET.SubElement(pyld_float, "ei:value").text = f"{approved_kw:.2f}"

        intervals_elem = ET.SubElement(sig_elem, "ei:intervals")
        interval_elem = ET.SubElement(intervals_elem, "ei:interval")
        int_dtstart = ET.SubElement(interval_elem, "dtstart")
        ET.SubElement(int_dtstart, "date-time").text = start_time_iso
        ET.SubElement(interval_elem, "duration").text = duration
        int_pyld = ET.SubElement(interval_elem, "signalPayload")
        int_pyld_float = ET.SubElement(int_pyld, "payloadFloat")
        ET.SubElement(int_pyld_float, "ei:value").text = f"{approved_kw:.2f}"

        target_elem = ET.SubElement(ei_event_elem, "ei:eiTarget")
        ET.SubElement(target_elem, "ei:targetID").text = tgt_id
        ET.SubElement(target_elem, "ei:resourceID").text = res_id

        ET.SubElement(oadr_event_elem, "oadr:oadrResponseRequired").text = "always"

        xml_str = ET.tostring(xml_root, encoding="utf-8", xml_declaration=True).decode("utf-8")

        return OpenADREventPayload(
            eventId=evt_id,
            vtnId=vtn_id,
            targetId=tgt_id,
            resourceId=res_id,
            status=event_status,
            priority=1,
            marketContext="http://marketcontext.org/DR/PeakCurtailment",
            startTime=start_time_iso,
            duration=duration,
            signalName="SIMPLE",
            signalType="level",
            signalId=sig_id,
            currentValue=approved_kw,
            approvedSetpointKw=approved_kw,
            controlMode=mode_label,
            intervals=intervals,
            eiEvent=ei_event,
            xmlPayload=xml_str,
            jsonPayload=json_payload,
        )

    def get_gateway_status(self, current_time: Optional[float] = None) -> Dict[str, Any]:
        """
        Returns live operational health, heartbeat telemetry, and failsafe status.
        """
        with self._lock:
            now_epoch = float(current_time) if current_time is not None else time.time()
            age = max(0.0, now_epoch - self._last_heartbeat_epoch)
            failsafe = (age > self.HEARTBEAT_TIMEOUT_SECONDS) or self._failsafe_active

            return {
                "gatewayOperational": True,
                "currentSetpointKw": self._current_setpoint_kw,
                "currentControlMode": self._current_control_mode,
                "currentControlModeLabel": self._get_mode_label(self._current_control_mode),
                "failsafeActive": failsafe,
                "lastHeartbeatTimestamp": self._last_heartbeat_iso,
                "lastHeartbeatSender": self._last_heartbeat_sender,
                "heartbeatAgeSeconds": round(age, 3),
                "heartbeatTimeoutLimitSeconds": self.HEARTBEAT_TIMEOUT_SECONDS,
                "watchdogCounter": self._watchdog_counter,
                "nominalVoltageV": self.NOMINAL_VOLTAGE_V,
                "voltageOperatingEnvelopeV": [
                    round(self.VOLTAGE_LOWER_RATIO * self.NOMINAL_VOLTAGE_V, 2),
                    round(self.VOLTAGE_UPPER_RATIO * self.NOMINAL_VOLTAGE_V, 2),
                ],
                "rampRateSlewLimitPctPerMin": self.RAMP_RATE_FRACTION_PER_MIN * 100.0,
                "deadbandThresholdKw": self.DEADBAND_THRESHOLD_KW,
                "statistics": {
                    "totalValidations": self._total_validations,
                    "totalApproved": self._total_dispatches_approved,
                    "totalRejections": self._total_rejections,
                },
                "governanceNotice": "Advisory decision support only. Local BMS remains authoritative.",
            }


# Authoritative singleton instance
grid_safety_gateway = GridSafetyGateway()

__all__ = [
    "CandidateDispatchRequest",
    "HeartbeatPingRequest",
    "ModbusRegisterMap",
    "OpenADREventPayload",
    "GridSafetyInterlockResult",
    "GridSafetyGateway",
    "grid_safety_gateway",
]
