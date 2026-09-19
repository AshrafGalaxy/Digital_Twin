# Digital Twin-Enabled Smart City Analytics
## Project Context

> **Document status:** Baseline / source of truth  
> **Study area:** Viman Nagar Chowk (Phoenix Mall) ↔ Somnath Nagar Chowk corridor, Nagar Road, Pune, Maharashtra, India  
> **Project type:** Engineering design innovation, research prototype, urban digital-twin system  
> **Primary interface:** 2D operations dashboard; optional immersive 3D presentation layer  
> **Decision authority:** Any change to the scope, study area, core stack, data contract, or safety boundaries must be recorded before implementation.

---

## 1. Purpose of this document

This file is the **single source of truth** for the project before implementation begins. Every agent, developer, researcher, designer, or reviewer must read this document before working on the system.

It defines:

- The project problem and intended contribution.
- The exact prototype study area.
- In-scope and out-of-scope work.
- The users, beneficiaries, and stakeholders.
- The digital-twin definition used by this project.
- The operating modes and data-provenance rules.
- The approved MVP technical direction.
- The research, data, platform, and engineering resources relevant to the project.
- Non-negotiable quality, safety, research, and documentation rules.

Detailed requirements, UI specifications, API contracts, ML details, and implementation milestones will be maintained in separate documents. This document establishes the context that those documents must follow.

---

## 2. Project identity

### 2.1 Title

**Digital Twin-Enabled Smart City Analytics using AI, IoT, and Real-Time Data Intelligence**

### 2.2 Working prototype title

**NagarRoad Twin: AI-Assisted Urban Mobility and Energy Analytics for the Viman Nagar–Somnath Nagar Corridor, Pune**

### 2.3 One-sentence description

A modular urban digital twin that combines geospatial city assets, real-time/replayed/simulated observations, AI forecasting, and SUMO what-if simulation to help users monitor, predict, and assess mobility and energy conditions in a small Pune corridor.

### 2.4 Core question

> Can a lightweight, standards-aligned, explainable digital twin provide useful traffic forecasting, energy forecasting, and scenario-based decision support for a constrained urban corridor without requiring a full city-scale enterprise platform?

---

## 3. Problem statement

Cities generate data from roads, intersections, signals, vehicles, buildings, weather, environmental systems, public infrastructure, and municipal operations. In practice, this data is fragmented, arrives at different rates, uses incompatible structures, and often remains disconnected from planning or operational decisions.

A conventional map or dashboard only describes the current or historical situation. A useful urban digital twin must additionally:

1. Represent physical urban assets digitally.
2. Maintain state as observations arrive.
3. Preserve historical, current, predicted, and simulated views separately.
4. Model relationships among roads, intersections, buildings, sensors, and scenarios.
5. Forecast likely near-future conditions.
6. Allow safe virtual testing of interventions before real-world action.
7. Explain its recommendations and uncertainty.

This project addresses those needs at a small, researchable scale.

---

## 4. Target problems

The prototype will address the following practical problems.

| Problem | Prototype response |
|---|---|
| Fragmented urban observations | Normalize simulation, replay, and optional live data into one canonical entity schema |
| Limited understanding of corridor traffic conditions | Maintain road/intersection twin state and spatially visualize speed, congestion, queues, and forecasts |
| Reactive rather than predictive traffic response | Produce short-horizon traffic forecasts, initially 15 minutes ahead |
| No safe way to compare interventions | Run baseline and intervention scenarios in SUMO before displaying a recommendation |
| Limited energy visibility | Represent one or more building/zone energy entities and forecast short-horizon demand |
| Environmental information is disconnected | Display available AQI/weather conditions and raise transparent threshold-based alerts |
| Opaque recommendations | Use explainable models and transparent rule-based decision support |
| Difficulty reproducing smart-city demonstrations | Support simulation, replay, and live modes through one downstream pipeline |
| Overly complex city-platform architecture | Use a modular, lightweight architecture suitable for a student research prototype |

---

## 5. Exact study area

