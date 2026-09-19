# Model Card: Commercial Energy Demand Forecaster (energy-xgb-v1)

## 1. Model Overview
- **Model ID:** `energy-xgb-v1`
- **Domain:** Commercial Building & Microgrid Energy Analytics
- **Task:** 60-minute ahead regression of active power demand ($t+60\text{m}$)
- **Target Entity:** `urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01` (Phoenix Marketcity Viman Nagar)
- **Target Metric:** `activePowerKw`
- **Unit:** $\text{kW}$
- **Architecture:** Gradient Boosted Decision Trees (`XGBRegressor`) with dual quantile regressors ($p_{10}$ and $p_{90}$) for 80% prediction intervals
- **Provenance Classification:** `PREDICTED`

---

## 2. Dataset & Chronological Split
- **Temporal Resolution:** 15-minute aggregated time steps
- **History Coverage:** 35 days continuous load measurements (3,360 samples)
- **Data Splitting Policy:** Chronological ordering (70% train, 15% val, 15% test)
  - **Train Split (70%):** Days 1 to 24.5 (2,284 samples)
  - **Validation Split (15%):** Days 24.5 to 29.75 (490 samples)
  - **Test Split (15%):** Days 29.75 to 35.0 (490 samples)
- **Temporal Leakage Audit:** All rolling statistics and historical lags are computed strictly over past observations ($t \le \text{now}$) with closed left boundaries.

---

## 3. Input Features (13 Total)

| Feature Name | Type | Description |
|---|---|---|
| `load_lag_1h` | Numerical | Active power at $t-1\text{h}$ (4 steps) |
| `load_lag_2h` | Numerical | Active power at $t-2\text{h}$ (8 steps) |
| `load_lag_3h` | Numerical | Active power at $t-3\text{h}$ (12 steps) |
| `load_lag_24h` | Numerical | Active power at same hour yesterday (96 steps) |
| `load_roll_mean_6h` | Numerical | 6-hour rolling mean demand |
| `load_roll_max_6h` | Numerical | 6-hour rolling peak demand |
| `load_roll_std_6h` | Numerical | 6-hour rolling demand variance |
| `sin_hour` | Cyclical | $\sin(2\pi \times \text{hour} / 24)$ |
| `cos_hour` | Cyclical | $\cos(2\pi \times \text{hour} / 24)$ |
| `day_of_week` | Categorical | Day index (0 = Monday, 6 = Sunday) |
| `is_weekend` | Binary | 1 if Saturday/Sunday, else 0 |
| `is_mall_open` | Binary | 1 during commercial retail hours (10:00–22:00) |
| `ambient_temp_c` | Numerical | Ambient Pune temperature in Celsius |

---

## 4. Evaluation vs. Required Baselines

Evaluated on the held-out chronological test split:

| Model / Baseline | Test MAE | Test RMSE | Relative Improvement |
|---|---|---|---|
| **Persistence Baseline** ($\hat{y}_{t+60}=y_t$) | 285.4 kW | 392.1 kW | — |
| **Same-Hour Baseline** (Hour $\times$ Weekend) | 210.8 kW | 295.4 kW | +26.1% |
| **Primary XGBoost Regressor** (`energy-xgb-v1`) | **92.6 kW** | **134.2 kW** | **+67.5% vs Persistence** |

---

## 5. Peak Demand Advisory Rule
- **Contracted Demand Limit:** 5,500 kW
- **Peak Alert Threshold:** 4,800 kW
- If the 60-minute prediction exceeds 4,800 kW, the platform emits an advisory peak load alert, prompting facility engineers to stage chiller precooling or shed discretionary lighting.

---

## 6. Mandatory Source Limitation Statement

> [!WARNING]
> **Mandatory Source Limitation Notice:**  
> This pilot energy stream uses representative commercial building load patterns and calibrated benchmark series. It demonstrates the data pipeline, feature engineering, and forecasting methodology but does not measure direct utility meter data from a building in the Pune pilot corridor.
