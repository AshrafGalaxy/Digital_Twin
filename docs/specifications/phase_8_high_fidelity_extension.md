# Phase 8 — Functional High-Fidelity Urban Digital Twin Extension
## Product Map, Spatial Twin Plan, and Research-Grade Expansion

> **Document status:** Proposed post-MVP extension roadmap  
> **Applies after:** MVP Phases 0–7 completion  
> **Pilot geography:** Viman Nagar Chowk ↔ Somnath Nagar Chowk corridor, Pune  
> **Goal:** Transform the completed functional MVP into a visually high-fidelity, spatially synchronized, research-grade urban digital-twin proof of concept.  
> **Core principle:** High-fidelity visuals must be synchronized with the same entities, simulation state, forecasts, and provenance rules as the functional twin. Visual realism alone is not a digital twin.

---

## 1. Purpose

The MVP has established the functional foundation:

- State management and provenance separation.
- Traffic and energy forecasting.
- SUMO-based scenario simulation.
- Human-governed advisory workflow.
- 2D MapLibre dashboard.
- APIs, tests, documentation, and evaluation artifacts.

This extension plan defines the next product level:

> A **functional, high-fidelity visual urban digital twin** in which the virtual city, roads, intersections, signal states, vehicles, sensors, buildings, predictions, scenario outputs, and recommendations refer to one shared spatial and temporal model.

This is not a plan to add decorative 3D. It is a plan to make the spatial representation a first-class interface to the existing digital twin.

---

## 2. Target outcome

### 2.1 Final proof-of-concept statement

> The platform provides a high-fidelity, geospatially aligned digital twin of the Viman Nagar–Somnath Nagar corridor. Authorized users can observe a virtual 3D representation of the corridor; view traffic signals, road approaches, buildings, sensors, simulated vehicle movement, forecasts, energy state, environmental context, and what-if scenarios; and inspect the data/model/simulation evidence behind every rendered state.

### 2.2 What “functional high-fidelity” means

The proof of concept must combine both dimensions:

| Dimension | Required meaning |
|---|---|
| Functional fidelity | State ingestion, forecasting, simulation, recommendations, scenario KPIs, provenance, and evidence workflow work end to end |
| Spatial fidelity | Roads, intersections, approaches, lanes, signals, buildings, sensors, and overlays align to common real-world coordinates |
| Temporal fidelity | Vehicle/signal/forecast state changes are tied to source timestamps or simulation clock |
| Visual fidelity | Buildings, terrain/context, roads, vehicles, signals, overlays, and camera views make the corridor understandable and compelling |
| Governance fidelity | The system clearly distinguishes live/replay/simulation/predicted data and never implies autonomous public control |

### 2.3 What it does not mean

The following must not be claimed without official data/partnership:

- Survey-grade GIS accuracy.
- BIM-grade building geometry.
- Official PMC/ATMS signal-controller configuration.
- Live vehicle tracking.
- Actual real-world performance of simulated interventions.
- Whole-city digital-twin coverage.
- Autonomous traffic management.

---

## 3. Current MVP baseline

The extension assumes the following MVP capabilities are complete:

| Area | MVP capability | Extension usage |
|---|---|---|
| Twin state | Observed/replay/simulation/predicted state separated | Supplies 3D overlays and entity state |
| Backend | FastAPI, REST, WebSocket, canonical entities | Supplies spatial/temporal 3D data stream |
| Storage | Postgres/TimescaleDB/PostGIS | Authoritative registry, geometry, state, history |
| Traffic ML | XGBoost 15-minute traffic forecast | Renders predicted corridor/segment conditions |
| Energy ML | XGBoost 60-minute demand forecast | Renders building/zone energy state |
| Simulation | SUMO + TraCI baseline/intervention scenarios | Supplies lane, vehicle, queue, signal, KPI stream |
| Governance | Rule-based advisories + review state | Adds evidence-linked 3D annotations |
| 2D UI | MapLibre operations dashboard | Remains primary operational fallback and analytical view |
| Provenance | `LIVE`, `REPLAY`, `SIMULATION`, `PREDICTED` | Must appear in 3D view identically |

---

## 4. Product-level extension map

