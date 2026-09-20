# Medallion Data Lakehouse Storage Architecture
## Digital Twin-Enabled Smart City Analytics Platform

> **Status:** Binding Data Lakehouse specification  
> **Reference:** `DATA_AND_ML_PLAN.md` (§8.2, §19.1)  
> **Pilot Corridor:** Viman Nagar Chowk ↔ Somnath Nagar Chowk, Pune

---

## 1. Lakehouse Medallion Overview

The platform organizes physical and logical data into four standard medallion storage tiers to ensure strict data lineage, reproducibility, and provenance separation.

```text
[ Raw Layer ]             [ Bronze Layer ]           [ Silver Layer ]           [ Gold Layer ]
External Sources / APIs   Append-only parsed logs   Validated & Canonicalized   Features & Aggregates
Immutable source files   Preserves wire format      NGSI-LD entity contracts    Parquet / Marts
```

---

## 2. Directory Hierarchy

```text
data/
  ├── README.md                      <- This Lakehouse architecture specification
  ├── digital_twin.db                <- Primary SQLite WAL Operational Twin store (PostgreSQL/TimescaleDB in prod)
  ├── quarantine.db                  <- Quarantine store for invalid/schema-violating telemetry
  ├── study_area.geojson             <- Pilot corridor bounding boundary
  │
  ├── raw/                           <- Layer 1: Raw immutable source dumps & API payloads
  │   ├── osm/                       <- Raw OpenStreetMap .osm / .pbf extracts
  │   ├── traffic/                   <- Raw Pune intersection counts & benchmark CSVs (D-03)
  │   ├── weather/                   <- Raw Open-Meteo & Meteostat weather responses (D-05, D-06)
  │   ├── energy/                    <- Raw UCI electricity / commercial power load feeds (D-10)
  │   └── environment/               <- Raw CPCB / OpenCity air quality reports (D-04)
  │
  ├── bronze/                        <- Layer 2: Parsed, append-only event stream records
  │   └── ingest_events.jsonl        <- Raw MQTT / REST ingestion payload logs before normalization
  │
  ├── silver/                        <- Layer 3: Conformed, schema-validated canonical entities
  │   └── (Authoritative records stored in digital_twin.db tables: traffic_observations, etc.)
  │
  ├── gold/                          <- Layer 4: High-value analytical marts, features & rollups
  │   ├── features/                  <- Offline ML feature store tables (.parquet & .csv)
  │   │   ├── traffic_features_v1.parquet
  │   │   ├── energy_features_v1.parquet
  │   │   └── feature_manifest.json
  │   └── aggregates/                <- Continuous aggregates, 15m & 1h rollups
  │
  ├── synthetic/                     <- Synthetic calibration curves & baseline profiles
  ├── samples/                       <- Registered static corridor assets & sensor catalogs
  ├── manifests/                     <- Formal dataset manifests with licensing & attribution
  └── external-references/           <- Reference benchmarks (METR-LA, PEMS-BAY metadata)

artifacts/
  ├── models/                        <- Serialized trained model weights (.joblib)
  ├── mlflow/                        <- Local MLflow experiment tracking registry & run metrics
  ├── scenarios/                     <- SUMO simulation scenario definitions and KPIs
  └── reports/                       <- Model cards, evaluation benchmarks, and research reports
```

---

## 3. Tier Storage Policies

| Tier | Policy | Retention | Provenance Tag |
|---|---|---|---|
| **Raw** | Strictly immutable. Raw files, API JSON dumps, or benchmark CSV extracts. Never mutated in place. | Permanent | `REPLAY` / `LIVE` / `SIMULATION` |
| **Bronze** | Append-only. Parsed wire-format logs preserving original source timestamps and payloads. | 90 days rolling | Retains source tag |
| **Silver** | Cleaned, validated, conformed to canonical NGSI-LD schemas. Invalid records diverted to `quarantine.db`. | Indefinite | Explicitly assigned |
| **Gold** | Versioned, recomputable analytical datasets. Engineered feature tables for XGBoost, Timescale continuous rollups. | Versioned by model/feature ID | `PREDICTED` / Aggregated |

---

## 4. Provenance Rules

Every row in the Silver and Gold tiers must retain:
1. `source_mode`: `LIVE`, `REPLAY`, `SIMULATION`, or `PREDICTED`.
2. `source_id`: Unique identifier of the sensor, simulator seed, or replay file.
3. `observed_at`: Exact UTC timestamp of observation.
4. `ingested_at`: UTC timestamp of system arrival.
5. `data_quality_score` & `data_quality_status`: Range 0.0–1.0 and validity enum (`valid`, `suspect`, `stale`, `invalid`).