### 5.1 Selected corridor

The project study area is the **Viman Nagar Chowk (Phoenix Mall) ↔ Somnath Nagar Chowk corridor**, located on/around Nagar Road in Pune.

The initial twin must model a deliberately limited area rather than all of Pune:

- **Primary junction:** Viman Nagar Chowk / Phoenix Mall junction.
- **Secondary junction:** Somnath Nagar Chowk.
- **Connector corridor:** the road network linking the two junctions and selected approach roads toward the Kalyani Nagar/Ramwadi side.
- **Initial network size:** 2 primary junctions, 8–15 road segments, and only the turns/routes required by defined scenarios.

### 5.2 Why this location was selected

This corridor was selected instead of a campus-only area or RTO Chowk because it offers:

- Visible and modern urban context: commercial, retail, hospitality, airport-adjacent, residential, and office activity.
- Signalized junctions and meaningful turning movements.
- Strong relevance to traffic management and corridor analytics.
- A credible smart-mobility narrative: Pune Smart City’s Adaptive Traffic Management System (ATMS) has been deployed across major junctions/corridors, including Nagar Road-area junctions such as Viman Nagar, Somnath Nagar, Kalyani Nagar, and nearby road-network nodes.
- A manageable network size for SUMO, data modeling, UI testing, and reproducible research.
- Better visual quality for a 2D map and optional 3D presentation than a campus-internal road network.

