# Task 04: Multi-Horizon Quantile Facility Load Forecaster (15m to 24h)

- **Task Identifier:** `TASK-04`
- **Domain:** Energy Management & Microgrid Optimization
- **Specification Reference:** [`ENERGY_MANAGEMENT.md`](../../FuturePlans/ENERGY_MANAGEMENT.md) Section 8.1
- **Primary Assignee:** Engineer 4 (ML & Forecasting)
- **Priority:** High
- **Type:** Machine Learning & Feature Engineering

---

## 1. Context & Objective

Current building energy forecasting relies on a single 60-minute heuristic/XGBoost active power model trained on raw kW. 

In a production microgrid, operational peak shaving and BESS charge scheduling require **multi-horizon demand forecasts spanning 15 minutes, 1 hour, 4 hours, and 24 hours** with rigorous prediction intervals. Furthermore, models must be **portable across commercial facilities** by utilizing normalized demand features rather than building-specific raw kW.

This task implements the **Multi-Horizon Quantile Facility Load Forecaster**. It trains an XGBoost Quantile Regressor outputting 10th, 50th, and 90th percentile demand envelopes ($\alpha \in \{0.10, 0.50, 0.90\}$), featuring weather normalization (Cooling Degree Days), diurnal cyclic encodings, and conformal prediction bounds.

---

## 2. Feature Engineering & Model Architecture

### 2.1 Feature Vector Formulation
For each commercial facility or microgrid bus at timestamp $t$:

1. **Dimensionless Normalized Demand:**
   $$\bar{P}_t = \frac{P_t}{\text{Sanctioned Load (kVA)}} \quad \text{or} \quad \frac{P_t}{\text{Floor Area } (\text{m}^2)}$$
2. **Weather & Degree Day Normalization:**
   - Cooling Degree Days: $\text{CDD} = \max(0, \; T_{\text{amb}} - 24.0^\circ\text{C})$
   - Heating Degree Days: $\text{HDD} = \max(0, \; 18.0^\circ\text{C} - T_{\text{amb}})$
   - Relative humidity (%), solar irradiance ($\text{W/m}^2$).
3. **Autoregressive Lag Features:**
   - $\bar{P}_{t-15\text{m}}$, $\bar{P}_{t-30\text{m}}$, $\bar{P}_{t-60\text{m}}$, $\bar{P}_{t-24\text{h}}$, $\bar{P}_{t-168\text{h}}$ (same hour prior week).
   - Rolling mean and rolling peak over 4-hour window.
4. **Cyclic Temporal Encodings:**
   $$\text{sin\_time} = \sin\left(\frac{2\pi \cdot m}{1440}\right), \quad \text{cos\_time} = \cos\left(\frac{2\pi \cdot m}{1440}\right)$$
   $$\text{day\_of\_week} \in \{0, \dots, 6\}, \quad \text{is\_holiday\_flag} \in \{0, 1\}$$

### 2.2 Quantile Loss Formulation (Pinball Loss)
$$\mathcal{L}_\alpha(y, \hat{y}) = \max\left(\alpha (y - \hat{y}), \; (1 - \alpha)(\hat{y} - y)\right)$$
Trained for $\alpha \in \{0.10, 0.50, 0.90\}$ to output lower bound, expected median, and conservative upper peak risk.

### 2.3 Model Governance & Baseline Invariants (AGENTS.md)
- Strict chronological 80/10/10 split without random shuffling.
- Evaluated against Persistence Baseline ($\hat{P}_{t+h} = P_t$) and Same-Time Historical Baseline ($\hat{P}_{t+h} = P_{t+h-168\text{h}}$) on the chronological holdout test set (MAE & RMSE required).
- Conformal confidence intervals and top-5 TreeSHAP feature attributions per inference.

---

## 3. Data Contracts & API Schema

### Endpoint: `GET /api/v1/energy/forecasts/load/{building_id}`
```json
{
  "buildingId": "urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01",
  "forecastGeneratedAt": "2026-09-26T12:00:00Z",
  "horizons": [
    {
      "horizonMinutes": 15,
      "targetTimestamp": "2026-09-26T12:15:00Z",
      "p10Kw": 3950.0,
      "p50Kw": 4120.0,
      "p90Kw": 4350.0,
      "conformalInterval90": [3880.0, 4420.0]
    },
    {
      "horizonMinutes": 60,
      "targetTimestamp": "2026-09-26T13:00:00Z",
      "p10Kw": 4200.0,
      "p50Kw": 4580.0,
      "p90Kw": 4920.0,
      "conformalInterval90": [4100.0, 5050.0]
    },
    {
      "horizonMinutes": 240,
      "targetTimestamp": "2026-09-26T16:00:00Z",
      "p10Kw": 4800.0,
      "p50Kw": 5250.0,
      "p90Kw": 5800.0,
      "conformalInterval90": [4650.0, 5990.0]
    }
  ],
  "topFeatures": [
    {"feature": "cdd_degree_days", "shapValue": 0.42},
    {"feature": "lag_168h_same_hour", "shapValue": 0.28},
    {"feature": "lag_15m_demand", "shapValue": 0.16}
  ],
  "provenance": {
    "sourceMode": "PREDICTED",
    "modelVersion": "energy-quantile-xgb-v2",
    "qualityStatus": "VALID"
  }
}
```

---

## 4. Step-by-Step Implementation Guide

1. **Training Script:** Implement `ml/training/train_quantile_load.py` using chronological split and pinball loss.
2. **Inference Service:** Implement `ml/inference/quantile_load_service.py` with multi-horizon dispatch (15m, 60m, 240m, 1440m).
3. **TreeSHAP Attributions:** Calculate top-5 contributing factors for each forecast.
4. **API Endpoints:** Mount `GET /api/v1/energy/forecasts/load/{building_id}`.
5. **Automated Tests:** Add hermetic tests in `tests/test_quantile_load_forecast.py` asserting superior MAE vs persistence baseline.

---

## 5. Architectural Invariants Checklist (`AGENTS.md`)
- [ ] **State Separation Invariant:** Predictions are stored strictly in `ml_forecasts` and never overwrite measured `energy_observations`.
- [ ] **Data Honesty:** Never call benchmark load predictions physical meter measurements.
- [ ] **Strictly Zero Emojis:** Zero emojis in code, logs, and API payloads.
