# Intelligent Traffic Mobility & Adaptive Corridor Control: Implementation Task Directory

> **System Component:** Pune Nagar Road Digital Twin (Viman Nagar Chowk ↔ Somnath Nagar Chowk)  
> **Master Specification:** [`TRAFFIC_MANAGEMENT.md`](../../FuturePlans/TRAFFIC_MANAGEMENT.md)  
> **Status:** Active Execution Blueprint

---

## 1. Executive Overview

This task suite translates the comprehensive architectural blueprint defined in [`TRAFFIC_MANAGEMENT.md`](../../FuturePlans/TRAFFIC_MANAGEMENT.md) into ten (10) modular, production-grade engineering tasks. Each task is self-contained with explicit mathematical formulations, database schemas, API data contracts, file targets, and acceptance criteria.

All tasks strictly uphold the architectural invariants defined in [`AGENTS.md`](../../AGENTS.md):
1. **Strict Non-Actuation:** Read-only decision support with dual-key human authorization.
2. **State Separation:** Strict partitioning between `LIVE`, `REPLAY`, `SIMULATION`, and `PREDICTED` records.
3. **Mandatory Provenance:** Every returned or visualized metric carries source mode, timestamp, unit, and quality score.
4. **Hermetic Test Isolation:** 100% self-contained automated tests passing in total isolation.
5. **Strictly Zero Emojis:** Professional vector iconography (Lucide React) and clean typography across all user interfaces.

---

## 2. Master Task Catalog

| Task ID | Task Title | Assignee | Spec Ref | Dependencies | Primary Deliverables |
|---|---|---|---|---|---|
| [`TASK-01`](./TASK-01-synthetic-traffic-generator.md) | Corridor Synthetic Telemetry Stream Generator | Engineer 1 (Backend) | §7.1 | None | `scripts/synthetic_traffic_generator.py`, schema migrations |
| [`TASK-02`](./TASK-02-sumo-actuated-tls-logic.md) | Dynamic Actuated Traffic Signal Control (TraCI) | Engineer 2 (Simulation) | §7.2 | None | `simulation/actuated_controller.py`, `tests/test_actuated_tls.py` |
| [`TASK-03`](./TASK-03-arterial-green-wave-optimizer.md) | Arterial Green Wave Two-Way Bandwidth Optimizer | Engineer 2 (Simulation) | §7.3 | None | `backend/services/green_wave_optimizer.py`, MAXBAND solver |
| [`TASK-04`](./TASK-04-transit-signal-priority.md) | Conditional Transit Signal Priority (TSP) Engine | Engineer 3 (Simulation) | §7.4 | `TASK-02` | `simulation/tsp_controller.py`, `tests/test_tsp_controller.py` |
| [`TASK-05`](./TASK-05-quantile-queue-forecasting.md) | Multi-Horizon Quantile Queue Length Forecaster | Engineer 4 (ML) | §8.1 | None | `ml/train_quantile_queue.py`, `ml/services/queue_forecast_service.py` |
| [`TASK-06`](./TASK-06-multimodal-transit-crowd-forecaster.md) | Transit Stop Crowd Flow & Dynamic Dwell Forecaster | Engineer 4 (ML) | §8.2 | None | `backend/services/transit_dwell_service.py`, surge alert evaluator |
| [`TASK-07`](./TASK-07-structural-health-monitoring.md) | Critical Infrastructure SHM Telemetry Pipeline | Engineer 1 (Backend) | §10.1 | None | `backend/services/shm_service.py`, `backend/api/v1/endpoints/shm.py` |
| [`TASK-08`](./TASK-08-spat-controller-feed-adapter.md) | Real-Time SPaT Controller Ingestion Adapter | Engineer 1 (Backend) | §7.3 | None | `backend/services/spat_adapter.py`, WebSocket live feed |
| [`TASK-09`](./TASK-09-spat-signal-head-3d-deckgl.md) | Deck.gl 3D Animated Signal Head & Queue Visualizer | Engineer 5 (Frontend) | §7.3, §11.2 | `TASK-08` | `SignalHeadLayer.tsx`, `LaneQueueLayer.tsx`, Map toolbar |
| [`TASK-10`](./TASK-10-closed-loop-decision-advisor-ui.md) | Operator Advisory Dossier & Audit Trail UI | Engineer 5 (Frontend) | §9.1, §9.2 | `TASK-03`, `TASK-05` | `AdvisoryCard.tsx`, `AuthorizeAdvisoryModal.tsx`, dispatch audit |

