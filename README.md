# Digital Twin-Enabled Smart City Analytics Platform

> **Document Status:** Authoritative System Documentation & Production Architecture  
> **Platform Classification:** Read-Only Municipal Decision-Support System  
> **Reference Pilot Corridor:** Viman Nagar Chowk to Somnath Nagar Chowk (1.8 km arterial corridor, Nagar Road, Pune, Maharashtra)  
> **Generalization Contract:** Open, modular urban analytics platform scalable to any municipal arterial network worldwide

---

## 1. Executive Summary

This **Digital Twin-Enabled Smart City Analytics Platform** is an evidence-backed urban decision-support and predictive intelligence system that couples road traffic mobility, commercial electrical microgrids, and ambient air quality into an integrated operational engine.

The platform continuously mirrors physical infrastructure conditions using event-driven MQTT sensor telemetry, forecasts speeds and energy demands 15, 30, and 60 minutes ahead via extreme gradient-boosted trees (XGBoost) with distribution-free Conformal Prediction uncertainty bands, and provides a microscopic what-if simulation sandbox (Eclipse SUMO) where city planners test mobility interventions in software before physical implementation.

**Core Operational Contract: Strict Non-Actuation**  
The platform is strictly a **read-only decision-support advisory system**. It will never autonomously actuate physical traffic signals or trip electrical substation breakers. All recommendations require explicit human inspection and authorization by certified municipal engineers outside the platform before any field action is taken.

---

## 2. Comprehensive System Architecture

The platform is engineered as a high-concurrency modular monolith with a resilient dual-engine persistence layer, real-time WebSocket distribution fabric, and an accessible React 18 / 3D Cesium photogrammetric operations console.

### 2.1 End-to-End System Architecture Flowchart

```mermaid
flowchart TD
    subgraph TIER1["1. IoT Sensor and Autonomous Telemetry Tier"]
        S1["Inductive Loops / Radar Speed Stations<br/>Space-Mean Speed, Flow Rate, Lane Occupancy"]
        S2["Traffic Signal Controllers NTCIP 1202<br/>Active Phase ID, Stage Countdown, SPaT Broadcasts"]
        S3["Commercial 3-Phase Smart Power Meters<br/>415V LL, 3600A Current, Active/Reactive Power"]
        S4["Rooftop Solar PV Inverters and BESS<br/>Solar Generation kW, Battery State of Charge %"]
        S5["CAAQMS Ambient Air Stations and Anemometers<br/>PM2.5, PM10, NO2, CO, Ultrasonic Wind Vectors"]
        S6["In-Process Autonomous Telemetry Worker<br/>telemetry_streamer.py: 2.0s Diurnal Heartbeat"]
    end

    subgraph TIER2["2. Ingestion Guard and Physical Sanity Firewall"]
        MQTT["Eclipse Mosquitto Message Broker<br/>MQTT 3.1.1 / 5.0 (corridor/{domain}/{id}/telemetry)"]
        FIREWALL["Pydantic Physical Sanity Bounds Firewall<br/>Validates: Speed 0-120 km/h, Power >= 0, Timestamps <= Now"]
        DLQ["Data Quarantine Queue (DLQ)<br/>quarantine_observations Table (INVALID Audit Tag)"]
    end

    subgraph TIER3["3. Resilient Dual-Engine Persistence and Spatial Registry"]
        ROUTER["Authoritative Storage Router"]
        PG["Primary Cloud Storage Engine:<br/>PostgreSQL 16 + TimescaleDB + PostGIS<br/>Hypertables, Spatial Geometries, Partitioning"]
        SQLITE["Resilient Local Storage Fallback:<br/>SQLite 3 (WAL Mode) via aiosqlite<br/>29 Relational Tables, 100% Offline Hermeticity"]
        CURRENT_STATE["entity_current_state<br/>Sub-Millisecond Authoritative State Upsert Cache"]
        SPATIAL_REG["Spatial Entity Registry (FIWARE NGSI-LD)<br/>RoadSegment, Intersection, BuildingZone, AirStation"]
    end

    subgraph TIER4["4. Core Analytics, Physics and Microscopic Simulation"]
        LOS_ENG["Indo-HCM (IRC:106) and US HCM Engine<br/>Dual-Criteria Speed and V/C Matrix, PCU Equivalence"]
        WEBSTER_ENG["Webster Signal Timing Optimizer<br/>Optimum Cycle C_0 = (1.5L + 5)/(1 - Y), Green Splits"]
        POWER_ENG["3-Phase AC Kirchhoff Power Balance Engine<br/>P = sqrt(3)*V*I*cos(phi), Feeder Thermal Headroom"]
        ENV_ENG["CPCB Linear AQI and Anomaly Detector<br/>Isolation Forest s(x, n) and Diurnal Z-Score Baselines"]
        SUMO_SIM["Microscopic Traffic Physics Simulator<br/>Eclipse SUMO 1.20 (TraCI) + Kinematic Fallback Runner"]
    end

    subgraph TIER5["5. Machine Learning, Conformal Prediction and Explainability"]
        XGB_ENG["Multi-Horizon XGBoost Regressors<br/>15m, 30m, 60m Speed and Building Power Forecasts"]
        CONF_ENG["Split Conformal Prediction Engine<br/>Distribution-Free 80% and 90% Empirical Confidence Bands"]
        SHAP_ENG["TreeSHAP Explainable AI (XAI)<br/>Top-5 Additive Feature Attribution Decompositions"]
        PSI_ENG["Population Stability Index (PSI)<br/>Feature Distribution Drift Monitor (PSI < 0.10 Stable)"]
    end

    subgraph TIER6["6. High-Concurrency API Gateway and Transport Fabric"]
        FASTAPI_APP["FastAPI 0.136 ASGI Engine (Python 3.11 + Uvicorn)<br/>REST Endpoints: /api/v1 (Corridor, Analytics, Health)"]
        WS_MGR["In-Memory WebSocket Connection Manager<br/>/ws/operations: Sub-2.0s JSON-LD Push Stream"]
        AUTH_GUARD["Stateless Cryptographic JWT Auth Guard<br/>Role-Based Access: Operator, Grid, Environment, Commissioner"]
    end

    subgraph TIER7["7. Operations Command Console and Governance UI"]
        MAP_2D["Tactical 2D GIS Operations Canvas<br/>Leaflet 1.9 / MapLibre GL JS Basemap"]
        CESIUM_3D["3D Photogrammetric Twin Viewer<br/>CesiumJS 1.120: 3D Terrain, Buildings and Animated Kinematics"]
        ANALYTICS_HUD["Live Corridor HUD and Telemetry Panels<br/>Recharts 2.12: Forecasts and Conformal Uncertainty Bands"]
        GOVERNANCE_UI["Advisory Governance and Decision Center<br/>Strict Non-Actuation: Officer Authorization and SHA-256 Audit"]
    end

    S1 & S2 & S3 & S4 & S5 --> MQTT
    S6 --> FIREWALL
    MQTT --> FIREWALL
    FIREWALL -- Valid Ingested Telemetry --> ROUTER
    FIREWALL -- Out of Bounds / Corrupted --> DLQ

    ROUTER --> PG & SQLITE
    PG & SQLITE --> CURRENT_STATE
    SPATIAL_REG -. Spatial Mapping .-> CURRENT_STATE

    CURRENT_STATE --> LOS_ENG & WEBSTER_ENG & POWER_ENG & ENV_ENG & SUMO_SIM
    CURRENT_STATE --> XGB_ENG
    XGB_ENG --> CONF_ENG --> SHAP_ENG --> PSI_ENG

    LOS_ENG & WEBSTER_ENG & POWER_ENG & ENV_ENG & SUMO_SIM --> FASTAPI_APP
    XGB_ENG & CONF_ENG & SHAP_ENG --> FASTAPI_APP
    CURRENT_STATE --> WS_MGR

    FASTAPI_APP --> AUTH_GUARD --> MAP_2D & CESIUM_3D & ANALYTICS_HUD & GOVERNANCE_UI
    WS_MGR --> MAP_2D & CESIUM_3D & ANALYTICS_HUD & GOVERNANCE_UI
```

