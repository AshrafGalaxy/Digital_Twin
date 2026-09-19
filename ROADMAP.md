# Roadmap
## Digital Twin-Enabled Smart City Analytics Platform

> **Document status:** Baseline implementation roadmap  
> **Companion documents:** `PROJECT_CONTEXT.md`, `PRD.md`, `TECHNICAL_ARCHITECTURE.md`, `DATA_AND_ML_PLAN.md`, `UI_UX_SPEC.md`  
> **Pilot study area:** Viman Nagar Chowk (Phoenix Mall) ↔ Somnath Nagar Chowk corridor, Pune  
> **Roadmap principle:** Complete a correct, evidence-backed pilot workflow before adding wider geography, advanced AI, production infrastructure, or optional 3D presentation features.

---

## 1. Purpose

This roadmap converts the product, data, architecture, and UX requirements into an implementation sequence.

It defines:

- What should be built first.
- Which modules depend on other modules.
- What agents/owners are responsible for each workstream.
- What evidence proves a phase is complete.
- Which work is MVP-critical versus deferred.
- How the pilot can progress from a reproducible prototype to a research-grade platform and, later, a city-scale governance platform.

This roadmap deliberately avoids a calendar deadline. It is dependency-driven. Teams may map phases to a semester, academic year, or funded development plan later without changing the technical sequence.

---

## 2. Roadmap overview

```text
Phase 0  Governance, scope, repository, and decisions
    ↓
Phase 1  Study area, GIS assets, data inventory, and contracts
    ↓
Phase 2  Core platform: database, APIs, MQTT, ingestion, twin state
    ↓
Phase 3  Replay/simulation streams and 2D operations dashboard
    ↓
Phase 4  SUMO network, scenario engine, and KPI comparison
    ↓
Phase 5  Traffic and energy ML forecasting
    ↓
Phase 6  Recommendations, governance UX, quality, and deployment
    ↓
Phase 7  Evaluation, research evidence, demo, and release
    ↓
Phase 8  Optional research-grade and scale extensions
```

---

## 3. Guiding rules

1. Do not build an advanced visual layer before the data/twin workflow works.
2. Do not train advanced models before a baseline and data-quality pipeline exist.
3. Do not expand geography before the selected two-junction pilot is stable.
4. Do not mix observed, replayed, predicted, or simulated data.
5. Do not claim live municipal integration without approved access and evidence.
6. Do not add Kafka, Kubernetes, context brokers, graph databases, GNNs, LLMs, blockchain, or physical control without a written architecture decision.
7. Every phase must produce an artifact that can be reviewed independently.
8. Every completed feature must update the relevant documentation.
9. The pilot is complete only when the full evidence chain works end to end.

---

## 4. Workstreams

The roadmap is organized across the following parallel workstreams.

| Workstream | Main responsibility |
|---|---|
| Product & governance | Scope, stakeholders, user requirements, advisory/safety boundaries |
| GIS & study area | Corridor boundary, OSM extraction, road/junction asset registry |
| Data engineering | Dataset manifests, ingestion, replay, validation, provenance, quality |
| Twin core & backend | Entity state, APIs, relationships, forecast/scenario persistence |
| Simulation | SUMO network, demand, baseline/intervention scenario runs, KPIs |
| ML & analytics | Features, baselines, XGBoost models, uncertainty, MLflow, explanations |
| UI/UX | Operations dashboard, analytics, Scenario Studio, recommendations, accessibility |
| Platform engineering | Docker, CI, security, health, logging, runbook |
| Research & delivery | Evaluation, figures, report/paper, demo, reproducibility evidence |

---

## 5. Phase 0 — Foundation, governance, and project setup

### 5.1 Objective

Freeze the product/pilot boundary, establish active documentation, initialize the repository, and define how decisions are made.

### 5.2 Dependencies

None.

### 5.3 Inputs

- `PROJECT_CONTEXT.md`
- `PRD.md`
- `TECHNICAL_ARCHITECTURE.md`
- `DATA_AND_ML_PLAN.md`
- `UI_UX_SPEC.md`
- Previous architecture/tech-stack research retained in `docs/reference/`

### 5.4 Tasks

