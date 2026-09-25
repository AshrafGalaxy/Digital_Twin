# Digital Twin

---

## 1. Executive Summary

This **Digital Twin** is an integrated urban analytics and decision-support platform combining physical infrastructure assets, event-driven MQTT sensor telemetry, machine learning forecasting (XGBoost), and Eclipse SUMO micro-simulation. It assists urban operators, planners, and analysts in observing network conditions, forecasting traffic and energy trends, and evaluating what-if mobility interventions in simulation before real-world implementation.

The platform is strictly **read-only decision support**; recommendations are advisory and require human authorization outside the platform prior to any field execution.

---

## 2. Documentation Architecture

Project documentation is structured into clear tiers for developers, contributors, and operators:

### Root Essential Documents
- [README.md](README.md) — System summary, navigation, quickstart commands, and directory overview.
- [CONTRIBUTING.md](CONTRIBUTING.md) — Contribution guidelines, dev setup, branch model, commit conventions, and PR checklist.
- [AGENTS.md](AGENTS.md) — Mandatory execution contract, core invariants, provenance rules, workspace hygiene, and Definition of Done.
- [PRD.md](PRD.md) — Executive Product Requirements Document (FR-01 to FR-10, NFRs, acceptance criteria).

### Future Enhancement Master Specifications (`FuturePlans/`)
- [FuturePlans/TRAFFIC_MANAGEMENT.md](FuturePlans/TRAFFIC_MANAGEMENT.md) — Master specification for location-agnostic traffic mobility, signal optimization, and transit priority.
- [FuturePlans/ENERGY_MANAGEMENT.md](FuturePlans/ENERGY_MANAGEMENT.md) — Master specification for microgrid optimization, BESS arbitrage, and building thermal flexibility.
- [FuturePlans/ENVIRONMENT_MANAGEMENT.md](FuturePlans/ENVIRONMENT_MANAGEMENT.md) — Master specification for urban air quality, dispersion modeling, and environmental monitoring.
- [FuturePlans/WATER_MANAGEMENT.md](FuturePlans/WATER_MANAGEMENT.md) — Master specification for distribution network hydraulics, pressure management, and leakage detection.
- [FuturePlans/WASTE_MANAGEMENT.md](FuturePlans/WASTE_MANAGEMENT.md) — Master specification for municipal solid waste telemetry, bin fill levels, and collection routing.