---

### 2.2 Text Architecture Representation

```text
+---------------------------------------------------------------------------------------------------+
|                            TIER 1: IOT SENSOR & TELEMETRY SOURCES                                 |
|  - Inductive Loops / Radar Speed Detectors (Velocity, Flow Rate, Detector Occupancy)              |
|  - Traffic Signal Controllers NTCIP 1202 (Active Phase, Stage Countdown, SPaT Broadcasts)         |
|  - Commercial 3-Phase Smart Meters (415V LL, 3600A Current, Active/Reactive Power)                |
|  - Rooftop Solar PV Inverters & BESS (Active Generation kW, Battery State of Charge %)            |
|  - CAAQMS Ambient Air Quality Stations (PM2.5, PM10, NO2, CO, Temperature, Wind Vector)          |
|  - In-Process Autonomous Telemetry Streamer (telemetry_streamer.py: 2.0s Diurnal Heartbeat)       |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                     TIER 2: INGESTION TRANSPORT & PHYSICAL SANITY FIREWALL                        |
|  - Eclipse Mosquitto MQTT Broker: Topics corridor/{domain}/{entityId}/telemetry                   |
|  - Pydantic Bounds Firewall: Speed [0, 120] km/h, Power >= 0, Timestamps <= Now                  |
|  - Dead-Letter Queue (DLQ): Rejected packets routed to quarantine_observations table              |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                 TIER 3: RESILIENT DUAL-ENGINE PERSISTENCE & SPATIAL REGISTRY                      |
|  - Primary Engine: PostgreSQL 16 + TimescaleDB Hypertables + PostGIS Spatial Geometries           |
|  - Resilient Fallback Engine: SQLite 3 (WAL Mode) via aiosqlite (29 Relational Tables)            |
|  - Fast Cache: entity_current_state table for sub-millisecond retrieval of all corridor assets   |
|  - Spatial Registry: FIWARE NGSI-LD standardized entities (RoadSegment, Intersection, Building)   |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                     TIER 4: CORE ANALYTICS, PHYSICS & SIMULATION ENGINES                          |
|  - Indo-HCM (IRC:106) & US HCM Engine: Dual-criteria Speed and V/C matrix, PCU equivalence        |
|  - Webster Signal Timing Optimizer: Minimum delay cycle time C_0 = (1.5L + 5)/(1 - Y)             |
|  - 3-Phase AC Kirchhoff Power Balance: P = sqrt(3)*V*I*cos(phi), Feeder Headroom Evaluation       |
|  - Environmental Engine: CPCB piecewise linear AQI interpolation, Isolation Forest anomaly scoring|
|  - Microscopic Simulation Sandbox: Eclipse SUMO 1.20 (TraCI) + Verified Kinematic Fallback Runner |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|               TIER 5: PREDICTIVE AI, CONFORMAL UNCERTAINTY & EXPLAINABILITY (XAI)                 |
|  - Multi-Horizon XGBoost Regressors: 15m, 30m, 60m Speed & Building Power Forecasters             |
|  - Split Conformal Prediction: Distribution-free 80% and 90% empirical coverage bands             |
|  - TreeSHAP Explainable AI: Top-5 additive feature attribution decompositions                     |
|  - Observability: Population Stability Index (PSI) drift monitoring (PSI < 0.10 Stable)           |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                     TIER 6: HIGH-CONCURRENCY API GATEWAY & TRANSPORT FABRIC                       |
|  - FastAPI 0.136 ASGI Engine (Python 3.11 + Uvicorn) serving asynchronous REST APIs               |
|  - In-Memory WebSocket Connection Manager: Pushes JSON-LD delta updates via /ws/operations        |
|  - Stateless Cryptographic JWT Authentication Guard with Role-Based Access Control (RBAC)         |
+---------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
|                 TIER 7: OPERATIONS COMMAND CONSOLE & HUMAN-IN-THE-LOOP GOVERNANCE                  |
|  - Tactical 2D GIS Operations Canvas: Leaflet 1.9 with dynamic speed-based polyline color coding  |
|  - 3D Photogrammetric Twin Viewer: CesiumJS 1.120 with 3D terrain and speed-matched kinematics    |
|  - Recharts 2.12 Visualizations: Multi-horizon forecasts, conformal bands, 24h load profiles      |
|  - Advisory Governance Center: Strict Non-Actuation review, candidate approval, SHA-256 audit log|
+---------------------------------------------------------------------------------------------------+
```

---

### 2.3 Detailed Architectural Tier Breakdown

1. **Tier 1: IoT Sensor and Autonomous Telemetry Tier**
   - Ingests direct measurements from induction loops, traffic signal controllers emitting SPaT over NTCIP 1202, commercial 3-phase power meters (415V line-to-line, 3600A), rooftop solar inverters, battery storage (BESS), and CAAQMS air quality stations.
   - For offline evaluation and testing without field permits, the **In-Process Autonomous Telemetry Streamer** (`backend/ingestion/telemetry_streamer.py`) computes physics-informed telemetry every 2.0 seconds based on diurnal commuter Gaussian rush curves and electrical impedance equations.
   - Emits and tracks **32 distinct physical and derived engineering metrics** across the four coupled infrastructure domains.