| ID | Task | Owner/workstream | Output |
|---|---|---|---|
| P0-01 | Confirm pilot geography as Viman Nagar–Somnath Nagar corridor | Product + GIS | Pilot boundary decision record |
| P0-02 | Confirm no unapproved product name/branding is used | Product | Naming rule in README/project context |
| P0-03 | Create repository structure | Platform | Repository skeleton |
| P0-04 | Add active documentation set | Project lead | Root Markdown files present |
| P0-05 | Move historical research/planning files to `docs/reference/` | Project lead | Clean active/reference separation |
| P0-06 | Create issue labels and workstream labels | Project management | Backlog organization |
| P0-07 | Define branch/PR/test/documentation conventions | Platform | `CONTRIBUTING.md` or README section |
| P0-08 | Record initial architecture decisions | Architecture | Decision log/ADR index |
| P0-09 | Identify data sensitivity and prohibited-data boundary | Governance | Privacy/safety note |
| P0-10 | Define first demo story | Product + UX | Demo narrative draft |

### 5.5 Recommended repository structure

```text
project-root/
├── README.md
├── PROJECT_CONTEXT.md
├── PRD.md
├── TECHNICAL_ARCHITECTURE.md
├── DATA_AND_ML_PLAN.md
├── UI_UX_SPEC.md
├── ROADMAP.md
├── DELIVERABLES.md
├── docs/
│   ├── reference/
│   ├── decisions/
│   ├── diagrams/
│   └── reports/
├── frontend/
├── backend/
├── simulation/
├── ml/
├── data/
│   ├── raw/
│   ├── bronze/
│   ├── silver/
│   ├── gold/
│   ├── synthetic/
│   └── samples/
├── infrastructure/
├── scripts/
├── tests/
├── artifacts/
└── compose.yaml
```

### 5.6 Exit criteria

- [ ] Active documents are approved and available at repository root.
- [ ] Reference files are retained but clearly non-binding.
- [ ] Scope/non-goals/safety rules are understood by all contributors.
- [ ] Repository structure exists.
- [ ] No coding begins on features that conflict with the frozen pilot boundary.

---

## 6. Phase 1 — Study area, GIS foundation, and data inventory

### 6.1 Objective

Create the authoritative spatial model of the pilot corridor and document every dataset before it enters the system.

### 6.2 Dependencies

- Phase 0 complete.

### 6.3 Tasks

| ID | Task | Owner/workstream | Output |
|---|---|---|---|
| P1-01 | Draw/finalize exact study-area polygon | GIS | `study_area.geojson` |
| P1-02 | Record bounding box, source, capture date, coordinate system | GIS | Study-area metadata |
| P1-03 | Extract OSM roads, intersections, and available building data | GIS | Raw OSM extract |
| P1-04 | Validate/correct road direction, junctions, critical turns, lanes where known | GIS + simulation | Curated pilot network input |
| P1-05 | Define 8–15 initial road segments and 2 core intersections | GIS + product | Asset registry seed |
| P1-06 | Register 5–15 logical traffic-source/sensor points | Data + GIS | Sensor registry seed |
| P1-07 | Define one representative energy building/zone entity | Product + data | Energy asset record |
| P1-08 | Create dataset manifests for all planned sources | Data | Dataset manifests |
| P1-09 | Download/store documented raw/small sample sources | Data | Raw data inventory |
| P1-10 | Verify source licenses/attribution/limitations | Governance + data | License notes |
| P1-11 | Select initial traffic target and time interval | ML + data | Decision record |
| P1-12 | Select first scenario/intervention type | Product + simulation | Scenario decision record |

### 6.4 Mandatory decisions

Before Phase 2, decide:

| Decision | Recommended initial answer |
|---|---|
| Road-network extent | Two major junctions plus required connector/approach segments |
| Traffic target | Average speed if available; otherwise documented congestion index |
| Raw interval | Preserve source interval; use 5–15 minute modeling interval |
| Forecast horizon | Traffic: 15 minutes; energy: 60 minutes |
| First intervention | Signal timing adjustment or turn restriction |
| Energy source | Permitted aggregate data if available; otherwise replay/benchmark/synthetic with label |
| Environment source | Pune station data + weather source, labelled regional context |

### 6.5 Exit criteria

