"""
test_grid_safety_gateway.py

Hermetic unit and integration tests for Grid Safety Interlocks, Communication Watchdog,
and OpenADR 2.0b / Modbus TCP Failsafe Dispatch Gateway (Issue #19, ENERGY-07).

Validates:
1. Voltage compliance within [390.1V, 439.9V] (0.94 to 1.06 of 415V nominal).
2. Voltage lockout on undervoltage (<390.1V) and overvoltage (>439.9V).
3. Ramp-rate compliance (<= 10%/min = 200 kW/min for 2000 kW BESS).
4. Slew throttling rejection on excessive ramp step (> 200 kW/min).
5. Dead-band suppression for setpoint adjustments < 15.0 kW.
6. Heartbeat verification: failsafe triggers when heartbeat age > 60.0s.
7. Heartbeat keepalive ping resets fallback timer and increments watchdog counter.
8. OpenADR 2.0b XML serialization and schema validity.
9. Modbus TCP register packing (40001-40005) and bitmask calculation.
10. REST API contracts for all 5 endpoints:
    - POST /api/v1/energy/dispatch/validate-safety
    - POST /api/v1/energy/dispatch/serialize-openadr
    - POST /api/v1/energy/dispatch/serialize-modbus
    - POST /api/v1/energy/dispatch/heartbeat
    - GET /api/v1/energy/dispatch/gateway-status
11. Zero emojis and zero em dashes across services, routes, and test suites.
"""

