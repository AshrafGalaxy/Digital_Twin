# Intelligent Traffic Mobility & Adaptive Corridor Control

## 1. Purpose

This domain is a reusable traffic digital twin for a city, district, campus, or corridor. It combines live traffic observations, road-network topology, short-horizon forecasting, SUMO scenario simulation, and safe signal-timing decision support.

The platform is designed to be **location-agnostic in software**, not zero-setup. Each new Study Area imports a road graph and then progressively verifies local signal, sensor, safety, legal, and operational data. Production operation is advisory by default; local traffic controllers and road-authority procedures remain authoritative.

## 2. Scope

The domain covers road links, intersections, pedestrian crossings, corridors, signal controllers, detectors, and multimodal movement including cars, two-wheelers, buses, freight, cyclists, and pedestrians where data is available.

Core capabilities:

- Monitor traffic volume, speed, occupancy, travel time, queue risk, signal state, and sensor health.
- Estimate current congestion, corridor performance, and Level of Service using locally configured definitions.
- Forecast speed, demand, congestion, and queue risk for 15 to 60 minutes.
- Run isolated SUMO what-if scenarios for signal plans, incidents, road closures, or corridor coordination.
- Recommend signal-cycle, split, offset, and priority adjustments inside a verified safety envelope.
- Preserve privacy by using aggregated edge analytics and anonymized/aggregated probe data only.

Initial exclusions: direct override of certified signal safety functions, emergency pre-emption, rail-crossing control, unsupervised signal-plan deployment, enforcement, surveillance, and storage of raw CCTV, faces, licence plates, or individual GPS trajectories.

## 3. Operating Modes

| Mode | Function | Signal-control permission |
|---|---|---|
| Map and simulate | Import the road graph and run non-live scenarios | None |
| Observe | Ingest and validate live traffic, controller, and device data | None |
| Advise | Forecast congestion and recommend timing plans | None |
| Supervised pilot | Submit a validated plan for road-authority approval | Approved plan only |
| Bounded automation | Execute pre-approved adjustments within a controller-certified envelope | Restricted; only after formal approval |
| Fallback | Suspend central optimization after fault or uncertainty | Local fixed-time/actuated controller only |

Manual local control, safety interlocks, emergency procedures, and certified controller logic always override the platform.

## 4. Architecture

```text
Detectors / Radar / Edge Vision / Fleet Probes / Signal Controllers
        │  MQTT, HTTPS, NTCIP or approved secure gateway
        ▼
Protocol Adapters and Validation
        ▼
Canonical Traffic Entities and Network/Signal Registry
        ├──────────────────┬──────────────────┐
        ▼                  ▼                  ▼
Time-series telemetry   Road/signal topology  Error/DLQ store
TimescaleDB             PostGIS               ingestion_errors
        └──────────────────┴──────────────────┘
                           ▼
State estimation, forecasting, SUMO scenarios, optimization, safety policy
                           ▼
Operator dashboard, evidence, recommendation queue, approved command workflow
```

The platform keeps separate, non-overwriting records:

- `observed`: validated sensor, probe, and controller telemetry.
- `predicted`: congestion, demand, queue, and travel-time forecasts.
- `scenario`: SUMO inputs, calibration version, outputs, and comparisons.
- `recommendation`: proposed timing plan, evidence, safety checks, reviewer decision, and expiry.
- `command`: approved, transmitted, acknowledged, active, rejected, failed, expired, or rolled-back actions.

## 5. Location Onboarding and Topology

A new Study Area can start with an imported map and progressively unlock capabilities.

| Onboarding layer | Source and purpose |
|---|---|
| Imported base map | OSM, official GIS, or campus map provides links, nodes, road class, geometry, and initial SUMO network |
| Verified network layer | Authority confirms lanes, turns, one-way rules, bus stops, crossings, speed limits, closures, and temporary restrictions |
| Connected device layer | Sensors, edge nodes, controller IDs, detector-to-lane mapping, and SPaT feeds are registered |
| Safety/policy layer | Approved phase plans, intergreen, amber, all-red, pedestrian clearance, priority, fallback, and command permissions are configured |
| Calibration layer | Historical and field observations tune demand, vehicle mix, behavior, and SUMO parameters |

The effective topology includes static road links and intersections plus dynamic closures, work zones, controller mode, detector health, phase-plan version, signal fault state, and confidence in each item. Every forecast, scenario, recommendation, and command stores the topology and signal-plan version used.