```text
Completed MVP: Functional 2D corridor twin
├── Twin state and data pipeline
├── Forecasting and recommendations
├── SUMO scenarios
├── 2D operations dashboard
└── Evaluation/reproducibility baseline

Phase 8A: Spatial fidelity foundation
├── Common coordinate/reference system
├── PostGIS ↔ SUMO ↔ 3D entity mapping
├── Lane/approach/turn/signal registry
├── Building/energy zone registry
└── Sensor/environment georegistry

Phase 8B: High-fidelity 3D corridor twin
├── CesiumJS viewer
├── 3D terrain/building/road context
├── Dynamic vehicles from SUMO
├── Signal state visualization
├── Sensor, traffic, energy, AQI overlays
└── Scenario playback/time controls

Phase 8C: Trustworthy AI and research intelligence
├── Conformal or quantile uncertainty intervals
├── Per-prediction SHAP explanations
├── Environmental anomaly engine
├── Simulation calibration and local data checks
└── Multi-objective scenario evaluation

Phase 8D: Interoperability and operational growth
├── FIWARE/NGSI-LD adapter
├── Real permitted APIs/sensors
├── Multi-corridor management
├── Role/audit/governance enhancement
└── Institutional/ICCC integration subject to agreement
```

---

## 5. Phase 8A — Spatial fidelity foundation

### 5.1 Goal

Create one versioned spatial registry so every visible object in the 2D map, 3D viewer, SUMO simulation, database, forecast, and scenario belongs to the same real-world entity and coordinate system.

### 5.2 Why this comes before 3D rendering

Without a shared spatial registry, the 3D view becomes decorative:

- SUMO lanes may not match displayed roads.
- Vehicles may visually drift or travel on incorrect geometry.
- Signals may not correspond to actual junction approaches.
- Sensor markers may not correspond to their modeled segment.
- Forecast overlays may attach to the wrong road/building.

The spatial registry is the technical basis for a credible virtual city.

### 5.3 Required spatial entity registry

| Entity | Required spatial fields | Required relationships |
|---|---|---|
| Study area | Boundary polygon, CRS, version | Contains all pilot entities |
| Road segment | PostGIS line geometry, direction, length, road class | Connected to intersections, SUMO edges, traffic states |
| Intersection | Point geometry, junction boundary/approach geometry | Connected to segments, signals, SUMO junction |
| Lane | Centerline/shape, direction, lane index, stop line | Maps to SUMO lane and approach/signal group |
| Movement/turn | From lane, to lane, turn geometry, priority | Maps to SUMO connection/phase |
| Signal controller | Point/reference, signal groups, phase plan/version | Controls movements; maps to SUMO traffic light |
| Signal group | Signal head/approach/movement relation | Maps to phase state/color |
| Traffic sensor | Point/ref, metric, observed segment/lane | Maps to traffic entity/observation stream |
| Building/energy zone | Footprint, height/source, entity ID | Maps to energy state/forecast |
| Environment station | Point geometry, station metadata | Maps to AQI/weather observations |
| Scenario annotation | Geometry/reference, scenario run ID | Maps to simulation output/recommendation |

### 5.4 Mapping tables

Create versioned mapping tables or equivalent records:

```text
road_segment_sumo_edge_map
sumo_lane_spatial_map
intersection_sumo_junction_map
signal_controller_sumo_tls_map
signal_group_movement_map
sensor_entity_map
building_energy_zone_map
scenario_geometry_map
```

### 5.5 Spatial reference rules

- Store authoritative platform geometry in WGS84 (`EPSG:4326`) for API/GeoJSON interoperability.
- Use projected/local coordinates only where simulation/rendering calculations require them; document transformations.
- Every geometry-bearing entity includes `geometryVersion`.
- Every SUMO network includes `networkVersion`.
- A scenario run must store both geometry/network version references.
- Do not manually copy coordinates between files without a mapping/source record.

### 5.6 Spatial validation tasks

| Check | Acceptance evidence |
|---|---|
| OSM road segments align to PostGIS geometry | Map comparison/screenshot + query validation |
| SUMO edges map to road segments | Mapping coverage report |
| SUMO lanes map to lane/approach geometry | Sample lane visual validation |
| SUMO junctions map to intersections | Junction mapping report |
| Traffic lights map to signal controllers/groups | Signal registry report |
| Building footprint maps to energy entity | 3D/2D entity selection test |
| Sensors map to correct segment/lane/source | API + map selection test |

