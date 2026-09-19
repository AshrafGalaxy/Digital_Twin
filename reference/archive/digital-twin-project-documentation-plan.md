# Digital Twin-Enabled Smart City Analytics
## Project Documentation and Agent Workplan

## Purpose

This document defines the documentation set required to build, evaluate, demonstrate, and publish a prototype of **Digital Twin-Enabled Smart City Analytics using AI, IoT, and Real-Time Data Intelligence**.

The intended prototype models a limited study area around a VIT Pune / Kondhwa campus zone or a small Pune urban corridor. It combines a synchronized digital representation of urban assets, simulation/replay/live data ingestion, AI forecasting, SUMO traffic scenarios, decision support, and 2D-first visualization with an optional 3D visualization extension.

This is the planning layer for agents and contributors. It answers:

- What modules exist?
- What work domains exist?
- Which Markdown files must be created?
- What belongs in each file?
- What technical stack is frozen for the first implementation?
- What must be delivered before the next module begins?

---

# 1. Scope summary

## Project problem

Urban data is fragmented across maps, traffic systems, environmental feeds, energy records, sensors, and simulations. Most small smart-city demonstrations show data on dashboards but do not maintain a synchronized stateful twin that can forecast conditions, simulate interventions, and explain recommended actions.

## Project objective

Build a modular digital twin for a limited Pune study area that can:

1. Represent roads, intersections, buildings, sensors, and related city assets.
2. Ingest simulated, replayed, and optionally live data through one canonical pipeline.
3. Maintain current, historical, predicted, and simulated city state.
4. Forecast traffic conditions and building/zone energy demand.
5. Monitor environmental indicators using transparent rules.
6. Run traffic what-if scenarios with SUMO.
7. Present state, forecasts, simulations, and explainable recommendations through an operator-facing dashboard.
8. Produce reproducible experiments and evidence suitable for an academic paper.

## Explicitly out of scope for the first prototype

- Citywide deployment.
- Direct control of real traffic signals or buildings.
- CCTV/video analytics.
- Facial recognition or personally identifiable information.
- Blockchain.
- Federated learning.
- LLM/agentic operational control.
- Kubernetes.
- Production municipal claims.

---

# 2. Frozen MVP technical stack

The following is the baseline stack. Agents must not replace it without an Architecture Decision Record (ADR).

| Layer | MVP selection | Role |
|---|---|---|
| Frontend | React + TypeScript + Vite | Dashboard application |
| Mapping | MapLibre GL JS + OpenStreetMap | 2D geospatial operations view |
| Optional 3D | CesiumJS; optional Google Photorealistic 3D Tiles | Presentation/immersive twin view only |
| Backend | Python + FastAPI | API, ingestion, twin services, scenario APIs |
| Messaging | MQTT + Eclipse Mosquitto | Sensor/simulation/replay event transport |
| Browser live updates | WebSockets | Dashboard current-state updates |
| Primary database | PostgreSQL | Relational entity and application data |
| Time-series | TimescaleDB extension | Observation and forecast time series |
| Spatial data | PostGIS extension | Roads, buildings, sensors, study-area geometry |
| Object storage | MinIO or local filesystem | Model artifacts, scenario output, raw imports |
| Canonical data model | NGSI-LD-inspired JSON entities | Portable urban entity representation |
| Traffic simulator | Eclipse SUMO + TraCI | Traffic behavior and what-if scenarios |
| Traffic ML | Persistence baseline + XGBoost | 15-minute speed/congestion forecast |
| Energy ML | Persistence baseline + XGBoost | 60-minute load forecast |
| Environment analytics | Rules first; Isolation Forest later | Threshold alerts and optional anomaly detection |
| Explainability | SHAP + feature importance | Explain prediction drivers |
| Decision support | Transparent rule engine | Human-approved recommendations |
| Experiment tracking | MLflow + Git | Metrics, models, runs, artifacts |
| Deployment | Docker Compose | Local/research/demo deployment |
| CI | GitHub Actions | Lint, unit tests, validation |

## Architecture principle

The project begins as a **modular monolith**. It is not a microservice platform. The system may later be separated by module only when load, maintenance, or research requirements justify it.

---