## 6. Data and Privacy

### 6.1 Inputs

| Source | Data used |
|---|---|
| Loop or virtual detector | Count, occupancy, headway, lane/approach ID |
| Radar or microwave sensor | Directional count, classified count, speed, lane/approach ID |
| Edge vision | Aggregated line-crossing count, class count, density, queue estimate, and confidence only |
| Fleet or transit probes | Aggregated segment travel time and speed; no individual trajectory storage |
| Signal controller | SPaT, phase-plan ID, stage duration, cycle length, detector state, fault and local/remote mode |
| Context feeds | Weather, planned events, roadworks, closures, and incidents where approved |

Topic format:

```text
citytwin/{environment}/{source_mode}/traffic/{study_area}/{device_type}/{device_id}
```

Example:

```text
citytwin/prod/live/traffic/corridor-a/radar/approach-north-01
```

### 6.2 Canonical Segment Event

```json
{
  "id": "urn:traffic:RoadSegment:corridor-a-seg-04",
  "type": "TrafficFlowObserved",
  "observedAt": "2026-09-25T16:20:00Z",
  "studyAreaId": "corridor-a",
  "topologyVersion": "traffic-network-corridor-a-v9",
  "averageSpeed": {"value": 18.4, "unit": "km/h", "qualityScore": 0.98},
  "vehicleCount": {"value": 112, "unit": "vehicle", "qualityScore": 0.97},
  "occupancy": {"value": 0.74, "unit": "1", "qualityScore": 0.96},
  "queueEstimate": {"value": 55, "unit": "m", "qualityScore": 0.80},
  "provenance": {"sourceMode": "LIVE", "gatewayId": "edge-traffic-01"}
}
```

All event timestamps are stored in UTC; operational schedules use the Study Area timezone.

The ingestion layer checks source authorization, schema, units, timestamp freshness, duplicate/late data, sensor location, lane/approach mapping, engineering plausibility, detector/vision health, and cross-source consistency. Invalid or low-confidence data is stored with a reason and excluded from automated recommendations.

Privacy rules:

- Do not store or transmit raw video, facial images, licence plates, or identifiable device IDs.
- Process vision at the edge and send aggregates only.
- Aggregate probe data spatially and temporally; apply retention and access policies.
- Audit access to traffic data, configuration, scenarios, and commands.

## 7. Traffic State and Simulation

### 7.1 Traffic State

The system derives traffic state from counts, speeds, occupancy, probes, and controller data. Fundamental relationships include hydrodynamic continuity and the Fundamental Diagram of Traffic Flow:

$$q = k \cdot v$$

$$\frac{\partial k}{\partial t} + \frac{\partial q}{\partial x} = 0$$

where $q$ is traffic volume or flow rate ($\text{vehicles/hour}$), $k$ is traffic density ($\text{vehicles/km}$), and $v$ is space-mean speed ($\text{km/h}$).

A normalized congestion score compares observed speed with locally verified free-flow speed ($v_{\text{free}}$):

$$CI = \min\left(1.0, \; \max\left(0.0, \; 1.0 - \frac{v_{\text{observed}}}{v_{\text{free}}}\right)\right)$$

Level of Service (LOS A through F per Indian Highway Capacity Manual / IRC:106 guidelines), saturation, queue thresholds, and alert severity are configured per road class and local policy. They are not assumed to be universal.

### 7.2 SUMO Microscopic Simulation & TraCI Integration

SUMO microscopic behavioral runs are strictly decoupled and isolated from live observations. A scenario records its road-network version, demand input, signal-plan version, vehicle mix, behavior parameters, random seed ($S_0$), and delta results.

```text
Live / Replay Observations ──► [PostgreSQL / TimescaleDB]
                                      │
                                      ▼
                        [TraCI Scenario Dispatcher]
                                      │
                 ┌────────────────────┴────────────────────┐
                 ▼ (Seed: S_0)                             ▼ (Seed: S_0)
        [SUMO Baseline Run]                      [SUMO Intervention Run]
        (Current Signal Timings)                 (Optimized Splits / Green Waves)
                 │                                         │
                 └────────────────────┬────────────────────┘
                                      ▼
                          [Delta KPI Calculator]
                   (Travel Time, Delay, Queue Length)
                                      │
                                      ▼
                         [Scenario Comparison UI]
```