2. **Tier 2: Ingestion Guard and Physical Sanity Firewall**
   - Transports sensor packets over standardized MQTT topics formatted as `corridor/{domain}/{entityId}/telemetry`.
   - The **Ingestion Guard** (`backend/ingestion/mqtt_consumer.py`) parses payloads against strict Pydantic v2 schemas and executes bounds checks (speed between 0 and 120 km/h, non-negative power, non-future timestamps).
   - Any packet violating physical laws or schema formatting is quarantined into `quarantine_observations` with an `INVALID` provenance tag, protecting analytics models from corrupted data.

3. **Tier 3: Resilient Dual-Engine Persistence and Spatial Registry**
   - **Dual-Engine Architecture:** In cloud deployments, connects to PostgreSQL 16 with TimescaleDB hypertables for time-series partitioning and PostGIS for spatial queries. For offline, field, and evaluation demonstrations, automatically falls back to an embedded **SQLite 3 Engine** (WAL mode via `aiosqlite`) containing all 29 relational tables.
   - **Fast State Cache:** Synchronously maintains the `entity_current_state` table, providing sub-millisecond lookups of the latest state for any corridor asset.
   - **Spatial Registry:** Standardizes all assets using FIWARE NGSI-LD URN specifications (`RoadSegment`, `Intersection`, `BuildingZone`, `AirQualityStation`).

4. **Tier 4: Core Analytics, Physics and Microscopic Simulation**
   - **Traffic Mobility:** Implements Greenshields hydrodynamic flow theory (`q = k * v`) and Indo-HCM (IRC:106) dual-criteria Level of Service (LOS) with Passenger Car Unit (PCU) equivalence for mixed traffic.
   - **Signal Optimization:** Implements F.V. Webster minimum-delay cycle time formulation: `C_0 = (1.5 * L + 5) / (1 - Y)` and allocates proportional green splits.
   - **Microgrid Power:** Computes 3-phase AC power physics (`P = sqrt(3) * V_LL * I_L * cos(phi)`), enforces Kirchhoff energy conservation (`P_grid + P_solar + P_bess = P_loads + P_losses`), and monitors 22kV feeder thermal ampacity and electrical headroom.
   - **Air Quality:** Computes official CPCB piecewise linear AQI interpolation and executes Scikit-Learn Isolation Forest anomaly detection (`s(x, n) = 2^(-E(h(x)) / c(n))`).
   - **Simulation Sandbox:** Integrates Eclipse SUMO 1.20 via Python TraCI with a verified kinematic fallback runner for what-if scenario testing.

5. **Tier 5: Machine Learning, Conformal Prediction and Explainability**
   - **Multi-Horizon Forecaster:** XGBoost extreme gradient-boosted tree regressors forecast traffic velocity and commercial building power at 15m, 30m, and 60m forward horizons using cyclical sine/cosine time features, autoregressive lags, and upstream queue states.
   - **Uncertainty Quantification:** Split Conformal Prediction calculates empirical non-conformity residuals on chronological calibration sets, yielding distribution-free 80% and 90% confidence bands without Gaussian assumptions.
   - **Explainable AI (XAI):** TreeSHAP decomposes predictions into the top-5 additive feature contributions (`f(x) = base_value + sum(shap_values)`).
   - **Model Observability:** Continuously tracks input feature drift using the Population Stability Index (`PSI < 0.10` Stable, `>= 0.25` Drift).

6. **Tier 6: High-Concurrency API Gateway and Transport Fabric**
   - High-performance FastAPI ASGI application running under Python 3.11 and Uvicorn.
   - Dedicated RESTful routes under `/api/v1` for corridor queries, live operations, analytics, recommendations, scenarios, evaluation benchmarks, and provisioning.
   - In-memory WebSocket Connection Manager broadcasting JSON-LD delta updates via `/ws/operations` every 2.0 seconds.
   - Stateless JWT authentication gateway with Role-Based Access Control (RBAC) supporting Traffic Operator, Grid Operator, Environmental Analyst, and Municipal Commissioner roles.

7. **Tier 7: Operations Command Console and Governance UI**
   - Built on React 18, TypeScript 5.5, and Vite 5.4.
   - Tactical 2D GIS map powered by Leaflet 1.9 with dynamic speed-based polyline color coding.
   - Immersive 3D Digital Twin Viewer powered by CesiumJS 1.120, rendering photogrammetric terrain, 3D extruded commercial buildings, and animated vehicles matched to physical sensor velocities.
   - Telemetry charts and forecast panels powered by Recharts 2.12.
   - **Advisory Governance Center:** Enforces the Strict Non-Actuation Invariant. Certified municipal engineers inspect recommendations, evaluate conflict matrices, and authorize intervention plans, with all approvals permanently written to a tamper-evident SHA-256 audit log.

---

## 3. Tri-Domain Physical Coupling: Traffic, Energy, and Environmental Dynamics

Conventional smart city platforms manage traffic signals, electrical substations, and ambient air monitors through isolated operational silos, displaying separate charts on disconnected dashboards. In physical reality, an urban arterial corridor functions as an intimately coupled thermodynamic, hydrodynamic, and electro-mechanical continuum.

The digital twin models the bidirectional physical interactions connecting these three domains in real time:

```text
+---------------------------------------------------------------------------------------------------+
|                                  THE TRI-DOMAIN PHYSICAL NEXUS                                    |
|                                                                                                   |
|     +-------------------------+                 +-------------------------+                       |
|     |     TRAFFIC MOBILITY    |                 |   ELECTRICAL MICROGRID  |                       |
|     |  Speed, Flow, Queues,   |                 | 3-Phase Power, Feeders, |                       |
|     |    Webster Cycle Time   |                 |   HVAC Chillers, BESS   |                       |
|     +-------------------------+                 +-------------------------+                       |
|           \             ^                             ^             /                             |
|            \           /                               \           /                              |
|   Tailpipe  \         / Traffic               Vehicular \         / Chiller Waste                 |
|   Emissions  \       /  Gating                 Arrival   \       /  Heat Rejection                |
|   & Queues    \     /   Advisories              Footfall  \     /   (UHI Plume)                   |
|                v   /                             & EVs     \   v                                  |
|            +---------------------------------------------------+                                  |
|            |                AMBIENT ENVIRONMENT                |                                  |
|            |            PM2.5, PM10, NO2, CO, CPCB             |                                  |
|            |           AQI, Temperature, Wind Vector           |                                  |
|            +---------------------------------------------------+                                  |
+---------------------------------------------------------------------------------------------------+
```

---

### 3.1 Traffic to Environment: Vehicle Kinematics, Emissions, and Dispersion

Vehicular exhaust emissions are not static constants; they are dynamic non-linear functions of vehicle space-mean speed, queue acceleration cycles, and traffic congestion states along each arterial link.

#### 1. Speed-Dependent Specific Emission Factors
Vehicle specific emission factors for criteria pollutant $p \in \{\text{PM}_{2.5}, \text{PM}_{10}, \text{NO}_x, \text{CO}\}$ are modeled as a function of space-mean velocity $v$ (in km/h) based on European COPERT and HBEFA kinematic formulations:

$$E_p(v) = \frac{\alpha_p + \beta_p \cdot v + \gamma_p \cdot v^2}{v} + \delta_p \cdot \exp(-\zeta_p \cdot v)$$

Where:
* $E_p(v)$: Specific emission rate per vehicle (in g/km).
* $\alpha_p, \beta_p, \gamma_p, \delta_p, \zeta_p$: Empirical vehicle fleet calibration coefficients reflecting engine displacement, fuel type mix, and catalytic converter efficiency.
* **Physical Insight:** Under free-flow conditions ($40 \le v \le 60\text{ km/h}$), internal combustion engines operate in their optimal thermal efficiency window, minimizing specific emissions. When space-mean speed collapses into hyper-congested stop-and-go conditions ($v < 15\text{ km/h}$), emissions spike exponentially due to repeated vehicle braking, rich air-fuel mixture transients, and sub-optimal catalytic conversion temperatures.

#### 2. Queue Acceleration Shockwaves and Tractive Power Spikes
During intersection signal cycling, vehicles accelerating from a standing queue exert high tractive force, emitting dramatically higher mass rates than steady-state cruising:

$$\dot{m}_p(t) = \dot{m}_{\text{idle}, p} + \kappa_p \cdot \max(0, \; P_{\text{tractive}}(t))$$

Where instantaneous vehicle tractive power $P_{\text{tractive}}(t)$ (in kW) is governed by vehicle mechanics:

$$P_{\text{tractive}}(t) = \left[ m \cdot a(t) + m \cdot g \cdot C_r + \frac{1}{2} \rho_{\text{air}} C_d A \cdot v(t)^2 \right] \cdot \frac{v(t)}{1000}$$

Where $m$ is vehicle mass (kg), $a(t)$ is instantaneous acceleration ($\text{m/s}^2$), $C_r$ is rolling resistance coefficient, $C_d$ is aerodynamic drag coefficient, and $A$ is frontal surface area ($\text{m}^2$). Uncoordinated traffic signals produce recurring stop-and-go shockwaves, generating up to $3.8\times$ higher localized particulate mass emissions compared to an arterial corridor synchronized via green wave coordination offsets.

#### 3. Atmospheric Street Canyon Dispersion
Tailpipe emissions accumulate within the street canyon based on vertical and lateral Gaussian dispersion:

$$C_p(x, z) = \sqrt{\frac{2}{\pi}} \frac{q_p}{u_{\text{eff}} \cdot \sigma_z(x)} \exp\left( -\frac{z^2}{2 \sigma_z^2(x)} \right) + C_{\text{background}, p}$$

Where:
* $q_p = \sum_{j} \dot{m}_{p, j} \cdot k \cdot v$: Link line-source emission strength (g/m-s), with density $k$ (veh/km) and velocity $v$ (km/h).
* $u_{\text{eff}} = \max(0.5, \; u_{\text{wind}} \cdot |\cos(\theta_{\text{canyon}})|)$: Effective wind velocity along the street canyon (m/s).
* $\sigma_z(x) = a \cdot x^b$: Vertical dispersion coefficient parameterized by downwind distance $x$ and atmospheric stability class.
* $C_{\text{background}, p}$: Regional background pollutant concentration ($\mu\text{g/m}^3$).

The resulting ground-level concentration $C_p$ directly determines the Central Pollution Control Board (CPCB) continuous sub-index:

$$I_p = I_{\text{low}} + \left[ \frac{I_{\text{high}} - I_{\text{low}}}{C_{\text{high}} - C_{\text{low}}} \right] \cdot (C_p - C_{\text{low}})$$

---

### 3.2 Traffic to Energy: Fleet Electrification, Customer Arrival, and Chiller Loads

Traffic flow directly drives commercial electrical demand through two distinct physical coupling mechanisms: dynamic Electric Vehicle (EV) charging loads and occupant-driven building thermal gains.

#### 1. Electric Vehicle (EV) Charging Demand at Commercial Hubs
As electric vehicle penetration increases, vehicle arrival rates at commercial hubs directly drive substation feeder loading:

$$\lambda_{\text{EV}}(t) = q_{\text{in}}(t) \cdot \eta_{\text{EV}}$$

Where $q_{\text{in}}(t)$ is vehicular ingress flow from the arterial link (veh/h) and $\eta_{\text{EV}}$ is the corridor fleet EV penetration ratio. The aggregate active power load demanded by DC fast-charging clusters ($P_{\text{EV}}$ in kW) is modeled as:

$$P_{\text{EV}}(t) = \sum_{j=1}^{N_{\text{chargers}}} P_{\text{rated}, j} \cdot u_j(t) \cdot \eta_{\text{charger}}$$

Where $u_j(t) \in \{0, 1\}$ indicates charger connection status and $\eta_{\text{charger}} \approx 0.94$ is AC-to-DC conversion efficiency.

#### 2. Vehicular Ingress, Space Occupancy, and Internal Thermal Gains
Commuter and customer arrivals at major commercial complexes (such as shopping centers, office parks, and retail districts) are a lagged convolution of corridor traffic flow:

$$N_{\text{occ}}(t) = \int_{0}^{t} q_{\text{in}}(\tau) \cdot p_{\text{enter}} \cdot \exp\left( -\frac{t - \tau}{\tau_{\text{dwell}}} \right) d\tau$$

Where $p_{\text{enter}}$ is the fraction of passing corridor vehicles entering the facility and $\tau_{\text{dwell}}$ is mean customer dwell time (typically 1.5 to 2.5 hours). Each occupant introduces internal sensible and latent thermal heat gains ($q_{\text{human}} \approx 100\text{ to } 120\text{ W/person}$), driving internal thermal load:

$$\dot{Q}_{\text{internal}}(t) = \frac{N_{\text{occ}}(t) \cdot q_{\text{human}}}{1000} + P_{\text{lighting}}(t) + P_{\text{plug}}(t) \quad [\text{kW}]$$

#### 3. Building HVAC Cooling Load and Feeder Thermal Headroom
The commercial facility's centralized chiller plant must balance envelope heat conduction and dynamic internal occupant heat gains to maintain statutory indoor temperature setpoints ($T_{\text{set}} \approx 24^\circ\text{C}$):

$$\dot{Q}_{\text{cooling}}(t) = U \cdot A_{\text{envelope}} \cdot (T_{\text{amb}}(t) - T_{\text{set}}) + \dot{Q}_{\text{internal}}(t)$$

The electrical active power required by the chiller plant is governed by its thermodynamic Coefficient of Performance (COP):

$$P_{\text{HVAC}}(t) = \frac{\dot{Q}_{\text{cooling}}(t)}{\text{COP}(T_{\text{amb}}(t))}$$

