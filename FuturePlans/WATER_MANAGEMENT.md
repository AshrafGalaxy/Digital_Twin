# Water Distribution & Quality Management

## 1. Purpose

This domain is a reusable digital twin for potable or utility-water networks in a city, campus, or industrial site. It combines live telemetry, network topology, hydraulic analysis, demand forecasting, water-quality monitoring, and safe operational recommendations.

It is **location-agnostic by design**, not plug-and-play: every new deployment must onboard its local assets, sensors, elevation data, operating rules, tariffs, regulations, and hydraulic calibration.

## 2. Scope

The domain covers District Metered Areas (DMAs), transmission and distribution pipes, tanks/reservoirs, booster stations, pumps, motorized valves, and pressure-reducing valves (PRVs).

Core capabilities:

- Monitor flow, pressure, tank level, pump/valve state, pH, chlorine, turbidity, conductivity, and device health.
- Estimate network state and identify pressure, flow-balance, quality, and data-quality anomalies.
- Detect and prioritize suspected leakage or burst events.
- Forecast water demand from 15 minutes to 24 hours.
- Recommend pump schedules and PRV setpoints to reduce energy use and excess pressure.
- Progress safely from monitoring to advice, supervised control, and only then bounded automation.

Out of scope for the initial release: automatic emergency pipe isolation, autonomous chemical dosing, and replacement of PLC/SCADA safety logic.

## 3. Operating Modes

| Mode | Function | Actuation |
|---|---|---|
| Observe | Collect, validate, store, and visualize field data | None |
| Advise | Produce alerts, forecasts, and recommended actions | None |
| Supervised control | Submit a validated command for authorized operator approval | Approved commands only |
| Bounded automation | Execute pre-approved, low-risk adjustments within fixed limits | Restricted and auditable |
| Fallback | Suspend remote optimization after faults or uncertainty | Local PLC/pilot control only |

Manual local control always overrides the platform.

## 4. Shared Architecture

```text
Sensors / SCADA / Edge Gateways
        │  MQTT, OPC UA, HTTPS over authenticated TLS
        ▼
Ingestion & Protocol Adapters
        ▼
Schema, unit, timestamp, range, and sensor-health validation
        ▼
Canonical Water Entity Normalization
        ├───────────────┬─────────────────┐
        ▼               ▼                 ▼
Time-series store   Asset/topology GIS   Error/DLQ store
TimescaleDB         PostGIS              ingestion_errors
        └───────────────┴─────────────────┘
                        ▼
Hydraulic balances, state estimation, forecasting, and optimization
                        ▼
Operator dashboard, explanations, alerts, and controlled command workflow
```

All operational records are stored as separate, non-overwriting states:

- `observed`: validated field telemetry and field-reported asset state.
- `predicted`: forecasts and inferred hydraulic/quality state.
- `scenario`: simulation and optimization output.
- `command`: proposed, approved, sent, acknowledged, verified, failed, or rolled-back actions.

## 5. Location and Topology Model

Assets use geographic coordinates and a connected graph of pipes, junctions, tanks, pumps, valves, and DMA boundaries. Analytics operate on this graph rather than on hardcoded place-specific rules.

A `StudyArea` configuration stores local timezone, holidays, weather source, service-pressure limits, quality thresholds, tariff rules, regulations, and operating schedules.

The system maintains an **effective hydraulic topology**, not just a static pipe map. It includes live or manually confirmed valve positions, pump states, bypasses, isolations, maintenance work, and confidence in each state. Every forecast, optimization, alert, and command references the topology version used.

## 6. Telemetry and Data Quality

### 6.1 Inputs

| Asset type | Main readings |
|---|---|
| Flow meters | Flow rate and totalized volume at DMA inlets/outlets |
| Pressure sensors | Pressure at critical nodes and DMA boundaries |
| Tanks/reservoirs | Level, volume, overflow/low-level condition |
| Water-quality probes | pH, free residual chlorine, turbidity, conductivity, and temperature where available |
| Pumps and valves | Running state, speed, fault state, position, local/remote mode |

Example topic:

```text
citytwin/{environment}/{source_mode}/water/{study_area}/{asset_type}/{asset_id}
```

Example:

```text
citytwin/prod/live/water/dma-central-04/flowmeter/fm-inlet-01
```

### 6.2 Canonical Event

