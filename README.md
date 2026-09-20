# Digital Twin: Smart City Analytics Platform
## Viman Nagar–Somnath Nagar Corridor, Pune

> **Type:** Urban Digital Twin & Municipal Decision-Support Platform Prototype  
> **Pilot Study Area:** Viman Nagar Chowk (Phoenix Marketcity) ↔ Somnath Nagar Chowk, Nagar Road, Pune (`[18.5575, 73.9120]` to `[18.5665, 73.9325]`)  
> **Status:** Fully Implemented & Tested (91 of 91 automated tests passing, 100% complete)

---

## 1. Executive Summary

This **Digital Twin** is an integrated corridor-scale urban analytics and decision-support platform that combines physical infrastructure assets, event-driven MQTT sensor telemetry, machine learning forecasting (XGBoost), and Eclipse SUMO micro-simulation. It assists urban governance bodies, traffic authorities, and infrastructure planners in observing corridor conditions, forecasting traffic/energy trends, and evaluating what-if mobility interventions in simulation before real-world implementation.

---

## 2. Documentation Architecture

All project documentation is organized hierarchically:

### Root Essential Documents
- [README.md](README.md) — System summary, quickstart commands, and documentation directory.
- [AGENTS.md](AGENTS.md) — Mandatory execution contract, core invariants, provenance rules, and Definition of Done.
- [PRD.md](PRD.md) — Executive Product Requirements Document (FR-01 to FR-10, NFRs, acceptance criteria).

### Technical Specifications (`docs/specifications/`)
- [technical_architecture.md](docs/specifications/technical_architecture.md) — Modular monolith architecture, multi-storage DB schemas, MQTT topic hierarchy, and REST/WS API contracts.
- [data_and_ml_plan.md](docs/specifications/data_and_ml_plan.md) — Medallion data lakehouse, feature store schemas, XGBoost models, conformal intervals, and drift monitoring.
- [design_system.md](docs/specifications/design_system.md) — Dual-theme CSS color tokens, Satoshi typography, 4px spacing scale, and WCAG 2.2 AA rules.
- [ui_ux_spec.md](docs/specifications/ui_ux_spec.md) — Operations dashboard screens, MapLibre 2D layer rules, and contextual drawer interaction flows.
- [project_context.md](docs/specifications/project_context.md) — Corridor boundaries, coordinates, arterial parameters, and municipal justification.
- [PROJECT_DELIVERABLES.md](docs/PROJECT_DELIVERABLES.md) — Verification matrix for all Deliverables (D-01 to D-14) and Phase 1–8 milestones.

### Decisions, Datasets, and Reports
- [docs/decisions/](docs/decisions/) — Architecture Decision Records (ADR-001 to ADR-004).
- [docs/datasets/](docs/datasets/) — Corridor spatial metadata and OpenStreetMap validation notes.
- [docs/reports/](docs/reports/) — Model cards (`MODEL_CARD_*.md`), operational runbook, demo script, and academic research evaluation report.

---

## 3. Approved Technical Stack

| Layer | Technology | Role |
|---|---|---|
| **Frontend** | React 18 + TypeScript + Vite | Civic operations dashboard with dual themes |
| **Geospatial Map** | MapLibre GL JS + OpenStreetMap tiles | 2D vector map canvas (3D strictly deferred) |
| **Backend Monolith** | Python 3.11 + FastAPI modular monolith | Async REST APIs (`/api/v1`), WebSockets, rule engine |
| **Message Broker** | Eclipse Mosquitto (MQTT 3.1.1/5.0) | Sensor telemetry transport (`nagartwin/#`, `dt/v1/corridor/#`) |
| **Primary DB** | PostgreSQL 16 + TimescaleDB + PostGIS | Canonical entity store, spatial queries, hypertable time-series |
| **Resilient Local DB**| SQLite 3 (WAL mode) + aiosqlite | Zero-dependency local persistence with automatic failover |
| **Traffic Simulation**| Eclipse SUMO 1.20+ via TraCI | Baseline (`SCEN-BASE-01`) vs adaptive green (`SCEN-INT-01`) |
| **Machine Learning** | XGBoost (15m traffic, 60m energy) | Speed & power forecasting with conformal bounds & TreeSHAP |
| **Decision Support** | Deterministic Python Rule Engine | Transparent advisory rules with mandatory human authorization |
| **Deployment** | Docker Compose with profiles | Modular container orchestration (`--profile full` for MinIO/MLflow) |

---

## 4. Quickstart: Running the Platform

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

## 5. Clean Repository Structure

```text
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
├── compose.yaml              # Multi-container Docker Compose definition
├── start_dev.bat             # Windows CMD one-click launcher
├── start_dev.ps1             # PowerShell one-click launcher
├── README.md                 # Project overview and navigation
├── AGENTS.md                 # Mandatory agent operating rules and invariants
├── PRD.md                    # Executive Product Requirements Document
├── docs/                     # Specifications, ADRs, datasets, and reports
│   ├── PROJECT_DELIVERABLES.md # Milestone & deliverables completion matrix
│   ├── decisions/            # ADR-001 through ADR-004
│   ├── datasets/             # Corridor spatial metadata
│   ├── diagrams/             # System and dataflow architecture diagrams
│   ├── reference/            # Architecture & tech stack research reference
│   ├── reports/              # Model cards, runbook, demo script, research report
│   └── specifications/       # Deep engineering blueprints (Architecture, ML, UI, Tokens)
├── data/                     # Medallion lakehouse (raw, bronze, silver, gold, manifests)
├── backend/                  # FastAPI modular monolith application
├── frontend/                 # React + TypeScript + MapLibre UI
├── simulation/               # Eclipse SUMO network, routes & scenarios
├── ml/                       # Feature pipelines, XGBoost models & calibrator
├── infrastructure/           # Docker Compose, Mosquitto & DB configurations
├── scripts/                  # run_local.py, publish_stream.py, benchmarks
└── tests/                    # 13 modular pytest test suites (100% passing)
```

---

## 6. License & Ethics Notice

This project is an academic research and engineering prototype. Data from OpenStreetMap is licensed under the [Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/). All external benchmark datasets are cataloged with explicit licenses and restrictions in `data/manifests/DATASET_REGISTRY.md`.