Total substation bus load combines baseline commercial power, HVAC cooling power, and EV charging power:

$$P_{\text{bus}}(t) = P_{\text{base}}(t) + P_{\text{HVAC}}(t) + P_{\text{EV}}(t)$$

Which directly stresses the 22kV distribution feeder thermal limit:

$$I_{\text{feeder}}(t) = \frac{P_{\text{bus}}(t)}{\sqrt{3} \cdot V_{\text{LL}} \cdot \text{PF}} \le I_{\text{rated}}$$

When evening commuter congestion coincides with retail shopping peaks, the combined surge in HVAC cooling and EV charging significantly reduces available feeder thermal headroom:

$$P_{\text{headroom}}(t) = \sqrt{3} \cdot V_{\text{LL}} \cdot \big(I_{\text{rated}} - I_{\text{feeder}}(t)\big) \cdot \text{PF} \quad [\text{kW}]$$

---

### 3.3 Energy to Environment: Microclimate Heat Rejection and Clean Generation

Energy consumption in commercial facilities exerts a direct reciprocal impact on the ambient corridor microclimate and regional air quality.

#### 1. HVAC Condenser Waste Heat Rejection (Urban Heat Island Plume)
Commercial refrigeration cycles operate by extracting thermal energy from building interiors and discharging that heat, plus compressor electrical work, directly into the surrounding ambient air canyon:

$$\dot{Q}_{\text{condenser}}(t) = \dot{Q}_{\text{cooling}}(t) \cdot \left( 1 + \frac{1}{\text{COP}(T_{\text{amb}}(t))} \right)$$

For multi-megawatt commercial complexes, the condenser heat rejection flux ($\dot{Q}_{\text{condenser}} > 3500\text{ kW}$) elevates street canyon ambient temperature by $1.5^\circ\text{C to } 3.5^\circ\text{C}$ above rural baselines. This localized Urban Heat Island (UHI) effect suppresses natural atmospheric boundary layer venting and traps particulate matter near ground level.

#### 2. Distributed Energy Resources (DER) and Emission Offsets
Corridor-level rooftop solar PV generation $P_{\text{solar}}(t)$ and Battery Energy Storage System (BESS) peak discharge $P_{\text{bess,dis}}(t)$ displace grid power imported from centralized fossil-fuel thermal plants:

$$\Delta \dot{M}_{\text{CO2}}(t) = \big( P_{\text{solar}}(t) + P_{\text{bess,dis}}(t) \big) \cdot EF_{\text{grid,marginal}} \quad [\text{kg CO}_2\text{/h}]$$

Where $EF_{\text{grid,marginal}} \approx 0.82\text{ kg CO}_2\text{/kWh}$ represents the marginal emissions intensity of thermal power stations on regional distribution grids.

---

### 3.4 Environmental Feedbacks to Traffic and Energy: Closed-Loop Governance

The physical coupling is fully closed loop: environmental conditions exert direct thermodynamic and operational feedbacks onto both the energy microgrid and arterial traffic control.

#### 1. Ambient Temperature Effect on Solar PV Efficiency
Photovoltaic cell temperature $T_{\text{cell}}(t)$ rises with ambient temperature $T_{\text{amb}}(t)$ and plane-of-array solar irradiance $G_{\text{poa}}(t)$:

$$T_{\text{cell}}(t) = T_{\text{amb}}(t) + G_{\text{poa}}(t) \cdot \left( \frac{\text{NOCT} - 20}{800} \right)$$

Where $\text{NOCT} \approx 45^\circ\text{C}$ is Nominal Operating Cell Temperature. High ambient temperatures degrade solar PV efficiency linearly above standard test conditions ($25^\circ\text{C}$):

$$P_{\text{solar}}(t) = P_{\text{STC}} \cdot \left( \frac{G_{\text{poa}}(t)}{1000} \right) \cdot \Big[ 1 - \gamma_{\text{temp}} \cdot \big(T_{\text{cell}}(t) - 25\big) \Big]$$

Where temperature power coefficient $\gamma_{\text{temp}} \approx 0.004\ /^\circ\text{C}$. For every $10^\circ\text{C}$ increase in corridor ambient temperature, solar generation drops by approximately 4%, reducing local clean energy supply exactly when air conditioning loads peak.

#### 2. Thermodynamic Chiller COP Degradation under Ambient Heat
As street canyon ambient temperature $T_{\text{amb}}$ increases, the thermodynamic Carnot efficiency limit of chiller refrigeration cycles drops:

$$\text{COP}(T_{\text{amb}}) = \eta_{\text{carnot}} \cdot \frac{T_{\text{chilled}} + 273.15}{(T_{\text{amb}} - T_{\text{chilled}})}$$

Where $T_{\text{chilled}} \approx 7^\circ\text{C}$ is chilled water supply temperature and $\eta_{\text{carnot}} \approx 0.55$ is empirical compressor efficiency. A $5^\circ\text{C}$ heatwave elevates chiller electricity demand by 15% to 20% for identical indoor cooling loads, exacerbating electrical substation stress.

#### 3. Air Quality Threshold Advisory on Traffic Signal Gating
When CAAQMS stations detect severe particulate accumulation ($C_{\text{PM2.5}} \ge 250\ \mu\text{g/m}^3$ or $I_{\text{AQI}} \ge 400$), the digital twin evaluates cross-domain mitigation advisories:

$$q_{\text{advisory,max}}(t) = q_{\text{nominal}}(t) \cdot \max\left(0.60, \; 1.0 - \frac{I_{\text{AQI}}(t) - 300}{250}\right)$$

The advisory engine recommends:
1. Extending arterial green wave progression offsets to clear stop-and-go queues ($v \to 40\text{ km/h}$), cutting idling emission factors by up to 45%.
2. Advisory gating on upstream highway feeder ramps to meter heavy commercial freight until street canyon particulate concentrations disperse below statutory warning levels.

---

### 3.5 Tri-Domain Physical Coupling Summary Matrix