- [ ] Versioned study-area GeoJSON exists.
- [ ] Pilot assets are registered with stable IDs.
- [ ] Every planned source has a manifest, source URL, license/terms, and limitation note.
- [ ] Local/non-local/synthetic/benchmark classification is recorded.
- [ ] Initial traffic target/time interval/first scenario are fixed.

---

## 7. Phase 2 — Core platform, canonical contract, and twin state

### 7.1 Objective

Build the minimal reliable technical foundation: database, canonical schemas, ingestion, validation, twin-state projection, and APIs.

### 7.2 Dependencies

- Phase 1 complete.

### 7.3 Tasks

| ID | Task | Owner/workstream | Output |
|---|---|---|---|
| P2-01 | Create Docker Compose base services | Platform | Compose stack: Postgres, Mosquitto, backend |
| P2-02 | Enable TimescaleDB and PostGIS | Backend/platform | Database initialization |
| P2-03 | Create database migrations/schemas | Backend | Core, telemetry, forecast, scenario tables |
| P2-04 | Import study area and static entities into PostGIS | GIS + backend | Seeded database |
| P2-05 | Implement canonical Pydantic schemas | Backend/data | Typed event/entity contracts |
| P2-06 | Define MQTT topic convention | Data/backend | Topic documentation/configuration |
| P2-07 | Implement MQTT consumer | Backend/data | Ingestion module |
| P2-08 | Implement validation pipeline | Backend/data | Schema/time/range/duplicate checks |
| P2-09 | Implement current-state upsert + historical observation storage | Twin core | State projection pipeline |
| P2-10 | Implement basic REST APIs | Backend | Study area/assets/current/history APIs |
| P2-11 | Implement WebSocket state events | Backend | State update events |
| P2-12 | Add health/readiness endpoints | Platform/backend | `/health` endpoint |
| P2-13 | Add structured logging and basic error storage | Platform/backend | Ingestion error/audit logs |

### 7.4 Core acceptance flow

```text
Publish valid traffic event to MQTT
→ backend consumes it
→ event validates
→ historical record is stored
→ current state is updated
→ WebSocket event is emitted
→ API returns entity state/history with provenance
```

### 7.5 Exit criteria

- [ ] Docker Compose starts required core services.
- [ ] Static entities are visible/queryable from PostGIS/API.
- [ ] Valid event flows from MQTT to history/current state.
- [ ] Invalid event is rejected/recorded without corrupting state.
- [ ] API returns provenance, timestamps, units, and quality status.
- [ ] WebSocket emits state update.

---

## 8. Phase 3 — Replay/simulation streams and operations dashboard

### 8.1 Objective

Make the digital twin visible and demonstrable using replayed and simulated events before introducing ML or complex scenarios.

### 8.2 Dependencies

- Phase 2 complete.

### 8.3 Tasks

| ID | Task | Owner/workstream | Output |
|---|---|---|---|
| P3-01 | Build replay worker for historical CSV/API dumps | Data | Configurable replay publisher |
| P3-02 | Build initial synthetic traffic/energy publisher | Data/simulation | Synthetic event stream |
| P3-03 | Implement source mode/provenance tagging | Backend/data | `LIVE`, `REPLAY`, `SIMULATION` handling |
| P3-04 | Initialize React + TypeScript + Vite frontend | UI/platform | Frontend shell |
| P3-05 | Add MapLibre base map and study-area boundary | UI/GIS | Operations map |
| P3-06 | Render roads, intersections, sensors, energy entity | UI | Asset layers |
| P3-07 | Render current traffic state and legend | UI/backend | Traffic overlay |
| P3-08 | Implement entity detail drawer | UI | State/history/provenance detail |
| P3-09 | Add status bar: freshness, source mode, health | UI | Global status component |
| P3-10 | Add data-quality/stale states | UI/backend | Correct degraded-state UI |
| P3-11 | Add operations summary/alert placeholder | UI | Corridor summary panel |

### 8.4 Demonstration checkpoint

At the end of Phase 3, a reviewer must be able to:

1. Open the map.
2. See the correct study area and registered assets.
3. Start replay/simulation stream.
4. Observe road state updates.
5. Click an entity.
6. Read source mode, last update, quality, and history.
7. Confirm that the UI does not falsely claim simulated/replayed data is live.

### 8.5 Exit criteria

