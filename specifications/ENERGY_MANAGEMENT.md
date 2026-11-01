# Energy Management & Microgrid Optimization

## 1. Purpose

This domain is a reusable digital twin for electricity use and distributed energy in a building, campus, district, or microgrid. It combines live electrical telemetry, asset topology, load and solar forecasts, optimization, and carefully bounded demand-response control.

It supports grid-connected operation first. Islanded operation, protection coordination, and emergency switching remain under approved local electrical protection, PLC, inverter, BMS, and utility controls.

## 2. Scope

The domain covers electrical feeders and substations, building zones, smart meters, rooftop solar PV, Battery Energy Storage Systems (BESS), HVAC/BMS flexibility, and managed EV charging.

Core capabilities:

- Monitor electrical demand, generation, feeder condition, power quality, BESS health, HVAC load, and EV charging.
- Forecast site load and solar generation from 15 minutes to 24 hours.
- Identify peak-demand risk, abnormal consumption, generation underperformance, and data/device faults.
- Recommend tariff-aware BESS, HVAC, and EV schedules.
- Reduce peak demand, improve renewable self-consumption, and preserve equipment and occupant constraints.
- Progress from monitoring to advice, supervised dispatch, and narrowly bounded automation.

Initial exclusions: protection relay control, unsupervised islanding/reconnection, bypassing inverter/BMS safety logic, and control of equipment without approved local integration.

## 3. Operating Modes

| Mode | Function | Control permission |
|---|---|---|
| Observe | Ingest, validate, store, and visualize live energy data | None |
| Advise | Forecast peaks and recommend dispatch or schedules | None |
| Supervised control | Submit validated BESS, HVAC, or EV actions for approval | Authorized action only |
| Bounded automation | Execute pre-approved low-risk actions within hard limits | Restricted and auditable |
| Fallback | Stop remote optimization after a fault or uncertainty | Local BMS/EMS/PLC/inverter logic only |

Local protection equipment, battery management systems, inverter controls, and manual electrical control always take priority.

## 4. Architecture

```text
Meters / Inverters / BESS / BMS / HVAC / EV Chargers / SCADA
        │  MQTT, OPC UA, BACnet/IP, OpenADR, Modbus through secure gateways
        ▼
Protocol Adapters and Validation
        ▼
Canonical Energy Entities and Asset/Topology Registry
        ├──────────────────┬──────────────────┐
        ▼                  ▼                  ▼
Time-series telemetry   Electrical GIS graph  Error/DLQ store
TimescaleDB             PostGIS               ingestion_errors
        └──────────────────┴──────────────────┘
                           ▼
State estimation, forecasts, optimization, and policy checks
                           ▼
Operator dashboard, explanations, alerts, and controlled dispatch workflow
```

The platform keeps non-overwriting states:

- `observed`: validated telemetry and device-reported state.
- `predicted`: load, solar, thermal, and state-estimation outputs.
- `scenario`: simulation and optimizer schedules.
- `command`: proposed, authorized, transmitted, acknowledged, verified, failed, expired, or rolled-back actions.

## 5. Location and Asset Model

The platform is **location-agnostic in software design**: it uses reusable asset types, topology, standard measurements, and configurable local policies rather than hardcoded city or building rules.

Each `StudyArea` still requires local onboarding: electrical single-line diagram, feeder/transformer ratings, phase connection, protection boundaries, meter mapping, building geometry, BESS/inverter limits, EV charger capabilities, tariff structure, grid code, timezone, weather source, occupancy schedules, and comfort policy.

The effective electrical topology includes static connections plus live breaker/switch states, inverter mode, BESS availability, fault/maintenance status, local/remote control mode, and confidence in each state. Every estimate, recommendation, and command records the topology version used.

## 6. Telemetry and Canonical Data

### 6.1 Inputs