| Primary Driving Domain | Impacted Domain | Physical Coupling Channel | Governing Mathematical Relationship | Physical Manifestation | Digital Twin Advisory Mitigation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Traffic Mobility** | **Environment** | Vehicle speed collapse and stop-and-go idling | $`E_p(v) = \frac{\alpha_p + \beta_p v + \gamma_p v^2}{v} + \delta_p e^{-\zeta_p v}`$ | Exponential spike in PM2.5 and NOx during traffic congestion (speed under 15 km/h) | Green Wave offset optimization to eliminate stopping shockwaves |
| **Traffic Mobility** | **Environment** | Acceleration from standing queue | $`\dot{m}_p(t) = \dot{m}_{\text{idle}, p} + \kappa_p P_{\text{tractive}}(t)`$ | Localized exhaust plume spike during signal queue discharge | Coordinated queue clearance phases preventing vehicle deceleration |
| **Traffic Mobility** | **Energy** | EV arrival and opportunistic fast charging | $`P_{\text{EV}}(t) = \sum P_{\text{rated}, j} \cdot u_j(t) \cdot \eta`$ | Sudden multi-hundred kilowatt power demand spikes on commercial bus | Time-of-Use smart charging modulation and BESS peak shaving |
| **Traffic Mobility** | **Energy** | Commuter footfall and commercial building ingress | $`N_{\text{occ}}(t) = \int q_{\text{in}}(\tau) p_{\text{enter}} e^{-\frac{t-\tau}{\tau_{\text{dwell}}}} d\tau`$ | Internal sensible heat gains forcing increased chiller electrical work | Pre-cooling building thermal mass via 2R-2C ETP setback optimizer |
| **Energy** | **Environment** | Chiller condenser thermal heat rejection | $`\dot{Q}_{\text{condenser}} = \dot{Q}_{\text{cooling}} \cdot \left(1 + \frac{1}{\text{COP}}\right)`$ | Street canyon Urban Heat Island heating (+1.5 C to +3.5 C), trapping particulate matter | Chiller sequencing and night-time cold thermal storage discharge |
| **Energy** | **Environment** | Clean DER generation displacing grid fossil power | $`\Delta \dot{M}_{\text{CO2}} = (P_{\text{solar}} + P_{\text{bess,dis}}) \cdot EF_{\text{marginal}}`$ | Net reduction in regional power generation greenhouse gas emissions | Real-time solar self-consumption and battery arbitrage dispatch |
| **Environment** | **Energy** | Ambient temperature degradation of solar PV panels | $`P_{\text{solar}} = P_{\text{STC}} \cdot \frac{G}{1000} \cdot [1 - \gamma (T_{\text{cell}} - 25)]`$ | 0.4% solar efficiency loss per degree Celsius of ambient heating | Dynamic BESS dispatch compensating for solar generation dips |
| **Environment** | **Energy** | Ambient heatwave degradation of chiller plant COP | $`\text{COP} = \eta_{\text{carnot}} \cdot \frac{T_{\text{chilled}}}{T_{\text{amb}} - T_{\text{chilled}}}`$ | Chiller power consumption surges by up to 20% during microclimate heatwaves | HVAC thermostat setbacks and fan speed throttling in low-occupancy zones |
| **Environment** | **Traffic** | Severe particulate accumulation (AQI above 400) | $`q_{\text{advisory,max}} = q_{\text{nominal}} \cdot \left[1 - \min\left(0.40, \frac{I_{\text{AQI}}-300}{250}\right)\right]`$ | Street canyon smog concentration exceeding safe human exposure thresholds | Upstream freight metering advisory and signal green wave progression |


---

## 4. Core Architectural Invariants

Every module, service, API endpoint, and UI component strictly preserves five non-negotiable architectural invariants:

1. **System of Record Invariant:** PostgreSQL/TimescaleDB (or the resilient local SQLite fallback engine) is the authoritative system of record. MQTT is message transport only.
2. **State Separation Invariant:** Ground truth observations (`LIVE`/`REPLAY`), physics simulations (`SIMULATION`), and machine learning predictions (`PREDICTED`) are strictly separated into distinct tables. Predictions and simulations never overwrite observed twin current state.
3. **Strict Non-Actuation Invariant:** The platform is read-only decision support. Recommendations are advisory and require human authorization by certified municipal engineers outside the platform before any field signal or electrical change.
4. **Mandatory Provenance Invariant:** Every dynamic value returned by APIs or displayed in the UI carries four mandatory metadata tags: `sourceMode` (`LIVE`, `REPLAY`, `SIMULATION`, `PREDICTED`, `STALE`), `observedAt`/`generatedAt`, engineering `unit`, and `qualityStatus` (`VALID`, `SUSPECT`, `CALIBRATED`, `INVALID`).
5. **Corridor Generalization Invariant:** The platform architecture, schemas, and UI are fully generalized for any municipal arterial corridor deployment worldwide. The 1.8 km Nagar Road reference pilot serves strictly as an empirical demonstration and calibration instance.

---

## 5. Complete Technical Stack

| Layer | Component | Approved Technology | Role & Exact Codebase Location |
| :--- | :--- | :--- | :--- |
| **Frontend Framework** | Application Shell | React 18 + TypeScript 5.5 | Reactive UI component tree and state management (`frontend/src/App.tsx`). |
| **Frontend Bundler** | Build Tool | Vite 5.4 | High-speed HMR and optimized production bundling (`frontend/vite.config.ts`). |
| **3D Twin Viewer** | Photogrammetric 3D | CesiumJS 1.120 | 3D photogrammetric terrain, extruded buildings, vehicle kinematics (`CesiumCorridorViewer.tsx`). |
| **2D Operational GIS** | Tactical GIS Map | Leaflet 1.9 / MapLibre GL JS | 2D corridor GIS rendering with dynamic road polylines (`MapOperationsView.tsx`). |
| **Telemetry UI** | Charts & Forecasts | Recharts 2.12 | Renders multi-horizon forecasts, conformal bands, and load curves (`ForecastPanel.tsx`). |
| **Icons & Styling** | Vector Design Tokens | Lucide React + Tailwind CSS | Accessible vector iconography (zero emojis) and responsive design tokens (`frontend/src/index.css`). |
| **Backend API Engine** | Modular Monolith | FastAPI 0.136 | Asynchronous ASGI RESTful endpoints and WebSocket controllers (`backend/main.py`). |
| **Web Server** | ASGI Server | Uvicorn 0.30 | High-concurrency asynchronous server running Python 3.11 (`backend/main.py`). |
| **Data Validation** | Schema Bounds Guard | Pydantic v2 (2.8) | Strict request/response validation and physical bounds checking (`backend/schemas/`). |
| **Database ORM & Driver** | Relational Access | SQLAlchemy 2.0 + aiosqlite | Asynchronous database connection pooling, migrations, and queries (`backend/core/database.py`). |
| **Time-Series Persistence** | Dual-Engine Database | PostgreSQL 16 / TimescaleDB | Hypertables with automatic, resilient local SQLite fallback (`digital_twin.db`). |
| **Message Transport** | Sensor Telemetry Bus | Eclipse Mosquitto (MQTT 3.1.1/5.0) | High-throughput publish/subscribe telemetry transport (`backend/ingestion/mqtt_consumer.py`). |
| **Telemetry Generator** | Autonomous Worker | Python Asyncio | In-process physical telemetry generator (`backend/ingestion/telemetry_streamer.py`). |
| **Machine Learning** | Tabular Forecaster | XGBoost 2.1 | Multi-horizon 15m/30m/60m speed and power forecasting (`ml/inference/forecaster.py`). |
| **Uncertainty Engine** | Coverage Bands | Split Conformal Prediction | Distribution-free 80% and 90% confidence bands without Gaussian assumptions (`ml/conformal.py`). |
| **Explainable AI (XAI)** | Feature Attribution | TreeSHAP (SHAP 0.46) | Decomposes forecasts into top-5 feature attributions (`ml/explainer.py`). |
| **Anomaly Detection** | Unsupervised ML | Scikit-Learn 1.5 | Isolation Forest scoring on environmental sensor streams (`backend/services/anomaly_detector.py`). |
| **Traffic Simulation** | Microscopic Physics | Eclipse SUMO 1.20 via TraCI | Microscopic car-following simulation with kinematic fallback runner (`simulation/runner.py`). |
| **Security & Auth** | Role-Based Access | Python-Jose + BCrypt | Stateless JWT tokens, role-based tab access, and audit log signing (`backend/api/v1/endpoints/auth.py`). |