- [ ] Replay mode works end to end.
- [ ] Simulation mode works end to end.
- [ ] Operations map renders all mandatory layers.
- [ ] Entity detail shows current state/history/provenance.
- [ ] UI visibly differentiates replay and simulation.
- [ ] Stale/invalid conditions are understandable.

---

## 9. Phase 4 — SUMO network, scenario engine, and KPI comparison

### 9.1 Objective

Build the traffic behavioral model and safe scenario-comparison workflow.

### 9.2 Dependencies

- Phase 1 GIS/network assets complete.
- Phase 2 persistence/API foundation complete.
- Phase 3 operations dashboard available for result display.

### 9.3 Tasks

| ID | Task | Owner/workstream | Output |
|---|---|---|---|
| P4-01 | Convert/construct pilot corridor SUMO network | Simulation + GIS | Network files/version |
| P4-02 | Validate junction/road connectivity and traffic-light assumptions | Simulation | Validated network notes |
| P4-03 | Create baseline demand/routes | Simulation | Baseline scenario configuration |
| P4-04 | Configure first intervention template | Simulation + product | Intervention configuration |
| P4-05 | Build TraCI control/query wrapper | Simulation/backend | Scenario service interface |
| P4-06 | Implement scenario-run database records | Backend | Immutable run metadata |
| P4-07 | Implement baseline and intervention execution | Simulation | Run artifacts/KPI outputs |
| P4-08 | Compute travel time, delay, queue length, throughput | Simulation | KPI calculator |
| P4-09 | Store outputs/artifacts separately from observed state | Backend | Scenario persistence |
| P4-10 | Implement scenario REST/WebSocket progress APIs | Backend | Scenario API/events |
| P4-11 | Build Scenario Studio UI | UI | Template selector/progress/results |
| P4-12 | Build baseline-vs-intervention KPI comparison | UI | Comparison table/chart |

### 9.4 Scenario implementation order

```text
Network validity
→ baseline demand/route validity
→ baseline run
→ KPI extraction
→ intervention run
→ comparable seed/config
→ KPI delta
→ persistence
→ UI display
```

### 9.5 Exit criteria

- [ ] Baseline SUMO run completes from documented command/config.
- [ ] One intervention run completes under comparable assumptions.
- [ ] Scenario run stores seed, network version, demand version, inputs, status, and artifacts.
- [ ] KPI comparison includes travel time, delay, queue length, throughput.
- [ ] Scenario results are labeled `SIMULATION`.
- [ ] Scenario output never overwrites current observed/replay state.

---

## 10. Phase 5 — Traffic and energy forecasting

### 10.1 Objective

Implement baseline-first ML, produce separate forecast state, and make forecasts usable in decision support.

### 10.2 Dependencies

- Phase 2 observation/history storage complete.
- Phase 3 replay/simulation data streams working.
- Phase 1 data catalog and source classifications complete.
- Phase 4 is recommended but traffic ML may begin in parallel after sufficient data is available.

### 10.3 Traffic ML tasks

| ID | Task | Owner/workstream | Output |
|---|---|---|---|
| P5-T01 | Finalize target/interval/horizon | ML + data | Target decision record |
| P5-T02 | Build chronological dataset creation pipeline | ML/data | Versioned train/val/test extracts |
| P5-T03 | Implement persistence baseline | ML | Baseline metrics |
| P5-T04 | Implement historical-average baseline if data supports it | ML | Baseline metrics |
| P5-T05 | Build lag/rolling/calendar/weather features | ML | Feature schema/version |
| P5-T06 | Train XGBoost traffic model | ML | Model artifact/run |
| P5-T07 | Evaluate MAE/RMSE and optional interval metrics | ML | Evaluation report |
| P5-T08 | Create model card | ML/research | Traffic model card |
| P5-T09 | Register/log with MLflow | ML | Experiment records |
| P5-T10 | Add scheduled inference | Backend/ML | Forecast persistence flow |
| P5-T11 | Add traffic forecast UI | UI | Forecast chart/overlay/explanation |

### 10.4 Energy ML tasks