Scenario comparisons evaluate:
- **Travel Time & Delay:** Average link travel time and stopped delay per vehicle.
- **Queue Length:** Maximum and mean queue length across approach lanes.
- **Throughput & Stops:** Net vehicles cleared per hour and deceleration stop count.
- **Fairness & Transit:** Side-road wait times, transit bus reliability, and pedestrian crossing clearance.

SUMO models must be calibrated and validated against field observations before being used to justify operational recommendations. Important calibration targets include turning proportions, approach flow, travel time, queue length, speed, vehicle mix (two-wheelers, auto-rickshaws, cars, heavy vehicles), and mixed/non-lane-based movement typical of Indian urban corridors.

## 8. Forecasting and Explainability

A quantile gradient boosted trees model (XGBoost Regressor) predicts 15- to 60-minute traffic conditions at low, expected, and high ranges ($\alpha \in \{0.10, 0.50, 0.90\}$).

Features include:
- **Normalized Flow Ratios:** Volume-to-Capacity ratio ($V/C = \frac{q}{C_{\text{veh}}}$) rather than absolute vehicle counts.
- **Topological Spatial Lags:** Speeds and densities from immediate 1st-degree and 2nd-degree upstream ($L_{-1}, L_{-2}$) and downstream ($L_{+1}$) road links extracted automatically from PostGIS network topology.
- **Temporal Lag Features:** Moving averages and lags at $t-5\text{m}$, $t-10\text{m}$, $t-15\text{m}$, $t-30\text{m}$, and $t-60\text{m}$.
- **Cyclic Temporal Encodings:**
  $$\sin\left(\frac{2\pi \cdot \text{minute\_of\_day}}{1440}\right), \quad \cos\left(\frac{2\pi \cdot \text{minute\_of\_day}}{1440}\right)$$
- **Contextual Features:** Rainfall intensity ($\text{mm/h}$) and visibility ($\text{km}$) ingested via local weather adapters.

Validation requires chronological back-testing against persistence and same-time historical baselines without random data shuffling. Every material forecast and recommendation includes TreeSHAP (SHapley Additive exPlanations) attributions identifying the top contributing factors (e.g. upstream queue spillback vs. adverse weather conditions).

### 8.2 Multimodal Transit Demand & Crowd Flow Forecasting

The twin forecasts public transport rider demand and passenger platform accumulations:
* **Transit Station Crowd Density:** Evaluates pedestrian crowd accumulation at bus stops and transit interchanges using optical/ToF occupancy sensors, forecasting 15- to 60-minute passenger boarding surges.
* **Transit Signal Priority (TSP) Synchronization:** Integrates dynamic bus dwell-time predictions with intersection signal controllers, ensuring green-phase extensions for high-occupancy buses are coordinated with actual passenger clearance times.

## 9. Signal Optimization and Safety

### 9.1 Adaptive Signal Timing Optimization Formulation

The optimizer recommends green phase splits and cycle lengths using a modified Webster delay minimization formulation under saturation constraints:

$$\min \sum_{j=1}^{M} D_j = \sum_{j=1}^{M} \left[ \frac{C (1 - \lambda_j)^2}{2(1 - \lambda_j x_j)} + \frac{x_j^2}{2 q_j (1 - x_j)} \right]$$

Subject to the following strict operational constraints:
* $\lambda_j = \frac{g_j}{C}$ (Green split ratio for phase $j$)
* $x_j = \frac{q_j}{s_j \lambda_j}$ (Degree of saturation, constrained to $x_j \le 0.85$ to prevent hyper-congested queue collapse)
* $g_{\min} \le g_j \le g_{\max} \quad \forall j$ (Phase green bounds)
* $C_{\min} \le \sum (g_j + l_j) \le C_{\max}$ (Cycle time bounds, e.g., $60\text{s} \le C \le 150\text{s}$)
* **Pedestrian Clearance Invariant:** Optimization cannot compress pedestrian walk phases below statutory crosswalk safety limits:
  $$t_{\text{walk}} \ge \frac{\text{crosswalk\_width}}{1.2\text{ m/s}}$$

No optimization may remove, shorten, or bypass a safety-critical interval.

### 9.2 Arterial Coordination (Green Wave)

For coordinated arterial corridors, offset optimization matches progression speed across sequential junctions:

$$\theta_{i, i+1} = \frac{d_{i, i+1}}{v_{\text{progression}}} \pmod C$$