### 5.7 Deliverables

- `spatial_registry_v1` database/schema migration.
- Versioned corridor geometry package.
- SUMO-to-PostGIS mapping export.
- Signal/junction/approach registry.
- Building/energy-zone registry.
- Mapping validation report.
- Architecture/data-flow update showing spatial identity path.

---

## 6. Phase 8B — High-fidelity 3D corridor twin

### 6.1 Goal

Build a CesiumJS-based 3D spatial interface that renders the same twin entities and state used by the existing 2D operational dashboard.

### 6.2 Recommended rendering architecture

```text
Authoritative twin backend
FastAPI + PostgreSQL/PostGIS + TimescaleDB
        │
        ├── REST: static geometry, entities, history, forecast, scenario metadata
        ├── WebSocket: current state, signal state, vehicle stream, alerts, progress
        └── Object storage: 3D assets, scenario playback files, optional 3D Tiles
                │
                ▼
CesiumJS 3D viewer
        ├── Terrain / basemap / building context
        ├── Roads, lanes, intersections, signal groups
        ├── Dynamic SUMO vehicles
        ├── Traffic signals and phases
        ├── Sensors and environmental stations
        ├── Energy building overlays
        ├── Forecast/congestion/queue overlays
        ├── Scenario-result annotations
        └── Provenance / timeline / inspector UI
```

### 6.3 Viewer selection

**Primary recommendation: CesiumJS.**

Reasons:

- Native support for 3D geospatial coordinates and terrain.
- Strong support for 3D Tiles.
- Dynamic time-based entities and animation clocks.
- Efficient rendering of vehicles/markers/polylines.
- Compatible with custom data overlays and optional Google Photorealistic 3D Tiles.
- Suitable for an urban corridor/city-scale growth path.

**Keep MapLibre GL JS** for the 2D operations dashboard. It remains the primary analytical interface and fallback when 3D is unavailable.

### 6.4 3D base context options

| Option | Use | Benefits | Limits | Decision |
|---|---|---|---|---|
| OSM building extrusions | First 3D iteration | Free, controllable, project-owned geometry | Less photorealistic; heights may be missing | Required starting point |
| Custom GeoJSON/3D Tiles | Curated pilot assets | Controlled/highly aligned | Requires asset preparation | Recommended after initial extrusion |
| Open terrain/elevation | Corridor visual context | Better elevation/camera context | Coverage/quality varies | Optional |
| Google Photorealistic 3D Tiles | Premium visual presentation | Realistic building/terrain context | Billing, attribution, use restrictions | Optional, not core |
| Official GIS/BIM/LiDAR | Municipal-grade accuracy | Highest fidelity | Requires partnership/license | Future only |

### 6.5 Required 3D scene layers

| Layer | Visual representation | Data source | Required? |
|---|---|---|---:|
| Terrain/base context | Terrain/neutral ground | Cesium base/approved terrain | Should |
| Buildings | Extruded footprints or 3D tiles | OSM/custom data | Yes |
| Roads | Polylines/surfaces | PostGIS/OSM/SUMO mapping | Yes |
| Lanes/approaches | Narrow line/surface overlays | Spatial lane registry | Yes for key junctions |
| Intersections | Junction surfaces/nodes | PostGIS/SUMO mapping | Yes |
| Traffic signals | Signal-head/controller entities | Signal registry + TraCI state | Yes |
| Vehicles | Instanced 3D models/billboards | SUMO TraCI vehicle stream | Yes |
| Queues | Lane-colored/vehicle-density overlay | SUMO queue/state | Should |
| Traffic congestion | Road color/pattern overlay | Twin state + forecast | Yes |
| Sensors | Small informative markers | Sensor registry | Yes |
| Buildings/energy | Building tint/label/roof marker | Energy entity + forecast | Yes |
| Environment | Station markers/heat layer/context | AQI/weather source | Should |
| Recommendations | Advisory markers/annotations | Rule engine | Should |
| Scenario result | Overlay/annotation/timeline | Scenario run artifacts | Yes |

---

## 7. Dynamic traffic signal twin

### 7.1 Goal

Represent signals as actual digital entities synchronized to SUMO simulation phases.

### 7.2 Required signal model