# 3. Work domains

The project has 10 engineering domains. Each domain maps to a group of Markdown documents and implementation deliverables.

| Domain | Objective | Main outputs |
|---|---|---|
| 1. Product and research | Define problem, scope, users, novelty, success criteria | PRD, BRD, research plan |
| 2. Urban/GIS modeling | Define study area and city asset representations | GIS inventory, entity schema |
| 3. Data engineering | Acquire, replay, simulate, validate, normalize, and store data | Data catalog, pipelines, quality rules |
| 4. Digital twin core | Maintain entity relationships and current/historical/predicted state | Twin state service, canonical model |
| 5. Traffic simulation | Create corridor/campus network and what-if scenarios | SUMO scenarios, KPI comparison |
| 6. AI/ML and analytics | Train/evaluate traffic and energy forecasts | Datasets, feature pipelines, models, experiments |
| 7. Decision intelligence | Convert forecasts and scenario output into traceable recommendations | Rule engine, recommendation schemas |
| 8. Frontend/UI/UX | Build usable spatial dashboard and scenario experience | Design system, dashboard, usability tests |
| 9. Platform engineering | Containerize, test, deploy, observe, and secure the stack | Docker Compose, CI, runbooks |
| 10. Research and dissemination | Evaluate, document, publish, demo, and prepare IP/funding materials | Paper, report, demo script, evidence pack |

---

# 4. Recommended implementation phases

There are 8 execution phases. A module should only begin when the stated entry criteria are met.

## Phase 0 — Foundation and decisions

**Goal:** Establish the problem boundary, study area, source-of-truth documents, repository structure, and success measures.

**Entry:** None.

**Outputs:**

- Problem statement and scope.
- Stakeholder/user definition.
- Study-area selection.
- Architecture baseline.
- Data availability assessment.
- Git repository and project conventions.

**Exit criterion:** Team can describe exactly what will be built, what will not be built, and how success will be measured.

## Phase 1 — Urban model and data foundation

**Goal:** Model roads, intersections, buildings, sensors, and observations; acquire baseline datasets and map data.

**Outputs:**

- OpenStreetMap study-area extraction.
- PostGIS layers.
- Canonical entity schema.
- Data catalog and licenses.
- Simulation/replay/live data-mode contracts.

**Exit criterion:** A map can display the study area and the backend can store valid canonical entities and observations.

## Phase 2 — Ingestion and twin-state core

**Goal:** Build the MQTT-to-FastAPI-to-Postgres pipeline and persist twin state.

**Outputs:**

- MQTT topics.
- Validation service.
- Current-state and historical-state tables.
- Provenance and data-quality fields.
- REST/WebSocket APIs.

**Exit criterion:** A simulated or replayed source updates the map and database through the same pipeline intended for live sources.

## Phase 3 — Traffic simulation and scenario engine

**Goal:** Model the selected traffic network and compare a baseline scenario with one intervention.

**Outputs:**

- SUMO network.
- Demand/route configuration.
- TraCI control service.
- Scenario registry.
- KPI output: travel time, delay, queue length, throughput.

**Exit criterion:** A user can trigger a scenario and compare it against a baseline without overwriting live twin state.

## Phase 4 — AI/ML forecasting

**Goal:** Train and evaluate the minimum required forecasting models.

**Outputs:**

- Traffic persistence baseline.
- Traffic XGBoost model.
- Energy persistence baseline.
- Energy XGBoost model.
- Feature pipeline.
- Evaluation reports.
- Prediction intervals and SHAP explanation artifacts.

**Exit criterion:** Models beat or honestly match simple baselines on a held-out chronological test set; predictions are written back to twin state.

## Phase 5 — Decision support and dashboard

**Goal:** Provide operator-facing analytics, explainable recommendations, and scenario controls.

**Outputs:**

- Live map and asset panel.
- Traffic, energy, and environment views.
- Forecast overlays.
- Recommendation cards with evidence.
- Scenario comparison views.
- Provenance badges: live/replay/simulation/predicted.

**Exit criterion:** A user can inspect conditions, understand a forecast, run a scenario, and see a justified recommendation.

## Phase 6 — Quality, security, and deployment

