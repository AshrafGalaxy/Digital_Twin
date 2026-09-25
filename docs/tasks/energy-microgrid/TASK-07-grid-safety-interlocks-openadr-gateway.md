# Task 07: Grid Safety Interlocks & OpenADR / Modbus Failsafe Dispatch Gateway

- **Task Identifier:** `TASK-07`
- **Domain:** Energy Management & Microgrid Optimization
- **Specification Reference:** [`ENERGY_MANAGEMENT.md`](../../FuturePlans/ENERGY_MANAGEMENT.md) Section 9.2, 9.3, 10
- **Component / Scope:** Backend & Telemetry
- **Priority:** High
- **Type:** Interlocks & Failsafe Communication

---

## 1. Context & Objective

In digital twin applications involving electrical microgrids, transmitting optimized setpoints to distributed inverters, BESS controllers, and building chillers requires **uncompromising electrical protection and communication failsafes**.

Sending an unverified or delayed dispatch signal can cause transformer overloading, voltage flickers, harmonic resonance, or battery degradation.

This task implements the **Grid Safety Interlocks & OpenADR / Modbus Failsafe Dispatch Gateway**. Before any approved demand-response or battery schedule is serialized to field hardware (via OpenADR 2.0b VEN/VTN or Modbus TCP registers), the gateway verifies four hard physical safety interlocks (Voltage Lockout, Ramp-Rate Slew Capping, Dead-Band Thresholding, and Communication Heartbeat Fallback).

---

## 2. Hard Safety Interlocks & Failsafe Invariants

### 2.1 Under/Over-Voltage Lockout Invariant (Section 9.3)
Remote battery discharge and HVAC load shifting are immediately suppressed if local feeder voltage drifts outside statutory bounds:
$$V_{\text{nominal}} \times 0.94 \le V_{\text{line}}(t) \le V_{\text{nominal}} \times 1.06 \quad (390.1\text{V} \le V \le 439.9\text{V} \text{ for 415V})$$
*Action upon violation:* Lock out remote control, revert to grid-following standby, and emit immediate grid quality alert.

### 2.2 Ramp-Rate Slew Throttling
To eliminate grid voltage flickers and power quality degradation, battery inverter power transitions are capped to a maximum slew rate of $10\%\text{ per minute}$:
$$\left|\frac{\Delta P_{\text{bess}}}{\Delta t}\right| \le 0.10 \times P_{\text{rated, bess}} \quad (\text{kW/min})$$

### 2.3 Dead-Band Thresholding
To prevent minor transient fluctuations from cycling equipment unnecessarily:
$$\text{Suppress dispatch if: } |\Delta P_{\text{shave}}| < 15.0\text{ kW}$$

### 2.4 Communication Loss Fallback Timer
Field actuator connections must maintain continuous bidirectional heartbeats:
$$t_{\text{now}} - t_{\text{heartbeat}} > 60.0\text{ s} \implies \text{Drop remote control; revert to local autonomous BMS/inverter logic}$$

---

## 3. Data Contracts & OpenADR 2.0b Payload

### Outgoing OpenADR 2.0b `distributeEvent` Payload:
```xml
<oadr:oadrDistributeEvent xmlns:oadr="http://openadr.org/oadr-2.0b/2012/07">
  <oadr:oadrResponse>
    <oadr:responseCode>200</oadr:responseCode>
    <oadr:responseDescription>OK</oadr:responseDescription>
  </oadr:oadrResponse>
  <oadr:oadrEvent>
    <ei:eventDescriptor>
      <ei:eventID>EVT-DR-20260926-004</ei:eventID>
      <ei:modificationNumber>1</ei:modificationNumber>
      <ei:priority>1</ei:priority>
      <ei:eiMarketContext>http://MarketContext/PuneDiscom/PeakShave</ei:eiMarketContext>
      <ei:createdDateTime>2026-09-26T12:00:00Z</ei:createdDateTime>
      <ei:eventStatus>far</ei:eventStatus>
    </ei:eventDescriptor>
    <ei:eiEventSignals>
      <ei:eiEventSignal>
        <ei:signalName>LOAD_DISPATCH</ei:signalName>
        <ei:signalType>level</ei:signalType>
        <ei:signalID>SIG-01</ei:signalID>
        <ei:currentValue>
          <ei:payloadFloat>
            <ei:value>-350.0</ei:value> <!-- Curtail/Discharge 350 kW -->
          </ei:payloadFloat>
        </ei:currentValue>
      </ei:eiEventSignal>
    </ei:eiEventSignals>
  </oadr:oadrEvent>
</oadr:oadrDistributeEvent>
```

---

## 4. Step-by-Step Implementation Guide

1. **Safety Interlock Engine:** Implement `backend/services/grid_safety_gateway.py` validating the 4 safety rules before dispatch serialization.
2. **Payload Serialization:** Build adapters for both OpenADR 2.0b XML/JSON and Modbus TCP register writes (holding registers for active power setpoints).
3. **Heartbeat & Watchdog:** Implement asynchronous background task checking connection timestamps every 10 seconds.
4. **Audit Logger:** Write every dispatch attempt, parameter payload, verification status, and actuator response to `energy_dispatch_audit_log`.
5. **Automated Tests:** Add hermetic tests in `tests/test_grid_safety_gateway.py` asserting that voltage anomalies and excessive slew rates immediately abort dispatches.

---

## 5. Architectural Invariants Checklist (`AGENTS.md`)
- [ ] **Strict Non-Actuation:** The gateway requires external human authorization signature before generating executable dispatch tickets.
- [ ] **Failsafe Invariant:** Communication timeouts ($>60\text{s}$) strictly drop central optimization and return local control to certified PLCs.
- [ ] **Strictly Zero Emojis:** Zero emojis in code, XML comments, or system logs.
