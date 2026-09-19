# Model Card: Traffic Speed Forecaster (traffic-xgb-v1)

## 1. Model Overview
- **Model ID:** `traffic-xgb-v1`
- **Domain:** Corridor Microscopic Traffic Analytics
- **Task:** 15-minute ahead regression of average vehicle speed ($t+15\text{m}$)
- **Target Entity:** `urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01` (Nagar Road Eastbound Approach to Viman Nagar Chowk)
- **Target Metric:** `averageSpeedKmh`
- **Unit:** $\text{km/h}$
- **Architecture:** Gradient Boosted Decision Trees (`XGBRegressor`) with dual quantile regressors ($p_{10}$ and $p_{90}$) for 80% prediction intervals
- **Provenance Classification:** `PREDICTED`

---

## 2. Dataset & Chronological Split
- **Temporal Resolution:** 5-minute aggregated time steps
- **History Coverage:** 21 days continuous observations (6,048 samples)
- **Data Splitting Policy:** Strictly chronological ordering without random shuffling
  - **Train Split (70%):** Days 1 to 14.7 (4,213 samples)
  - **Validation Split (15%):** Days 14.7 to 17.85 (903 samples)
  - **Test Split (15%):** Days 17.85 to 21.0 (904 samples)
- **Temporal Leakage Audit:** All rolling statistics, lags, and aggregations are computed strictly over past observations ($t \le \text{now}$) with closed left boundaries.

---

## 3. Input Features (16 Total)

| Feature Name | Type | Description |
|---|---|---|
| `speed_lag_5m` | Numerical | Speed at $t-5$ minutes |
| `speed_lag_10m` | Numerical | Speed at $t-10$ minutes |
| `speed_lag_15m` | Numerical | Speed at $t-15$ minutes |
| `speed_lag_30m` | Numerical | Speed at $t-30$ minutes |
| `speed_lag_60m` | Numerical | Speed at $t-60$ minutes |
| `speed_roll_mean_30m` | Numerical | 30-minute rolling mean speed |
| `speed_roll_std_30m` | Numerical | 30-minute rolling speed volatility |
| `speed_roll_mean_60m` | Numerical | 60-minute rolling mean speed |
| `speed_roll_min_60m` | Numerical | 60-minute rolling minimum speed |
| `speed_roll_max_60m` | Numerical | 60-minute rolling maximum speed |
| `sin_hour` | Cyclical | $\sin(2\pi \times \text{hour} / 24)$ |
| `cos_hour` | Cyclical | $\cos(2\pi \times \text{hour} / 24)$ |
| `day_of_week` | Categorical | Day index (0 = Monday, 6 = Sunday) |
| `is_weekend` | Binary | 1 if Saturday/Sunday, else 0 |
| `is_peak_hour` | Binary | 1 during 08:30–10:30 or 17:30–21:00 |
| `ambient_temp_c` | Numerical | Ambient temperature in Celsius |

---

## 4. Evaluation vs. Required Baselines

Evaluated on the held-out chronological test split:

| Model / Baseline | Test MAE | Test RMSE | Relative Improvement |
|---|---|---|---|
| **Persistence Baseline** ($\hat{y}_{t+15}=y_t$) | 4.82 km/h | 6.14 km/h | — |
| **Historical Average Baseline** (Hour $\times$ Weekend) | 3.95 km/h | 5.02 km/h | +18.0% |
| **Primary XGBoost Regressor** (`traffic-xgb-v1`) | **2.38 km/h** | **3.12 km/h** | **+50.6% vs Persistence** |

---

## 5. Mandatory Locality & Scope Limitations

> [!WARNING]
> **Mandatory Pilot Limitation Notice:**  
> Initial traffic-model evaluation uses publicly available Pune intersection data and calibrated corridor simulation/replay streams. It validates the forecasting pipeline and prototype decision-support behavior but does not establish measured operational forecasting accuracy for the Viman Nagar–Somnath Nagar corridor until physical Pune ATMS detector ground truth is connected.

---

## 6. Failure Modes & Degradation Handling
- **Missing Recent History:** If fewer than 12 prior steps (60 minutes) are available, the inference engine flags `inputQualityStatus="DEGRADED"` and falls back to a calibrated diurnal persistence model with widened confidence intervals.
- **Extreme Speed Outliers:** Speeds outside the physical corridor bounds ($[5.0, 55.0]\text{ km/h}$) are clipped.
