# Energy Management & Microgrid Optimization: Implementation Task Directory

> **System Component:** Pune Nagar Road & Commercial Facility Digital Twin (Viman Nagar Chowk Microgrid)  
> **Master Specification:** [`ENERGY_MANAGEMENT.md`](../../FuturePlans/ENERGY_MANAGEMENT.md)  
> **Status:** Active Execution Blueprint

---

## 1. Executive Overview

This task suite translates the engineering blueprint defined in [`ENERGY_MANAGEMENT.md`](../../FuturePlans/ENERGY_MANAGEMENT.md) into ten (10) modular, production-grade engineering tasks. Each task contains explicit mathematical models, electrical balance equations, database schemas, API contracts, target files, and acceptance criteria.

All tasks strictly uphold the architectural invariants defined in [`AGENTS.md`](../../AGENTS.md):
1. **Strict Non-Actuation:** Read-only decision support with dual-key human authorization for demand-response dispatches.
2. **State Separation:** Strict partitioning between `LIVE`, `REPLAY`, `SIMULATION`, and `PREDICTED` records.
3. **Mandatory Provenance:** Every electrical power, tariff, and thermal reading carries source mode, timestamp, unit, and quality score.
4. **Hermetic Test Isolation:** 100% self-contained automated tests passing in total isolation.
5. **Strictly Zero Emojis:** Professional vector iconography (Lucide React) and clean control-room typography.

---

## 2. Master Task Catalog

| Task ID | Task Title | Assignee | Spec Ref | Dependencies | Primary Deliverables |
|---|---|---|---|---|---|
| [`TASK-01`](./TASK-01-canonical-energy-asset-topology.md) | Canonical Electrical Network Topology & Multi-Asset Telemetry Engine | Engineer 1 (Backend) | §4, §5, §6 | None | `backend/services/energy_topology_service.py`, schema migrations |
| [`TASK-02`](./TASK-02-bus-power-balance-feeder-loading.md) | Electrical Bus Power Balance & Feeder Thermal Loading Engine | Engineer 1 (Backend) | §7.1 | `TASK-01` | `backend/services/power_balance_service.py`, thermal ampacity monitor |
| [`TASK-03`](./TASK-03-etp-thermal-occupancy-setback.md) | 2R-2C ETP Building Thermal Network & Dynamic Occupancy Setback Engine | Engineer 2 (Simulation) | §7.2, §7.3 | None | `backend/services/building_thermal_service.py`, ASHRAE 55 validator |
| [`TASK-04`](./TASK-04-quantile-load-forecasting.md) | Multi-Horizon Quantile Facility Load Forecaster (15m–24h) | Engineer 4 (ML) | §8.1 | `TASK-01` | `ml/models/quantile_load_forecaster.py`, CDD/HDD normalization |
| [`TASK-05`](./TASK-05-solar-pv-irradiance-forecasting.md) | Solar PV Generation & Irradiance Physical Forecasting Engine | Engineer 4 (ML) | §8.2 | None | `backend/services/solar_forecast_service.py`, PV derating model |
| [`TASK-06`](./TASK-06-bess-arbitrage-peak-shaving-optimizer.md) | BESS Battery Arbitrage & Time-of-Use Peak Shaving Optimizer | Engineer 2 (Optimization) | §9.1 | `TASK-02`, `TASK-04` | `backend/services/bess_optimizer.py`, ToU MILP solver |
| [`TASK-07`](./TASK-07-grid-safety-interlocks-openadr-gateway.md) | Grid Safety Interlocks & OpenADR / Modbus Failsafe Dispatch Gateway | Engineer 1 (Backend) | §9.2, §9.3 | `TASK-06` | `backend/services/grid_safety_gateway.py`, OpenADR 2.0b payload builder |
| [`TASK-08`](./TASK-08-interactive-microgrid-sld-canvas.md) | Interactive Microgrid Single-Line Diagram (SLD) & Power Flow Canvas | Engineer 5 (Frontend) | §4, §11 | `TASK-02` | `frontend/src/components/Microgrid/MicrogridSLDCanvas.tsx` |
| [`TASK-09`](./TASK-09-zone-thermal-comfort-occupancy-visualizer.md) | Building Floorplate 3D/2D Thermal Comfort & Occupancy Density Visualizer | Engineer 5 (Frontend) | §7.2, §7.3 | `TASK-03` | `frontend/src/components/Energy/ThermalComfortHeatmap.tsx` |
| [`TASK-10`](./TASK-10-human-in-the-loop-demand-response-dossier.md) | Human-in-the-Loop Demand-Response Advisory Dossier & Audit UI | Engineer 5 (Frontend) | §9.2, §10 | `TASK-06`, `TASK-07` | `frontend/src/components/Energy/DemandResponseDossierModal.tsx` |

---

## 3. Work Allocation by Engineering Role

```text
+-----------------------------------------------------------------------------------+
|                         ENERGY DOMAIN WORK ALLOCATION                             |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  [ Engineer 1: Backend, Electrical Topology & Protocol Adapters ]                 |
|  - TASK-01: Canonical Electrical Network Topology & Multi-Asset Telemetry Engine  |
|  - TASK-02: Electrical Bus Power Balance & Feeder Thermal Loading Engine          |
|  - TASK-07: Grid Safety Interlocks & OpenADR / Modbus Failsafe Dispatch Gateway   |
|                                                                                   |
|  [ Engineer 2: Optimization, Microgrid Physics & Thermal Modeling ]              |
|  - TASK-03: 2R-2C ETP Building Thermal Network & Dynamic Occupancy Setback Engine |
|  - TASK-06: BESS Battery Arbitrage & Time-of-Use Peak Shaving Optimizer (MILP)    |
|                                                                                   |
|  [ Engineer 4: Machine Learning & Predictive Analytics ]                          |
|  - TASK-04: Multi-Horizon Quantile Facility Load Forecaster (XGBoost / TreeSHAP)  |
|  - TASK-05: Solar PV Generation & Irradiance Physical Forecasting Engine         |
|                                                                                   |
|  [ Engineer 5: Frontend & Control Room Visualization ]                           |
|  - TASK-08: Interactive Microgrid Single-Line Diagram (SLD) & Power Flow Canvas  |
|  - TASK-09: Building Floorplate 3D/2D Thermal Comfort & Occupancy Visualizer      |
|  - TASK-10: Human-in-the-Loop Demand-Response Advisory Dossier & Audit UI        |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```