| ID | Task | Owner/workstream | Output |
|---|---|---|---|
| P5-E01 | Confirm energy source type and limitation label | Product/data | Energy data decision |
| P5-E02 | Build energy replay/synthetic ingestion path | Data/backend | Energy observations |
| P5-E03 | Build persistence/same-hour baseline | ML | Baseline metrics |
| P5-E04 | Build load/calendar/weather feature pipeline | ML | Feature schema/version |
| P5-E05 | Train XGBoost energy model | ML | Model artifact/run |
| P5-E06 | Evaluate MAE/RMSE | ML | Evaluation report |
| P5-E07 | Create energy model card | ML/research | Model card |
| P5-E08 | Add scheduled inference | Backend/ML | Forecast persistence flow |
| P5-E09 | Add energy forecast UI | UI | Energy chart/source warning/peak state |

### 10.5 Required ML quality gates

- [ ] Chronological split used.
- [ ] No feature leakage identified.
- [ ] Baseline metrics reported.
- [ ] XGBoost metrics reported.
- [ ] Model/data limitations documented.
- [ ] Model artifact, feature list, seed, data version, and metrics logged.
- [ ] Forecast output is separate from observed state.
- [ ] UI shows `PREDICTED`, horizon, timestamp, input quality, and model version.

### 10.6 Exit criteria

- [ ] Traffic model produces a 15-minute forecast.
- [ ] Energy model produces a 60-minute forecast.
- [ ] Models are evaluated against baselines.
- [ ] Forecasts persist and appear in dashboard.
- [ ] Low-quality/missing feature behavior is explicit.
- [ ] Locality and synthetic/replay limitations are visible/documented.

---

## 11. Phase 6 — Recommendations, quality, security, and deployment hardening

### 11.1 Objective

Convert evidence into transparent advisory decision support and make the pilot reliable enough for review/demo.

### 11.2 Dependencies

- Phase 3 operations dashboard complete.
- Phase 4 scenario workflow complete.
- Phase 5 forecasts complete.

### 11.3 Tasks

| ID | Task | Owner/workstream | Output |
|---|---|---|---|
| P6-01 | Define configurable traffic/energy/environment thresholds | Governance + product | Threshold configuration |
| P6-02 | Implement deterministic rule engine | Backend | Recommendation generator |
| P6-03 | Persist recommendation evidence/links | Backend | Advisory records |
| P6-04 | Build Recommendations view | UI | Advisory feed/detail/review state |
| P6-05 | Link recommendation to forecast/scenario/model evidence | UI/backend | Traceable drill-down |
| P6-06 | Implement user acknowledgement/review state | UI/backend | Review lifecycle |
| P6-07 | Implement basic auth/roles for remote demo | Platform/backend | Viewer/analyst/admin capability |
| P6-08 | Add MQTT authentication/configuration | Platform | Secure broker setup |
| P6-09 | Add `.env.example`, secret handling, configuration docs | Platform | Secure configuration baseline |
| P6-10 | Improve health/data-quality UI | UI/backend | Source/model/scenario health view |
| P6-11 | Implement unit/integration/end-to-end tests | All | Test suite |
| P6-12 | Configure GitHub Actions | Platform | CI workflow |
| P6-13 | Create runbook/demo recovery instructions | Platform/product | Operations runbook |

### 11.4 Exit criteria

- [ ] Forecast/scenario evidence can generate a documented advisory.
- [ ] Recommendation clearly states human approval required.
- [ ] User can inspect all evidence behind recommendation.
- [ ] No feature sends commands to real infrastructure.
- [ ] Basic authentication/secrets rules are implemented for remote demo.
- [ ] Core test suite passes.
- [ ] Health, stale, error, and degraded states are visible.

---

## 12. Phase 7 — Evaluation, research evidence, demo, and release

### 12.1 Objective

Turn the working pilot into a defensible engineering/research output with measurable evidence, clear limitations, and reproducible demonstration.

### 12.2 Dependencies

- Phases 0–6 complete.

### 12.3 Tasks