```json
{
  "id": "urn:ngsi-ld:TrafficSignalController:viman-nagar-001",
  "type": "TrafficSignalController",
  "intersectionId": "urn:ngsi-ld:Intersection:viman-nagar-chowk",
  "location": {"type": "Point", "coordinates": [0, 0]},
  "networkVersion": "network-v1",
  "signalGroups": [
    {
      "id": "sg-northbound-through",
      "movementId": "northbound-through",
      "sumoLinkIndex": 0,
      "state": "red"
    }
  ],
  "phase": {
    "phaseId": "phase-2",
    "remainingSeconds": 18,
    "sourceMode": "simulation"
  }
}
```

### 7.3 Signal visualization requirements

- Render a simple but recognizable 3D signal head or directional signal icon.
- Show red/amber/green state based on TraCI signal group state.
- Associate each signal group with its approach/movement.
- Display phase ID and remaining time only in inspector/advanced mode unless it improves user understanding.
- Label all state `SIMULATION` unless real authorized signal data exists.
- Never visually imply that the platform controls a real Pune signal.

### 7.4 Signal scenario visualization

When comparing baseline vs intervention:

- Allow toggle between baseline/intervention signal plan.
- Show phase-duration/offset change as scenario metadata.
- Animate only the simulated replay, not a fictional real-time control feed.
- Link signal configuration to scenario KPI results.

---

## 8. Dynamic vehicle-stream module

### 8.1 Goal

Render moving vehicles that follow actual simulated lanes and simulation time, making traffic flow and queues visible in the virtual corridor.

### 8.2 Vehicle data pipeline

```text
SUMO / TraCI step
        ↓
Vehicle state query
(vehicle ID, type, lane ID, position, speed, angle, route)
        ↓
SUMO lane → spatial lane mapping
        ↓
Coordinate transformation / interpolation
        ↓
Backend stream payload
        ↓
WebSocket or time-indexed playback endpoint
        ↓
CesiumJS entity/instanced model update
```

### 8.3 Minimum vehicle event contract

```json
{
  "simulationTimeSeconds": 120.0,
  "sourceMode": "simulation",
  "scenarioRunId": "scenario-run-001",
  "vehicleId": "veh-123",
  "vehicleClass": "car",
  "sumoLaneId": "edge-001_0",
  "spatialLaneId": "urn:ngsi-ld:Lane:segment-001-0",
  "longitude": 73.914,
  "latitude": 18.567,
  "altitude": 0,
  "headingDegrees": 92.3,
  "speedKph": 21.4,
  "queueState": false
}
```

### 8.4 Vehicle rendering rules

- Vehicle position must derive from SUMO lane/coordinate data, not random animation.
- Vehicle animation uses simulation clock/timeline.
- Use simple lightweight models or colored low-poly assets initially.
- Distinguish vehicle classes only if SUMO provides them and the distinction adds value.
- Use instancing/billboards for performance where possible.
- Vehicle tooltip/inspector must state `SIMULATION` and scenario run.
- Do not expose individual-real-world tracking language or personal identifiers.

### 8.5 Vehicle classes

Initial optional classes:

| Class | Visual | Use |
|---|---|---|
| Car | Compact neutral 3D vehicle | Main traffic flow |
| Bus | Larger rectangular vehicle | Public-transport context if modeled |
| Truck | Larger freight vehicle | Heterogeneous traffic context |
| Two-wheeler | Small simplified icon/model | Indian traffic context, only if simulation supports it |

### 8.6 Performance requirements

- Begin with capped vehicle count and update frequency suitable for browser performance.
- Use level of detail: close vehicles use models, distant vehicles use simplified markers/billboards.
- Do not transmit unnecessary historical vehicle paths each frame.
- Support pause, resume, replay-speed control, and reset to simulation time.

---

## 9. Buildings, energy, and urban context

### 9.1 Building model levels

| Level | Geometry | Data source | Claim allowed |
|---|---|---|---|
| B1 | Footprint extrusion | OSM footprint + height tag/estimate | Approximate contextual building model |
| B2 | Curated simple 3D model | Custom GeoJSON/3D Tiles | Pilot-focused representation |
| B3 | Photorealistic city mesh | Google/other licensed 3D tiles | Visual context only |
| B4 | Official BIM/GIS/LiDAR | Institution/municipality data | Subject to source accuracy/license |

### 9.2 MVP extension target

Target **B1 + selected B2**:

- Extrude available OSM footprints.
- Use OSM `building:levels`/height tags where present.
- If estimated height is needed, tag it as `estimated` in metadata.
- Create one highlighted energy-zone building/entity.
- Allow selection to view energy state, forecast, source type, and advisory.

### 9.3 Energy visual encoding

| Energy state | 3D treatment |
|---|---|
| Normal load | Neutral building tint or small roof icon |
| Rising demand | Amber edge/roof overlay + label |
| Peak forecast | Red/amber non-glowing overlay + `PREDICTED` badge |
| Synthetic/replay source | Persistent provenance label in inspector/panel |
| Unknown/stale | Neutral gray/striped overlay |

Do not color every building. Only color the explicit modeled energy entity/entities.

---

## 10. High-fidelity traffic, forecast, and scenario overlays

### 10.1 Road congestion overlay

Render on roads/lane groups using twin state:

| State | Visual rule |
|---|---|
| Observed/replayed/simulated current state | Solid traffic color based on congestion/speed |
| Predicted 15-minute state | Dashed/offset blue overlay; visible horizon label |
| Scenario state | Purple/hatched overlay; scenario run reference |
| Stale/unknown | Gray dashed surface/line; last update shown |

### 10.2 Queue overlay

- Visualize queue length by lane/approach as a semi-transparent segment, stacked marker, or vehicle density treatment.
- Show exact count/estimate in inspector.
- Mark source as `SIMULATION` for SUMO queues.

### 10.3 Forecast overlay

A forecast must always display:

```text
PREDICTED
Target time / horizon
Model version
Input completeness
Interval or confidence representation
Underlying source mode where needed
```

### 10.4 Scenario playback mode

Provide a timeline with:

```text
Baseline / Intervention switch
Play / Pause
Simulation time
Replay speed: 1×, 2×, 5×
Reset
Selected KPI overlay
Scenario metadata
```

The timeline is a **simulation playback control**, not a real-time operational control.

---

## 11. 3D user experience and interface structure

### 11.1 Primary role of 3D view

The 3D view supports:

- Executive/municipal presentation.
- Planning explanation.
- Spatial scenario playback.
- Signal/queue/vehicle-flow understanding.
- Public-facing demo later, only after governance review.

The 2D MapLibre Operations view remains the preferred interface for dense analytics, filtering, detailed charts, tables, and accessibility fallback.

### 11.2 3D viewer layout

```text
┌─────────────────────────────────────────────────────────────────────┐
│ Header: Pilot · Source mode · Simulation timeline · System status    │
├───────────────┬──────────────────────────────────────┬──────────────┤
│ Layer panel   │ Cesium 3D corridor viewer             │ Inspector    │
│ - traffic     │ Roads/buildings/signals/vehicles       │ Entity state │
│ - signals     │ Forecast/scenario overlays             │ Forecast     │
│ - energy      │ Camera controls/timeline               │ Provenance   │
│ - environment │                                       │ Evidence     │
├───────────────┴──────────────────────────────────────┴──────────────┤
│ Scenario KPI/forecast/recommendation tray                             │
└─────────────────────────────────────────────────────────────────────┘
```

### 11.3 Required controls

- Home/reset camera.
- Select entity.
- Toggle layers.
- Baseline/intervention switch.
- Simulation timeline/playback speed.
- Time/filter selection.
- 2D/3D switch or return link.
- Provenance legend.
- Scenario metadata drawer.

### 11.4 Camera presets

Provide:

- Corridor overview.
- Viman Nagar junction view.
- Somnath Nagar junction view.
- Selected entity focus.
- Scenario comparison view.

Avoid free-camera default disorientation. Always offer a home view.

---

## 12. High-fidelity research extensions

### 12.1 Uncertainty-aware forecasting

#### Goal

Make traffic and energy forecasts more appropriate for governance by showing calibrated uncertainty.

#### Recommended implementation

| Step | Deliverable |
|---|---|
| 1 | Select quantile XGBoost or conformal prediction method |
| 2 | Keep a calibration split separate from final test set |
| 3 | Produce 90% and/or 95% prediction intervals |
| 4 | Evaluate coverage probability and interval width |
| 5 | Render interval in 2D/3D inspector and charts |
| 6 | Reduce recommendation confidence when input completeness/interval quality is poor |

