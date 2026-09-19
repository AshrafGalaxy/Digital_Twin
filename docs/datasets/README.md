# Data Catalog & Provenance Index

All datasets utilized within the **Digital Twin** are cataloged here with explicit provenance classifications, licenses, and boundary statements. In accordance with [DATA_AND_ML_PLAN.md](../../DATA_AND_ML_PLAN.md) and [AGENTS.md](../../AGENTS.md), non-local datasets and simulations are never presented as field-observed corridor truth.

## Master Dataset Directory

| ID | Dataset Name | Locality Classification | Default Provenance | License | Link to Manifest |
|---|---|---|---|---|---|
| **D-01** | OpenStreetMap Corridor Geometry | PILOT_LOCAL | `LIVE_EXTRACT` | ODbL 1.0 | [D-01 Manifest](../../data/manifests/D-01-OpenStreetMap.md) |
| **D-02** | OSMnx Corridor Network Model | PILOT_LOCAL | `DERIVED` | MIT | [D-02 Manifest](../../data/manifests/D-02-OSMnx-Network.md) |
| **D-03** | Pune Heterogeneous Traffic Counts | PUNE_NON_LOCAL | `REPLAY` | CC BY 4.0 | [D-03 Manifest](../../data/manifests/D-03-Pune-Traffic-Counts.md) |
| **D-04** | Pune Hourly Air Quality Reports | REGIONAL_CONTEXT | `REPLAY` | ODbL / OpenCity | [D-04 Manifest](../../data/manifests/D-04-Pune-Hourly-AQI.md) |
| **D-05** | Open-Meteo Historical & Current Weather | REGIONAL_CONTEXT | `LIVE_API` | CC BY 4.0 | [D-05 Manifest](../../data/manifests/D-05-OpenMeteo-Weather.md) |
| **D-06** | Commercial Zone Energy Demand Profile | BENCHMARK_SYNTHETIC | `SIMULATION` | Project Open Derivative | [D-06 Manifest](../../data/manifests/D-06-Commercial-Energy-Profile.md) |
| **D-07** | SUMO Microscopic Traffic Simulation | SIMULATION | `SIMULATION` | EPL-2.0 | [D-07 Manifest](../../data/manifests/D-07-SUMO-Corridor-Simulation.md) |

---

## Provenance Rules & Non-Negotiable Boundaries
- **No Truth Pollution:** `SIMULATION` and `PREDICTED` data points must never overwrite authoritative ground-truth observations.
- **Locality Honesty:** Datasets recorded at other Pune junctions (e.g. Alankar Chowk or RTO Chowk in D-03) cannot be presented as Viman Nagar Chowk observations.
- **No PII:** The platform ingests zero personal travel traces, license plates, biometrics, or video surveillance feeds.