**Goal:** Make the prototype reproducible, testable, secure enough for its data class, and deployable.

**Outputs:**

- Docker Compose environment.
- Secrets/configuration guidance.
- Health checks.
- Test suite.
- GitHub Actions workflow.
- Data backup/export plan.
- Threat model and privacy statement.

**Exit criterion:** A new contributor can clone the repository, follow the runbook, and reproduce the demonstration.

## Phase 7 — Evaluation, paper, and final demonstration

**Goal:** Produce scientific evidence and a defensible demonstration.

**Outputs:**

- Experiment results.
- Architecture diagram.
- Dataset and model documentation.
- Research paper draft.
- Demo script.
- Final report.
- Limitations statement.

**Exit criterion:** Claims in the paper/demo are backed by logged experiments and reproducible artifacts.

---

# 5. Documentation inventory

Create the Markdown files below. Numbering is intentional: it gives agents a clear reading order.

## Root documents

| File | Owner/domain | Purpose |
|---|---|---|
| `README.md` | Project lead | Project overview, quick start, repository map, demo summary |
| `PROJECT_CONTEXT.md` | Product/research | Single source of truth: topic, problem, scope, constraints, users |
| `PRD.md` | Product | Product requirements and acceptance criteria |
| `BRD.md` | Product/research | Business/research requirements, stakeholders, value, constraints |
| `ROADMAP.md` | Project management | Phases, dependencies, milestones, risks |
| `DELIVERABLES.md` | Project management | Exact outputs, acceptance criteria, evidence required |
| `GLOSSARY.md` | Project lead | Definitions: twin, observation, scenario, forecast, etc. |
| `DECISIONS.md` | Architecture | Index of architecture decisions and rationale |
| `RISK_REGISTER.md` | Project management | Data, technical, research, licensing, scope risks |
| `CONTRIBUTING.md` | Engineering | Branching, PR, code review, test, doc conventions |

## Product and research documents

| File | Purpose |
|---|---|
| `docs/product/USER_PERSONAS.md` | Operators, planners, researchers, student users, beneficiaries |
| `docs/product/USER_STORIES.md` | Atomic user stories and acceptance criteria |
| `docs/product/USE_CASES.md` | Traffic, energy, environment, what-if scenario flows |
| `docs/research/RESEARCH_QUESTIONS.md` | Research questions, hypotheses, scope of claims |
| `docs/research/LITERATURE_REVIEW.md` | Curated papers, platforms, findings, gaps |
| `docs/research/COMPETITOR_ANALYSIS.md` | FIWARE, Snap4City, Ditto, Azure DT, Bentley, etc. |
| `docs/research/NOVELTY_AND_LIMITATIONS.md` | Contribution framing and non-claims |
| `docs/research/EVALUATION_PLAN.md` | Metrics, baselines, ablations, experiment protocol |
| `docs/research/PUBLICATION_PLAN.md` | Paper structure, evidence checklist, target venue criteria |

## Architecture documents

| File | Purpose |
|---|---|
| `docs/architecture/SYSTEM_ARCHITECTURE.md` | End-to-end system, logical and deployment views |
| `docs/architecture/DATA_FLOW.md` | Source → ingestion → twin → model → dashboard flow |
| `docs/architecture/TWIN_MODEL.md` | Entity, state, relationship, synchronization design |
| `docs/architecture/CANONICAL_DATA_MODEL.md` | NGSI-LD-inspired JSON contracts and examples |
| `docs/architecture/API_CONTRACTS.md` | REST/WebSocket/MQTT interfaces and error contracts |
| `docs/architecture/SCENARIO_ARCHITECTURE.md` | SUMO scenario workflow and isolation from live state |
| `docs/architecture/ADR/` | One Markdown ADR per irreversible technical decision |
| `docs/architecture/DIAGRAMS.md` | Links/code for Eraser diagrams, conventions, revisions |

## Data and GIS documents

