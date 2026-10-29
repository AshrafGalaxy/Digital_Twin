# Master Demo Handbook - Volume 3: Screen-by-Screen Operator Manual

## 1. Overview of the 11 Platform Screens

The platform is structured into 11 distinct operational workspaces accessible via the top navigation header or URL hash parameters. This guide explains every screen, what every value means, and exact instructions on how to demonstrate it to the judges.

---

## 2. Screen 0: Landing Page (`#landing`)

### Purpose
The welcoming public gateway explaining the digital twin platform architecture to city commissioners, mayors, and municipal stakeholders.

### Key Sections and Modules
1. **Hero Diorama Section:**
   - Displays a dynamic isometric visualization of the urban corridor with real-time statistics tickers.
   - **Key Action:** Click the **"Launch Operational Console"** button to enter the main dashboard.
2. **Four Architecture Showcase Pillars:**
   - **Traffic Mobility:** Highlights 2-second telemetry streams, signal timing, and Indo-HCM Level of Service.
   - **Microgrid & Energy:** Highlights 3-phase AC power balance, solar PV, BESS storage, and feeder thermal loading.
   - **Conformal Machine Learning:** Highlights distribution-free uncertainty intervals and TreeSHAP explainability.
   - **Microscopic Physics:** Highlights SUMO TraCI simulation and kinematic fallback modeling.
3. **Corridor Comparison Slider:**
   - An interactive before-and-after slider showing the corridor under uncoordinated traffic vs coordinated digital twin optimization.
4. **Governance Protocol Workflow:**
   - Visualizes the 4-step governance cycle: Ingest -> Analyze & Forecast -> Simulate -> Human-Authorized Advisory.
5. **Interactive FAQ Accordion:**
   - Answers common questions regarding data privacy (no license plate or facial recognition cameras), sensor installation requirements, and municipal cloud deployment.

### Demo Talking Point
*"The landing page demonstrates that this is not an ad-hoc project, but an enterprise-ready municipal platform built to serve multiple agencies with zero facial surveillance and strict data privacy."*

---

## 3. Screen 0B: Digital Twin Provisioning Intake (`#provisioning`)

### Purpose
Allows municipal authorities from any city (e.g. Mumbai, Bengaluru, Delhi, or international metropolises) to request onboarding and provision a new digital twin corridor.

### Key Form Fields and Controls
- **Organization Name:** The municipal agency (e.g. Pune Municipal Corporation, Transport for London).
- **Official Work Email:** Enforces municipal domain validation (rejects generic public domains like gmail.com or yahoo.com).
- **Jurisdiction Level:** Dropdown selecting authority scope (e.g. Municipal Corporation, Metropolitan Regional Transport Authority, State Highway Department).
- **Infrastructure Scale:** Selects scale (1-10 Intersections for pilot sandbox up to 200+ Intersections for urban metropolises).
- **Primary Operational Domain:** Selects domain focus (Intelligent Traffic Mobility, Municipal Energy Grid, or Cross-Agency Unified Operations).
- **Submit Request Button:** Dispatches the intake inquiry to the backend database and generates a unique **Corridor Reference ID** (e.g. `INQ-PUNE-2026-9042`) with a copy-to-clipboard button.
- **Admin Provisioning Modal Trigger:** Administrators can open the modal to define corridor boundaries, import GeoJSON files, and prime new intersection assets.

### Demo Talking Point
*"This screen demonstrates corridor generalization. We are not hardcoding Pune Nagar Road. Any municipality can submit their corridor geometry and sensor specifications to provision an isolated digital twin instance."*

---

## 4. Screen 0C: Municipal Authentication Gateway (`#auth`)

### Purpose
Provides cryptographic JWT-based authentication and role-based access control (RBAC).

### Key Elements
- **Quick Demo Account Selector Pills:**
  Allows one-click login for four certified municipal roles:
  - **Traffic Systems Engineer** (Yellow Badge, email: `traffic.engineer@pmc.gov.in`)
  - **Energy Grid Manager** (Green Badge, email: `grid.manager@pmc.gov.in`)
  - **Executive Auditor** (Blue Badge, email: `auditor@pmc.gov.in`)
  - **Municipal Analyst** (Purple Badge, email: `analyst@pmc.gov.in`)
- **Sign In / Sign Up Toggle:** Allows switching between logging into an existing account or registering a new officer with a specific municipal role.
- **Single-Use Magic Access Links:** Supports passwordless authentication via URL tokens.

### Demo Talking Point
*"City operations require strict access controls. An energy grid operator should not modify traffic signal plans, and a traffic engineer should not alter substation breaker limits. Our cryptographic JWT gateway enforces these boundaries."*