---

## 6. Master Documentation Suite (4 Volumes)

The repository provides a complete 4-volume engineering handbook and evaluation briefing suite in both Markdown and publication-grade PDF format:

1. **Volume 1: System Architecture and Data Flow**
   - [Markdown](docs/Volume_1_System_Architecture.md) | [PDF](docs/Volume_1_System_Architecture.pdf)
   - Complete technical stack, implementation reality breakdown, end-to-end data pipeline, data provenance vocabulary, master inventory of all 32 emitted physical metrics, and municipal ROI.
2. **Volume 2: Domain Engineering and Mathematical Foundations**
   - [Markdown](docs/Volume_2_Domain_Engineering_and_Math.md) | [PDF](docs/Volume_2_Domain_Engineering_and_Math.pdf)
   - First-principles mathematical derivations: Greenshields traffic continuum, Indo-HCM (IRC:106) dual-criteria Level of Service, Webster minimum delay signal optimization, Green Wave progression offsets, 3-phase AC Kirchhoff power balance, feeder thermal headroom, CPCB AQI linear interpolation, Isolation Forest anomaly scoring, Conformal Prediction, and TreeSHAP.
3. **Volume 3: Screen-by-Screen Operator Manual and UI Guide**
   - [Markdown](docs/Volume_3_Screen_Operator_Guide.md) | [PDF](docs/Volume_3_Screen_Operator_Guide.pdf)
   - Granular manual for all 11 application views: explains every button, toggle, and click action; explains every number, gauge, and badge; explains Persistence Baselines, Gain vs Base, Forecast Skill Scores, and XGBoost vs neural networks.
4. **Volume 4: Judge Defense, Critical Q&A, Demo Script, and Forensic Audit**
   - [Markdown](docs/Volume_4_Judge_Defense_and_Script.md) | [PDF](docs/Volume_4_Judge_Defense_and_Script.pdf)
   - 20 bulletproof answers to the hardest technical judge questions, screen-by-screen live demonstration script with simple words and visual pause cues, and the complete Forensic Architecture and Flaws Resolution Dossier.

---

## 7. Active Future Enhancement Tracks (21 GitHub Issues)

The platform is expanding through two prioritized enhancement tracks covering 21 detailed engineering tasks:

### Track 1: Intelligent Traffic Mobility & Adaptive Control (11 Tasks)
Detailed directory: [docs/tasks/traffic-mobility/](docs/tasks/traffic-mobility/)