---

## 3. Work Allocation by Engineering Role

```
+-----------------------------------------------------------------------------------+
|                           ENGINEERING TEAM WORK ALLOCATION                        |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  [ Engineer 1: Backend & Telemetry ]                                             |
|  - TASK-01: Corridor Synthetic Telemetry Stream Generator (MQTT / Trajectories)    |
|  - TASK-07: Critical Infrastructure SHM Telemetry Pipeline (Vibration / Strain)   |
|  - TASK-08: Real-Time SPaT Controller Ingestion Adapter (NTCIP 1202 / J2735)      |
|                                                                                   |
|  [ Engineer 2: Simulation & Microscopic Modeling ]                                |
|  - TASK-02: Microscopic SUMO Actuated Traffic Signal Control (TraCI gap-out)      |
|  - TASK-03: Arterial Green Wave Two-Way Progression Optimizer (MAXBAND / MILP)    |
|                                                                                   |
|  [ Engineer 3: Simulation & Scenario Integration ]                                |
|  - TASK-04: Conditional Transit Signal Priority (TSP) Logic Engine                |
|                                                                                   |
|  [ Engineer 4: Machine Learning & Predictive Analytics ]                          |
|  - TASK-05: Multi-Horizon Quantile Queue Length Forecaster (XGBoost / TreeSHAP)   |
|  - TASK-06: Multimodal Transit Stop Crowd Flow & Dynamic Dwell Time Forecaster     |
|                                                                                   |
|  [ Engineer 5: Frontend & GIS Geospatial Visualization ]                          |
|  - TASK-09: Deck.gl 3D Animated Signal Head & Lane Queue Visualizer               |
|  - TASK-10: Operator Advisory Dossier & Audit Trail Decision Support UI           |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

---

## 4. Execution Dependency Flowchart

```mermaid
flowchart TD
    subgraph Data & Telemetry Ingestion [Engineer 1]
        T1["TASK-01<br/>Synthetic Telemetry Generator"]
        T7["TASK-07<br/>SHM Telemetry Pipeline"]
        T8["TASK-08<br/>SPaT Controller Adapter"]
    end

    subgraph Simulation Engines [Engineers 2 & 3]
        T2["TASK-02<br/>SUMO Actuated Signal Control"]
        T3["TASK-03<br/>Green Wave Bandwidth Optimizer"]
        T4["TASK-04<br/>Transit Signal Priority (TSP)"]
        T2 --> T4
    end

    subgraph Machine Learning [Engineer 4]
        T5["TASK-05<br/>Quantile Queue Length Forecaster"]
        T6["TASK-06<br/>Transit Stop Crowd & Dwell Forecaster"]
        T6 --> T4
    end

    subgraph Frontend & Operator UI [Engineer 5]
        T9["TASK-09<br/>3D Deck.gl Signal Heads & Queues"]
        T10["TASK-10<br/>Operator Advisory Dossier & Audit"]
        T8 --> T9
        T3 --> T10
        T5 --> T10
    end

    classDef primary fill:#1e293b,stroke:#06b6d4,stroke-width:2px,color:#f8fafc;
    class T1,T2,T3,T4,T5,T6,T7,T8,T9,T10 primary;
```

---

## 5. Definition of Done Checklist for Every Task

Before any task in this directory is signed off as completed, it must pass this verification protocol:
- [ ] **Architecture Check:** Fully conforms to the mathematical model and data schema outlined in its task specification.
- [ ] **State Separation Invariant:** Dynamic values persist strictly to designated tables (`traffic_flow_observations`, `simulation_runs`, `ml_forecasts`).
- [ ] **Data Honesty:** No replayed data labeled as live; confidence intervals and model baselines strictly documented.
- [ ] **Automated Tests:** Comprehensive unit and hermetic tests in `tests/` passing cleanly with 100% pass rate (`pytest`).
- [ ] **Build Validation:** If frontend components are modified, `npm run build` compiles with 0 errors.
- [ ] **Zero Emojis:** Strictly no emoji glyphs in code, logs, or UI elements.
- [ ] **Git Discipline:** Commit messages are clean, conventional, and contain zero phase tags or "phase" numbers.