#### Research contribution

> Provenance-aware, uncertainty-calibrated traffic/energy forecasts integrated into a spatially synchronized urban digital twin.

### 12.2 Per-prediction SHAP explanations

#### Goal

Explain why a specific forecast/recommendation was generated.

#### Deliverables

- SHAP calculation service/artifact for selected forecast.
- Waterfall or ranked contribution visualization.
- Plain-language explanation layer.
- Link from recommendation to explanation.
- Computation-performance strategy: on-demand/cached, not every frame.

#### Example UX

```text
Why is congestion predicted to increase?
+ Recent 5-minute speed decline
+ Peak-period time pattern
+ Elevated upstream demand
− Lower expected precipitation impact

Model: traffic-xgb-v2
Input completeness: 93%
```

### 12.3 Environmental anomaly engine

#### Goal

Add a third urban domain without pretending to have local regulatory-grade sensors.

#### Deliverables

- Weather/AQI ingest/replay pipeline.
- Station metadata and geographic caveat.
- Rolling Z-score baseline.
- Optional Isolation Forest after adequate history exists.
- Anomaly record, threshold/explanation, map/3D marker.
- False-positive review/evaluation process.

### 12.4 Simulation calibration and local observation protocol

#### Goal

Reduce the gap between generic/other-Pune data and the pilot corridor.

#### Deliverables

- Aggregate manual traffic-count protocol.
- Observation time windows and weather/event note template.
- No-camera/no-PII collection procedure.
- Demand calibration process for SUMO.
- Qualitative/quantitative comparison of simulation and local aggregate counts.
- Updated limitation statement.

### 12.5 Multi-objective scenario evaluation

#### Goal

Move beyond “reduce delay” to governance-relevant trade-offs.

#### Candidate objectives

- Average travel time.
- Queue length.
- Throughput.
- Estimated emissions if validly configured.
- Transit priority if modeled.
- Pedestrian wait/safety proxy if modeled.
- Energy/EV demand impact in later expansion.

#### Deliverable

A scenario comparison that explicitly shows trade-offs, not only the best metric.

---

## 13. Interoperability extension

### 13.1 Goal

Demonstrate that the platform can exchange context data with smart-city ecosystems rather than remaining a closed custom prototype.

### 13.2 FIWARE/NGSI-LD adapter

#### Deliverables

- Canonical entity → NGSI-LD transformation adapter.
- Outbound publisher to Orion-LD or compatible endpoint.
- Entity examples for road, traffic observation, building/energy, forecast, recommendation.
- Subscription/update demonstration.
- Schema/semantic mapping documentation.
- Docker Compose optional profile for Orion-LD.

### 13.3 Success criterion

The system can publish selected corridor context entities without changing its core state model or rewriting the existing API/database pipeline.

### 13.4 Do not do yet

- Do not replace the existing core twin state with a broker before adapter behavior is proven.
- Do not claim citywide interoperability solely because JSON resembles NGSI-LD.

---

## 14. Deployment and operational extension

### 14.1 Full container validation

The MVP must transition from fallback local persistence to verified multi-service operation.

#### Required services

```text
frontend
backend
worker/scheduler
mosquitto
postgres + timescaledb + postgis
minio
mlflow
sumo-worker
optional: cesium asset host/3D service
optional: orion-ld profile
```

#### Deliverables

- `docker compose up --build` proof.
- Data initialization/seed script.
- Health checks for services.
- Persistent volumes/backup instructions.
- Environment configuration guide.
- Clean-machine reproduction report.

### 14.2 Observability upgrade

Add incrementally:

1. Structured logs with correlation IDs.
2. Source freshness metrics.
3. Ingestion acceptance/rejection counters.
4. Model inference latency and failure count.
5. Scenario run duration/status.
6. Optional Prometheus/Grafana only after core metrics are exposed.

---

## 15. Full extension sequencing

### 15.1 Recommended order