from datetime import datetime, timezone
import json
import time
from typing import Any, Dict
import xml.etree.ElementTree as ET

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.grid_safety_gateway import (
    CandidateDispatchRequest,
    GridSafetyGateway,
    GridSafetyInterlockResult,
    HeartbeatPingRequest,
    ModbusRegisterMap,
    OpenADREventPayload,
    grid_safety_gateway,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_gateway():
    """
    Hermetic isolation fixture: resets gateway singleton state before each test.
    """
    grid_safety_gateway.reset_gateway_state(initial_setpoint_kw=0.0)
    yield
    grid_safety_gateway.reset_gateway_state(initial_setpoint_kw=0.0)


# ===========================================================================
# 1. Instantiation and Electrical Engineering Constants
# ===========================================================================


def test_grid_safety_gateway_constants_and_instantiation():
    """
    Verifies electrical engineering bounds, bitmask constants, and control modes.
    """
    gw = GridSafetyGateway()
    assert gw.NOMINAL_VOLTAGE_V == 415.0
    assert gw.VOLTAGE_LOWER_RATIO == 0.94
    assert gw.VOLTAGE_UPPER_RATIO == 1.06

    # Nominal bounds for 415V
    v_lower = round(gw.VOLTAGE_LOWER_RATIO * gw.NOMINAL_VOLTAGE_V, 1)
    v_upper = round(gw.VOLTAGE_UPPER_RATIO * gw.NOMINAL_VOLTAGE_V, 1)
    assert v_lower == 390.1
    assert v_upper == 439.9

    # Ramp rate and dead-band
    assert gw.DEFAULT_BESS_RATED_KW == 2000.0
    assert gw.RAMP_RATE_FRACTION_PER_MIN == 0.10
    max_ramp = gw.RAMP_RATE_FRACTION_PER_MIN * gw.DEFAULT_BESS_RATED_KW
    assert max_ramp == 200.0
    assert gw.DEADBAND_THRESHOLD_KW == 15.0
    assert gw.HEARTBEAT_TIMEOUT_SECONDS == 60.0

    # Bitmask definitions (Register 40004)
    assert gw.BIT_VOLTAGE == 1       # Bit 0
    assert gw.BIT_RAMP == 2          # Bit 1
    assert gw.BIT_SOC == 4           # Bit 2
    assert gw.BIT_HEARTBEAT == 8      # Bit 3
    assert gw.ALL_PASS_BITMASK == 15  # 1 + 2 + 4 + 8

    # Control Modes
    assert gw.CONTROL_MODE_STANDBY == 0
    assert gw.CONTROL_MODE_CHARGE == 1
    assert gw.CONTROL_MODE_DISCHARGE == 2
    assert gw.CONTROL_MODE_FAILSAFE == 3


# ===========================================================================
# 2. Voltage Compliance Within Operating Envelope [390.1V, 439.9V]
# ===========================================================================


def test_voltage_compliance_within_envelope():
    """
    Verifies that voltages within [390.1V, 439.9V] pass the voltage interlock.
    """
    gw = GridSafetyGateway()
    test_voltages = [390.1, 400.0, 415.0, 425.5, 439.9]

    for v in test_voltages:
        res = gw.validate_safety(
            candidate_power_kw=100.0,
            current_power_kw=0.0,
            line_voltage_v=v,
            nominal_voltage_v=415.0,
            delta_t_minutes=1.0,
            action="DISCHARGE",
        )
        assert res.voltage_compliant is True, f"Voltage {v}V should be compliant."
        assert res.line_voltage_v == v
        assert res.voltage_lower_bound_v == 390.1
        assert res.voltage_upper_bound_v == 439.9
        assert (res.interlock_bitmask & gw.BIT_VOLTAGE) == gw.BIT_VOLTAGE


# ===========================================================================
# 3. Voltage Lockout on Undervoltage (<390.1V) and Overvoltage (>439.9V)
# ===========================================================================


def test_voltage_lockout_undervoltage_and_overvoltage():
    """
    Verifies that undervoltage (<390.1V) and overvoltage (>439.9V) trigger lockout,
    reverting dispatch to grid-following standby (control mode 0) and zeroing setpoint.
    """
    gw = GridSafetyGateway()

    # Undervoltage cases
    undervoltages = [390.0, 385.0, 370.0, 320.0, 0.0]
    for v in undervoltages:
        res = gw.validate_safety(
            candidate_power_kw=150.0,
            current_power_kw=0.0,
            line_voltage_v=v,
            nominal_voltage_v=415.0,
            delta_t_minutes=1.0,
            action="DISCHARGE",
        )
        assert res.voltage_compliant is False, f"Voltage {v}V should trigger undervoltage lockout."
        assert res.is_safe is False
        assert res.action_taken == "REJECTED_STANDBY"
        assert res.approved_power_kw == 0.0
        assert res.control_mode == gw.CONTROL_MODE_STANDBY
        assert res.control_mode_label == "STANDBY"
        assert (res.interlock_bitmask & gw.BIT_VOLTAGE) == 0
        assert res.rejection_reason is not None
        assert "VOLTAGE_LOCKOUT" in res.rejection_reason
        assert any("Under-voltage lockout" in viol for viol in res.violations)

    # Overvoltage cases
    overvoltages = [440.0, 445.0, 460.0, 500.0]
    for v in overvoltages:
        res = gw.validate_safety(
            candidate_power_kw=150.0,
            current_power_kw=0.0,
            line_voltage_v=v,
            nominal_voltage_v=415.0,
            delta_t_minutes=1.0,
            action="DISCHARGE",
        )
        assert res.voltage_compliant is False, f"Voltage {v}V should trigger overvoltage lockout."
        assert res.is_safe is False
        assert res.action_taken == "REJECTED_STANDBY"
        assert res.approved_power_kw == 0.0
        assert res.control_mode == gw.CONTROL_MODE_STANDBY
        assert (res.interlock_bitmask & gw.BIT_VOLTAGE) == 0
        assert res.rejection_reason is not None
        assert "VOLTAGE_LOCKOUT" in res.rejection_reason
        assert any("Over-voltage lockout" in viol for viol in res.violations)


# ===========================================================================
# 4. Ramp-Rate Compliance (<= 10%/min = 200 kW/min for 2000 kW BESS)
# ===========================================================================


def test_ramp_rate_compliance():
    """
    Verifies ramp rates <= 200 kW/min pass the ramp rate interlock.
    """
    gw = GridSafetyGateway()

    # Step from 0 to 200 kW in 1 min (exactly 200 kW/min)
    res = gw.validate_safety(
        candidate_power_kw=200.0,
        current_power_kw=0.0,
        rated_power_kw=2000.0,
        delta_t_minutes=1.0,
        action="DISCHARGE",
    )
    assert res.ramp_rate_compliant is True
    assert res.ramp_rate_kw_per_min == 200.0
    assert res.max_ramp_rate_kw_per_min == 200.0
    assert res.is_safe is True
    assert res.action_taken == "APPROVED"
    assert res.approved_power_kw == 200.0
    assert (res.interlock_bitmask & gw.BIT_RAMP) == gw.BIT_RAMP

    # Step from 500 to 650 kW in 1 min (150 kW/min <= 200 kW/min)
    res2 = gw.validate_safety(
        candidate_power_kw=650.0,
        current_power_kw=500.0,
        rated_power_kw=2000.0,
        delta_t_minutes=1.0,
        action="DISCHARGE",
    )
    assert res2.ramp_rate_compliant is True
    assert res2.ramp_rate_kw_per_min == 150.0
    assert res2.action_taken == "APPROVED"
    assert res2.approved_power_kw == 650.0

    # Step from 0 to 100 kW in 0.5 min (200 kW/min)
    res3 = gw.validate_safety(
        candidate_power_kw=100.0,
        current_power_kw=0.0,
        rated_power_kw=2000.0,
        delta_t_minutes=0.5,
        action="DISCHARGE",
    )
    assert res3.ramp_rate_compliant is True
    assert res3.ramp_rate_kw_per_min == 200.0
    assert res3.action_taken == "APPROVED"


# ===========================================================================
# 5. Slew Throttling Rejection on Excessive Ramp Step (> 200 kW/min)
# ===========================================================================


def test_ramp_rate_slew_throttling_rejection():
    """
    Verifies that candidate step changes exceeding 200 kW/min are rejected,
    retaining the previous setpoint and setting action to REJECTED_STANDBY.
    """
    gw = GridSafetyGateway()

    # Step from 0 to 250 kW in 1 min (250 kW/min > 200 kW/min limit)
    res = gw.validate_safety(
        candidate_power_kw=250.0,
        current_power_kw=0.0,
        rated_power_kw=2000.0,
        delta_t_minutes=1.0,
        action="DISCHARGE",
    )
    assert res.ramp_rate_compliant is False
    assert res.is_safe is False
    assert res.action_taken == "REJECTED_STANDBY"
    assert res.approved_power_kw == 0.0  # keeps previous setpoint
    assert (res.interlock_bitmask & gw.BIT_RAMP) == 0
    assert res.rejection_reason is not None
    assert "RAMP_RATE_SLEW_EXCEEDED" in res.rejection_reason
    assert any("Ramp-rate slew violation" in viol for viol in res.violations)

    # Step from 200 kW to 450 kW in 1 min (250 kW/min > 200 kW/min)
    res2 = gw.validate_safety(
        candidate_power_kw=450.0,
        current_power_kw=200.0,
        rated_power_kw=2000.0,
        delta_t_minutes=1.0,
        action="DISCHARGE",
    )
    assert res2.ramp_rate_compliant is False
    assert res2.approved_power_kw == 200.0  # retains 200 kW previous setpoint

    # Step from 0 to 150 kW in 0.5 min (300 kW/min > 200 kW/min)
    res3 = gw.validate_safety(
        candidate_power_kw=150.0,
        current_power_kw=0.0,
        rated_power_kw=2000.0,
        delta_t_minutes=0.5,
        action="DISCHARGE",
    )
    assert res3.ramp_rate_compliant is False
    assert res3.ramp_rate_kw_per_min == 300.0
    assert res3.action_taken == "REJECTED_STANDBY"


# ===========================================================================
# 6. Dead-Band Suppression for Setpoint Adjustments < 15.0 kW
# ===========================================================================


def test_deadband_suppression_under_fifteen_kw():
    """
    Verifies that step adjustments smaller than 15.0 kW are suppressed to avoid
    inverter chattering and battery cycle degradation, maintaining current setpoint.
    """
    gw = GridSafetyGateway()

    # Case 1: Baseline 100 kW, candidate 110 kW (delta = 10 kW < 15 kW threshold)
    res = gw.validate_safety(
        candidate_power_kw=110.0,
        current_power_kw=100.0,
        delta_t_minutes=1.0,
        action="DISCHARGE",
    )
    assert res.deadband_suppressed is True
    assert res.is_safe is True  # interlocks are healthy
    assert res.action_taken == "SUPPRESSED_DEADBAND"
    assert res.approved_power_kw == 100.0  # keeps previous setpoint
    assert res.delta_power_kw == 10.0
    assert res.rejection_reason is None

    # Case 2: Baseline 0 kW, candidate 14.9 kW (delta = 14.9 kW < 15 kW)
    res2 = gw.validate_safety(
        candidate_power_kw=14.9,
        current_power_kw=0.0,
        delta_t_minutes=1.0,
        action="DISCHARGE",
    )
    assert res2.deadband_suppressed is True
    assert res2.approved_power_kw == 0.0

    # Case 3: Exactly 15.0 kW step (threshold met -> approved, not suppressed)
    res3 = gw.validate_safety(
        candidate_power_kw=15.0,
        current_power_kw=0.0,
        delta_t_minutes=1.0,
        action="DISCHARGE",
    )
    assert res3.deadband_suppressed is False
    assert res3.action_taken == "APPROVED"
    assert res3.approved_power_kw == 15.0

    # Case 4: 25.0 kW step (> 15.0 kW -> approved)
    res4 = gw.validate_safety(
        candidate_power_kw=125.0,
        current_power_kw=100.0,
        delta_t_minutes=1.0,
        action="DISCHARGE",
    )
    assert res4.deadband_suppressed is False
    assert res4.action_taken == "APPROVED"
    assert res4.approved_power_kw == 125.0


# ===========================================================================
# 7. Heartbeat Verification: Failsafe Triggers When Heartbeat Age > 60.0s
# ===========================================================================


def test_heartbeat_failsafe_trigger_after_sixty_seconds():
    """
    Verifies that when heartbeat age exceeds 60.0s, COMMUNICATION_LOST_FAILSAFE
    triggers, control mode switches to 3 (FAILSAFE), and setpoint is zeroed.
    """
    gw = GridSafetyGateway()
    t_start = 1700000000.0
    gw.record_heartbeat(sender_id="BMS-ACTUATOR-TEST", timestamp=t_start)

    # Within 60s window (e.g. at t_start + 45s) -> valid
    res_valid = gw.validate_safety(
        candidate_power_kw=100.0,
        current_power_kw=0.0,
        current_time=t_start + 45.0,
    )
    assert res_valid.heartbeat_compliant is True
    assert res_valid.is_safe is True
    assert (res_valid.interlock_bitmask & gw.BIT_HEARTBEAT) == gw.BIT_HEARTBEAT

    # Exceeding 60s limit (e.g. at t_start + 60.5s) -> failsafe
    res_failsafe = gw.validate_safety(
        candidate_power_kw=100.0,
        current_power_kw=0.0,
        current_time=t_start + 60.5,
    )
    assert res_failsafe.heartbeat_compliant is False
    assert res_failsafe.is_safe is False
    assert res_failsafe.action_taken == "REJECTED_FAILSAFE"
    assert res_failsafe.control_mode == gw.CONTROL_MODE_FAILSAFE
    assert res_failsafe.control_mode_label == "FAILSAFE"
    assert res_failsafe.approved_power_kw == 0.0
    assert (res_failsafe.interlock_bitmask & gw.BIT_HEARTBEAT) == 0
    assert res_failsafe.rejection_reason is not None
    assert "COMMUNICATION_LOST_FAILSAFE" in res_failsafe.rejection_reason
    assert any("Communication loss" in viol for viol in res_failsafe.violations)

    # Watchdog evaluation check
    wd_status = gw.check_watchdog(current_time=t_start + 65.0)
    assert wd_status["status"] == "COMMUNICATION_LOST_FAILSAFE"
    assert wd_status["failsafeActive"] is True
    assert wd_status["controlMode"] == gw.CONTROL_MODE_FAILSAFE


# ===========================================================================
# 8. Heartbeat Keepalive Ping Resets Fallback Timer
# ===========================================================================


def test_heartbeat_keepalive_resets_fallback_timer():
    """
    Verifies that registering a keepalive heartbeat resets the timer, increments
    the watchdog counter, and clears the failsafe condition.
    """
    gw = GridSafetyGateway()
    t0 = 1700000000.0
    gw.record_heartbeat(sender_id="BMS-ACTUATOR-TEST", timestamp=t0)

    # Fast forward beyond 60s to trigger failsafe
    res_expired = gw.validate_safety(
        candidate_power_kw=100.0,
        current_power_kw=0.0,
        current_time=t0 + 75.0,
    )
    assert res_expired.heartbeat_compliant is False

    # Actuator sends keepalive ping at t0 + 80.0
    t1 = t0 + 80.0
    hb_ack = gw.record_heartbeat(sender_id="BMS-ACTUATOR-TEST", timestamp=t1)
    assert hb_ack["status"] == "HEARTBEAT_ACKNOWLEDGED"
    assert hb_ack["failsafeActive"] is False
    assert hb_ack["watchdogCounter"] >= 2

    # Now validate at t1 + 5.0s -> healthy again
    res_recovered = gw.validate_safety(
        candidate_power_kw=100.0,
        current_power_kw=0.0,
        current_time=t1 + 5.0,
    )
    assert res_recovered.heartbeat_compliant is True
    assert res_recovered.is_safe is True
    assert res_recovered.heartbeat_age_seconds == 5.0
    assert res_recovered.action_taken == "APPROVED"


# ===========================================================================
# 9. State of Charge (SoC) Boundary Protection
# ===========================================================================


def test_soc_envelope_boundary_protection():
    """
    Verifies SoC operating boundaries [20%, 90%]:
    - Discharge rejected if SoC <= 20%
    - Charge rejected if SoC >= 90%
    """
    gw = GridSafetyGateway()

    # Discharge attempted at 18% SoC (violates lower limit)
    res_dis_low = gw.validate_safety(
        candidate_power_kw=100.0,
        current_power_kw=0.0,
        soc_pct=18.0,
        action="DISCHARGE",
    )
    assert res_dis_low.soc_bounded is False
    assert res_dis_low.is_safe is False
    assert res_dis_low.action_taken == "REJECTED_STANDBY"
    assert (res_dis_low.interlock_bitmask & gw.BIT_SOC) == 0

    # Charge attempted at 92% SoC (violates upper limit)
    res_chg_high = gw.validate_safety(
        candidate_power_kw=-100.0,
        current_power_kw=0.0,
        soc_pct=92.0,
        action="CHARGE",
    )
    assert res_chg_high.soc_bounded is False
    assert res_chg_high.is_safe is False
    assert res_chg_high.action_taken == "REJECTED_STANDBY"
    assert (res_chg_high.interlock_bitmask & gw.BIT_SOC) == 0

    # Operation within 50% SoC -> compliant
    res_mid = gw.validate_safety(
        candidate_power_kw=100.0,
        current_power_kw=0.0,
        soc_pct=50.0,
        action="DISCHARGE",
    )
    assert res_mid.soc_bounded is True
    assert (res_mid.interlock_bitmask & gw.BIT_SOC) == gw.BIT_SOC


# ===========================================================================
# 10. OpenADR 2.0b XML and JSON Serialization
# ===========================================================================


def test_openadr_serialization_and_xml_schema_validity():
    """
    Verifies OpenADR 2.0b distributeEvent Profile B serialization,
    XML namespace conformity, and structural validity.
    """
    gw = GridSafetyGateway()
    interlock_res = gw.validate_safety(
        candidate_power_kw=150.0,
        current_power_kw=0.0,
        line_voltage_v=415.0,
        nominal_voltage_v=415.0,
        action="DISCHARGE",
    )
    assert interlock_res.is_safe is True

    payload = gw.serialize_openadr(
        interlock_result=interlock_res,
        event_id="EVT-TEST-001",
        target_id="urn:ngsi-ld:Building:TEST-BLD-01",
        resource_id="BESS-TEST-01",
        duration="PT1H",
        vtn_id="VTN-TEST-HUB-01",
    )

    # Check Pydantic model fields
    assert payload.event_id == "EVT-TEST-001"
    assert payload.vtn_id == "VTN-TEST-HUB-01"
    assert payload.target_id == "urn:ngsi-ld:Building:TEST-BLD-01"
    assert payload.resource_id == "BESS-TEST-01"
    assert payload.status == "active"
    assert payload.approved_setpoint_kw == 150.0
    assert payload.control_mode == "DISCHARGE"

    # Check JSON payload structure
    json_data = payload.json_payload
    assert "oadrDistributeEvent" in json_data
    oadr_evt = json_data["oadrDistributeEvent"]
    assert oadr_evt["vtnID"] == "VTN-TEST-HUB-01"
    ei_evt = oadr_evt["oadrEvent"]["eiEvent"]
    assert ei_evt["eventDescriptor"]["eventID"] == "EVT-TEST-001"
    assert ei_evt["eiTarget"]["targetID"] == "urn:ngsi-ld:Building:TEST-BLD-01"

    # Validate XML parsing and namespace compliance
    xml_str = payload.xml_payload
    assert isinstance(xml_str, str)
    assert len(xml_str) > 100

    # Parse with standard ElementTree
    root = ET.fromstring(xml_str)
    assert root.tag.endswith("oadrDistributeEvent")

    # Find namespaces and key child elements
    namespaces = {
        "oadr": "http://openadr.org/oadr-2.0b/2012/07",
        "ei": "http://docs.oasis-open.org/ns/energyinteroperation/201110",
    }
    vtn_elem = root.find("oadr:vtnID", namespaces)
    assert vtn_elem is not None
    assert vtn_elem.text == "VTN-TEST-HUB-01"

    event_id_elem = root.find(".//ei:eventID", namespaces)
    assert event_id_elem is not None
    assert event_id_elem.text == "EVT-TEST-001"

    val_elem = root.find(".//ei:currentValue/ei:payloadFloat/ei:value", namespaces)
    assert val_elem is not None
    assert float(val_elem.text) == 150.0


# ===========================================================================
# 11. Modbus TCP Register Packing and Bitmask Calculation
# ===========================================================================


def test_modbus_register_packing_and_bitmask():
    """
    Verifies Modbus TCP holding register packing (40001-40005):
    - 40001 (high word) and 40002 (low word) of 32-bit power setpoint.
    - 40003 control mode (0=Standby, 1=Charge, 2=Discharge, 3=Failsafe).
    - 40004 interlock bitmask (bits 0, 1, 2, 3).
    - 40005 monotonic watchdog counter.
    """
    gw = GridSafetyGateway()

    # Case 1: Approved 450 kW discharge dispatch (all 4 interlocks pass -> bitmask 15)
    res_pass = gw.validate_safety(
        candidate_power_kw=450.0,
        current_power_kw=300.0,
        action="DISCHARGE",
    )
    assert res_pass.is_safe is True
    assert res_pass.interlock_bitmask == 15  # 1 + 2 + 4 + 8

    mb_map = gw.serialize_modbus(interlock_result=res_pass, watchdog_counter=102)
    assert mb_map.setpoint_high == 0
    assert mb_map.setpoint_low == 450
    assert mb_map.control_mode == gw.CONTROL_MODE_DISCHARGE  # 2
    assert mb_map.interlock_bitmask == 15
    assert mb_map.watchdog_counter == 102
    assert mb_map.raw_registers[40001] == 0
    assert mb_map.raw_registers[40002] == 450
    assert mb_map.raw_registers[40003] == 2
    assert mb_map.raw_registers[40004] == 15
    assert mb_map.raw_registers[40005] == 102
    assert mb_map.to_register_list() == [0, 450, 2, 15, 102]

    # Case 2: Large setpoint spanning two 16-bit words (70,000 kW)
    # 70000 = (1 << 16) + 4464
    res_large = gw.validate_safety(
        candidate_power_kw=70000.0,
        current_power_kw=70000.0,  # delta = 0 -> suppressed or unchanged
    )
    mb_large = gw.serialize_modbus(interlock_result=res_large, watchdog_counter=5)
    assert mb_large.setpoint_high == 1
    assert mb_large.setpoint_low == 4464
    assert (mb_large.setpoint_high << 16) + mb_large.setpoint_low == 70000

    # Case 3: Voltage lockout (bit 0 fails -> bitmask = 14 = 2 + 4 + 8)
    res_volt_fail = gw.validate_safety(
        candidate_power_kw=100.0,
        current_power_kw=0.0,
        line_voltage_v=370.0,  # below 390.1V
    )
    mb_volt = gw.serialize_modbus(interlock_result=res_volt_fail)
    assert mb_volt.setpoint_high == 0
    assert mb_volt.setpoint_low == 0
    assert mb_volt.control_mode == gw.CONTROL_MODE_STANDBY  # 0
    assert mb_volt.interlock_bitmask == 14  # bit 0 is 0

    # Case 4: Communication failsafe (bit 3 fails -> bitmask = 7 = 1 + 2 + 4)
    t0 = 1700000000.0
    gw.record_heartbeat(timestamp=t0)
    res_hb_fail = gw.validate_safety(
        candidate_power_kw=100.0,
        current_power_kw=0.0,
        current_time=t0 + 70.0,
    )
    mb_hb = gw.serialize_modbus(interlock_result=res_hb_fail)
    assert mb_hb.setpoint_high == 0
    assert mb_hb.setpoint_low == 0
    assert mb_hb.control_mode == gw.CONTROL_MODE_FAILSAFE  # 3
    assert mb_hb.interlock_bitmask == 7  # bit 3 is 0


# ===========================================================================
# 12. REST API Integration: POST /api/v1/energy/dispatch/validate-safety
# ===========================================================================


def test_api_validate_safety_success_and_violations():
    """
    Verifies the REST API endpoint POST /api/v1/energy/dispatch/validate-safety
    across compliant dispatch, undervoltage, overvoltage, and ramp violations.
    """
    # 1. Compliant dispatch
    payload_valid = {
        "facilityId": "urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01",
        "candidatePowerKw": 150.0,
        "currentPowerKw": 0.0,
        "lineVoltageV": 415.0,
        "nominalVoltageV": 415.0,
        "socPct": 55.0,
        "ratedPowerKw": 2000.0,
        "deltaTMinutes": 1.0,
        "action": "DISCHARGE",
    }
    resp = client.post("/api/v1/energy/dispatch/validate-safety", json=payload_valid)
    assert resp.status_code == 200
    data = resp.json()
    assert data["isSafe"] is True
    assert data["actionTaken"] == "APPROVED"
    assert data["approvedPowerKw"] == 150.0
    assert data["voltageCompliant"] is True
    assert data["rampRateCompliant"] is True
    assert data["socBounded"] is True
    assert data["heartbeatCompliant"] is True
    assert data["interlockBitmask"] == 15
    assert data["controlMode"] == 2
    assert data["controlModeLabel"] == "DISCHARGE"

    # Alias endpoint test (/dispatch/validate)
    resp_alias = client.post("/api/v1/energy/dispatch/validate", json=payload_valid)
    assert resp_alias.status_code == 200
    assert resp_alias.json()["isSafe"] is True

    # 2. Undervoltage lockout (<390.1V)
    payload_undervolt = dict(payload_valid, lineVoltageV=380.0)
    resp_uv = client.post("/api/v1/energy/dispatch/validate-safety", json=payload_undervolt)
    assert resp_uv.status_code == 200
    data_uv = resp_uv.json()
    assert data_uv["isSafe"] is False
    assert data_uv["voltageCompliant"] is False
    assert data_uv["actionTaken"] == "REJECTED_STANDBY"
    assert data_uv["approvedPowerKw"] == 0.0
    assert data_uv["controlMode"] == 0
    assert "VOLTAGE_LOCKOUT" in data_uv["rejectionReason"]

    # 3. Excessive ramp-rate slew violation (>200 kW/min)
    payload_ramp = dict(payload_valid, candidatePowerKw=300.0, currentPowerKw=0.0, deltaTMinutes=1.0)
    resp_rr = client.post("/api/v1/energy/dispatch/validate-safety", json=payload_ramp)
    assert resp_rr.status_code == 200
    data_rr = resp_rr.json()
    assert data_rr["isSafe"] is False
    assert data_rr["rampRateCompliant"] is False
    assert data_rr["actionTaken"] == "REJECTED_STANDBY"
    assert data_rr["approvedPowerKw"] == 0.0
    assert "RAMP_RATE_SLEW_EXCEEDED" in data_rr["rejectionReason"]


# ===========================================================================
# 13. REST API Integration: POST /api/v1/energy/dispatch/serialize-openadr
# ===========================================================================


def test_api_serialize_openadr_endpoint():
    """
    Verifies POST /api/v1/energy/dispatch/serialize-openadr endpoint.
    """
    payload = {
        "facilityId": "urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01",
        "candidatePowerKw": 175.0,
        "currentPowerKw": 0.0,
        "lineVoltageV": 415.0,
        "nominalVoltageV": 415.0,
        "socPct": 60.0,
        "ratedPowerKw": 2000.0,
        "deltaTMinutes": 1.0,
        "action": "DISCHARGE",
        "duration": "PT1H",
    }
    resp = client.post("/api/v1/energy/dispatch/serialize-openadr", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert "eventId" in data
    assert data["targetId"] == "urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01"
    assert data["approvedSetpointKw"] == 175.0
    assert data["controlMode"] == "DISCHARGE"
    assert "xmlPayload" in data
    assert "jsonPayload" in data

    # Verify XML is valid XML
    xml_str = data["xmlPayload"]
    root = ET.fromstring(xml_str)
    assert root.tag.endswith("oadrDistributeEvent")


# ===========================================================================
# 14. REST API Integration: POST /api/v1/energy/dispatch/serialize-modbus
# ===========================================================================


def test_api_serialize_modbus_endpoint():
    """
    Verifies POST /api/v1/energy/dispatch/serialize-modbus endpoint.
    """
    payload = {
        "facilityId": "urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01",
        "candidatePowerKw": 180.0,
        "currentPowerKw": 0.0,
        "lineVoltageV": 415.0,
        "action": "DISCHARGE",
    }
    resp = client.post("/api/v1/energy/dispatch/serialize-modbus", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["setpointHigh"] == 0
    assert data["setpointLow"] == 180
    assert data["controlMode"] == 2  # Discharge
    assert data["interlockBitmask"] == 15  # All pass
    assert "watchdogCounter" in data
    assert "rawRegisters" in data
    assert "namedRegisters" in data
    assert "registerList" in data
    assert len(data["registerList"]) == 5
    assert data["registerList"][:4] == [0, 180, 2, 15]


# ===========================================================================
# 15. REST API Integration: Heartbeat Ping and Gateway Status Endpoints
# ===========================================================================


def test_api_heartbeat_and_gateway_status_endpoints():
    """
    Verifies:
    - POST /api/v1/energy/dispatch/heartbeat
    - GET /api/v1/energy/dispatch/gateway-status (and /dispatch/status alias)
    """
    # 1. Heartbeat registration
    hb_payload = {
        "senderId": "BMS-ACTUATOR-UNIT-01",
    }
    resp_hb = client.post("/api/v1/energy/dispatch/heartbeat", json=hb_payload)
    assert resp_hb.status_code == 200
    hb_data = resp_hb.json()
    assert hb_data["status"] == "HEARTBEAT_ACKNOWLEDGED"
    assert hb_data["senderId"] == "BMS-ACTUATOR-UNIT-01"
    assert hb_data["failsafeActive"] is False
    assert hb_data["watchdogCounter"] >= 1

    # 2. Gateway Status query
    resp_stat = client.get("/api/v1/energy/dispatch/gateway-status")
    assert resp_stat.status_code == 200
    stat_data = resp_stat.json()
    assert stat_data["gatewayOperational"] is True
    assert stat_data["failsafeActive"] is False
    assert stat_data["nominalVoltageV"] == 415.0
    assert stat_data["voltageOperatingEnvelopeV"] == [390.1, 439.9]
    assert stat_data["rampRateSlewLimitPctPerMin"] == 10.0
    assert stat_data["deadbandThresholdKw"] == 15.0
    assert stat_data["heartbeatAgeSeconds"] >= 0.0

    # 3. Status alias endpoint (/dispatch/status)
    resp_alias = client.get("/api/v1/energy/dispatch/status")
    assert resp_alias.status_code == 200
    assert resp_alias.json()["gatewayOperational"] is True


# ===========================================================================
# 16. Invariant Verification: Strictly Zero Emojis and Zero Em Dashes
# ===========================================================================


def test_zero_emojis_and_em_dashes_in_gateway_modules():
    """
    Verifies that backend/services/grid_safety_gateway.py,
    backend/api/v1/endpoints/energy.py, and tests/test_grid_safety_gateway.py
    contain strictly zero emojis and zero em dashes or en dashes.
    """
    files_to_check = [
        "backend/services/grid_safety_gateway.py",
        "backend/api/v1/endpoints/energy.py",
        "tests/test_grid_safety_gateway.py",
    ]

    # Em dash and en dash code points
    em_dash = chr(0x2014)
    en_dash = chr(0x2013)

    for filepath in files_to_check:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        if filepath == "tests/test_grid_safety_gateway.py":
            # Strip this test function itself to prevent self-matching the chr definitions
            content = content[:content.find("def test_zero_emojis_and_em_dashes_in_gateway_modules")]

        assert em_dash not in content, f"Em dash found in {filepath}"
        assert en_dash not in content, f"En dash found in {filepath}"

        # Check for typical emojis in range
        for ch in content:
            code = ord(ch)
            # Standard emoji ranges
            is_emoji = (
                (0x1F600 <= code <= 0x1F64F)  # emoticons
                or (0x1F300 <= code <= 0x1F5FF)  # misc symbols and pictographs
                or (0x1F680 <= code <= 0x1F6FF)  # transport and map
                or (0x1F700 <= code <= 0x1F77F)  # alchemical
                or (0x1F780 <= code <= 0x1F7FF)  # geometric shapes extended
                or (0x1F800 <= code <= 0x1F8FF)  # supplemental arrows
                or (0x1F900 <= code <= 0x1F9FF)  # supplemental symbols and pictographs
                or (0x1FA00 <= code <= 0x1FA6F)  # chess symbols
                or (0x1FA70 <= code <= 0x1FAFF)  # symbols and pictographs extended-a
                or (0x2600 <= code <= 0x26FF)    # misc symbols
                or (0x2700 <= code <= 0x27BF)    # dingbats
            )
            assert not is_emoji, f"Emoji character '{ch}' (U+{code:04X}) found in {filepath}"