| Asset | Required operational data |
|---|---|
| Smart meter / feeder | Active/reactive power, voltage, current, frequency, power factor, import/export energy, phase values where available |
| Solar inverter | AC/DC power, energy, status, fault code, inverter limits, irradiance or weather reference |
| BESS / BMS | SoC, state of health, charge/discharge power, temperature, alarms, availability, cycle count, local/remote mode |
| HVAC/BMS | Zone temperature, setpoint, occupancy state, cooling/heating load, equipment state, local override |
| EV charger | Connector status, charging power, session energy, availability, target departure/energy when consented, local schedule |

Topic format:

```text
citytwin/{environment}/{source_mode}/energy/{study_area}/{asset_type}/{asset_id}
```

Example:

```text
citytwin/prod/live/energy/campus-main/smartmeter/feeder-04
```

### 6.2 Canonical Meter Event

```json
{
  "id": "urn:energy:Meter:campus-main-feeder-04",
  "type": "EnergyMeter",
  "observedAt": "2026-09-25T16:15:00Z",
  "studyAreaId": "campus-main",
  "topologyVersion": "campus-electrical-v12",
  "activePower": {"value": 348.5, "unit": "kW", "qualityScore": 0.99},
  "reactivePower": {"value": 72.1, "unit": "kvar", "qualityScore": 0.99},
  "voltage": {"value": 415.0, "unit": "V", "qualityScore": 0.98},
  "current": {"value": 485.0, "unit": "A", "qualityScore": 0.98},
  "frequency": {"value": 50.0, "unit": "Hz", "qualityScore": 0.99},
  "powerFactor": {"value": 0.96, "unit": "1", "qualityScore": 0.99},
  "provenance": {"sourceMode": "LIVE", "gatewayId": "gw-energy-01"}
}
```

Use separate entities for meters, PV inverters, BESS, HVAC zones, EV chargers, transformers, feeders, and breakers. Link them through the topology registry instead of combining unrelated assets in one event.

Validation checks schema, unit conversion, timestamp freshness, duplicate events, device health, calibration, engineering range, phase consistency, topology mapping, and source authorization. Invalid data is isolated in `ingestion_errors` and excluded from automated dispatch.

## 7. Physical and Thermal Models

### 7.1 Electrical Power Balance and Feeder Thermal Limits

At any electrical bus, substation feeder, or microgrid Point of Common Coupling (PCC), conservation of power is computed:

$$P_{\text{grid}}(t) + P_{\text{pv}}(t) \pm P_{\text{bess}}(t) - \sum_{i=1}^{N} P_{\text{load}, i}(t) - P_{\text{loss}}(t) = 0$$

Where $P_{\text{bess}}(t) = P_{\text{bess,dis}}(t) - P_{\text{bess,ch}}(t)$.

Feeder thermal capacity constraints are continuously evaluated across distribution branches:

$$I_{k}(t) \le I_{\text{rated}, k} \quad \forall k \in \text{DistributionFeeders}$$

The system monitors active (kW) and reactive power (kVAR), line voltage (V), phase current (A), grid frequency (Hz), power factor (PF), and phase unbalance. It provides advisory state estimation and does not substitute for certified utility protection relays.

### 7.2 Building Thermal Flexibility (2R-2C ETP Model)

To model HVAC load shifting and pre-cooling without violating occupant thermal comfort boundaries (ASHRAE 55), zones use a lumped-capacitance 2R-2C Equivalent Thermal Parameter (ETP) network:

$$\frac{dT_{\text{in}}}{dt} = \frac{1}{R_1 C_{\text{in}}} (T_{\text{amb}} - T_{\text{in}}) + \frac{1}{R_2 C_{\text{in}}} (T_{\text{envelope}} - T_{\text{in}}) + \frac{\dot{Q}_{\text{hvac}} + \dot{Q}_{\text{internal}}}{C_{\text{in}}}$$