```text
8A-1  Freeze and validate spatial registry
8A-2  Map PostGIS entities ↔ SUMO edges/lanes/junctions/signals
8A-3  Add signal/approach/movement registry
8A-4  Add building/energy-zone geometry registry

8B-1  Create CesiumJS viewer shell and 2D/3D navigation
8B-2  Render OSM building extrusions + roads + intersections
8B-3  Render sensor, energy, environment, and provenance overlays
8B-4  Stream/render SUMO signal states
8B-5  Stream/render SUMO vehicles on aligned lanes
8B-6  Add forecast and congestion overlays
8B-7  Add scenario playback/timeline/KPI tray

8C-1  Add conformal/quantile prediction intervals
8C-2  Add per-prediction SHAP explanation
8C-3  Add environmental threshold/anomaly module
8C-4  Perform local aggregate observation/calibration work
8C-5  Add multi-objective scenario comparison

8D-1  Verify full Docker multi-container deployment
8D-2  Add FIWARE/NGSI-LD adapter
8D-3  Add real permitted external sources
8D-4  Expand to another corridor only after pilot validation
```

### 15.2 Critical dependencies

| Extension | Depends on |
|---|---|
| Cesium 3D viewer | Spatial registry, stable API, static geometry |
| Moving vehicles | SUMO lane mapping, vehicle-state stream, timeline |
| Signal visualization | Signal/movement registry, TraCI phase state |
| Building energy overlays | Building/energy geometry mapping, energy forecast API |
| Scenario playback | Stored time-indexed scenario output, run metadata |
| Uncertainty UI | Calibrated interval method and evaluation |
| SHAP UI | Stable model/version + explanation artifacts |
| FIWARE adapter | Stable canonical entity model |
| Local calibration | Approved observation protocol/data source |

---

## 16. Product modules after extension

```text
Digital Twin-Enabled Smart City Analytics Platform
│
├── A. Core Twin Platform (completed MVP)
│   ├── Canonical entity/state model
│   ├── Ingestion + provenance + validation
│   ├── Current/history/forecast/scenario separation
│   ├── REST/WebSocket APIs
│   └── Governance advisory workflow
│
├── B. Mobility Twin (completed + extension)
│   ├── Road/intersection registry
│   ├── SUMO simulation
│   ├── Traffic forecast
│   ├── Signal/approach/lane twin
│   ├── Dynamic vehicle stream
│   └── Scenario playback
│
├── C. Energy Twin (completed + extension)
│   ├── Building/zone entity
│   ├── Energy forecast
│   ├── 3D building overlay
│   └── Future demand/energy scenario model
│
├── D. Environmental Context Twin (extension)
│   ├── Weather/AQI sources
│   ├── Threshold advisories
│   ├── Anomaly engine
│   └── Spatial context/heat overlays
│
├── E. 2D Operations Interface (completed MVP)
│   ├── MapLibre map
│   ├── Analytics/charts
│   ├── Scenario Studio
│   ├── Advisory Center
│   └── System health
│
├── F. 3D Spatial Interface (Phase 8)
│   ├── CesiumJS corridor view
│   ├── Buildings/terrain/roads
│   ├── Signals/lanes/vehicles
│   ├── Forecast/scenario overlays
│   └── Timeline/camera/presentation controls
│
├── G. Trustworthy AI Layer (Phase 8)
│   ├── Prediction intervals
│   ├── SHAP explanations
│   ├── Data quality/freshness
│   └── Evidence-linked advisories
│
└── H. Interoperability & Growth (Phase 8+)
    ├── FIWARE/NGSI-LD adapter
    ├── Permitted live sources
    ├── Multi-corridor expansion
    └── Institutional integration subject to agreements
```

---

## 17. Research and novelty positioning

### 17.1 Strong contribution statement

> A spatially aligned, provenance-aware, uncertainty-aware, explainable urban corridor digital twin that synchronizes simulation, replay, and future live data; integrates mobility and representative energy analytics; renders lane/signal/vehicle behavior in a high-fidelity 3D interface; and supports human-governed scenario-based decision making under resource-constrained deployment conditions.

### 17.2 What is not novel by itself

- Showing a 3D map.
- Rendering moving vehicles.
- Using SUMO.
- Using XGBoost.
- Using CesiumJS.
- Building a dashboard.
- Connecting generic APIs.

### 17.3 What can be novel in combination