| File | Purpose |
|---|---|
| `docs/data/DATA_CATALOG.md` | Every external/local dataset, owner, license, fields, limits |
| `docs/data/DATA_REQUIREMENTS.md` | Minimum fields and data quality needed per feature/model |
| `docs/data/DATA_PIPELINES.md` | Simulation, replay, live ingestion design |
| `docs/data/DATA_QUALITY_RULES.md` | Schema, range, time, duplicate, missing-data checks |
| `docs/data/DATA_PROVENANCE.md` | Live/replay/simulation/prediction provenance rules |
| `docs/data/DATA_GOVERNANCE.md` | Privacy, retention, access, licensing, consent boundaries |
| `docs/data/STUDY_AREA.md` | VIT/Pune location choice, boundaries, OSM extraction method |
| `docs/data/GIS_MODEL.md` | Layers, spatial IDs, coordinate systems, PostGIS design |
| `docs/data/DATASET_SETUP.md` | Download/import commands and local storage conventions |

## AI/ML documents

| File | Purpose |
|---|---|
| `docs/ml/ML_STRATEGY.md` | Why only two trained MVP models; model lifecycle |
| `docs/ml/TRAFFIC_FORECASTING.md` | Target, features, baselines, XGBoost, training, evaluation |
| `docs/ml/ENERGY_FORECASTING.md` | Target, features, data constraints, training, evaluation |
| `docs/ml/ENVIRONMENT_ANALYTICS.md` | Thresholds, optional anomaly detection, limitations |
| `docs/ml/FEATURE_ENGINEERING.md` | Lags, rolling windows, time and weather features |
| `docs/ml/TRAINING_PIPELINE.md` | Chronological split, leakage prevention, MLflow logging |
| `docs/ml/INFERENCE_AND_SERVING.md` | Scheduled inference, model API, outputs, rollback |
| `docs/ml/MODEL_EVALUATION.md` | MAE/RMSE/sMAPE, interval coverage, baselines |
| `docs/ml/EXPLAINABILITY.md` | SHAP, model cards, uncertainty, user explanation rules |
| `docs/ml/MODEL_CARDS/` | One model card per trained model/version |

## Simulation documents

| File | Purpose |
|---|---|
| `docs/simulation/SUMO_SETUP.md` | Installation, network import, routes, configuration |
| `docs/simulation/SCENARIO_CATALOG.md` | Baseline and intervention scenario definitions |
| `docs/simulation/KPI_DEFINITIONS.md` | Travel time, delay, queue, throughput, emissions if used |
| `docs/simulation/TRACI_INTEGRATION.md` | Python interaction contract and output schemas |
| `docs/simulation/ENERGY_SYNTHETIC_DATA.md` | Synthetic load model assumptions and limitations |
| `docs/simulation/REPRODUCIBILITY.md` | Seeds, run IDs, inputs, artifacts, comparison procedure |

## UI/UX documents

| File | Purpose |
|---|---|
| `docs/design/UI_UX_BRIEF.md` | Design purpose, users, scenarios, success criteria |
| `docs/design/INFORMATION_ARCHITECTURE.md` | Dashboard navigation and screen hierarchy |
| `docs/design/DESIGN_SYSTEM.md` | Colors, typography, states, components, accessibility |
| `docs/design/DASHBOARD_SPEC.md` | Map, panels, charts, alerts, scenario interface |
| `docs/design/MAP_VISUALIZATION.md` | Layer rules, legends, colors, markers, animation, provenance |
| `docs/design/USER_FLOWS.md` | Operator monitoring and scenario-analysis flows |
| `docs/design/ACCESSIBILITY.md` | Keyboard, color contrast, screen-reader and motion rules |
| `docs/design/USABILITY_TEST_PLAN.md` | Tasks, participants, measures, feedback capture |
| `docs/design/3D_VISUALIZATION_OPTION.md` | Cesium/Google Tiles option, costs, terms, fallback plan |

## Backend and platform documents

