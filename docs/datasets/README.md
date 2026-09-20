# Data Catalog & Provenance Index

All datasets utilized within the **Digital Twin** are cataloged here with explicit provenance classifications, licenses, and boundary statements. In accordance with [data_and_ml_plan.md](../specifications/data_and_ml_plan.md) and [AGENTS.md](../../AGENTS.md), non-local datasets and simulations are never presented as field-observed corridor truth.

## Master Dataset Directory

| ID | Dataset Name | Locality Classification | Default Provenance | License | Link to Manifest |
|---|---|---|---|---|---|
| **D-01** | OpenStreetMap Corridor Geometry | PILOT_LOCAL | `LIVE_EXTRACT` | ODbL 1.0 | [Registry](../../data/manifests/DATASET_REGISTRY.md#d-01) |
| **D-02** | OSMnx Corridor Network Model | PILOT_LOCAL | `DERIVED` | MIT | [Registry](../../data/manifests/DATASET_REGISTRY.md#d-02) |
| **D-03** | Pune Heterogeneous Traffic Counts | PUNE_NON_LOCAL | `REPLAY` | CC BY 4.0 | [Registry](../../data/manifests/DATASET_REGISTRY.md#d-03) |
| **D-04** | Pune Hourly Air Quality Reports | REGIONAL_CONTEXT | `REPLAY` | ODbL / OpenCity | [Registry](../../data/manifests/DATASET_REGISTRY.md#d-04) |
| **D-05** | Open-Meteo Historical & Current Weather | REGIONAL_CONTEXT | `LIVE_API` | CC BY 4.0 | [Registry](../../data/manifests/DATASET_REGISTRY.md#d-05) |
| **D-06** | Commercial Zone Energy Demand Profile | BENCHMARK_SYNTHETIC | `SIMULATION` | Project Open Derivative | [Registry](../../data/manifests/DATASET_REGISTRY.md#d-06) |
| **D-07** | SUMO Microscopic Traffic Simulation | SIMULATION | `SIMULATION` | EPL-2.0 | [Registry](../../data/manifests/DATASET_REGISTRY.md#d-07) |

---

## Provenance Rules & Non-Negotiable Boundaries
- **No Truth Pollution:** `SIMULATION` and `PREDICTED` data points must never overwrite authoritative ground-truth observations.
- **Locality Honesty:** Datasets recorded at other Pune junctions (e.g. Alankar Chowk or RTO Chowk in D-03) cannot be presented as Viman Nagar Chowk observations.
- **No PII:** The platform ingests zero personal travel traces, license plates, biometrics, or video surveillance feeds.