Where:
* $T_{\text{in}}$, $T_{\text{amb}}$, $T_{\text{envelope}}$: Indoor zone, ambient external, and building envelope temperatures (°C).
* $C_{\text{in}}$: Effective thermal capacitance of indoor air mass ($\text{kJ/}^\circ\text{C}$).
* $R_1, R_2$: Thermal resistances of windows/ventilation and exterior envelope walls ($^\circ\text{C/kW}$).
* $\dot{Q}_{\text{hvac}}$: Thermal cooling/heating energy delivered by the chiller/VRF system ($\text{kW}$).
* $\dot{Q}_{\text{internal}}$: Dynamic heat gains driven by occupant density proxies and equipment plug loads ($\text{kW}$).

Thermostat setpoint modulation (e.g. $\pm 1.0^\circ\text{C}$ to $\pm 1.5^\circ\text{C}$ pre-cooling during low-tariff hours) must respect configured zone comfort bands, occupancy schedules, and local manual overrides.

### 7.3 Real-Time Space Utilization & Occupancy-Driven Setbacks

Building HVAC and lighting micro-management dynamically adapts to live spatial usage:
* **Occupancy Telemetry:** Integrates PIR motion detectors, BLE beacon signals, turnstile footfall counts, and zone NDIR CO2 accumulation to estimate live spatial occupancy density.
* **Dynamic Setback Optimization:** When zone occupancy drops below a 10% threshold during operating hours, the digital twin commands an automated thermal setback ($\pm 2.5^\circ\text{C}$ temperature drift tolerance and fan speed throttling), drastically cutting chiller work in under-utilized zones without sacrificing occupant comfort in populated zones.

## 8. Forecasting and Analytics

### 8.1 Short-Horizon Load Forecasting (15-min to 24-hr)

A quantile gradient boosted trees model (XGBoost Regressor) predicts demand targets alongside prediction envelopes ($\alpha \in \{0.10, 0.50, 0.90\}$).

Features include:
* **Dimensionless Normalization:** Load normalized by transformer kVA capacity or floor area ($W/\text{m}^2$) rather than raw kW to facilitate cross-facility portability.
* **Weather Normalization:** Cooling Degree Days (CDD) and Heating Degree Days (HDD) relative to base comfort temperatures:
  $$\text{CDD} = \max(0, \; T_{\text{mean}} - T_{\text{base}})$$
* **Autoregressive Lags:** Lagged consumption at $t-15\text{m}$, $t-30\text{m}$, $t-60\text{m}$, $t-24\text{h}$, and $t-168\text{h}$ (same hour prior week).
* **Cyclic Temporal Encodings:** Sine and cosine diurnal/weekly transforms.

### 8.2 Solar PV Generation Forecasting

Estimates short-term generation using Global Horizontal Irradiance (GHI) and ambient temperature feeds:

$$\hat{P}_{\text{pv}}(t) = \eta_{\text{sys}} \cdot A_{\text{pv}} \cdot \text{GHI}(t) \cdot \left[1 - \gamma (T_{\text{cell}}(t) - 25)\right]$$

Where:
* $\eta_{\text{sys}}$: Total system efficiency including inverter and wiring losses.
* $A_{\text{pv}}$: Effective photovoltaic collector area ($\text{m}^2$).
* $\gamma$: Thermal power derating coefficient ($\% / ^\circ\text{C}$, calibrated from historical residuals).
* $T_{\text{cell}}$: Estimated PV cell temperature.

### 8.3 Energy and Equipment Alerts

Alerts cover peak-demand risk, power-factor degradation, transformer overload risk, PV underperformance, BESS SoC/cell-temperature warnings, EV charger congestion, and telemetry dropouts.

## 9. Optimization and Controlled Dispatch

### 9.1 Peak Shaving & BESS Arbitrage Formulation

The optimizer minimizes total energy cost under dynamic Time-of-Use (ToU) tariffs and monthly maximum demand charges:

$$\min \sum_{t=1}^{T} \left( C_{\text{tou}}(t) \cdot P_{\text{grid}}(t) \Delta t + C_{\text{peak}} \cdot \max_{t} [P_{\text{grid}}(t)] \right)$$