| File | Purpose |
|---|---|
| `docs/backend/BACKEND_ARCHITECTURE.md` | FastAPI modules, boundaries, services, dependencies |
| `docs/backend/DATABASE_SCHEMA.md` | Postgres/Timescale/PostGIS tables, indexes, migrations |
| `docs/backend/MQTT_TOPICS.md` | Topic naming, QoS, message examples, security |
| `docs/backend/VALIDATION_AND_ERRORS.md` | Pydantic schemas, error handling, dead-letter policy |
| `docs/backend/WEBSOCKET_EVENTS.md` | Dashboard event types and payload contracts |
| `docs/platform/DOCKER_COMPOSE.md` | Service topology, local commands, configuration |
| `docs/platform/DEPLOYMENT.md` | Laptop/VM deployment, domains, reverse proxy, backups |
| `docs/platform/OBSERVABILITY.md` | Logs, health checks, metrics, alert plan |
| `docs/platform/SECURITY.md` | JWT, MQTT auth, TLS, secrets, access roles |
| `docs/platform/CI_CD.md` | GitHub Actions, tests, checks, release workflow |
| `docs/platform/RUNBOOK.md` | Start, stop, debug, restore, demo procedures |

## Delivery documents

| File | Purpose |
|---|---|
| `docs/delivery/TEST_PLAN.md` | Unit, integration, end-to-end, failure tests |
| `docs/delivery/ACCEPTANCE_CRITERIA.md` | Definition of done by feature/module |
| `docs/delivery/DEMO_SCRIPT.md` | Repeatable demonstration narrative and steps |
| `docs/delivery/PRESENTATION_OUTLINE.md` | Review/funding presentation structure |
| `docs/delivery/PAPER_OUTLINE.md` | Research-paper sections and evidence mapping |
| `docs/delivery/FINAL_CHECKLIST.md` | Pre-submission, demo, release, and reproducibility checks |

---

# 6. Agent work packages

Use these work packages to assign agents without overlapping ownership.

| Agent/work package | Primary documents | Build scope | Must not do |
|---|---|---|---|
| Product & research agent | PRD, BRD, research docs | Problem, users, requirements, evaluation, literature | Change architecture unilaterally |
| GIS/data agent | Data catalog, study area, GIS model | OSM extraction, dataset imports, data schema | Train models without data contract |
| Data pipeline agent | Data pipelines, quality, provenance | MQTT ingestion, replay, validators, storage writes | Change canonical schema without ADR |
| Twin-core agent | Twin model, API contracts | Entity state, relationships, REST/WebSockets | Add unapproved brokers/services |
| Simulation agent | SUMO docs, scenario catalog | SUMO network, TraCI, scenarios, KPIs | Treat simulated results as live state |
| ML agent | ML strategy and domain docs | Features, baselines, XGBoost, evaluation, model cards | Add deep models without evidence/data need |
| Decision-support agent | Recommendation rules, scenario APIs | Rules, evidence, approval workflow | Implement autonomous physical actuation |
| UI/UX agent | Design docs | Dashboard, maps, scenario UX, accessibility | Mislabel simulated/predicted data as live |
| Platform agent | Docker, deployment, security, CI docs | Containers, tests, env config, runbook | Introduce Kubernetes without ADR |
| Research/delivery agent | Evaluation, paper, demo docs | Experiments, figures, reporting, presentation | Overclaim outcomes or novelty |

---

# 7. Required datasets and resources

## Primary data sources

| Resource | Use | Notes |
|---|---|---|
| OpenStreetMap | Study-area roads, intersections, buildings, geometry | Must retain ODbL attribution |
| Pune heterogeneous traffic count dataset | Local traffic-count training/prototype validation | Short duration; document geographic and temporal limitations |
| SUMO output | Repeatable traffic simulation and replay stream | Synthetic; not evidence of real-world performance |
| Meteostat/Open-Meteo | Weather features | Record source, retrieval time, and units |
| Pune air-quality data | Environment visualization and threshold monitoring | Station data may not represent the campus exactly |
| Campus meter data, if permitted | Best energy training data | Requires permission and privacy review |
| Synthetic energy load curves | Pipeline testing/energy demo fallback | Clearly label as synthetic |
| UCI Electricity Load Diagrams | Energy-model benchmark/testing | Not local building energy data |
| METR-LA/PEMS-BAY | Advanced traffic-model benchmark only | Not valid for Pune-local accuracy claims |

## Core open-source resources

