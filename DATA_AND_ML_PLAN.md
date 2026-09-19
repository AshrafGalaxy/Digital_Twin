# Data and Machine Learning Plan
## Digital Twin-Enabled Smart City Analytics Platform

> **Document status:** Baseline data and ML specification  
> **Companion documents:** `PROJECT_CONTEXT.md`, `PRD.md`, `TECHNICAL_ARCHITECTURE.md`  
> **Pilot study area:** Viman Nagar Chowk (Phoenix Mall) ↔ Somnath Nagar Chowk corridor, Pune  
> **Scope:** Data acquisition, provenance, schemas, model inputs/outputs, training, evaluation, and research-validity rules  
> **Core principle:** Data quality, provenance, and valid evaluation matter more than model complexity.

---

## 1. Purpose

This document defines the data and machine-learning plan for the **Digital Twin-Enabled Smart City Analytics Platform**.

It answers:

- What data is required for the pilot?
- Which datasets are available and what may each dataset be used for?
- Which datasets are local, non-local, synthetic, replayed, or benchmark-only?
- What exact models are trained in the MVP?
- What data goes into each model?
- What does each model output?
- How will models be trained, validated, deployed, monitored, and explained?
- How will the project avoid invalid local-performance claims?
- What must agents document before using a dataset or model?

This document is binding for data, GIS, ML, simulation, backend, UI, evaluation, and research agents.

---

## 2. Data and ML strategy summary

### 2.1 MVP decision

The MVP trains **two primary supervised forecasting models**:

1. **Traffic forecasting model** — predicts average speed or congestion index 15 minutes ahead.
2. **Energy forecasting model** — predicts representative building/zone demand 60 minutes ahead.

The platform does **not** require a trained 3D model, a trained digital-twin model, a recommendation model, a traffic-signal control model, an LLM, a computer-vision model, or a graph neural network in the MVP.

### 2.2 Baseline-first rule

For every trained model:

```text
Simple baseline
        ↓
Feature-engineered XGBoost model
        ↓
Evaluation on future-held-out data
        ↓
Explanation and uncertainty
        ↓
Deployment only if evidence is adequate
```

A more complex model is never introduced merely to appear advanced.

### 2.3 Three compatible data modes

| Mode | Purpose | Required for MVP | Core rule |
|---|---|---:|---|
| `simulation` | Create repeatable SUMO and synthetic streams; test scenarios | Yes | Never presented as real measured city state |
| `replay` | Replay historical data as event streams | Yes | Keeps original observation time and shows `REPLAY` provenance |
| `live` | Ingest approved sensors/APIs | No | Must use the same canonical contract and pass validation |
| `predicted` | Store model forecasts | Yes | Never overwrites observed state |

All modes must transform into the same canonical contract before storage, feature generation, inference, and UI display.

---

## 3. Data-governance principles

### 3.1 Required principles

1. **Provenance first:** Every value must record where it came from and whether it is live, replayed, simulated, or predicted.
2. **Locality honesty:** Data collected at another intersection/city must never be described as pilot-corridor measurement.
3. **License compliance:** Every dataset must have source, license/terms, access date, attribution, and permitted-use documentation.
4. **No hidden transformations:** Cleaning, resampling, synthetic generation, imputation, and aggregation must be recorded.
5. **Privacy by exclusion:** Do not ingest CCTV, faces, plates, individual GPS traces, or personal energy/mobility records.
6. **Reproducibility:** Raw/source data, derived datasets, schemas, feature versions, model runs, and scenario inputs must be traceable.
7. **Data-quality transparency:** Missingness, staleness, outliers, and validation failures must be visible to downstream users and models.
8. **Simulation separation:** Simulation output is useful for software/system validation and scenario analysis, not proof of real-world intervention impact.

### 3.2 Dataset admission checklist

A dataset may enter the project only after recording:

- Dataset name.
- Source organization and direct URL.
- License/terms of use.
- Access/download date.
- Geographic coverage.
- Temporal coverage.
- Sampling frequency.
- Fields and units.
- Personal/sensitive-data assessment.
- Intended use category.
- Known limitations.
- Attribution requirement.
- Data owner/contact if applicable.

---

## 4. Data source catalog

### 4.1 Primary pilot sources