| Contribution dimension | Novelty potential |
|---|---|
| One synchronized entity identity across PostGIS, SUMO, ML, 2D, and 3D | High practical/research value |
| Provenance-aware mixing of replay, simulation, future live, and predicted state | Strong governance/research value |
| Lane/signal/vehicle spatial synchronization with explainable forecasts | Strong technical demonstration |
| Uncertainty-aware recommendation workflow for resource-constrained Indian corridor | Strong research positioning |
| Traffic + energy + environment under one small-footprint architecture | Medium to strong if evaluated rigorously |
| Local observation-assisted SUMO calibration | Stronger external validity |
| FIWARE adapter without replacing lightweight core | Good interoperability contribution |

### 17.4 Patent caution

A patent claim is not established by this roadmap. Any patent work requires prior-art search and professional legal advice. Potential patent directions must focus on a genuinely new technical method, such as a specific synchronization, calibration, uncertainty, or multi-domain decision method—not the general idea of a smart-city digital twin.

---

## 18. Extension acceptance criteria

### 18.1 Phase 8A complete when

- [ ] All primary corridor assets have versioned spatial identities.
- [ ] SUMO roads, lanes, junctions, and signals map to PostGIS/twin entities.
- [ ] Building/energy/sensor/environment entities have validated locations.
- [ ] Mapping coverage/validation report is complete.

### 18.2 Phase 8B complete when

- [ ] CesiumJS displays the corridor with aligned road/building/intersection context.
- [ ] 3D view uses same entity IDs and APIs as the 2D twin.
- [ ] SUMO vehicles move on mapped lane geometry with simulation timeline.
- [ ] Signal states render from TraCI simulation state.
- [ ] Traffic, forecast, energy, environment, and scenario overlays display provenance.
- [ ] Baseline/intervention scenario playback is available.
- [ ] 2D MapLibre workflow remains functional as fallback.

### 18.3 Phase 8C complete when

- [ ] Forecast intervals are generated and evaluated.
- [ ] Per-prediction explanation is accessible in UI.
- [ ] Environmental threshold/anomaly workflow is evaluated if added.
- [ ] Local calibration/observation evidence is documented if collected.
- [ ] Multi-objective scenario trade-offs are shown if implemented.

### 18.4 Phase 8D complete when

- [ ] Full multi-container deployment succeeds reproducibly.
- [ ] Optional FIWARE adapter publishes/consumes documented entities.
- [ ] Any live source has license/permission/provenance controls.
- [ ] Expansion maintains data quality, security, and provenance invariants.

---

## 19. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| 3D begins before spatial mapping is correct | Decorative/misaligned virtual city | Complete Phase 8A before Cesium vehicle rendering |
| Vehicle rendering overloads browser | Poor demo performance | Instancing, LOD, capped count, playback controls |
| OSM lacks lane/signal detail | Spatial mismatch | Curated manual registry; document assumptions |
| Google 3D cost/terms | Dependency/risk | Use OSM extrusions first; preserve 2D fallback |
| SUMO network not calibrated | Weak real-world claim | Label simulation; add aggregate local observations later |
| Too many extensions at once | Unfinished/fragile project | Follow sequencing; protect dependencies |
| 3D hides provenance | Misleading interface | Mandatory badge/inspector/legend in 3D |
| Complex AI adds weak value | Delays research | Add uncertainty/SHAP before deep models |

---

## 20. Immediate next actions

1. Audit the existing MVP’s corridor geometry, SUMO network, and entity IDs.
2. Define and implement the spatial registry/mapping tables.
3. Verify lane, junction, signal, and road mapping coverage.
4. Build a minimal CesiumJS route/viewer using the same backend asset APIs.
5. Render OSM building extrusions, road geometries, intersections, and sensor markers.
6. Add SUMO signal state stream and render signal groups.
7. Add SUMO vehicle-state stream and synchronized timeline playback.
8. Add congestion/forecast/energy overlays with provenance.
9. Add scenario baseline/intervention visual playback and KPI tray.
10. Add conformal/quantile intervals and per-prediction SHAP explanation after spatial layer works.

---

## 21. Final extension statement

> The next level of the project is a high-fidelity, functional 3D urban digital twin—not a cosmetic 3D map. It will be built on a shared spatial registry that binds real-world corridor geometry, SUMO lanes and signals, PostGIS entities, sensor locations, ML forecasts, scenario results, and governance advisories into one time-aware virtual environment. The completed MVP supplies the functional intelligence; Phase 8 supplies the spatial fidelity, visual clarity, uncertainty awareness, and interoperability needed to elevate the work into a research-grade smart-city digital-twin proof of concept.