---

## 5. Screen 1: Corridor Operations Console (`#operations`)

### Purpose
The primary 24/7 command center map console used by city operators to monitor live traffic, energy demand, and active sensor status.

### Key Components

#### 1. Corridor Metrics Card (Top-Left HUD)
A floating glass-morphism heads-up display showing four continuous real-time numbers:
- **Avg Arterial Speed (km/h):** The corridor-wide space-mean speed across all active segments (typically 24 to 45 km/h).
- **Congestion Index (%):** Overall corridor traffic stress:
  - `< 30%`: `NOMINAL` (Green Pill)
  - `30% - 60%`: `ELEVATED` (Amber Pill)
  - `> 60%`: `STRESSED` (Red Pill)
- **Commercial Energy (kW):** Sum of active power demand across commercial facilities (typically 4,200 to 5,400 kW).
- **Active Sensors:** Total count of online sensor nodes (10 of 10 nodes active).
- **Live Pulse Dot:** A pulsing emerald beacon confirming active WebSocket telemetry streaming.

#### 2. The 2D Operational GIS Map (Leaflet)
- **Road Segments:** Rendered as thick polylines color-coded by current speed and Level of Service:
  - Emerald Green: Speed >= 42 km/h (LOS A)
  - Light Green: Speed 38-42 km/h (LOS B)
  - Yellow: Speed 32-38 km/h (LOS C)
  - Amber Orange: Speed 25-32 km/h (LOS D)
  - Crimson Red: Speed < 18 km/h (LOS F / Congested)
- **Intersection Markers:** Circular icons representing signalized junctions (`INT-VN-01` and `INT-SN-01`). The outer halo dynamically mirrors the active signal phase (Red, Amber, or Green).
- **Surveyed Stoplines:** Precise white stopline bars marking where vehicles queue.
- **Commercial Building Outlines:** Semi-transparent polygon footprints for commercial entities like Phoenix Marketcity.

#### 3. The 3D Digital Twin Viewer (CesiumJS)
- Clicking the **3D Globe Toggle** switches from 2D Leaflet to full photogrammetric 3D Cesium visualization.
- **3D Extruded Buildings:** Commercial malls and office towers rendered with realistic building heights and window textures.
- **Live Kinematic Traffic Simulation:** 3D vehicle models (cars, buses, delivery vans) moving smoothly along the corridor road splines. Their speeds automatically speed up or slow down to match the actual measured segment speeds.
- **Camera Preset Controls:** One-click buttons to fly the camera to:
  - *Corridor Overview:* High-altitude bird-eye view of the full 1.8 km arterial.
  - *Viman Nagar Chowk:* Close-up inspection of the western intersection.
  - *Somnath Nagar Chowk:* Close-up inspection of the eastern junction.
  - *Commercial Substation:* Close-up inspection of the Phoenix 22kV transformer yard.

#### 4. Map Type Selector Toolbar (Top-Right)
- **2D / 3D Toggle:** Switches between 2D GIS and 3D Cesium.
- **Basemap Modes:**
  - *Dark:* High-contrast tactical mode for nighttime operations.
  - *Satellite:* High-resolution aerial satellite imagery.
  - *Streets:* Standard daytime cartographic street map.
- **Table Mode Toggle:** Replaces the map with an inventory table of all corridor assets with inline filtering and search.

#### 5. Map Legend (Bottom-Left)
Displays the color scale for arterial velocities and Level of Service definitions so operators immediately understand road conditions.

#### 6. Entity Details Drawer (Slide-Out Right Panel)
Clicking on any road segment or intersection on the map slides open the **Entity Details Drawer**:
- **Asset Metadata:** Entity ID, road name, direction, number of lanes, speed limit.
- **Live State Gauges:** Current speed, flow (veh/h), queue length (meters), and Level of Service badge.
- **Opposing Bound Switcher:** One-click button to jump to the opposite bound (e.g. Eastbound to Westbound).
- **Side-by-Side Comparison Mode:** Select another segment to compare speeds and congestion differentials side by side.
- **Integrated Forecast Panel:** Embedded 15m, 30m, and 60m future predictions with conformal bands.

### Demo Talking Point
*"The Operations Map gives the operator immediate situational awareness. In 2D, you see tactical road network congestion. In 3D Cesium, you see realistic vehicle movement and building extrusions. Clicking any segment provides instant diagnostics without page reloads."*

---

## 6. Screen 2: Traffic Analytics and Near-Term Forecasting (`#traffic`)