Subject to:
* $P_{\text{grid}}(t) = P_{\text{load}}(t) - P_{\text{solar}}(t) + P_{\text{bess,ch}}(t) - P_{\text{bess,dis}}(t)$
* $SoC_{\min} \le SoC(t) \le SoC_{\max} \quad \forall t$ (e.g. $20\% \le SoC \le 90\%$ to extend cycle life)
* $0 \le P_{\text{bess,ch}}(t) \le P_{\text{ch,max}}$
* $0 \le P_{\text{bess,dis}}(t) \le P_{\text{dis,max}}$
* Maximum battery degradation ramp rates (C-rate constraints).
* Feeder thermal headroom: $P_{\text{grid}}(t) \le P_{\text{transformer,rated}}$.

### 9.2 Closed-Loop Dispatch Architecture

```text
                  Optimized Dispatch
[Twin State Engine] ───────────────► [Grid Safety Interlocks]
                                             │
                                   Valid?    ├──► Violations: Lockout & Alert
                                             │
                                             ▼
                                [OpenADR / Modbus Gateway]
                                             │
                                             ▼
                             [Field Hardware (BESS / HVAC / EV)]
                                             │
                                             ▼
                             [Substation Current & Power Response]
                                             │
                                             ▼
                             [Closed-Loop State Reconciliation]
```

### 9.3 Safety Interlocks & Failsafe Protocols

1. **Under/Over-Voltage Lockout:** Remote dispatch immediately locks out if feeder voltage drifts beyond statutory limits ($\pm 6\%$ of nominal 415V/230V).
2. **Ramp-Rate Throttling:** BESS inverter setpoint shifts are capped to a maximum slew rate of $10\%\text{ per minute}$ to eliminate harmonic resonance and voltage flicker.
3. **Dead-Band Thresholding:** Dispatch commands are suppressed if the forecasted peak reduction is less than $15\text{ kW}$ or falls within measurement noise margins.
4. **Communication Loss Fallback:** If MQTT heartbeat or OpenADR keep-alive signals fail for $>60\text{ seconds}$, field actuators revert to autonomous local controllers (e.g. internal BESS peak-shaving logic).

## 10. Security, Audit, and Compliance

Use segmented IT/OT networks, mutually authenticated encrypted connections, device certificates, least-privilege role-based access, explicit command authorization, credential rotation, and tamper-evident audit records.

Keep traceable records of data corrections, topology updates, forecast/model versions, scenarios, recommendations, approvals, dispatches, acknowledgments, overrides, and failures. Local grid codes, utility interconnection agreements, demand-response contracts, building policy, and electrical safety requirements are configured per deployment.

## 11. Rollout and Acceptance

1. **Foundation:** onboard assets, single-line topology, device mapping, limits, tariffs, grid rules, building policy, and security controls.
2. **Read-only twin:** validate telemetry, show operational dashboards, reconcile meter totals, and monitor data quality.
3. **Analytics:** deploy demand/PV forecasting, peak-risk alerts, BESS health visibility, and equipment anomaly detection.
4. **Decision support:** recommend BESS, HVAC, and EV schedules with explanations and operator feedback.
5. **Supervised pilot:** test tightly constrained actions in selected assets with approval, verification, and rollback.
6. **Bounded automation:** enable only after measured performance, safety tests, operational approval, and reliable fallback behavior.

Minimum readiness requirements:

- Critical measurements and asset mappings are accurate, sufficiently complete, and traceable.
- Electrical topology, local/remote state, and equipment limits are current.
- Forecasts and optimization outputs meet locally defined accuracy and safety criteria.
- All commands are authenticated, time-limited, idempotent, logged, and field-verified.
- Operators can view, pause, override, and roll back automation at any time.

## 12. Open Configuration Decisions

- Target environment: building, campus, district microgrid, or industrial site.
- Available integrations: smart meters, SCADA, BMS, BESS EMS/BMS, inverters, and EV charging platform.
- Applicable tariff, demand-charge, grid-code, interconnection, and demand-response rules.
- Comfort policy, critical-load definition, battery reserve requirement, and EV charging priority.
- Assets allowed in observe, advise, supervised-control, and bounded-automation modes.