### Implementation Task Directories (`docs/tasks/`)
- [docs/tasks/traffic-mobility/README.md](docs/tasks/traffic-mobility/README.md) — 11 modular engineering tasks for Traffic Mobility (Issues #2–#12).
- [docs/tasks/energy-microgrid/README.md](docs/tasks/energy-microgrid/README.md) — 10 modular engineering tasks for Energy & Microgrids (Issues #13–#22).

### Technical Architecture & Catalogs
- [docs/architecture.md](docs/architecture.md) — Authoritative engineering blueprint: modular monolith architecture, 25 multi-storage DB schemas, MQTT topic hierarchy, spatial registry, and REST/WebSocket API contracts.
- [data/manifests/DATASET_REGISTRY.md](data/manifests/DATASET_REGISTRY.md) — Full data governance catalog, licensing, and schema definitions.
- [data/spatial/corridor_spatial_registry.json](data/spatial/corridor_spatial_registry.json) — Canonical PostGIS-to-SUMO cross-referencing and 3D spatial definitions.

---

## 3. Active Future Enhancement Tracks (21 GitHub Issues)

The platform is expanding through two prioritized enhancement tracks covering 21 detailed engineering tasks:

### Track 1: Intelligent Traffic Mobility & Adaptive Control (11 Tasks)
Detailed directory: [docs/tasks/traffic-mobility/](docs/tasks/traffic-mobility/)

| Task ID | Issue | Task Title | Spec Ref | Milestone | Component / Scope |
|---|---|---|---|---|---|
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
|---|---|---|---|---|---|
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

## 4. Technical Stack

| Layer | Technology | Role |
|---|---|---|
| **Frontend** | React 18 + TypeScript + Vite | Civic operations dashboard & control room UI |
| **Geospatial & 3D** | MapLibre GL JS + Deck.gl + OpenStreetMap | 2D vector maps, 3D extruded queues, signal heads |
| **Backend Monolith** | Python 3.11 + FastAPI modular monolith | Async REST APIs (`/api/v1`), WebSockets, rule engine |
| **Message Broker** | Eclipse Mosquitto (MQTT 3.1.1/5.0) | Sensor telemetry transport (`nagartwin/#`, `citytwin/#`) |
| **Primary Database** | PostgreSQL 16 + TimescaleDB + PostGIS | Canonical entity store, spatial queries, hypertables |
| **Resilient Local DB**| SQLite 3 (WAL mode) + aiosqlite | Zero-dependency local persistence with automated fallback |
| **Simulation** | Eclipse SUMO 1.20+ via TraCI | Microscopic corridor traffic, green wave, and TSP |
| **Machine Learning** | XGBoost (Quantile & Regression) | Speed, load, queue, and solar forecasting with TreeSHAP |
| **Optimization** | SciPy Optimization / MILP | Webster signal timing & BESS peak shaving arbitrage |
| **Decision Support** | Deterministic Python Rule Engine | Transparent advisory rules with mandatory human authorization |
| **Containerization** | Docker Compose with profiles | Modular container orchestration (`--profile full` for MLflow) |

---

## 5. Quickstart: Running the Platform

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
- **Backend API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)
- **WebSocket Stream:** `ws://localhost:8000/ws/operations`

---

## 6. Repository Directory Structure

```text
├── .github/                        # GitHub Actions CI, issue & PR templates
│   ├── ISSUE_TEMPLATE/             # Domain task issue template
│   ├── workflows/                  # ci.yml (Tests, TypeScript build, asset validation)
│   └── pull_request_template.md    # Standard PR template with architectural invariants
├── FuturePlans/                    # Master domain enhancement specifications
│   ├── TRAFFIC_MANAGEMENT.md       # Intelligent Traffic Mobility & Control blueprint
│   ├── ENERGY_MANAGEMENT.md        # Microgrid & Energy Management blueprint
│   ├── ENVIRONMENT_MANAGEMENT.md   # Air quality & environmental monitoring blueprint
│   ├── WATER_MANAGEMENT.md         # Municipal water distribution blueprint
│   └── WASTE_MANAGEMENT.md         # Solid waste collection & routing blueprint
├── docs/                           # Architecture blueprints and task directories
│   ├── architecture.md             # Technical architecture and DB schemas
│   └── tasks/                      # Modular engineering implementation task directories
│       ├── traffic-mobility/       # 11 engineering tasks for Traffic Mobility (Tasks 01–11)
│       └── energy-microgrid/       # 10 engineering tasks for Energy Management (Tasks 01–10)
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
│   ├── src/components/             # UI components, Map views, and modals
│   ├── src/services/               # API clients and WebSocket managers
│   └── src/types/                  # TypeScript interface definitions
├── simulation/                     # Eclipse SUMO networks, vehicle fleets, TraCI runners
├── ml/                             # XGBoost training pipelines, models, and evaluators
├── infrastructure/                 # Docker Compose, Mosquitto, and database configs
├── scripts/                        # Development utilities and synthetic stream runners
├── tests/                          # 15 modular pytest suites (114 hermetic tests)
├── CONTRIBUTING.md                 # Developer onboarding and contribution guidelines
├── AGENTS.md                       # Mandatory operating rules and architectural invariants
├── PRD.md                          # Executive Product Requirements Document
├── compose.yaml                    # Multi-container Docker Compose configuration
├── start_dev.ps1                   # One-click PowerShell local development launcher
└── README.md                       # Root system overview and navigation
```

---

## 7. License & Ethics Notice

This project is an academic research and engineering prototype. Data from OpenStreetMap is licensed under the [Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/). All external benchmark datasets are cataloged with explicit licenses and restrictions in `data/manifests/DATASET_REGISTRY.md`.