### Purpose
Dedicated workspace for traffic engineers to analyze hydrodynamic traffic flow, inspect intersection signal phasing (SPaT), and compute optimal signal retiming.

### Key Components
1. **Segment Selector & Policy Toggle:**
   - Dropdown to select any road segment.
   - **Policy Toggle:** Switch between **Indo-HCM (IRC:106)** and **US HCM 6th Edition** to see how Indian mixed-traffic standards alter Level of Service grades.
2. **Key Traffic Metric Cards:**
   - **Current Speed:** Space-mean speed in km/h.
   - **Hourly Flow:** Volume in vehicles per hour.
   - **Volume/Capacity Ratio (V/C):** Indicates how close the road is to saturation (e.g. 0.82 means 82% capacity).
   - **Density:** Vehicle concentration in vehicles per kilometer.
   - **Active LOS Grade:** Large colored badge (A through F).
3. **Ranked Segment Congestion Table:**
   - Lists all 10 corridor segments sorted by highest V/C ratio, highlighting congestion bottlenecks first.
4. **SPaT (Signal Phase and Timing) Live Card:**
   - Shows the live status of the selected intersection signal controller:
     - Active Phase: North-South Green, East-West Red, All-Red Clearance.
     - Countdown Timer: Remaining seconds before the next phase transition.
     - Cycle Length: Total seconds per complete rotation (e.g. 120s).
5. **Webster Signal Timing Modal Trigger:**
   - Clicking **"Compute Webster Signal Optimization"** opens an interactive calculator:
     - Allows adjusting lost time per cycle (`L`) and approach saturation flows (`s`).
     - Calculates the optimal cycle length: `C_0 = (1.5 * L + 5) / (1 - Y)`.
     - Displays recommended green phase splits.
     - Includes a button to propose an advisory plan to the governance center.
6. **15-Min, 30-Min, and 60-Min Forecast Panel:**
   - Interactive line chart powered by XGBoost.
   - Displays shaded **Conformal Prediction Bands** (80% and 90% confidence).
   - Displays the **TreeSHAP Top-5 Feature Contributions** explaining why the forecast was made.

### Demo Talking Point
*"Traffic Analytics bridges real-time telemetry with predictive physics. An engineer can observe a queue forming at Viman Nagar Chowk, inspect the SPaT signal clock, compute an optimized Webster cycle time, and see the AI 60-minute speed forecast."*

---

## 7. Screen 3: Energy Analytics and Microgrid Integration (`#energy`)

### Purpose
Dedicated workspace for electrical grid managers to monitor substation power flow, 3-phase AC balance, feeder thermal headroom, and commercial demand response.

### Key Components
1. **Electrical Topology Tree:**
   - Interactive tree visualizing the corridor microgrid hierarchy:
     - `22kV Primary Substation Feeder`
       - `Distribution Feeder A (Eastbound Arterial)` -> Phoenix Marketcity Commercial Mall
       - `Distribution Feeder B (Westbound Arterial)` -> Solitaire Business Hub
       - `Distribution Feeder C (Hospitality Zone)` -> Hyatt Regency Hotel
       - `Distributed Energy Resources (DER)` -> 1.2 MW Rooftop Solar PV & 500 kWh BESS
2. **Three-Phase Telemetry Card:**
   - Displays precise electrical measurements:
     - Line-to-Line Voltages: `V_AB`, `V_BC`, `V_CA` (balanced around 415V / 22kV).
     - Phase Currents: `I_A`, `I_B`, `I_C` (amperes).
     - Active Power: Total real power in kW.
     - Reactive Power: Inductive power in kVAR.
     - Power Factor: Operational efficiency (e.g. 0.97).
3. **Feeder Thermal Loading Card:**
   - Radial gauge showing percentage ampacity utilization (`I_measured / I_rated * 100%`).
   - Estimated conductor temperature (degrees Celsius).
   - Remaining electrical headroom in kW before thermal overload.
4. **Microgrid Power Balance Card:**
   - Real-time balance: `Grid Import + Solar Generation + BESS Discharge = Commercial Load + Losses`.
5. **Demand Response Dossier Modal:**
   - Proposes peak-shaving demand management:
     - Pre-cooling commercial mall chillers during low-cost morning hours.
     - Discharging BESS during evening peak demand (18:00 - 21:00).
     - Throttling commercial EV fast-charging stations by 25% during grid stress.

### Demo Talking Point
*"In smart cities, traffic and energy are intimately connected. Evening traffic jams coincide with peak shopping mall lighting and AC loads. This screen gives the grid manager complete visibility into 3-phase power balance and thermal feeder safety."*