| Task ID | Issue | Task Title | Spec Ref | Milestone | Component / Scope |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TASK-01` | [#2](https://github.com/AshrafGalaxy/Digital_Twin/issues/2) | Canonical Level of Service (LOS) & Hydrodynamic State Engine | Section 7.1 | Milestone 1 | Backend & Telemetry |
| `TASK-08` | [#3](https://github.com/AshrafGalaxy/Digital_Twin/issues/3) | Real-Time Signal Phase and Timing (SPaT) Controller Feed Adapter | Section 7.3 | Milestone 1 | Backend & Telemetry |
| `TASK-07` | [#4](https://github.com/AshrafGalaxy/Digital_Twin/issues/4) | Critical Infrastructure Structural Health Monitoring (SHM) Pipeline | Section 10.1 | Milestone 1 | Backend & Telemetry |
| `TASK-11` | [#5](https://github.com/AshrafGalaxy/Digital_Twin/issues/5) | Location-Agnostic Study Area Onboarding & Network Topology Importer | Section 5 | Milestone 1 | Architecture & Backend |
| `TASK-02` | [#6](https://github.com/AshrafGalaxy/Digital_Twin/issues/6) | Webster Delay-Minimizing Adaptive Signal Timing Optimizer | Section 9.1 | Milestone 2 | Simulation & Control |
| `TASK-03` | [#7](https://github.com/AshrafGalaxy/Digital_Twin/issues/7) | Arterial Two-Way Green Wave Progression & Offset Optimizer | Section 9.2 | Milestone 2 | Simulation & Control |
| `TASK-04` | [#8](https://github.com/AshrafGalaxy/Digital_Twin/issues/8) | SUMO TraCI Multimodal Transit Bus Routes & Priority Simulation | Section 7.2 | Milestone 2 | Simulation & Modeling |
| `TASK-05` | [#9](https://github.com/AshrafGalaxy/Digital_Twin/issues/9) | Multi-Horizon Quantile Queue Length Forecaster (XGBoost + TreeSHAP) | Section 8.1 | Milestone 3 | Machine Learning |
| `TASK-06` | [#10](https://github.com/AshrafGalaxy/Digital_Twin/issues/10) | Multimodal Transit Stop Crowd Flow & Dynamic Dwell Time Forecaster | Section 8.2 | Milestone 3 | Machine Learning |
| `TASK-09` | [#11](https://github.com/AshrafGalaxy/Digital_Twin/issues/11) | Deck.gl 3D Animated Signal Head & Approach Lane Queue Visualizer | Section 7.3, 11 | Milestone 4 | Frontend & UI |
| `TASK-10` | [#12](https://github.com/AshrafGalaxy/Digital_Twin/issues/12) | Human-in-the-Loop Operator Advisory Dossier & Audit Trail UI | Section 9.1, 9.2 | Milestone 4 | Frontend & UI |

### Track 2: Energy Management & Microgrid Optimization (10 Tasks)
Detailed directory: [docs/tasks/energy-microgrid/](docs/tasks/energy-microgrid/)

| Task ID | Issue | Task Title | Spec Ref | Milestone | Component / Scope |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ENERGY-01` | [#13](https://github.com/AshrafGalaxy/Digital_Twin/issues/13) | Canonical Electrical Network Topology & Multi-Asset Telemetry Engine | Section 4, 5, 6 | Milestone 5 | Backend & Telemetry |
| `ENERGY-02` | [#14](https://github.com/AshrafGalaxy/Digital_Twin/issues/14) | Electrical Bus Power Balance & Feeder Thermal Loading Engine | Section 7.1 | Milestone 5 | Backend & Telemetry |
| `ENERGY-03` | [#15](https://github.com/AshrafGalaxy/Digital_Twin/issues/15) | 2R-2C ETP Building Thermal Network & Dynamic Occupancy Setback Engine | Section 7.2, 7.3 | Milestone 6 | Simulation & Control |
| `ENERGY-05` | [#16](https://github.com/AshrafGalaxy/Digital_Twin/issues/16) | Solar PV Generation & Irradiance Physical Forecasting Engine | Section 8.2 | Milestone 6 | Machine Learning |
| `ENERGY-04` | [#17](https://github.com/AshrafGalaxy/Digital_Twin/issues/17) | Multi-Horizon Quantile Facility Load Forecaster (15m to 24h) | Section 8.1 | Milestone 7 | Machine Learning |
| `ENERGY-06` | [#18](https://github.com/AshrafGalaxy/Digital_Twin/issues/18) | BESS Battery Arbitrage & Time-of-Use Peak Shaving Optimizer | Section 9.1 | Milestone 7 | Optimization & Control |
| `ENERGY-07` | [#19](https://github.com/AshrafGalaxy/Digital_Twin/issues/19) | Grid Safety Interlocks & OpenADR / Modbus Failsafe Dispatch Gateway | Section 9.2, 9.3 | Milestone 8 | Backend & Telemetry |
| `ENERGY-08` | [#20](https://github.com/AshrafGalaxy/Digital_Twin/issues/20) | Interactive Microgrid Single-Line Diagram (SLD) & Power Flow Canvas | Section 4, 11 | Milestone 8 | Frontend & UI |
| `ENERGY-09` | [#21](https://github.com/AshrafGalaxy/Digital_Twin/issues/21) | Building Floorplate 3D/2D Thermal Comfort & Occupancy Visualizer | Section 7.2, 11 | Milestone 8 | Frontend & UI |
| `ENERGY-10` | [#22](https://github.com/AshrafGalaxy/Digital_Twin/issues/22) | Human-in-the-Loop Demand-Response Advisory Dossier & Audit UI | Section 9.2, 10 | Milestone 8 | Frontend & UI |

---

## 8. Quickstart: Running the Platform

### Option A: Local Development (Windows / PowerShell)
```powershell
# Starts FastAPI backend (port 8000) and Vite frontend (port 5173) in parallel
.\start_dev.ps1
```

### Option B: Docker Compose
```bash
# Core platform (PostgreSQL, Mosquitto, Backend, Frontend)
docker compose up -d

# Full research platform (includes MinIO and MLflow)
docker compose --profile full up -d
```

### Access URLs:
- **Operations Dashboard:** [http://localhost:5173](http://localhost:5173)
- **Backend API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check Endpoint:** [http://localhost:8000/health](http://localhost:8000/health)
- **Real-Time WebSocket Stream:** `ws://localhost:8000/ws/operations`

---

## 9. Repository Directory Structure

```text
├── .github/                        # GitHub Actions CI, issue & PR templates
│   ├── ISSUE_TEMPLATE/             # Domain task issue template
│   ├── workflows/                  # ci.yml (Tests, TypeScript build, asset validation)
│   └── pull_request_template.md    # Standard PR template with architectural invariants
├── specifications/                 # Master domain enhancement specifications
│   ├── TRAFFIC_MANAGEMENT.md       # Intelligent Traffic Mobility & Control blueprint
│   ├── ENERGY_MANAGEMENT.md        # Microgrid & Energy Management blueprint
│   ├── ENVIRONMENT_MANAGEMENT.md   # Air quality & environmental monitoring blueprint
│   ├── WATER_MANAGEMENT.md         # Municipal water distribution blueprint
│   └── WASTE_MANAGEMENT.md         # Solid waste collection & routing blueprint
├── docs/                           # Architecture blueprints, master handbook & task directories
│   ├── Volume_1_System_Architecture.md # Vol 1: Architecture, data flow & 32 metrics catalog
│   ├── Volume_2_Domain_Engineering_and_Math.md # Vol 2: First-principles physics & mathematical derivations
│   ├── Volume_3_Screen_Operator_Guide.md # Vol 3: Exhaustive screen-by-screen operator & UI manual
│   ├── Volume_4_Judge_Defense_and_Script.md # Vol 4: 20 judge Q&As, live demo script & forensic audit
│   ├── architecture.md             # Technical architecture and DB schemas
│   └── tasks/                      # Modular engineering implementation task directories
│       ├── traffic-mobility/       # 11 engineering tasks for Traffic Mobility (Tasks 01 to 11)
│       └── energy-microgrid/       # 10 engineering tasks for Energy Management (Tasks 01 to 10)
├── data/                           # Corridor GIS assets, spatial registry, and manifests
│   ├── manifests/                  # Data catalogs and governance definitions
│   └── spatial/                    # GeoJSON corridor networks and PostGIS geometries
├── backend/                        # FastAPI modular monolith application
│   ├── api/v1/                     # REST and WebSocket endpoints
│   ├── core/                       # Config, database connections, schema migrator
│   ├── ingestion/                  # Telemetry streamers, MQTT consumers, validators
│   ├── models/                     # Data models and entities
│   ├── schemas/                    # Pydantic serialization schemas
│   └── services/                   # Business logic, rule engine, scenarios, forecasts
├── frontend/                       # React 18 + TypeScript + Vite operations UI
│   ├── src/components/             # UI components, Map views, Cesium 3D and modals
│   ├── src/services/               # API clients and WebSocket managers
│   └── src/types/                  # TypeScript interface definitions
├── simulation/                     # Eclipse SUMO networks, vehicle fleets, TraCI runners
├── ml/                             # XGBoost training pipelines, models, and evaluators
├── infrastructure/                 # Docker Compose, Mosquitto, and database configs
├── scripts/                        # Development utilities and synthetic stream runners
├── tests/                          # 25 modular pytest suites (183 hermetic tests)
├── CONTRIBUTING.md                 # Developer onboarding and contribution guidelines
├── AGENTS.md                       # Mandatory operating rules and architectural invariants
├── PRD.md                          # Executive Product Requirements Document
├── compose.yaml                    # Multi-container Docker Compose configuration
├── start_dev.ps1                   # One-click PowerShell local development launcher
└── README.md                       # Root system overview, architecture diagram & navigation
```

---

## 10. License & Ethics Notice

This project is an academic research and engineering prototype. Data from OpenStreetMap is licensed under the [Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/). All external benchmark datasets are cataloged with explicit licenses and restrictions in `data/manifests/DATASET_REGISTRY.md`.