```json
{
  "id": "urn:ngsi-ld:WaterDistributionNode:dma-central-04-node-12",
  "type": "WaterDistributionNode",
  "observedAt": "2026-09-25T16:10:00Z",
  "studyAreaId": "dma-central-04",
  "topologyVersion": "water-topology-dma-central-04-v17",
  "pressure": {"value": 3.42, "unit": "bar", "qualityScore": 0.99},
  "flowRate": {"value": 142.8, "unit": "L/s", "qualityScore": 0.98},
  "waterQuality": {
    "freeResidualChlorine": {"value": 0.85, "unit": "mg/L"},
    "turbidity": {"value": 1.12, "unit": "NTU"},
    "pH": {"value": 7.35, "unit": "pH"}
  },
  "provenance": {"sourceMode": "LIVE", "gatewayId": "gw-water-02"}
}
```

All events use UTC timestamps. The system derives local schedules, minimum-night-flow windows, tariffs, and holidays using the configured IANA timezone.

Validation checks schema, identifiers, timestamps, units, duplicates, engineering ranges, calibration status, device health, and geographic/asset mapping. Invalid or suspicious events go to `ingestion_errors`; they do not feed operational models until resolved.

## 7. Analytics & Physical Hydraulics

### 7.1 Water Mass Balance & Minimum Night Flow (MNF)

For each District Metered Area (DMA), the system continuously evaluates conservation of mass over each time step $[t_1, t_2]$:

$$\Delta V_{\text{storage}} = \int_{t_1}^{t_2} \left( \sum Q_{\text{in}}(t) - \sum Q_{\text{out}}(t) \right) dt$$

1. **Mass Balance Discrepancy ($Q_{\text{loss}}$):**
   $$Q_{\text{loss}} = Q_{\text{net\_inflow}} - Q_{\text{authorized\_consumption}} - \frac{\Delta V_{\text{storage}}}{\Delta t}$$
2. **Dynamic Leakage Index & Burst Detection:** During low-demand night hours (02:00–04:00 local time), real-time net inflow is compared against baseline Minimum Night Flow ($MNF_{\text{baseline}}$). An anomalous step change ($\Delta Q > 3\sigma$) triggers an immediate pipe burst / transient acoustic alert.

### 7.2 Dynamic Hydraulic Grade Line (HGL) State Estimation

The platform estimates nodal pressure, flow, and head across uninstrumented junctions using Hazen-Williams head-loss equations mapped to PostGIS pipe geometry:

$$h_f = 10.67 \cdot \frac{L \cdot Q^{1.852}}{C^{1.852} \cdot D^{4.8704}}$$

Where:
* $L$: Pipe length (m) extracted from PostGIS geometry.
* $D$: Hydraulic diameter (m) from the pipe asset registry.
* $C$: Hazen-Williams roughness coefficient calibrated by pipe material and operational age.

### 7.3 Predictive Demand Forecasting

A Quantile XGBoost Regressor forecasts water demand for 15-minute to 24-hour horizons across 5th, 50th, and 95th percentiles ($\alpha \in \{0.05, 0.50, 0.95\}$) using the pinball loss function:

$$\mathcal{L}_{\text{quantile}}(y, \hat{y}_\alpha) = \max\Big(\alpha(y - \hat{y}_\alpha), (\alpha - 1)(y - \hat{y}_\alpha)\Big)$$

Features include:
* Sine/Cosine cyclical encoding of hour-of-day and day-of-week, plus statutory holiday flags.
* Autoregressive lags at $t-15\text{m}$, $t-30\text{m}$, $t-1\text{h}$, $t-24\text{h}$, and $t-7\text{d}$.
* Rolling statistics (3-hour mean, variance, min/max ratios).
* Ambient dry-bulb temperature, solar radiation, and rainfall indicators from local weather adapters.

### 7.4 Chemical Dispersion & Disinfection Decay Modeling

Predicts chlorine decay across long retention transit paths using first-order kinetic transport coupled with water temperature features:

$$C(t) = C_0 \cdot e^{-k \cdot t}$$

Where decay coefficient $k$ is adjusted in real time via an empirical regression sub-model driven by water temperature, initial organic load, and pipe wall material coefficients.

### 7.5 Dual-Method Pipeline: Mapped Utilities vs. Unmapped Sector Fallback

The twin supports a dual-tier analytical strategy to accommodate varying infrastructure maturity:
1. **Digitally Mapped Networks:** Ingests PostGIS pipe topologies, valve states, and digital elevation models (DEM) to run Hazen-Williams fluid mechanics and continuous nodal pressure/flow estimation.
2. **Unmapped or Developing Sectors:** Acts as a resilient fallback by employing proxy models driven by aggregate municipal billing records, demographic census data, and population heuristics to estimate localized demand and detect macro-level distribution anomalies without requiring dense subterranean sensor instrumentation.

### 7.6 Supply Reserve Runway & Rainwater Harvesting Tracking