Where $d_{i, i+1}$ is the link distance between consecutive intersections extracted from PostGIS edge lengths (e.g., $850\text{ m}$ between Viman Nagar Chowk and Somnath Nagar Chowk) and $v_{\text{progression}}$ is the design progression speed (e.g., $40\text{ km/h} \approx 11.11\text{ m/s}$). A proposed green wave offset is rejected if downstream storage capacity is insufficient or causes queue spillback.

### 9.3 Safety Interlocks, Governance, and Recommendation Lifecycle

```text
Proposed → Simulation & Evidence Attached → Safety Policy Validated (x_j <= 0.85)
→ Authority Review & Approval → Sent to Approved Gateway → Controller Acknowledged
→ Active State Verified → Completed, Failed, Expired, or Rolled Back
```

Key Safety Invariants:
1. **Pilot Mode Advisory Invariant:** In pilot operating mode, all optimization vectors are written to the `recommendations` table with status `REQUIRES_HUMAN_APPROVAL`. The platform strictly prohibits direct autonomous signal override.
2. **Phase-Flapping Prevention:** Any automated phase modulation is constrained by a minimum hold-down timer ($t_{\text{hold}} \ge 120\text{s}$) to avoid rapid cycle shifting that disorients drivers.
3. **Communication Loss Fallback:** If edge controllers lose heartbeat connection to the central twin for $>30\text{ seconds}$, controllers immediately drop to isolated, local fixed-time or vehicle-actuated fallbacks.
4. **Data Stale Lockout:** Optimization proposals are suppressed if sensor observations are older than $180\text{s}$.

## 10. Emergency, Security, and Governance

### 10.1 Structural Health Monitoring (SHM) of Critical Infrastructure

The platform ingests real-time structural telemetry on key corridor assets (e.g., flyovers, bridges, and elevated viaducts):
* **Sensor Suite:** Tri-axial accelerometers, piezoelectric vibration transducers, and fiber-optic strain gauges reporting modal frequencies and micro-strain ($\mu\varepsilon$).
* **Axle Load Correlation:** Telemetry is correlated with heavy commercial vehicle (HCV) axle loads from Weigh-in-Motion (WIM) sensors, tracking cumulative stress cycles and alerting highway authorities to micro-cracking risks for proactive preventive maintenance.

### 10.2 Emergency Coordination and Operational Governance

Emergency vehicle pre-emption, public-transit priority, rail crossings, evacuation routing, school zones, and incident response are controlled by separately approved authority policies. They cannot be inferred or overridden by the optimizer.

Use segmented IT/OT networks, authenticated encrypted gateways, controller/device identities, least-privilege access, signed or auditable command handling, credential rotation, and tamper-evident logs. Keep a full history of topology updates, signal-plan versions, sensor status, scenarios, model versions, recommendations, approvals, commands, overrides, and failures.

## 11. Rollout and Acceptance

1. **Map and baseline:** import the road graph, verify key geometry, and build an initial non-live SUMO model.
2. **Observe:** connect traffic and controller telemetry; validate mapping, quality, privacy, and dashboard outputs.
3. **Predict:** deploy congestion forecasts, alerts, and confidence/fallback handling.
4. **Simulate:** calibrate SUMO and compare scenarios with observed travel time, queues, and flows.
5. **Advise:** deliver operator-reviewed timing recommendations within a verified safety envelope.
6. **Supervised pilot:** trial limited, time-bound changes with authority approval, controller acknowledgement, and rollback.
7. **Bounded automation:** permit only after formal traffic-authority approval, demonstrated safety, and tested local fallback.

Minimum readiness requirements:

- Verified network geometry, lanes, turns, crossings, signal phases, safety intervals, and controller capabilities for the pilot area.
- Accurate device-to-lane/approach mapping and sufficient data completeness for the selected use case.
- SUMO and forecasts validated against locally agreed performance targets.
- A formally approved safety envelope, escalation procedure, manual override, and fallback plan.
- Every approved action is authenticated, time-limited, logged, acknowledged, and field-verified.

## 12. Open Configuration Decisions

- Initial deployment area: campus, corridor, district, or city network.
- Available feeds: loops, radar, edge vision, controller SPaT, buses/fleet probes, roadwork, and incident data.
- Local signal-controller vendors, interfaces, and permitted command capabilities.
- Applicable traffic rules, pedestrian standards, authority approval process, and data-retention policy.
- Priority and fairness policy for pedestrians, buses, emergency response, cyclists, freight, and side roads.
- Whether the first release remains simulation/advisory only or includes a supervised pilot.
