# Digital Twin: Smart City Analytics Platform
## Viman Nagar–Somnath Nagar Corridor, Pune

> **Type:** Urban Digital Twin & Municipal Decision-Support Platform Prototype  
> **Pilot Study Area:** Viman Nagar Chowk (Phoenix Marketcity) ↔ Somnath Nagar Chowk, Nagar Road, Pune (`[18.5575, 73.9120]` to `[18.5665, 73.9325]`)  
> **Status:** Fully Implemented & Tested (99 of 99 automated tests passing, 100% complete)

---

## 1. Executive Summary

This **Digital Twin** is an integrated corridor-scale urban analytics and decision-support platform that combines physical infrastructure assets, event-driven MQTT sensor telemetry, machine learning forecasting (XGBoost), and Eclipse SUMO micro-simulation. It assists urban governance bodies, traffic authorities, and infrastructure planners in observing corridor conditions, forecasting traffic/energy trends, and evaluating what-if mobility interventions in simulation before real-world implementation.

---

## 2. Documentation Architecture

Project documentation is structured concisely:

### Root Essential Documents
- [README.md](README.md) — System summary, quickstart commands, and directory navigation.
- [CONTRIBUTING.md](CONTRIBUTING.md) — Team contribution guidelines, dev setup, branching, testing, and PR workflow.
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) — Contributor Covenant v2.1 code of conduct and community standards.
- [AGENTS.md](AGENTS.md) — Mandatory execution contract, core invariants, provenance rules, workspace hygiene, and Definition of Done.
- [PRD.md](PRD.md) — Executive Product Requirements Document (FR-01 to FR-10, NFRs, acceptance criteria).

### Technical Architecture
- [docs/architecture.md](docs/architecture.md) — Authoritative engineering blueprint: modular monolith architecture, 25 multi-storage DB schemas, MQTT topic hierarchy, spatial registry, and REST/WebSocket API contracts.

### Dataset Catalogs
- [data/manifests/DATASET_REGISTRY.md](data/manifests/DATASET_REGISTRY.md) — Full data governance catalog, licensing, and schema definitions.
- [data/spatial/corridor_spatial_registry.json](data/spatial/corridor_spatial_registry.json) — Canonical PostGIS-to-SUMO cross-referencing and 3D spatial definitions.

---

## 3. Approved Technical Stack

| Layer | Technology | Role |
|---|---|---|
| **Frontend** | React 18 + TypeScript + Vite | Civic operations dashboard |
| **Geospatial Map** | MapLibre GL JS + OpenStreetMap | 2D vector map canvas and layer overlays |
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
├── docs/                     # Authoritative system architecture blueprint
│   └── architecture.md       # Technical architecture specification
├── data/                     # Data assets, spatial registry, and manifests
├── backend/                  # FastAPI modular monolith application
├── frontend/                 # React + TypeScript + MapLibre UI
├── simulation/               # Eclipse SUMO network, routes & scenarios
├── ml/                       # Feature pipelines, XGBoost models & calibrator
├── infrastructure/           # Docker Compose, Mosquitto & DB configurations
├── scripts/                  # run_local.py, publish_stream.py, benchmarks
└── tests/                    # 15 modular pytest test suites (100% passing)
```

---

## 6. License & Ethics Notice

This project is an academic research and engineering prototype. Data from OpenStreetMap is licensed under the [Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/). All external benchmark datasets are cataloged with explicit licenses and restrictions in `data/manifests/DATASET_REGISTRY.md`.