| Resource | Purpose |
|---|---|
| FastAPI | Python API/backend |
| Pydantic | API/schema validation |
| PostgreSQL | Relational state and app data |
| TimescaleDB | Time series |
| PostGIS | Spatial data |
| Mosquitto | MQTT broker |
| SUMO | Traffic simulation |
| TraCI | SUMO control/query API |
| XGBoost | Tabular prediction models |
| MLflow | Experiment tracking |
| SHAP | Explainability |
| React/Vite | Frontend |
| MapLibre GL JS | 2D map |
| OSMnx | OSM road-network extraction |
| Docker Compose | Local deployment |

---

# 8. Minimum deliverable chain

The project is complete only if this chain works end to end:

```text
Study area and asset registry
  → simulation/replay/live source
  → MQTT ingestion
  → validation and provenance tagging
  → PostgreSQL/TimescaleDB/PostGIS
  → feature generation
  → traffic/energy prediction
  → twin-state update
  → rule-based recommendation
  → MapLibre dashboard
  → SUMO what-if comparison
  → logged evaluation and reproducible demo
```

## Minimum final demo

1. Show a defined VIT/Pune study area in MapLibre.
2. Display 5–10 road segments and at least one building/energy entity.
3. Stream simulated or replayed data through MQTT.
4. Show current-state updates with provenance.
5. Display a 15-minute traffic forecast.
6. Display a 60-minute energy forecast or clearly labeled synthetic energy forecast.
7. Generate one explainable recommendation.
8. Run one SUMO what-if scenario against a baseline.
9. Show KPI comparison.
10. Reproduce the flow from Docker Compose using documented setup steps.

---

# 9. Document creation order

Create and approve documents in this order:

1. `PROJECT_CONTEXT.md`
2. `PRD.md`
3. `BRD.md`
4. `ROADMAP.md`
5. `DELIVERABLES.md`
6. `docs/research/RESEARCH_QUESTIONS.md`
7. `docs/architecture/SYSTEM_ARCHITECTURE.md`
8. `docs/architecture/CANONICAL_DATA_MODEL.md`
9. `docs/data/DATA_CATALOG.md`
10. `docs/data/DATA_REQUIREMENTS.md`
11. `docs/data/STUDY_AREA.md`
12. `docs/architecture/API_CONTRACTS.md`
13. `docs/backend/DATABASE_SCHEMA.md`
14. `docs/data/DATA_PIPELINES.md`
15. `docs/simulation/SUMO_SETUP.md`
16. `docs/ml/ML_STRATEGY.md`
17. `docs/ml/TRAFFIC_FORECASTING.md`
18. `docs/ml/ENERGY_FORECASTING.md`
19. `docs/design/UI_UX_BRIEF.md`
20. `docs/design/DASHBOARD_SPEC.md`
21. `docs/platform/DOCKER_COMPOSE.md`
22. `docs/research/EVALUATION_PLAN.md`
23. `docs/delivery/TEST_PLAN.md`
24. `docs/delivery/DEMO_SCRIPT.md`
25. `docs/delivery/PAPER_OUTLINE.md`

---

# 10. Rules for every agent

1. Read `PROJECT_CONTEXT.md`, `PRD.md`, `SYSTEM_ARCHITECTURE.md`, `CANONICAL_DATA_MODEL.md`, and `DECISIONS.md` before beginning work.
2. Do not change the canonical schema, tech stack, or scope without an ADR.
3. Every dataset must be entered in `DATA_CATALOG.md` before use.
4. Every dataset must carry license, source, download date, geographic coverage, temporal coverage, and usage limitation.
5. Every displayed value must state provenance: `live`, `replay`, `simulation`, or `predicted`.
6. Every trained model needs a model card, reproducible experiment run, baseline comparison, and chronological validation split.
7. Never label synthetic data as live or real.
8. Never claim local Pune/VIT accuracy from a foreign dataset.
9. Keep simulation results isolated from current/live twin state.
10. Do not implement physical actuation; all recommendations require human approval.
11. Do not add an LLM, blockchain, GNN, Kafka, Kubernetes, or a graph database without a documented problem and ADR.
12. Update the relevant Markdown document in the same pull request as the code.

---

# 11. Next action

Create the first five root documents:

1. `PROJECT_CONTEXT.md`
2. `PRD.md`
3. `BRD.md`
4. `ROADMAP.md`
5. `DELIVERABLES.md`

Then create the architecture and data documents before starting application code.