---

## 8. Screen 4: Environmental Context and Air Quality (`#environment`)

### Purpose
Monitors urban air quality, pollutant concentrations, and atmospheric dispersion along the arterial corridor.

### Key Components
1. **CAAQMS Station Selector:**
   - Allows toggling between regional government monitoring stations (e.g. Airport Sector CAAQMS, Central Sector MPCB Station) and on-corridor IoT micro-climate stations.
2. **Air Quality Index (AQI) Meter:**
   - Large radial meter showing the current AQI (e.g. 135 - Moderate).
   - Color badge indicating health category (Good, Satisfactory, Moderate, Poor, Very Poor, Severe).
   - Identifies the **Determining Pollutant** (e.g. PM2.5).
3. **Pollutant Concentration Cards:**
   - **PM2.5:** Fine respirable dust (micrograms per cubic meter).
   - **PM10:** Coarse particulate matter (micrograms per cubic meter).
   - **NO2:** Nitrogen dioxide from vehicular exhaust emissions.
   - **CO:** Carbon monoxide concentration.
4. **Ambient Weather & Wind Dispersion Meters:**
   - Ambient temperature (degrees Celsius).
   - Relative humidity (%).
   - Wind velocity (km/h) and compass dispersion direction (e.g. WSW 242 degrees).
5. **Isolation Forest Anomaly Badge:**
   - Shows real-time anomaly status based on machine learning scoring. If emissions spike beyond diurnal expectations, a yellow or red warning badge appears with the calculated Z-score.
6. **24-Hour Diurnal Historical Trend Chart:**
   - Shows the rise of emissions during morning and evening rush hours.

### Demo Talking Point
*"Vehicular traffic is the primary source of urban PM2.5 and NO2. By coupling environmental sensors with traffic flow, city planners can measure the exact air quality penalty of arterial traffic jams."*

---

## 9. Screen 5: Scenario Studio Simulation Sandbox (`#scenarios`)

### Purpose
A microscopic simulation testing sandbox. City engineers can simulate what-if scenarios safely in software using the SUMO (Simulation of Urban MObility) physics engine before making physical changes.

### Key Components
1. **Scenario Template Selector:**
   Pre-configured scenarios:
   - **Arterial Green Wave:** Optimizes cycle offsets between Viman Nagar and Somnath Nagar to create an unhindered green corridor.
   - **Peak Congestion Surge:** Tests network resilience against a 25% to 50% sudden surge in traffic volume.
   - **Corridor Incident Closure:** Simulates a lane blockage or vehicle breakdown on Eastbound Nagar Road.
   - **Severe Weather / Waterlogging:** Simulates reduced road capacity and lowered driver speeds due to monsoon rainfall.
2. **Simulation Parameter Sliders:**
   - **Green Extension:** Adds extra green seconds (0 to 30s) to the critical approach.
   - **Coordination Offset:** Adjusts progression delay (0 to 60s) between intersections.
   - **Demand Multiplier:** Scales traffic volume from 0.5x up to 2.0x baseline.
   - **Random Seed:** Ensures scientific reproducibility across simulation runs.
3. **Run Simulation Button:**
   - Executes SUMO TraCI in the background (or our verified kinematic fallback runner).
   - Generates second-by-second vehicle trajectory metrics.
4. **Baseline vs Scenario Comparison Cards:**
   Displays the quantitative outcome of the simulation:
   - Average Speed: e.g. +4.2 km/h improvement.
   - Queue Length: e.g. -28% shorter vehicle queues.
   - Total Delay: e.g. -185 vehicle-hours saved.
   - Fuel / Carbon Impact: Estimated reduction in idling emissions.
5. **"Propose Advisory from Simulation" Button:**
   - If the simulation yields positive results, the engineer can submit the parameter set directly to the **Recommendations Center** for formal municipal authorization.

### Demo Talking Point
*"Scenario Studio is where the digital twin proves its economic value. Instead of guessing or running risky trials on real commuters, engineers test timing changes in simulation first, proving delay reductions before deployment."*

---

## 10. Screen 6: Governance and Advisory Center (`#recommendations`)

### Purpose
The formal municipal decision-support clearinghouse. It collects AI and rule-generated recommendations, evaluates potential conflicts, and enforces human-in-the-loop authorization.

### Key Components
1. **Domain & Status Filter Tabs:**
   - Domain Filters: `ALL`, `TRAFFIC`, `ENERGY`.
   - Status Filters: `PENDING` (Awaiting review), `APPROVED` (Authorized by officer), `REJECTED` (Declined).
