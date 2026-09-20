# Data & Machine Learning Specification
## Digital Twin-Enabled Smart City Analytics Platform

> **Status:** Authoritative Data Engineering & ML Architecture Blueprint  
> **Pilot Focus:** 15-Minute Corridor Traffic Speed & 60-Minute Commercial Facility Power Forecasting  
> **Governance Standard:** MLflow Tracking, Conformal Prediction, TreeSHAP Explainability, PSI Drift Detection

---

## 1. Medallion Data Lakehouse Architecture

| Tier | Storage Path | Retention & Mutability | Contents & Pipeline Stage |
|---|---|---|---|
| **Raw** | `data/raw/{domain}/` | Immutable original raw files | Source extracts from OSM, Pune counts, UCI electricity, Open-Meteo weather. |
| **Bronze** | `data/bronze/` | Append-only raw event logs | Unvalidated ingestion dumps with arrival timestamps and transport metadata. |
| **Silver** | PostgreSQL / SQLite | Validated canonical records | Conformed tables (`traffic_observations`, `energy_observations`, `quarantine_observations`). |
| **Gold** | `data/gold/features/` | Versioned Parquet tables | Clean feature store tables (`traffic_features_v1.parquet`, `energy_features_v1.parquet`). |
| **Aggregates** | `data/gold/aggregates/` | Pre-computed rollups | Continuous 15-minute and hourly aggregate rollups for analytics and reporting. |

---

## 2. Feature Engineering & Feature Store

### 2.1 Traffic Feature Store (`traffic_features_v1.parquet`)
Target: `speed_target_15m` (km/h)  
Feature Columns (15 features):
- Lags: `speed_lag_5m`, `speed_lag_10m`, `speed_lag_15m`, `speed_lag_30m`, `speed_lag_60m`
- Rolling Statistics: `speed_roll_mean_15m`, `speed_roll_std_15m`, `speed_roll_min_30m`, `speed_roll_max_30m`
- Temporal Cyclical: `sin_hour`, `cos_hour`, `day_of_week`, `is_weekend`, `is_peak_hour`
- Ambient Weather: `ambient_temp_c`

### 2.2 Commercial Energy Feature Store (`energy_features_v1.parquet`)
Target: `load_target_60m` (kW)  
Feature Columns (14 features):
- Lags: `load_lag_1h`, `load_lag_2h`, `load_lag_3h`, `load_lag_24h`
- Rolling Statistics: `load_roll_mean_6h`, `load_roll_max_6h`, `load_roll_std_6h`
- Temporal Cyclical: `sin_hour`, `cos_hour`, `day_of_week`, `is_weekend`, `is_mall_open`
- Ambient Weather: `ambient_temp_c`

---

## 3. Chronological Train / Validation / Test Splitting

To prevent temporal data leakage, all datasets use strict chronological partitioning:
- **Train Set (80%):** Earliest chronological observations.
- **Validation Set (10%):** Immediate chronological continuation used for hyperparameter tuning.
- **Test Set (10%):** Final holdout period used solely for final model evaluation against baselines.
- Random shuffling is strictly prohibited.

---

## 4. Model Evaluation & Benchmark Baselines

### 4.1 Traffic Forecaster (Experiment E-01)
- **Primary Model:** XGBoost Regressor (`traffic_xgb_v1.joblib`)
- **Baseline:** 15-minute Persistence (`speed(t + 15m) = speed(t)`)
- **Evaluation Metrics (Test Set):**
  - XGBoost MAE: **2.92 km/h** | RMSE: **3.84 km/h**
  - Baseline MAE: **4.43 km/h** | RMSE: **5.61 km/h**
  - **Improvement over Baseline:** **+34.1%**

### 4.2 Building Energy Forecaster (Experiment E-02)
- **Primary Model:** XGBoost Regressor (`energy_xgb_v1.joblib`)
- **Baseline:** Same-Hour / 24-Hour Persistence Baseline
- **Evaluation Metrics (Test Set):**
  - XGBoost MAE: **148.5 kW** | RMSE: **192.1 kW**
  - Baseline MAE: **208.7 kW** | RMSE: **271.4 kW**
  - **Improvement over Baseline:** **+28.8%**

---

## 5. Uncertainty Quantification & Explainability

### 5.1 Conformal Prediction Calibrator
Rather than assuming Gaussian errors, the inference engine computes empirical non-conformity scores on holdout validation data:
- Coverage levels: 80% and 90% confidence bands.
- Traffic 90% Conformal Margin: $\pm 4.80$ km/h.
- Energy 90% Conformal Margin: $\pm 235.0$ kW.

### 5.2 TreeSHAP Local Feature Explanations
Every prediction computes the top-5 feature contributions (SHAP values) explaining why the predicted value deviates from the global baseline.

---

## 6. Drift Detection & Quarantine Standards

### 6.1 Population Stability Index (PSI) Thresholds
- $PSI < 0.10$: `STABLE` (Data matches baseline distribution).
- $0.10 \le PSI < 0.25$: `MODERATE_DRIFT` (Early warning logged).
- $PSI \ge 0.25$: `DRIFT_DETECTED` (Model flags predictions as `suspect` quality).

### 6.2 Dead-Letter Quarantine (`quarantine_observations`)
All malformed events, future timestamps ($> 60$s in future), out-of-bound speeds ($> 120$ km/h), or unmapped entity IDs are redirected to the dead-letter queue with structured reason codes.