The platform tracks upstream water security by integrating storage reserves and natural replenishment:
* **Reservoir & Dam Storage Balance:** Models daily municipal drawdown rates against current storage capacity to compute depletion runway (days of remaining reserve under prevailing consumption trends).
* **Rainwater Harvesting Catchment Yields:** Calculates potential stormwater capture across public and institutional catchment surfaces using rainfall telemetry ($Y = P \cdot A \cdot C_{\text{runoff}}$), advising operators on aquifer recharge and raw water abstraction offset opportunities.

## 8. Closed-Loop Optimization & Control

### 8.1 Pressure Management

The system optimizes PRV setpoints across DMAs to ensure minimum critical pressure ($P_{\text{crit}} \ge 1.5\text{ bar}$) is sustained at the highest topological elevation node while minimizing background pressure to reduce burst frequencies.

### 8.2 Energy-Efficient Pump Scheduling (Water-Energy Nexus)

Balancing reservoir filling is scheduled to minimize electricity tariff costs:

$$\min \sum_{t=1}^{T} \left( \text{Tariff}(t) \cdot P_{\text{pump}}(Q(t), H(t)) \right)$$

Subject to:
* $V_{\min} \le V_{\text{tank}}(t) \le V_{\max} \quad \forall t \in T$
* $P_{\text{node}}(t) \ge P_{\text{service\_min}}$
* Mechanical cycling limit: maximum 3 pump start/stop cycles per pump per hour to prevent motor fatigue.

### 8.3 Closed-Loop Actuation Architecture

```text
                  Optimized Setpoints
[Twin State Engine] ───────────────► [Control Safety Interlock]
                                            │
                                  Valid?    ├──► Reject: Alert Operator
                                            │
                                            ▼
                                [Actuator Driver Gateway]
                                            │
                                            ▼ (Modbus / Industrial MQTT)
                              [Physical Hardware (PRVs / VFDs)]
                                            │
                                            ▼
                                [Field Response Telemetry]
                                            │
                                            ▼
                               [State Verification & Delta Log]
```

### 8.4 Safety Interlocks and Failsafe Protocols

All commands are validated against physical invariants:
1. **Rate-of-Change Limiter:** Actuator valve modulation is constrained to $\le 5\%$ position change per minute to eliminate hydraulic water hammer shockwaves.
2. **Dead-Band Threshold:** Setpoint adjustments are suppressed if state variance is within a $\pm 3\%$ dead-band to prevent actuator hunting.
3. **Heartbeat Loss Fallback:** If communication with the field gateway experiences heartbeat timeouts exceeding 90 seconds, all controllers freeze in their last known safe configuration or revert to local hydraulic pilot control.
4. **Non-Bypass Invariant:** The platform never bypasses local PLC, mechanical, or process-safety interlocks.

## 9. Security, Audit, and Compliance

The deployment requires segmented IT/OT networking, authenticated encryption, device certificates, least-privilege user roles, command authorization, certificate rotation, and tamper-evident audit logs.

All data changes, model versions, recommendations, approvals, commands, acknowledgments, overrides, and failures must be traceable. Water-quality thresholds, escalation roles, confirmatory sampling, and reporting procedures are configured per jurisdiction and utility policy.

## 10. Rollout Plan and Readiness

1. **Foundation:** onboard assets, sensors, DMA boundaries, data units, calibration records, topology, and local rules.
2. **Read-only twin:** validate telemetry, store history, show GIS and operational dashboards, and monitor data quality.
3. **Analytics:** introduce demand forecasts, water balance, pressure residuals, quality alerts, and suspected-loss prioritization.
4. **Decision support:** provide explainable PRV and pump recommendations; record operator acceptance or rejection.
5. **Supervised pilot:** test constrained commands in a selected DMA or pump station with direct operator approval and rollback.
6. **Bounded automation:** enable only after measured safety, accuracy, availability, and operator-acceptance criteria are met.

Minimum readiness criteria:

- Critical telemetry is sufficiently complete, valid, calibrated, and traceable.
- Asset topology and live operational state are reliable enough for the selected use case.
- Forecast and hydraulic models meet locally defined validation targets.
- Commands are authenticated, idempotent, time-limited, logged, and independently verified.
- Operators can pause, override, and roll back all automation.

## 11. Open Configuration Decisions

- Target deployment: municipal DMA, campus, industrial site, potable water, or utility water.
- Available data sources: real sensors, SCADA/PLC, manual entries, historical datasets, or simulation.
- Hydraulic solver and calibration process.
- Applicable water-quality standards, service-pressure policy, tariffs, and incident ownership.
- Assets permitted for observation, advice, supervised control, and bounded automation.