| ID | Source | Direct link | Data provided | Intended use | Geographic relevance | Important limitation |
|---|---|---|---|---|---|---|
| D-01 | OpenStreetMap | [openstreetmap.org](https://www.openstreetmap.org/) | Roads, junctions, geometry, building footprints, tags | Study-area geometry, MapLibre, SUMO network input | Directly usable for Viman Nagar area | Attribute completeness, lane counts, turn restrictions, and signal metadata need validation |
| D-02 | OSMnx | [GitHub](https://github.com/gboeing/osmnx) | Python tools to retrieve/model OSM network | Study-area extraction, network graph, geometry processing | Directly usable for Viman Nagar area | OSM source quality constraints remain |
| D-03 | Pune heterogeneous traffic count dataset | [Mendeley Data](https://data.mendeley.com/datasets/xnf2k6n288/1) | Directional, vehicle-class-wise traffic counts from 3 signalized Pune intersections | First traffic-model prototype, feature engineering, replay, demand-profile inspiration | Pune-wide contextual relevance, not pilot-local | Recorded at Alankar Chowk, Jehangir Chowk, and RTO Chowk; short time duration; cannot establish Viman Nagar accuracy |
| D-04 | Pune Hourly Air Quality Reports | [OpenCity](https://data.opencity.in/dataset/pune-hourly-air-quality-reports) | Historical AQI/pollutant reports for Pune stations | Environmental context, replay, threshold alerts | Pune regional context | Station readings are not necessarily corridor-level values |
| D-05 | Meteostat historical data | [Meteostat](https://dev.meteostat.net/data) | Weather/climate time series, station data | Traffic/energy features, weather context | Pune-area station/point context | Coverage and completeness vary by station/date |
| D-06 | Open-Meteo historical weather API | [API documentation](https://open-meteo.com/en/docs/historical-weather-api) | Historical/reanalysis weather by coordinates | Weather alternative/fallback, reproducible feature retrieval | Coordinate-based Pune area | API/reanalysis values are not local sensor truth; requests must be logged |
| D-07 | Pune electricity consumption data | [OpenCity](https://data.opencity.in/dataset/pune-electricity-consumption-data) | Historic sector/city electricity data | Context, energy-domain understanding | Pune-level context | Not building-level high-frequency data for direct pilot energy forecasting |
| D-08 | Pune Corporation Open Data Portal | [opendata.pmc.gov.in](https://opendata.pmc.gov.in/) | City datasets; availability may change | Discovery/optional public datasets | Pune context | Must inspect license, schema, freshness, and downloadability individually |
| D-09 | Smart Cities Mission Pune portal | [smartcities.data.gov.in](https://smartcities.data.gov.in/cities/Pune) | Government catalog/discovery | Dataset discovery and institutional context | Pune context | Catalog availability does not guarantee stream/API access |

### 4.2 Benchmark and development datasets

| ID | Source | Direct link | Intended use | Must not be used for |
|---|---|---|---|---|
| D-10 | UCI Electricity Load Diagrams 2011–2014 | [UCI dataset](https://archive.ics.uci.edu/dataset/321/electricityloaddiagrams20112014) | Energy model pipeline, feature testing, benchmark forecasting | Claiming Viman Nagar/Pune building-energy accuracy |
| D-11 | METR-LA / PEMS-BAY CSV | [Zenodo](https://zenodo.org/records/5146275) | Advanced traffic benchmark, research comparison, future GNN experiment | Local Pune deployment claim or pilot corridor calibration |
| D-12 | DCRNN repository | [GitHub](https://github.com/liyaguang/DCRNN) | Reference implementation for advanced traffic forecasting | MVP dependency or unvalidated pretrained deployment |
| D-13 | Microsoft StemGNN | [GitHub](https://github.com/microsoft/StemGNN) | Advanced multivariate time-series research reference | MVP dependency or local accuracy claim |
| D-14 | Monash Time Series Forecasting Repository | [Hugging Face](https://huggingface.co/datasets/Monash-University/monash_tsf) | Forecasting benchmark/pipeline testing | Local urban performance claim |
| D-15 | PEMS-BAY on Hugging Face | [Hugging Face](https://huggingface.co/datasets/THUgewu/PEMS-BAY) | Convenient benchmark access | Pune-specific training evidence |
| D-16 | METR-LA on Hugging Face | [Hugging Face](https://huggingface.co/datasets/witgaw/METR-LA) | Convenient benchmark access | Pune-specific training evidence |

### 4.3 Optional pilot-local data collection

| ID | Source | Collection method | Use | Conditions |
|---|---|---|---|---|
| D-17 | Manual corridor traffic counts | Observation at selected pilot points, aggregate counts only | Calibration sanity check; local replay data | No personal data/video retention; record observation protocol |
| D-18 | Permitted building/campus aggregate meter export | Written permission from facility authority | Best energy training/replay data | Use aggregate/non-personal data; document consent/retention |
| D-19 | Low-cost environmental sensor | ESP32/Raspberry Pi + approved sensor, if available | Optional local environmental stream | Calibrate/document accuracy; do not claim regulatory-grade AQI |
| D-20 | Public permitted traffic/API source | Approved API with terms compliance | Optional live/replay context | Do not violate terms, scrape restricted sources, or assume free access |

---

## 5. Dataset selection decisions

### 5.1 Traffic dataset decision

**Primary initial traffic-model dataset:** D-03, Pune heterogeneous traffic count dataset.

Why:

- Pune-specific traffic composition is more relevant than foreign benchmarks.
- Contains directional and vehicle-class-wise counts from signalized intersections.
- Useful for traffic feature design, replay pipeline, and a first XGBoost proof of concept.
- Suitable for understanding heterogeneous Indian urban traffic patterns.

Limitations:

- It is not from Viman Nagar/Somnath Nagar.
- Its coverage is limited to three other Pune intersections.
- A short dataset cannot demonstrate robustness to long seasonal variation.
- It may provide counts rather than all desired speed/congestion targets.

**Required wording in reports:**

> The initial traffic forecasting pipeline is trained/evaluated using publicly available Pune intersection observations. It validates the architecture and forecasting workflow but does not establish measured prediction accuracy for the Viman Nagar–Somnath Nagar pilot corridor.

### 5.2 Pilot corridor traffic-state decision

**Primary pilot-corridor state source:** SUMO-generated and replayed traffic data based on the extracted Viman Nagar–Somnath Nagar network.

Why:

- The project needs corridor-specific entity IDs, routes, signal logic, queues, travel times, and intervention scenarios.
- SUMO supports controlled baseline/intervention comparison.
- Local live operational data is not assumed available.

Required labeling:

- SUMO output: `SIMULATION`.
- Historical data replay: `REPLAY`.
- Any later approved real feed: `LIVE`.

### 5.3 Energy dataset decision

**Priority order:**

1. Permitted aggregate meter data from a campus/building/facility.
2. Replayed public/benchmark load data used as a representative entity.
3. Transparent synthetic load generator.

**Use UCI Electricity Load Diagrams only for:**

- Testing the energy forecasting pipeline.
- Evaluating XGBoost vs baseline on high-frequency electricity series.
- Demonstrating reproducible ML methodology.

**Do not use UCI data to claim:**

- Pune local energy patterns.
- Viman Nagar building behavior.
- Actual peak-reduction savings.

### 5.4 Weather data decision

Use Meteostat as the first historical weather source and Open-Meteo as coordinate-based fallback. Store:

- retrieval source;
- coordinates/station;
- request parameters;
- time zone;
- units;
- retrieval time;
- resampling method.

### 5.5 Environmental data decision

Use Pune OpenCity/CPCB-derived station data as **regional context**. The UI must show station/source name and caution that it may not describe exact micro-location conditions at the pilot corridor.

---

## 6. Data source-to-feature mapping

| Domain | Required data | Preferred source | Fallback | Use in product |
|---|---|---|---|---|
| Study area/GIS | Roads, junctions, direction, geometry, buildings | OSM + manual validation | Hand-curated GeoJSON | Map, PostGIS, SUMO input |
| Traffic observation | Counts, speed, congestion, direction, timestamp | Pune dataset + SUMO | Manual aggregate counts | Model training, replay, twin state |
| Traffic scenario | Network, demand, routes, signals | SUMO + OSM-derived network | Small hand-built SUMO network | What-if comparison |
| Weather | Temperature, precipitation, humidity, wind | Meteostat | Open-Meteo | Model feature/context |
| Energy | Time-stamped kWh/kW | Permitted meter data | UCI replay/synthetic curve | Energy model/twin state |
| Environment | AQI/PM, weather | OpenCity/CPCB | Approved external API/synthetic test stream | Context/alerts |
| Model benchmark | Multi-node traffic/electricity series | METR-LA/PEMS/UCI/Monash | None | Research comparison only |

---

## 7. Canonical data requirements

### 7.1 Required provenance fields

Every observation, forecast, scenario output, and recommendation must include:

```json
{
  "sourceMode": "simulation | replay | live | predicted",
  "sourceId": "source-or-run-identifier",
  "observedAt": "ISO-8601 UTC timestamp",
  "ingestedAt": "ISO-8601 UTC timestamp",
  "dataQualityScore": 0.0,
  "dataQualityStatus": "valid | suspect | stale | duplicate | invalid | missing",
  "units": {},
  "schemaVersion": "v1"
}
```

### 7.2 Core static entities

| Entity | Minimum required fields |
|---|---|
| StudyArea | ID, name, boundary geometry, version, source, capture date |
| RoadSegment | ID, name, geometry, direction, lane count if known, capacity assumption, from/to intersection |
| Intersection | ID, name, geometry, connected road IDs, signal/priority assumption |
| TrafficSensor | ID, location/ref, observed entity, source mode, metric types |
| BuildingZone | ID, geometry/ref, category, energy source metadata |
| EnergyMeter | ID, building/zone reference, metric/unit, source mode |
| WeatherStation | ID, coordinates, source, station/API metadata |
| AirQualityStation | ID, coordinates, source, pollutants/metrics |
| ScenarioTemplate | ID, version, permitted parameters, network version |

### 7.3 Traffic observation schema

```json
{
  "id": "urn:ngsi-ld:TrafficFlowObserved:segment-001:2026-09-19T12:00:00Z",
  "type": "TrafficFlowObserved",
  "entityId": "urn:ngsi-ld:RoadSegment:segment-001",
  "observedAt": "2026-09-19T12:00:00Z",
  "sourceMode": "simulation",
  "sourceId": "sumo:baseline-run-001",
  "averageVehicleSpeed": 24.8,
  "vehicleCount": 54,
  "congestionIndex": 0.46,
  "direction": "eastbound",
  "locationRef": "urn:ngsi-ld:RoadSegment:segment-001",
  "units": {
    "averageVehicleSpeed": "km/h",
    "vehicleCount": "vehicles",
    "congestionIndex": "ratio"
  },
  "dataQualityScore": 1.0,
  "dataQualityStatus": "valid",
  "ingestedAt": "2026-09-19T12:00:02Z",
  "schemaVersion": "v1"
}
```

### 7.4 Energy observation schema

```json
{
  "id": "urn:ngsi-ld:EnergyConsumptionObserved:building-zone-001:2026-09-19T12:00:00Z",
  "type": "EnergyConsumptionObserved",
  "entityId": "urn:ngsi-ld:BuildingZone:building-zone-001",
  "observedAt": "2026-09-19T12:00:00Z",
  "sourceMode": "replay",
  "sourceId": "uci-electricity:client-001",
  "energyDemand": 12.7,
  "metricType": "load",
  "units": {
    "energyDemand": "kW"
  },
  "dataQualityScore": 0.95,
  "dataQualityStatus": "valid",
  "ingestedAt": "2026-09-19T12:00:04Z",
  "schemaVersion": "v1"
}
```

### 7.5 Forecast schema

```json
{
  "id": "urn:ngsi-ld:Forecast:traffic-segment-001:2026-09-19T12:15:00Z",
  "type": "TrafficForecast",
  "targetEntityId": "urn:ngsi-ld:RoadSegment:segment-001",
  "targetMetric": "congestionIndex",
  "generatedAt": "2026-09-19T12:00:00Z",
  "targetTime": "2026-09-19T12:15:00Z",
  "horizonMinutes": 15,
  "prediction": 0.71,
  "lowerBound": 0.62,
  "upperBound": 0.80,
  "modelVersion": "traffic-xgb-v1",
  "sourceMode": "predicted",
  "inputCompleteness": 0.95,
  "explanationRef": "artifact://mlflow/...",
  "dataQualityStatus": "valid",
  "schemaVersion": "v1"
}
```

---

## 8. Data ingestion and preparation plan

### 8.1 Ingestion pipeline

```text
Source file / API / SUMO / optional sensor
        ↓
Adapter or publisher
        ↓
MQTT topic or scheduled ingestion job
        ↓
Schema, unit, timestamp, identity, range, and duplicate validation
        ↓
Canonical entity transformation
        ↓
PostgreSQL/TimescaleDB/PostGIS persistence
        ↓
Current-state projection
        ↓
Feature generation / forecast scheduling
        ↓
Dashboard/API/WebSocket output
```

### 8.2 Raw, bronze, silver, gold conceptual layers

The project may use these logical layers even if all are stored in one database/object-storage setup.

| Layer | Content | Mutation policy |
|---|---|---|
| Raw | Original downloaded files/API responses/SUMO raw output | Immutable; retain source metadata |
| Bronze | Parsed but minimally transformed records | Immutable or append-only |
| Silver | Validated/canonicalized observations | Append-only; quality flags allowed |
| Gold | Aggregates, features, forecasts, KPI summaries, dashboard-ready views | Recomputable/versioned |

### 8.3 Required transformations

| Transformation | Reason |
|---|---|
| Timestamp normalization to UTC | Prevent time-zone ambiguity |
| Unit normalization | Ensure comparable speed/energy/environment values |
| Entity ID mapping | Connect source records to pilot twin entities |
| Direction mapping | Support approach/road-segment traffic context |
| Resampling | Align sources to selected 5/10/15-minute interval |
| Missing-value flags | Prevent silent false precision |
| Duplicate detection | Protect counts/current state |
| Outlier/range checks | Prevent impossible observations entering models |
| Feature-window generation | Create leakage-safe ML inputs |

### 8.4 Data interval decision

**Recommended initial interval: 5 minutes for raw/traffic where available; 15 minutes for first model feature/prediction windows if data is sparse.**

Rationale:

- 5 minutes is common in traffic benchmarks and provides temporal resolution.
- The Pune traffic dataset is described as approximately 5-minute aggregated intervals.
- A 15-minute forecast horizon is manageable and meaningful for corridor monitoring.
- Energy data may be 15-minute or hourly depending on source; resampling must be documented.

Final interval selection must be recorded before feature generation and cannot be changed without recreating experiments.

---

## 9. Data-quality plan

### 9.1 Validation checks

| Category | Validation |
|---|---|
| Schema | Required fields, field types, allowed enumerations |
| Time | Valid ISO-8601, UTC conversion, no impossible future time, freshness limit |
| Identity | Known entity/source IDs or approved registration workflow |
| Units | Explicit, supported, convertable units |
| Range | Non-negative count/load, reasonable speed/AQI/weather ranges |
| Spatial | Valid reference/geometry coordinate ranges |
| Completeness | Required target and timestamp present; optional-feature missingness tracked |
| Duplicate | Event ID or deterministic hash check |
| Consistency | Source mode, entity type, metric type, and unit compatible |

### 9.2 Example range rules

These are validation guards, not scientific limits. Final values require review.

| Metric | Initial guard |
|---|---|
| Vehicle count | Integer ≥ 0 |
| Average speed | 0–160 km/h; values outside range are suspect/invalid by context |
| Congestion index | 0–1 if using normalized index |
| Energy demand | ≥ 0; upper sanity cap configured per source/entity |
| Temperature | -10 to 60 °C for generic validation |
| Relative humidity | 0–100% |
| AQI | ≥ 0; station/source-specific scale documented |

### 9.3 Missing data policy

| Situation | Policy |
|---|---|
| Missing current observation | Mark entity stale after configured threshold; retain last known state with stale label |
| Missing non-critical feature | Use model-supported missing handling only if documented; record completeness score |
| Missing target in training | Exclude row from supervised target training; do not impute target |
| Short gap in continuous feature | Use documented forward-fill/interpolation only after split to avoid leakage |
| Long gap | Mark missing; exclude/impute only with justified procedure |
| API unavailable | Mark context stale; do not block unrelated pipeline functions |

### 9.4 Outlier policy

- Do not delete values solely because they are unusual.
- Flag values outside physical/schema bounds as invalid/suspect.
- Compare unusual but possible events against source mode and scenario context.
- Preserve raw input and reason for exclusion.
- Report outlier handling in model cards/evaluation.

---

## 10. Traffic forecasting plan

### 10.1 Objective

Forecast one selected traffic target for a specific road segment/intersection **15 minutes ahead**.

### 10.2 Target-selection decision

Choose one primary target before training:

| Candidate target | Recommended use | Notes |
|---|---|---|
| Average speed | Preferred if SUMO/live/source speed is available | Intuitive for users and supports travel-time interpretation |
| Congestion index | Preferred if normalized speed/capacity metric is consistently available | Useful map overlay; formula must be documented |
| Vehicle count | Use when only count data is reliably available | Good for demand/queue context but less direct corridor performance measure |
| Travel time | Future extension | Requires reliable route/segment calculation |
| Queue length | Scenario KPI first; future forecast target | More dependent on simulator/network configuration |

**Recommended MVP target:** average speed if available; otherwise a clearly defined congestion index derived consistently from traffic counts/speed assumptions.

### 10.3 Input features

| Feature group | Candidate features | Required? |
|---|---|---:|
| Traffic history | Previous speed/count/congestion values; lags at 5/10/15/30/60 minutes | Yes |
| Rolling statistics | Mean, min, max, standard deviation over defined windows | Yes |
| Calendar | Hour, minute bucket, day of week, weekend/holiday flag | Yes |
| Road context | Segment ID, lane count, capacity assumption, direction | Yes where available |
| Weather | Temperature, precipitation, humidity, wind | Should |
| Junction/signal context | Signal phase/approach/turn flag if simulation data provides it | Should |
| Neighbor context | Aggregated nearby segment status | Could; only after topology and data alignment are correct |
| Incident/event context | Manual event flag if available | Could |

### 10.4 Baselines

| Baseline | Formula/use |
|---|---|
| Persistence | \(\hat{y}_{t+h}=y_t\) |
| Historical average | Mean for equivalent time-of-day/day-of-week bucket where enough history exists |

A primary model must be compared against at least persistence.

### 10.5 Selected model

**XGBoost regressor**.

Reasons:

- Strong performance on tabular/time-lag engineered data.
- Trains quickly on laptop-scale data.
- Supports missing values in tree-based operation, while quality/completeness must still be tracked.
- Offers feature importance and SHAP compatibility.
- Lower operational and tuning complexity than deep temporal/spatial models.

### 10.6 Training dataset construction

```text
Validated traffic observations
        ↓
Sort by entity and observation time
        ↓
Resample to chosen interval
        ↓
Create lag/rolling/calendar/weather features using only prior data
        ↓
Create target shifted forward by 15 minutes
        ↓
Remove rows lacking target or required history
        ↓
Chronological split
        ↓
Train baseline and XGBoost
```

### 10.7 Chronological evaluation split

Never randomly shuffle a time series before splitting.

Recommended initial split:

```text
First 60–70% of time: training
Next 15–20%: validation/tuning
Last 15–20%: final test
```

If using several entities, preserve time ordering for every entity and avoid future information leaking into earlier rows.

### 10.8 Required output

```json
{
  "targetEntityId": "urn:ngsi-ld:RoadSegment:segment-001",
  "targetMetric": "averageVehicleSpeed",
  "generatedAt": "2026-09-19T12:00:00Z",
  "targetTime": "2026-09-19T12:15:00Z",
  "horizonMinutes": 15,
  "prediction": 24.8,
  "lowerBound": 20.4,
  "upperBound": 29.1,
  "unit": "km/h",
  "modelVersion": "traffic-xgb-v1",
  "inputCompleteness": 0.95,
  "sourceMode": "predicted"
}
```

### 10.9 Metrics

| Metric | Why required |
|---|---|
| MAE | Easy-to-interpret average absolute error |
| RMSE | Penalizes larger errors |
| sMAPE/MAPE | Optional relative error where no near-zero instability occurs |
| Prediction-interval coverage | Required if intervals are shown |
| Inference latency | System performance evidence |
| Completeness rate | Input-data quality context |

### 10.10 Locality limitation

A model trained on D-03 is a **Pune intersection prototype model**, not a calibrated Viman Nagar corridor model. The pilot UI and research report must state this where model results are presented.

---

## 11. Energy forecasting plan

### 11.1 Objective

Forecast energy demand/load for one representative building/zone entity **60 minutes ahead**.

### 11.2 Energy source hierarchy

| Priority | Source type | Research validity |
|---:|---|---|
| 1 | Permitted aggregate local meter data | Highest pilot relevance |
| 2 | Approved aggregate institutional/utility data | High if geography/entity relationship documented |
| 3 | Replayed benchmark series | Good for pipeline/model evaluation; not local claim |
| 4 | Synthetic load generator | Good for system demo only; clearly simulated |

### 11.3 Input features

| Feature group | Candidate features | Required? |
|---|---|---:|
| Load history | Lags, rolling mean/min/max/std | Yes |
| Calendar | Hour, weekday, weekend, holiday flag | Yes |
| Weather | Temperature, humidity, precipitation, irradiance if available | Should |
| Building/zone metadata | Type, floor area/category proxy, operating profile | Could |
| Occupancy proxy | Schedule or aggregate occupancy indicator | Could; only if non-personal |
| Energy context | Solar/EV/HVAC schedule if available | Future |

### 11.4 Baselines

| Baseline | Formula/use |
|---|---|
| Persistence | \(\hat{y}_{t+h}=y_t\) |
| Same-hour historical average | Average demand for comparable hour/day bucket |

### 11.5 Selected model

**XGBoost regressor**, using lagged load, calendar, and weather features.

### 11.6 Required output

```json
{
  "targetEntityId": "urn:ngsi-ld:BuildingZone:building-zone-001",
  "targetMetric": "energyDemand",
  "generatedAt": "2026-09-19T12:00:00Z",
  "targetTime": "2026-09-19T13:00:00Z",
  "horizonMinutes": 60,
  "prediction": 12.7,
  "lowerBound": 11.1,
  "upperBound": 14.4,
  "unit": "kW",
  "modelVersion": "energy-xgb-v1",
  "inputCompleteness": 0.90,
  "sourceMode": "predicted",
  "underlyingDataMode": "replay"
}
```

### 11.7 Metrics and limitations

Use MAE/RMSE, optionally sMAPE. If the underlying data is UCI or synthetic, reports must say:

> This model demonstrates the energy-forecasting pipeline on replayed/synthetic/benchmark series and does not measure actual demand or savings for a Viman Nagar building.

---

## 12. Environment analytics plan

### 12.1 MVP objective

Provide environmental context and transparent threshold-based alerts; do not overstate the environmental module as a localized predictive air-quality twin.

### 12.2 Inputs

- AQI and/or pollutant values from documented Pune station source.
- Weather variables.
- Station coordinates/source metadata.
- Observation timestamp and freshness.

### 12.3 MVP logic

```text
If value exceeds documented threshold
→ create environment advisory/alert
→ show metric, threshold, station/source, timestamp, quality, and geographic caveat
```

### 12.4 Optional anomaly model

Isolation Forest may be added only if:

- enough continuous station/sensor history exists;
- a false-positive/false-negative evaluation plan exists;
- anomaly meaning is reviewed rather than assumed;
- the result is shown as an anomaly score, not a confirmed environmental incident.

---

## 13. Recommendation data and rule plan

### 13.1 Rule inputs

| Rule domain | Inputs |
|---|---|
| Traffic advisory | Forecast target, interval/confidence, input completeness, current state, threshold, optional scenario KPI |
| Energy advisory | Load forecast, peak threshold, source quality, optional demand scenario |
| Environment advisory | AQI/pollutant value, threshold, station/source quality/freshness |

### 13.2 Minimum recommendation evidence

```json
{
  "recommendationId": "recommendation-001",
  "type": "traffic",
  "status": "advisory",
  "targetEntityId": "urn:ngsi-ld:RoadSegment:segment-001",
  "triggerRuleId": "traffic-congestion-v1",
  "trigger": "15-minute predicted congestion >= 0.70",
  "evidence": {
    "currentValue": 0.55,
    "forecastValue": 0.71,
    "forecastInterval": [0.62, 0.80],
    "inputCompleteness": 0.95,
    "sourceMode": "predicted",
    "modelVersion": "traffic-xgb-v1"
  },
  "suggestedAction": "Review approved signal-timing scenario before considering corridor intervention.",
  "linkedScenarioRunId": "optional",
  "requiresHumanApproval": true,
  "createdAt": "2026-09-19T12:00:00Z"
}
```

### 13.3 Rule governance

- Thresholds are configuration, not hidden code constants.
- Rule changes must be versioned/audited.
- Recommendations must include source quality and uncertainty.
- A recommendation is not a command or official government directive.

---

## 14. Prediction uncertainty plan

### 14.1 Requirement

If forecast intervals are displayed, their construction method must be explicit and evaluated.

### 14.2 Candidate methods

| Method | Suitability | MVP decision status |
|---|---|---|
| XGBoost quantile regression | Practical; trains lower/median/upper quantile models | Recommended initial option |
| Conformal prediction | Strong distribution-free coverage framing; requires careful calibration split | Recommended research-quality option |
| Bootstrap ensemble | Conceptually accessible but can increase runtime | Optional |
| Neural probabilistic models | Unnecessary complexity for MVP | Deferred |

### 14.3 Recommended choice

Start with **quantile XGBoost** if prediction intervals are needed early. Move to conformal prediction if the evaluation/paper focuses on calibrated uncertainty.

### 14.4 Evaluation

Report:

- Interval coverage probability.
- Average interval width.
- Coverage by data mode where meaningful.
- Cases where low input completeness reduces confidence.

---

## 15. ML experiment tracking and model registry

### 15.1 Required MLflow fields

Every training run must log:

| Category | Required fields |
|---|---|
| Data | Dataset ID/version/hash, source mode, geography, time range, sampling interval |
| Split | Train/validation/test dates and entity filters |
| Features | Feature list/version, imputation policy, scaling/encoding policy |
| Model | Algorithm, hyperparameters, random seed, library version |
| Evaluation | MAE, RMSE, optional sMAPE, interval metrics, baseline metrics |
| Artifact | Model file, feature schema, plots, SHAP summary, evaluation report |
| Validity | Locality limitations, simulation/replay/synthetic status |

### 15.2 Model status lifecycle

```text
draft
  → evaluated
  → approved-for-demo
  → active
  → superseded / archived
```

Only a model marked `approved-for-demo` or `active` may generate dashboard forecasts.

### 15.3 Model card requirement

Create one model card per active model version. Each card must state:

- Intended target and horizon.
- Input features.
- Training data and geography.
- Evaluation split and metrics.
- Baseline comparison.
- Known limitations/failure modes.
- Appropriate uses and prohibited uses.
- Provenance/prediction interpretation.

---

## 16. Training and inference deployment plan

### 16.1 Training

- Training runs offline/on-demand from versioned data extracts.
- Training must not run automatically on unreviewed incoming data in MVP.
- Store trained artifact in MLflow and/or MinIO/local artifact path.
- Register metadata in database/model registry.

### 16.2 Scheduled inference

```text
Every configured interval (recommended 5 minutes):
  1. Query current/history/context features.
  2. Check feature completeness/freshness.
  3. Load approved model version.
  4. Generate forecast and interval.
  5. Store forecast separately.
  6. Evaluate recommendation rules.
  7. Publish dashboard update.
```

### 16.3 Failure behavior

| Failure | Required behavior |
|---|---|
| Model artifact cannot load | Log error; mark forecast unavailable; do not fabricate value |
| Required features missing | Skip target forecast; expose reason and completeness state |
| Source stale | Use configured policy; forecast may be withheld or labeled low-quality |
| Inference exceeds expected time | Log latency; report status; investigate before increasing complexity |
| Model underperforms baseline | Keep baseline as active/default and report result honestly |

---

## 17. Simulation-data relationship

### 17.1 Purpose of SUMO data

SUMO output is used for:

- Building corridor-specific traffic state streams.
- Testing ingestion/twin/dashboard behavior.
- Creating repeatable traffic feature data.
- Running controlled baseline-versus-intervention comparisons.
- Visualizing vehicles, congestion, queues, and scenario KPIs.

### 17.2 SUMO data must not be used to claim

- Measured real-world traffic condition at Viman Nagar.
- Validated real-world traffic-signal performance.
- Confirmed travel-time savings for citizens.
- Official city operational recommendation.

### 17.3 Simulation-to-real mitigation plan

1. Use OSM geometry and reasonable documented network assumptions.
2. Use Pune traffic counts to inform demand patterns where compatible.
3. Collect small aggregate manual local counts if permitted.
4. Compare simulation patterns to publicly observable conditions only as qualitative sanity check.
5. Keep all claims bounded to simulation unless real local validation is obtained.

---

## 18. Evaluation plan

### 18.1 Required experiments

| ID | Experiment | Evidence produced |
|---|---|---|
| E-01 | Traffic persistence baseline vs XGBoost | MAE/RMSE comparison on chronological holdout |
| E-02 | Energy persistence baseline vs XGBoost | MAE/RMSE comparison on chronological holdout |
| E-03 | Traffic feature ablation | With/without weather or selected feature group comparison |
| E-04 | End-to-end pipeline latency | Source event to dashboard/twin-state latency distribution |
| E-05 | Data-quality resilience | Missing/duplicate/stale event handling evidence |
| E-06 | SUMO baseline vs intervention | Travel-time/delay/queue/throughput KPI deltas |
| E-07 | Forecast uncertainty evaluation | Coverage/width if intervals implemented |
| E-08 | Usability/task walkthrough | Operator can inspect, forecast, scenario-test, and interpret provenance |

### 18.2 Minimum metrics

| Category | Metrics |
|---|---|
| Traffic/energy forecasting | MAE, RMSE, optional sMAPE |
| Baseline comparison | Delta/improvement or honest non-improvement |
| Uncertainty | Interval coverage, interval width |
| Ingestion/system | End-to-end latency, rejected/duplicate rate, freshness/completeness |
| Simulation | Travel time, delay, queue, throughput |
| UI/usability | Task completion, provenance comprehension, qualitative feedback |

### 18.3 Evaluation validity rules

- Use future-held-out chronological data for forecast evaluation.
- Do not tune on the final test set.
- Do not compare models trained on different data splits without stating it.
- Do not compare synthetic and real results as equivalent.
- Do not report only favorable metrics.
- Report dataset size, duration, missingness, and geographic limitations.

---

## 19. Dataset directory and versioning convention

### 19.1 Suggested directory structure

```text
data/
  README.md
  raw/
    osm/
    traffic/
    weather/
    energy/
    environment/
  bronze/
  silver/
  gold/
  external-references/
  synthetic/
  samples/

artifacts/
  models/
  mlflow/
  scenarios/
  reports/
```

### 19.2 Source-control policy

- Do not commit large raw datasets, secrets, or proprietary data to Git.
- Commit small documented samples suitable for tests/demo.
- Store large artifacts in MinIO/local ignored path/release storage as appropriate.
- Commit download scripts, checksums, schemas, and dataset metadata.
- Use a dataset manifest file for every imported dataset.

### 19.3 Dataset manifest template

```yaml
dataset_id: D-03
name: Pune heterogeneous traffic count dataset
source_url: https://data.mendeley.com/datasets/xnf2k6n288/1
accessed_at: 2026-09-19
license: VERIFY_BEFORE_USE
geography: Alankar Chowk, Jehangir Chowk, RTO Chowk, Pune
pilot_locality: non_local_pune
frequency: approximately_5_minutes
intended_use:
  - traffic_model_prototype
  - feature_engineering
  - replay
prohibited_claims:
  - Viman_Nagar_measured_accuracy
limitations:
  - short_duration
  - different_intersections
  - unknown_transferability
attribution_required: true
raw_file_checksum: TO_BE_FILLED
```

---

## 20. Agent responsibilities

| Agent | Data/ML responsibilities | Must not do |
|---|---|---|
| Data/GIS agent | Study-area extraction, source manifests, entity mapping, import scripts | Claim source data is local when it is not |
| Data pipeline agent | MQTT/replay adapters, validation, canonical transform, quality flags | Bypass canonical schema/validation |
| ML agent | Feature creation, baseline/XGBoost training, evaluation, model cards, MLflow | Introduce deep model without documented need/evidence |
| Simulation agent | SUMO demand/network outputs, scenario artifacts, KPI exports | Treat simulation output as live observations |
| Backend agent | Storage schemas, inference scheduling, forecast/recommendation APIs | Mix predicted/simulated/observed state |
| UI/UX agent | Provenance labels, uncertainty/freshness display, source caveats | Hide synthetic/non-local limitations |
| Research agent | Evaluation protocol, claims/limitations, paper evidence | Overclaim generalizability or local accuracy |

---

## 21. Data and ML acceptance checklist

Before a data or model feature is marked complete:

### Dataset checklist

- [ ] Source and direct URL documented.
- [ ] License/terms checked.
- [ ] Geography and time range recorded.
- [ ] Sampling interval and units understood.
- [ ] Intended use and prohibited claims stated.
- [ ] Source data retained or reproducibly downloadable.
- [ ] Manifest/checksum/version recorded.
- [ ] Data-quality validation implemented.
- [ ] UI provenance/caveat requirement identified.

### Model checklist

- [ ] Target and horizon fixed.
- [ ] Input features documented.
- [ ] Baseline implemented.
- [ ] Chronological split used.
- [ ] Leakage reviewed.
- [ ] Model metrics logged.
- [ ] Comparison against baseline completed.
- [ ] Model artifact and feature schema stored.
- [ ] Model card written.
- [ ] Prediction provenance/quality output implemented.
- [ ] Locality/simulation limitations stated.

### Forecast deployment checklist

- [ ] Approved model version selected.
- [ ] Input completeness checked.
- [ ] Failure mode returns explicit unavailable/low-quality status.
- [ ] Forecast stored separately from observed state.
- [ ] Rule engine receives evidence/provenance.
- [ ] UI displays timestamp, interval/quality, and source mode.

---

## 22. Phased data and ML implementation order

1. Finalize study-area boundary and static OSM asset registry.
2. Create canonical schemas and dataset manifests.
3. Download/import Pune traffic dataset, weather source, and benchmark energy dataset.
4. Build replay publisher and validation pipeline.
5. Build SUMO network and simulation publisher.
6. Store observations/current state and expose through API.
7. Select traffic target and data interval.
8. Create traffic baseline and feature pipeline.
9. Train/evaluate traffic XGBoost; create model card.
10. Create energy replay/synthetic data pipeline.
11. Train/evaluate energy XGBoost; create model card.
12. Add scheduled inference and forecast persistence.
13. Add recommendation rules and UI provenance.
14. Add weather/AQI context and optional environmental thresholds.
15. Run formal evaluation experiments and produce reports.

---

## 23. Deferred data and ML capabilities

| Capability | Why deferred | Trigger to add |
|---|---|---|
| Local live traffic feed | Access not guaranteed | Permitted, licensed source available |
| Local building meter data | Permission/data availability uncertain | Aggregate non-personal export approved |
| Environmental anomaly ML | Insufficient local history | Adequate time series + evaluation plan |
| STGNN/GNN | Needs many well-connected observed segments | Topology and sufficient synchronized data exist |
| LSTM/Transformer | Needs stronger baseline/data volume justification | Research comparison question approved |
| Reinforcement-learning control | Requires calibration, safety, and control study | Formal simulation/control research scope |
| Computer vision | Privacy/compute/data concerns | Explicit approved problem and governance plan |
| Foundation model fine-tuning | No evidence it improves MVP objectives | Clear benchmark and data justification |

---

## 24. Final plan statement

> The pilot will build a trustworthy data and ML foundation before pursuing advanced AI. It will use OpenStreetMap for the Viman Nagar–Somnath Nagar spatial model; Pune traffic data for initial traffic forecasting pipeline work; SUMO for corridor-specific simulated state and intervention experiments; weather and regional environmental data for context; and permitted, benchmark, replayed, or synthetic energy data for energy forecasting. The MVP trains two XGBoost models against simple baselines, tracks provenance and limitations rigorously, and never claims that non-local, synthetic, replayed, or simulated data represents direct measured performance at the pilot corridor.