| ID | Task | Owner/workstream | Output |
|---|---|---|---|
| P7-01 | Execute formal traffic baseline vs XGBoost evaluation | ML/research | Metrics/report/figures |
| P7-02 | Execute formal energy baseline vs XGBoost evaluation | ML/research | Metrics/report/figures |
| P7-03 | Run feature ablation experiment | ML/research | Ablation evidence |
| P7-04 | Measure end-to-end latency | Platform/research | Latency report |
| P7-05 | Test missing/duplicate/stale data handling | Data/backend/research | Resilience report |
| P7-06 | Run formal baseline vs intervention scenario experiment | Simulation/research | KPI comparison/report |
| P7-07 | Conduct usability/provenance comprehension walkthrough | UI/research | Findings/report |
| P7-08 | Prepare architecture/data/model figures | Research/UI | Publication-quality figures |
| P7-09 | Write limitations and threat-to-validity section | Research | Honest limitations section |
| P7-10 | Create final demo script | Product/UI | Repeatable demonstration |
| P7-11 | Create project report/paper outline and evidence map | Research | Report/paper draft |
| P7-12 | Run clean-environment reproducibility test | Platform | Reproduction evidence |

### 12.4 Required evaluation evidence

| Area | Minimum evidence |
|---|---|
| Traffic ML | Baseline vs XGBoost MAE/RMSE; locality limitation statement |
| Energy ML | Baseline vs XGBoost MAE/RMSE; source-type statement |
| Data pipeline | Accepted/rejected/duplicate/stale handling evidence |
| Performance | Event-to-dashboard latency measurement |
| Simulation | Baseline/intervention KPI comparison with assumptions/seed |
| UX | User can identify provenance, forecast, scenario limitation, advisory evidence |
| Reproducibility | Docker Compose + documented run succeeds from clean setup |

### 12.5 Release criteria

- [ ] All Definition of Done items in PRD are satisfied.
- [ ] Every claim shown in demo/report is backed by an artifact/metric/source.
- [ ] No source/provenance ambiguity remains in UI.
- [ ] A new contributor can reproduce core demo.
- [ ] Limitations are prominent and accurate.
- [ ] Final release tag/demo package is created.

---

## 13. Phase 8 — Research-grade and scale extensions

This phase is not MVP work. Start only after Phase 7 evidence is complete.

### 13.1 Research-grade extensions

| Extension | Value | Prerequisite |
|---|---|---|
| Local aggregate traffic counts | Better pilot-corridor calibration | Permitted observation plan/data collection |
| Local aggregate meter data | Better local energy validity | Written approval and privacy review |
| Conformal prediction | Stronger uncertainty calibration | Stable forecast pipeline/evaluation split |
| SHAP per-prediction view | Better explanation | Stable model and UI performance |
| Environmental anomaly detection | Better monitoring research | Enough time series + validation protocol |
| EnergyPlus building model | More realistic energy scenarios | Building metadata/HVAC assumptions |
| FIWARE/Orion-LD adapter | Interoperability demonstration | Stable canonical schema |
| Eclipse Ditto integration | Device/twin policy state | Real device/digital-twin use case |
| Cesium/3D view | Stronger spatial presentation | Complete 2D workflow; demonstrated 3D value |
| STGNN/GNN comparison | Research novelty benchmark | Multi-segment synchronized data/topology |

### 13.2 Government/platform extensions

| Extension | Value | Prerequisite |
|---|---|---|
| Multiple Pune corridors | Wider mobility coverage | Pilot stability and asset onboarding process |
| Additional departments/domains | Multi-domain governance | Shared canonical model and stakeholders |
| Water/waste/infrastructure assets | Broader city service use | Approved datasets and domain requirements |
| ICCC data integration | Operational relevance | Government partnership, secure data agreement |
| Public transparency view | Citizen benefit | Content, privacy, policy, accessibility review |
| Enhanced IAM/audit | Governance readiness | Real multi-user institutional deployment |
| Managed database/object storage | Reliability/scaling | Real operational load and funding |
| Kafka/event platform | Higher-volume multi-consumer data | Measured event bottleneck |
| Kubernetes | Multi-node/high availability need | Operational evidence, team capacity |

---

## 14. Dependency matrix

| Capability | Depends on |
|---|---|
| Operations map | Study area, static assets, API, frontend shell |
| Traffic overlay | Ingestion, state storage, map layers, source provenance |
| Replay mode | Dataset manifest, adapter, MQTT, validation, storage |
| SUMO scenario | Valid corridor network, demand, backend scenario records, UI |
| Traffic forecast | Valid traffic history, target decision, feature pipeline, model evaluation |
| Energy forecast | Energy source/replay/synthetic stream, feature pipeline, model evaluation |
| Recommendation | Forecast and/or scenario evidence, rules, UI detail |
| System health | Ingestion/model/scenario status instrumentation |
| Optional 3D | Stable APIs/map data and complete 2D workflow |
| Paper/research output | Reproducible data, model/scenario experiments, documented limitations |