2. **Actionable Advisory Cards:**
   Each card displays:
   - Advisory Title and Target Entity (e.g. *"Signal Timing Optimization for Viman Nagar Chowk"*).
   - Recommended Action (e.g. *"Extend Phase 1 Eastbound Green by 12 seconds; shift offset to 38s"*).
   - Expected Impact (e.g. *"+3.8 km/h speed increase; 18% queue reduction"*).
   - AI Confidence Score (e.g. *92% Confidence*).
   - Conflict Warning System: Checks if an energy advisory contradicts a traffic advisory (e.g. throttling EV chargers while traffic is diverted to an alternate route).
3. **Human Authorization Action Buttons:**
   - **"Authorize Advisory Plan":** Formally approves the recommendation, stamps the reviewer municipal role and timestamp, and transitions the status to `APPROVED`.
   - **"Reject Plan":** Declines the recommendation with required notes explaining why the action was rejected.
4. **Immutable Advisory Audit Log:**
   - A tamper-evident log recording every single authorization or rejection event for municipal transparency and accountability.

### Demo Talking Point
*"This screen proves our strict non-actuation invariant. The AI is an advisor, not the driver. A human officer must inspect the impact assessment, check for multi-agency conflicts, and explicitly click Authorize."*

---

## 11. Screen 7: Pilot Evaluation and Executive Reporting (`#evaluation`)

### Purpose
The executive reporting suite for city commissioners, funding bodies, and academic evaluators. It benchmarks machine learning accuracy against chronological holdout data and generates formal briefing reports.

### Key Components
1. **Chronological Holdout Benchmark Table (80/10/10 Split):**
   - Displays scientific evaluation metrics across 15-minute, 30-minute, and 60-minute prediction horizons:
     - **MAE (Mean Absolute Error):** Measured in km/h or kW.
     - **RMSE (Root Mean Squared Error):** Penalizes large outlier errors.
     - **MAPE (Mean Absolute Percentage Error):** Normalized percentage error.
     - **Comparison against Persistence Baseline:** Proves that our XGBoost model outperforms a naive persistence baseline (the assumption that future speed will equal current speed) by 18% to 32%.
2. **Executive Summary Briefing Tab:**
   - Formatted text report summarizing corridor mobility improvements, energy demand savings, carbon reduction estimates, and system reliability metrics.
   - **Briefing Mode Toggle:** Switch between a formatted executive card view and raw GitHub Flavored Markdown.
3. **Export Actions:**
   - **Copy to Clipboard:** Copies the entire executive report in one click.
   - **Download Markdown:** Downloads `corridor_executive_briefing.md` directly to disk.
   - **Download Corridor Data Bundle:** Exports the full JSON data package for independent audit.

### Demo Talking Point
*"City commissioners demand measurable return on investment. The Pilot Evaluation view provides rigorous holdout benchmarks, persistence comparisons, and one-click executive briefing downloads."*

---

## 12. Screen 8: System and Data Health Observability (`#health`)

### Purpose
The technical observability dashboard for DevOps engineers and IT administrators to verify database connectivity, ingestion pipeline latency, schema integrity, and sensor health.

### Key Components
1. **Dual-Engine Database Status Card:**
   - Reports the active persistence backend: `PostgreSQL / TimescaleDB` or `SQLite (Resilient Local Engine)`.
   - Displays verified table count (29+ authoritative tables).
   - Connection pool health and round-trip ping latency.
2. **Autonomous Telemetry Streamer Control:**
   - Shows streamer worker status (`RUNNING` / `ACTIVE`).
   - Displays generated ticks count and emission interval (1.0s to 2.4s).
   - Includes manual controls to trigger an immediate telemetry tick or pause the stream.
3. **MQTT Consumer & WebSocket Stream Health:**
   - WebSocket broadcast status and count of active browser connections.
   - Message delivery latency (typically < 15 milliseconds).
4. **Dataset Manifests Catalog Modal:**
   - Clicking **"Inspect Telemetry Manifests"** opens a modal detailing every historical and replayed dataset, including sensor station IDs, sample counts, survey dates, and data license terms.
5. **Data Quarantine Queue Modal:**
   - Clicking **"Inspect Quarantine Queue"** reveals records that failed schema or physical boundary validation, ensuring corrupted data never pollutes analytical models.

### Demo Talking Point
*"System Health proves that our digital twin is engineered for enterprise reliability. If PostgreSQL goes down, SQLite automatically takes over. If a sensor sends bad data, it is quarantined rather than crashing the system."*

