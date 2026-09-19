# Digital Twin: Smart City Analytics

> **Sub-title:** AI-Assisted Urban Mobility and Energy Analytics for the Viman Nagar–Somnath Nagar Corridor, Nagar Road, Pune  
> **Type:** Urban Digital Twin & Municipal Decision-Support Platform Prototype  
> **Status:** Active Research & Engineering Development (Phase 1)

---

## 1. Executive Summary

This **Digital Twin** is a corridor-scale urban analytics platform that combines physical city assets, event-driven sensor observations, AI forecasting, and Eclipse SUMO what-if traffic simulations. It is engineered to assist urban governance bodies, traffic authorities, and infrastructure planners in monitoring, evaluating, and safely simulating corridor mobility interventions and energy trends.

### Core Study Area
- **Primary Junction 1:** Viman Nagar Chowk / Phoenix Marketcity junction (`18.5602° N, 73.9168° E`)
- **Primary Junction 2:** Somnath Nagar Chowk (`18.5630° N, 73.9280° E`)
- **Connector Highway:** ~1.2 km section of the Pune–Ahmednagar Highway (Nagar Road) with key approach legs toward Ramwadi and Kalyani Nagar.

---

## 2. Mandatory Documentation Order

Contributors, agents, and researchers must read the binding root documentation in the following sequence:

1. [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) — Problem statement, study area boundary, operational modes, and core questions.
2. [PRD.md](PRD.md) — Product Requirements Document, user personas, functional criteria, and non-goals.
3. [TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md) — Modular monolith design, component boundaries, and event contracts.
4. [DATA_AND_ML_PLAN.md](DATA_AND_ML_PLAN.md) — Data catalog, provenance taxonomy, XGBoost models, and baselines.
5. [UI_UX_SPEC.md](UI_UX_SPEC.md) — Operations dashboard screens, MapLibre layout, and interaction wireframes.
6. [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) — Civic design tokens, Satoshi typography, and accessibility guidelines.
7. [ROADMAP.md](ROADMAP.md) — Phased implementation sequence (Phase 0 to Phase 8).
8. [DELIVERABLES.md](DELIVERABLES.md) — Master deliverable index (D-01 to D-14) and acceptance criteria.
9. [AGENTS.md](AGENTS.md) — Mandatory execution rules, architectural invariants, and safety boundaries.

---

## 3. Approved Technical Stack

| Layer | Approved MVP Technology |
|---|---|
| **Frontend** | React 18 + TypeScript + Vite |
| **2D Operational Map** | MapLibre GL JS + OpenStreetMap tiles |
| **Backend Monolith** | Python 3.11 + FastAPI (modular monolith) |
| **Message Broker** | Eclipse Mosquitto (MQTT transport) |
| **Primary Persistence** | PostgreSQL 16 |
| **Spatial Engine** | PostGIS 3.4 extension |
| **Time-Series Engine** | TimescaleDB extension |
| **Traffic Simulation** | Eclipse SUMO + TraCI |
| **Machine Learning** | XGBoost (15-min traffic, 60-min energy) + persistence baselines |
| **Decision Support** | Transparent deterministic rule engine |
| **Deployment** | Docker Compose |

---

## 4. Architecture & Data Invariants

1. **System of Record:** PostgreSQL/TimescaleDB/PostGIS is the authoritative system of record; MQTT is transport only.
2. **State Separation:** Observed/Live, Replayed, Simulated, and Predicted states are strictly segregated.
3. **Data Provenance:** Every metric surfaces an explicit source mode (`LIVE`, `REPLAY`, `SIMULATION`, `PREDICTED`, `STALE`, `INVALID`).
4. **Governance Safety:** All decision recommendations are advisory and require human approval outside the platform. Direct physical actuation of signals or infrastructure is prohibited in the MVP.
5. **No Unsupported Claims:** Non-local datasets (e.g., Pune RTO/Alankar/Jehangir counts) or simulations cannot be represented as live local measurements.

---

## 5. Repository Structure

```text
├── README.md                 # Project overview and navigation
├── PROJECT_CONTEXT.md        # Core project context & source of truth
├── PRD.md                    # Product Requirements Document
├── TECHNICAL_ARCHITECTURE.md # System architecture specification
├── DATA_AND_ML_PLAN.md       # Data governance & ML model specification
├── UI_UX_SPEC.md             # Operations dashboard specification
├── DESIGN_SYSTEM.md          # Civic tokens & styling guidelines
├── ROADMAP.md                # Phase-wise roadmap
├── DELIVERABLES.md           # Deliverable contracts & acceptance criteria
├── AGENTS.md                 # Mandatory agent operating rules
├── docs/                     # Documentation, ADRs, and reports
│   ├── decisions/            # Architecture Decision Records (ADRs)
│   ├── datasets/             # Data source manifests and catalogs
│   ├── diagrams/             # System diagrams and assets
│   ├── reference/            # Legacy research and archive notes
│   └── reports/              # Research evaluation and KPI reports
├── data/                     # Corridor datasets and manifests
│   ├── raw/                  # Immutable raw extracts
│   ├── samples/              # Corridor asset and sensor registry seeds
│   ├── manifests/            # Source metadata & license manifests
│   └── synthetic/            # SUMO and test stream records
├── backend/                  # FastAPI modular monolith application
├── frontend/                 # React + TypeScript + MapLibre UI
├── simulation/               # Eclipse SUMO networks, routes & scenarios
├── ml/                       # Feature pipelines, XGBoost models & baselines
├── infrastructure/           # Docker Compose, Mosquitto & DB configurations
├── scripts/                  # Data extraction and simulation utilities
└── tests/                    # Unit, integration, and schema validation tests
```

---

## 6. License & Ethics Notice

This project is an academic research and engineering prototype. Data from OpenStreetMap is licensed under the [Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/). All external benchmark datasets are cataloged with explicit licenses and restrictions in `docs/datasets/`.