Pune Smart City’s ATMS documentation describes adaptive traffic controllers, traffic signals, sensors, variable-message signs, and command-control integration; public reporting describes ATMS deployment and operation across Pune junctions. These references provide real-world context but **do not grant access to the city’s live ATMS feeds or control systems**.[Pune Smart City ATMS PDF](https://www.punesmartcity.in/assets/PANCITY/Adaptive%20Traffic%20Management%20System.pdf) · [Pune Smart City project page](https://www.punesmartcity.in/smart-city/project) · [Indian Express reporting on ATMS](https://indianexpress.com/article/cities/pune/pune-reduce-traffic-chaos-busy-roads-ai-8990201/)

### 5.3 Study-area boundary procedure

The exact geometry must be finalized before SUMO or UI implementation.

1. Open the target area in OpenStreetMap.
2. Draw a boundary polygon that includes Viman Nagar Chowk, Somnath Nagar Chowk, connector roads, and only required approaches.
3. Save the boundary as `study_area.geojson`.
4. Record the exact bounding box and capture date.
5. Extract the road network with OSMnx or SUMO `netconvert` tooling.
6. Store authoritative prototype geometry in PostGIS.
7. Version the GeoJSON in Git.

**Boundary rule:** Do not add Kharadi, Wagholi, the entire Nagar Road, or all airport approaches to the initial network. Expansion requires a documented reason and a revised experiment plan.

### 5.4 Campus connection

VIT Kondhwa and VIT Bibwewadi are not the primary traffic study area. They may be mentioned as the project team’s institutional context. A building/energy entity may be modeled generically as a representative campus/commercial building, but it must not be presented as a measured VIT meter unless permission and real meter data are obtained.

VIT publicly lists its Bibwewadi and Kondhwa campus addresses.[VIT contact information](https://www.vit.edu/contact/)

---

## 6. Intended users and beneficiaries

| Group | Role in the prototype | Benefit |
|---|---|---|
| Traffic/operator user | Views corridor state, forecasts, alerts, scenarios, and recommendations | Faster situational awareness and safer planning decisions |
| Urban planner/researcher | Tests planned interventions and compares scenario KPIs | Evidence before proposing changes |
| Energy/facility user | Views energy state and short-horizon demand forecast | Better visibility of demand peaks and potential reduction scenarios |
| Student/research team | Builds, evaluates, and documents the platform | Reproducible applied research and engineering learning |
| General public/corridor user | Indirect beneficiary; not a direct platform user in MVP | Potentially better journey planning and future congestion reduction |
| Academic evaluator/sponsor | Reviews architecture, evidence, research quality, and outcomes | Clear demonstration of engineering design and research rigor |

---

## 7. Project goals

### 7.1 Primary goals

1. Build a stateful corridor-scale digital twin rather than a static map/dashboard.
2. Demonstrate a shared pipeline for **simulation**, **replay**, and optional **live** data.
3. Forecast traffic conditions for the selected corridor.
4. Forecast energy demand for a representative building/zone dataset.
5. Support at least one traffic what-if scenario in SUMO.
6. Generate human-readable, evidence-based recommendations.
7. Evaluate technical quality using reproducible metrics.
8. Produce a credible foundation for a paper, portfolio, academic review, or future funding proposal.

### 7.2 Secondary goals

- Show environmental status using weather/AQI data where available.
- Demonstrate standards-aware modeling through an NGSI-LD-inspired data contract.
- Provide explainability via feature importance and/or SHAP.
- Offer an optional 3D visualization extension without making 3D a dependency for core correctness.

---

## 8. Non-goals and hard scope boundaries

The following are intentionally excluded from the initial prototype:

- Full Pune or citywide coverage.
- Direct access to or control of Pune ATMS infrastructure.
- Live traffic-signal actuation.
- Collection or processing of CCTV video.
- Facial recognition, vehicle identification, or personally identifiable information.
- Claims of municipal-production readiness.
- Claims that simulated outputs represent real-world measured outcomes.
- Claims of Viman Nagar model accuracy based solely on data collected at other Pune intersections.
- Blockchain, federated learning, LLM/agentic operations, autonomous control, Kubernetes, Kafka, or graph databases unless approved later through a documented technical decision.

**Safety rule:** Every recommendation is advisory. No command generated by the system can change a physical traffic signal, route-management system, building system, or public service.

---

## 9. Definition of digital twin in this project

The project uses a strict definition to avoid calling a visualization-only system a digital twin.

| Capability | Required in MVP? | Implementation intent |
|---|---:|---|
| Physical assets | Yes | Roads, intersections, sensors, building/energy entity, environmental source |
| Digital entities | Yes | Canonical structured JSON + database records |
| Asset relationships | Yes | Road-to-junction, sensor-to-road, meter-to-building relationships |
| Current state | Yes | Latest valid observation per entity |
| Historical state | Yes | Time-series observations in TimescaleDB |
| Predicted state | Yes | Traffic and energy forecasts stored separately |
| Simulated state | Yes | SUMO scenario outputs stored separately |
| Behavior model | Yes | SUMO traffic model; lightweight energy model/replay input |
| Synchronization | Yes | MQTT/replay/API ingestion at a defined update interval |
| Scenario testing | Yes | Baseline versus intervention comparisons |
| Explanation | Yes | Feature importance/SHAP and rule evidence |
| Physical actuation | No | Human-readable recommendations only |
| Full semantic context broker | No, initially | NGSI-LD-inspired schema without running Orion-LD in MVP |

A static 3D map alone is not a digital twin. The twin is the combination of asset representation, continuously updated state, time history, prediction, simulation, relationships, provenance, and decision support.

---

## 10. Operating modes and provenance

The system has three input modes. They must converge to the same canonical schema before twin storage, model feature generation, API output, and dashboard display.

| Mode | Description | Primary use | Mandatory label |
|---|---|---|---|
| `simulation` | SUMO outputs and synthetic energy/environment streams | Development, controlled experiments, what-if scenarios | `SIMULATION` |
| `replay` | Historical CSV/API dumps republished at controlled speed | Demonstrations, deterministic tests, model evaluation | `REPLAY` |
| `live` | Real permitted sensors or approved external APIs | Optional real-time demonstration | `LIVE` |
| `predicted` | ML forecast generated from current/historical features | Short-horizon decision support | `PREDICTED` |

### Provenance rule

Every observation, chart, map layer, alert, forecast, scenario result, and recommendation must expose its origin. Minimum provenance fields are:

```json
{
  "sourceMode": "simulation | replay | live | predicted",
  "sourceId": "human-readable-source-name",
  "observedAt": "ISO-8601 timestamp",
  "ingestedAt": "ISO-8601 timestamp",
  "dataQualityScore": 0.0,
  "modelVersion": "optional-model-version",
  "scenarioRunId": "optional-scenario-run-id"
}
```

Never show a simulated, replayed, or predicted value as a live measurement.

---

## 11. Approved MVP architecture

### 11.1 Logical flow

```text
Data source
(simulation / replay / optional live API or sensor)
        ↓
MQTT broker or scheduled API/replay publisher
        ↓
FastAPI ingestion and validation
        ↓
Canonical NGSI-LD-inspired entity transformation
        ↓
PostgreSQL + TimescaleDB + PostGIS
(current state + historical observations + geometry)
        ↓
Feature generation
        ↓
Traffic / energy model inference
        ↓
Predicted twin state + confidence + explanation
        ↓
Rule-based recommendation engine
        ↓
React + MapLibre dashboard
        ↕
SUMO + TraCI scenario service
(baseline vs intervention; outputs kept separate from live state)
```

### 11.2 Core architectural principles

- Start as a **modular monolith**, not a microservice estate.
- Use one PostgreSQL instance with TimescaleDB and PostGIS for the MVP.
- Use MQTT for lightweight event transport.
- Use REST for request/response operations and WebSockets for dashboard state updates.
- Use a canonical data contract now so FIWARE/Orion-LD or Eclipse Ditto can be introduced later without rewriting entity semantics.
- Keep simulation state separate from live/replay state.
- Prefer interpretable tabular ML before deep sequence or graph models.
- Keep 3D optional and never let it delay data, twin state, simulation, or evaluation.

---

## 12. Approved MVP technical stack

| Layer | Approved MVP choice | Why |
|---|---|---|
| Frontend | React + TypeScript + Vite | Strong ecosystem and fit for dashboard development |
| 2D spatial UI | MapLibre GL JS + OpenStreetMap | Open, lightweight, suitable for analytical map overlays |
| Optional 3D UI | CesiumJS | Compatible with 3D Tiles; presentation extension only |
| Optional photorealistic 3D basemap | Google Photorealistic 3D Tiles | Optional paid/terms-bound visual layer; not twin data source |
| Backend | Python + FastAPI | Data/ML integration and typed API development |
| Message transport | Eclipse Mosquitto + MQTT | Simple IoT/replay/simulation messaging |
| Live browser updates | WebSockets | Dashboard status and map-layer updates |
| Primary store | PostgreSQL | Entity, application, and relational state |
| Time series | TimescaleDB extension | Observation and forecast tables |
| Spatial store | PostGIS extension | Roads, junctions, sensors, study boundary |
| Object/artifact storage | MinIO or local filesystem | Scenario, model, and raw-import artifacts |
| Twin data model | Custom JSON modeled on NGSI-LD / Smart Data Models | Interoperability-aware but lightweight |
| Traffic simulation | Eclipse SUMO + TraCI | Open traffic simulation and Python control |
| Traffic ML | Persistence baseline + XGBoost | Fast, interpretable, laptop-friendly forecasting |
| Energy ML | Persistence baseline + XGBoost | Practical demand forecasting baseline/primary model |
| Environment analytics | Threshold rules first; Isolation Forest later | Transparent with limited local data |
| Explainability | SHAP / model-native feature importance | Traceability of predictions |
| Decision support | Rule engine | Transparent, non-autonomous recommendations |
| Experiment tracking | MLflow + Git | Reproducible runs, metrics, artifacts |
| Local/development deployment | Docker Compose | Low operational overhead |
| CI | GitHub Actions | Linting, tests, and validation |

### 12.1 Technologies explicitly deferred

- FIWARE Orion-LD context broker.
- Eclipse Ditto.
- Apache Kafka/Flink.
- Neo4j or another graph database.
- Kubernetes.
- Deep learning models such as LSTM, TCN, Transformers, and STGNNs.
- Reinforcement learning signal control.
- EnergyPlus/Modelica building simulation.
- CityGML/3D Tiles conversion pipelines.
- Prometheus/Grafana production observability stack.

Deferred does not mean rejected forever. It means the MVP must prove a clear need before these technologies are introduced.

---

## 13. Data strategy

### 13.1 Required data categories

| Category | Minimum input | MVP source approach |
|---|---|---|
| Road network and geometry | Roads, junctions, directionality, geometry | OpenStreetMap extraction |
| Traffic state | Vehicle counts and/or speed per segment/intersection | Pune dataset for model prototyping; SUMO for local corridor simulation; optional manual/local data later |
| Traffic simulation | Network, demand, signal plans, routes | SUMO + OSM-derived network + defined assumptions |
| Weather | Temperature, precipitation, wind/humidity if available | Meteostat or Open-Meteo |
| Energy | Time-stamped consumption/load | Campus permission if possible; otherwise synthetic/replayed profile; UCI benchmark only for model testing |
| Environment | AQI/PM values and weather | OpenCity/CPCB Pune resources or approved API; clearly label station distance/coverage |
| Study-area entities | Roads, intersections, buildings, sensors | OSM + manually curated registry |

### 13.2 Primary dataset resources

| Resource | Intended use | Important limitation |
|---|---|---|
| [OpenStreetMap](https://www.openstreetmap.org/) | Geometry, road network, buildings, context | ODbL attribution/licensing must be followed; attributes may be incomplete |
| [OSMnx](https://github.com/gboeing/osmnx) | Download/construct road networks from OSM | Validate intersections, lanes, turns before SUMO use |
| [Pune heterogeneous traffic count dataset (Mendeley Data)](https://data.mendeley.com/datasets/xnf2k6n288/1) | Traffic model prototyping and feature pipeline | Collected at Alankar Chowk, Jehangir Chowk, and RTO Chowk—not Viman Nagar |
| [Pune Hourly Air Quality Reports (OpenCity)](https://data.opencity.in/dataset/pune-hourly-air-quality-reports) | AQI/environment visualization and optional analytics | Monitoring station readings do not equal exact corridor/campus conditions |
| [Meteostat datasets](https://dev.meteostat.net/data) | Historical weather features | Station coverage and temporal completeness vary |
| [Open-Meteo historical weather API](https://open-meteo.com/en/docs/historical-weather-api) | Weather API alternative | Record request parameters/date for reproducibility |
| [Pune electricity consumption data (OpenCity)](https://data.opencity.in/dataset/pune-electricity-consumption-data) | Context and high-level energy evidence | Not building-level time series suitable for direct Viman Nagar load prediction |
| [UCI Electricity Load Diagrams 2011–2014](https://archive.ics.uci.edu/dataset/321/electricityloaddiagrams20112014) | Benchmark energy model/data pipeline | Not Pune/VIT local data |
| [METR-LA / PEMS-BAY CSV (Zenodo)](https://zenodo.org/records/5146275) | Advanced traffic benchmark only | Not local data; no local-accuracy claim allowed |

### 13.3 Data use rules

1. Every dataset must be documented with source URL, license, download date, geography, temporal range, fields, and limitations.
2. Pune data from other intersections must not be described as Viman Nagar measurements.
3. Synthetic energy data must be labelled synthetic in every UI and report.
4. OSM data must retain required attribution.
5. Google photorealistic tiles, if used, are visualization-only and must not be mined for geometry, ML training, or offline data extraction.
6. No personal data, CCTV video, number plates, face data, or personally identifiable mobility traces may be ingested.

---

## 14. AI/ML scope

### 14.1 Minimum trained models

The MVP requires only **two trained supervised models**.

| Model | Target | Inputs | Baseline | Primary model | Output |
|---|---|---|---|---|---|
| Traffic forecast | Average speed or congestion index, 15-minute horizon | Lagged speed/count, rolling stats, time features, weather, road features | Persistence + historical average | XGBoost regressor | Forecast, interval, features/explanation, model version |
| Energy forecast | Building/zone demand, 60-minute horizon | Lagged load, time features, weather, occupancy proxy if available | Persistence + same-hour average | XGBoost regressor | Forecast, interval, features/explanation, model version |

### 14.2 Optional later model

| Model | When justified | Not a day-one requirement |
|---|---|---|
| Isolation Forest environment anomaly detector | After sufficient multi-week/month sensor series exists | Yes |
| LSTM/TCN/Transformer | After baseline is established and enough data exists | Yes |
| Graph neural traffic model | After multiple well-connected segments and verified topology/time-series data exist | Yes |
| Reinforcement learning | Only after reliable simulator calibration and safety-aware objective are established | Yes |

### 14.3 ML non-negotiables

- Use a chronological train/validation/test split.
- Prevent temporal leakage.
- Compare every model against a simple baseline.
- Record data version, features, metrics, seed, parameters, and model artifact.
- Use MAE and RMSE at minimum; use sMAPE/MAPE where valid.
- Do not report classification accuracy for regression forecasting.
- Do not claim a synthetic-data model has demonstrated real-world local performance.
- Explain predictions with SHAP or model-native feature attribution where practical.

---

## 15. Simulation scope

### 15.1 Traffic

SUMO is the behavioral traffic model. TraCI is used from Python to start runs, query network/vehicle state, apply scenario parameters, and collect KPIs.

The MVP must contain:

- One baseline scenario.
- At least one intervention scenario.
- Identical seed/controlled inputs for fair baseline-versus-intervention comparison.
- Stored scenario input, configuration, seed, output, and KPI summary.

### 15.2 First intervention candidates

Choose **one** initially:

1. Adjust signal phase timing at Viman Nagar Chowk.
2. Restrict a turning movement in the simulated network.
3. Reroute selected demand through an alternate segment.
4. Introduce a peak-demand surge and test an operational response.

### 15.3 Required simulation KPIs

- Average travel time.
- Average delay.
- Queue length.
- Average speed.
- Throughput/vehicles completed.
- Optional estimated emissions, only if configured and documented.

### 15.4 Energy

The MVP does not claim a building-physics simulation. Energy input is either:

- permitted meter data;
- replayed benchmark data; or
- a transparent synthetic load generator.

EnergyPlus/Modelica is a future enhancement after obtaining building geometry, occupancy, HVAC, and equipment assumptions.

---

## 16. UI/UX context

### 16.1 Main user experience

The interface is an **operator/researcher dashboard**, not a public navigation application.

The user must be able to:

1. See the selected corridor on a 2D map.
2. Inspect current road/intersection/building/sensor state.
3. Identify whether data is live, replayed, simulated, or predicted.
4. View traffic and energy forecasts.
5. Read the reason behind an alert/recommendation.
6. Select and run a what-if scenario.
7. Compare baseline and intervention KPIs.
8. Export or cite an experiment/scenario run.

### 16.2 Required UI views

- Corridor operational map.
- Asset/entity detail panel.
- Traffic trend and forecast view.
- Energy trend and forecast view.
- Environmental status view.
- Alerts and recommendations view.
- Scenario configuration and comparison view.
- Data/model provenance details.

### 16.3 Visual rules

- Do not use red/green color alone to convey critical meaning.
- Show legends for all map layers.
- Use distinct badges for `LIVE`, `REPLAY`, `SIMULATION`, and `PREDICTED`.
- Label scenario output explicitly as simulated.
- Show measurement/forecast timestamp and freshness.
- Show units for speed, time, energy, AQI, and confidence intervals.
- Avoid a 3D view until the 2D analytical workflow is complete.

### 16.4 Optional 3D view

CesiumJS can later render a 3D view using open 3D data or Google Photorealistic 3D Tiles. The 3D view may display custom overlays such as vehicles, roads, sensors, congestion, temperature, energy state, and scenario results.

It is optional because it must not block core data, simulation, ML, or evaluation work.

If Google Photorealistic 3D Tiles are used:

- Billing account, API key, usage limits, and visible attribution are required.
- Tiles are for visualization only.
- Do not extract geodata, use the imagery for ML/object detection, or operate offline in violation of policy.

Resources: [Google Photorealistic 3D Tiles](https://developers.google.com/maps/documentation/tile/3d-tiles) · [Google Map Tiles policies](https://developers.google.com/maps/documentation/tile/policies) · [CesiumJS](https://cesium.com/platform/cesiumjs/)

---

## 17. Security, privacy, and ethics

### 17.1 Data boundaries

Allowed data:

- Aggregate traffic counts and speeds.
- Public/approved road geometry.
- Weather and AQI measurements.
- Aggregate/synthetic energy values.
- Simulated vehicle states.
- Anonymous entity IDs.

Disallowed data:

- CCTV footage.
- Facial data.
- Number plates.
- Individual GPS traces.
- Personal travel histories.
- Personal energy consumption records.
- Any sensitive data without documented permission and safeguards.

### 17.2 Minimum security requirements

- Store credentials in environment variables, not Git.
- Use application authentication for the dashboard/API.
- Use MQTT authentication; enable TLS if any real network-connected device is used.
- Restrict database credentials and rotate secrets when exposed.
- Log system events without logging secret values.
- Keep an audit field for data source and scenario/model version.

### 17.3 Ethical statement

The platform is a research prototype for decision support. It must not be presented as an authority that autonomously controls public infrastructure or makes decisions affecting people without human review.

---

## 18. Success criteria

### 18.1 Functional minimum

The system is successful when it can:

1. Display the exact selected Viman Nagar–Somnath Nagar study area.
2. Register roads, intersections, sensors, and one energy entity.
3. Ingest simulation/replay data via MQTT.
4. Validate, transform, store, and expose canonical observations.
5. Update current twin state and retain historical observations.
6. Show current traffic state and at least one forecast overlay.
7. Run a SUMO baseline and intervention scenario.
8. Compare and display travel time/delay/queue KPI differences.
9. Train/evaluate traffic and energy forecasting models against baselines.
10. Generate at least one traceable rule-based recommendation.
11. Distinguish all data provenance classes in UI/API.
12. Run reproducibly through Docker Compose.

### 18.2 Research minimum

The research output must include:

- Clear study-area boundary and assumptions.
- Dataset catalog and license records.
- Model training/evaluation protocol.
- Baseline comparison.
- End-to-end latency measurement.
- Data-completeness assessment.
- Scenario KPI comparison.
- Limitations, including simulation-to-real transfer limitations.
- Reproducible environment or detailed execution instructions.

---

## 19. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Dataset does not match Viman Nagar | Weak local-validity claim | Clearly separate Pune dataset training from Viman Nagar simulation; later collect small local observations |
| No campus/building meter data | Energy model becomes synthetic/benchmark-based | Label data honestly; use synthetic/replay mode; request permitted aggregate data later |
| SUMO network complexity grows | Slow/brittle simulation | Freeze a 2-junction network first; expand only after baseline works |
| ML model does not beat persistence baseline | Weak predictive result | Report honestly; improve features/data before adding complex models |
| Google 3D costs/terms interfere | Presentation dependency | Keep MapLibre 2D as default/fallback |
| Scope expansion | Delayed core system | Follow hard boundaries and approval process |
| Data quality issues | Incorrect forecast/alerts | Validate schema, time, range, duplicates, and missingness; expose quality scores |
| Misleading UI | Loss of research integrity | Enforce provenance labels and scenario separation |

---

## 20. Reference resources

### Digital twin and smart-city frameworks

- [FIWARE Smart Data Models](https://smart-data-models.github.io/data-models/)
- [NGSI-LD](https://ngsi-ld.org/)
- [FIWARE Digital Twins resources](https://www.fiware.org/wp-content/uploads/FF_PositionPaper_FIWARE4DigitalTwins.pdf)
- [Eclipse Ditto](https://eclipse.dev/ditto/)
- [Snap4City](https://www.snap4city.org/)
- [Azure Digital Twins documentation](https://learn.microsoft.com/en-us/azure/digital-twins/)

### Geospatial and urban-data standards

- [OpenStreetMap](https://www.openstreetmap.org/)
- [OSMnx](https://github.com/gboeing/osmnx)
- [OGC CityGML](https://www.ogc.org/standards/citygml/)
- [OGC SensorThings API](https://www.ogc.org/standards/sensorthings/)
- [W3C Web of Things Architecture](https://www.w3.org/TR/wot-architecture11/)

### Traffic simulation

- [Eclipse SUMO](https://eclipse.dev/sumo/)
- [SUMO documentation](https://sumo.dlr.de/docs/)
- [SUMO TraCI documentation](https://sumo.dlr.de/docs/TraCI.html)
- [SUMO traffic-light tutorial](https://sumo.dlr.de/docs/Tutorials/TraCI4Traffic_Lights.html)

### AI/ML

- [XGBoost documentation](https://xgboost.readthedocs.io/)
- [MLflow](https://mlflow.org/)
- [SHAP](https://shap.readthedocs.io/)
- [DCRNN repository](https://github.com/liyaguang/DCRNN) — advanced traffic benchmark/reference, not an MVP dependency
- [Microsoft StemGNN](https://github.com/microsoft/StemGNN) — advanced multivariate time-series reference, not an MVP dependency

### Platform engineering

- [FastAPI](https://fastapi.tiangolo.com/)
- [Eclipse Mosquitto](https://mosquitto.org/)
- [PostgreSQL](https://www.postgresql.org/)
- [TimescaleDB](https://www.timescale.com/)
- [PostGIS](https://postgis.net/)
- [MinIO](https://min.io/)
- [Docker Compose](https://docs.docker.com/compose/)
- [GitHub Actions](https://docs.github.com/actions)

### Pune and local context

- [Pune Smart City](https://www.punesmartcity.in/)
- [Pune Smart City ATMS document](https://www.punesmartcity.in/assets/PANCITY/Adaptive%20Traffic%20Management%20System.pdf)
- [Pune Smart City / Government datasets](https://smartcities.data.gov.in/cities/Pune)
- [Pune Corporation Open Data Portal](https://opendata.pmc.gov.in/)
- [OpenCity Pune data catalog](https://data.opencity.in/dataset/?groups=pune)
- [VIT Pune contact/campus locations](https://www.vit.edu/contact/)

---

## 21. Required reading order for agents

Before development begins, every contributor must read:

1. This file: `PROJECT_CONTEXT.md`.
2. `PRD.md` when created.
3. `TECHNICAL_ARCHITECTURE.md` when created.
4. `DATA_AND_ML_PLAN.md` when created.
5. `UI_UX_SPEC.md` when created, if working on frontend/design.
6. `ROADMAP.md` and `DELIVERABLES.md` when created.

Agents must not change the study area, core stack, canonical schema, provenance rules, or scope boundaries without a written decision update.

---

## 22. Immediate next documents

After approving this context, create documents in this order:

1. `PRD.md` — features, users, user stories, acceptance criteria.
2. `TECHNICAL_ARCHITECTURE.md` — components, data flow, APIs, modules, deployment.
3. `DATA_AND_ML_PLAN.md` — data catalog, required fields, datasets, model training/evaluation plan.
4. `UI_UX_SPEC.md` — screen inventory, UX flows, design system, map behavior, scenario UX.
5. `ROADMAP.md` — execution phases, dependencies, milestones.
6. `DELIVERABLES.md` — module outputs and definition of done.

---

## 23. Final project statement

> NagarRoad Twin is a corridor-scale, research-oriented smart-city digital twin for the Viman Nagar–Somnath Nagar area of Pune. It uses a lightweight, standards-aware architecture to integrate simulated, replayed, and optionally live urban observations; maintain twin state; forecast traffic and energy conditions; simulate traffic interventions; and present explainable recommendations to human users. It is not a citywide deployment, not an autonomous control system, and not a claim of direct access to Pune’s operational traffic infrastructure.