---

## 15. Parallelization guidance

### 15.1 Work that can run in parallel after Phase 1

| Parallel track A | Parallel track B | Coordination point |
|---|---|---|
| Backend database/schema setup | GIS OSM extraction/SUMO exploration | Stable entity IDs and canonical schema |
| Frontend shell/design system | Replay data preparation | API contract and example fixtures |
| SUMO network construction | ML dataset inspection/baseline notebooks | Time interval/target definition |
| Documentation/research review | Docker/CI setup | Shared repo conventions |

### 15.2 Work that must not be parallelized without agreement

- Canonical entity schema changes.
- Study-area boundary changes.
- Database migration design.
- Traffic target/interval changes after model feature work starts.
- Scenario KPI definition changes after baseline results are produced.
- Provenance label semantics.
- Core UI status color/label semantics.

---

## 16. Milestone definitions

| Milestone | Name | Evidence |
|---|---|---|
| M0 | Project foundation approved | Active docs, repo, scope, boundary decision |
| M1 | Spatial/data foundation ready | GeoJSON, assets, manifests, source classifications |
| M2 | Twin core operational | MQTT-to-state pipeline and APIs working |
| M3 | Visible twin demo | Replay/simulation updates visible on 2D map |
| M4 | Simulation capability demonstrated | Baseline/intervention SUMO comparison |
| M5 | Forecasting capability demonstrated | Traffic/energy baseline vs XGBoost results visible |
| M6 | Governance advisory workflow demonstrated | Evidence-backed recommendations and review state |
| M7 | Release/research evidence complete | Tests, metrics, demo, report/paper artifacts |

---

## 17. MVP critical path

The following sequence is the non-negotiable critical path:

```text
Pilot boundary and assets
→ canonical schema and data manifests
→ database + ingestion + validation
→ current/historical twin state
→ replay/simulation data stream
→ 2D operations map
→ SUMO baseline/intervention
→ traffic/energy baselines + XGBoost forecasts
→ forecast persistence + dashboard
→ evidence-backed recommendations
→ testing/evaluation/reproducible demo
```

Optional features must not block this path.

---

## 18. Scope-control rules

### 18.1 Do now

- Small corridor.
- Two junctions.
- Replay and simulation.
- Two XGBoost models plus baselines.
- One scenario intervention.
- 2D dashboard.
- Provenance, quality, and explanation.
- Docker Compose and tests.

### 18.2 Do later

- Multiple corridors.
- Real local devices/data where permitted.
- Full context broker.
- 3D visualization.
- Complex ML/GNNs/RL.
- Multiple city domains.
- Public portal.
- Enterprise operations stack.

### 18.3 Do not do without a new approved requirement

- Real actuation.
- CCTV/PII.
- Claims of citywide deployment.
- Claims of official Pune government integration.
- Claims that SUMO result proves real-world effect.
- Claims of Viman Nagar forecast accuracy based only on other-intersection or foreign datasets.

---

## 19. Roadmap review cadence

Review the roadmap at each milestone.

At every review, ask:

1. Does the current work still satisfy the pilot scope?
2. Has any dataset/model/result been incorrectly described as local or live?
3. Are model/simulation claims supported by evaluation?
4. Is any deferred technology now justified by a measured bottleneck or new requirement?
5. Has documentation been updated with implementation changes?
6. Is the critical path still protected?

Changes to study area, stack, data contract, safety boundary, or evaluation claims require a written decision record.

---

## 20. Final roadmap statement

> The platform will be built as a sequence of evidence-producing modules: first scope and spatial assets, then canonical data ingestion and twin state, then visible replay/simulation operations, then SUMO scenario comparison, then baseline-first forecasting, then advisory governance workflow, and finally evaluation and reproducible release. The roadmap protects the core purpose of the project: proving that a transparent, human-governed urban digital twin can support better city decision-making without overclaiming data, AI, simulation, or operational maturity.
