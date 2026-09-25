# Task 05: Multi-Horizon Quantile Queue Length & Spillback Forecasting

- **Task Identifier:** `TASK-05`
- **Domain:** Intelligent Traffic Mobility & Adaptive Corridor Control
- **Specification Reference:** [`TRAFFIC_MANAGEMENT.md`](../../FuturePlans/TRAFFIC_MANAGEMENT.md) Section 8.1
- **Component / Scope:** Machine Learning
- **Priority:** High
- **Type:** Machine Learning & Feature Store Pipeline

---

## 1. Context & Objective

Current traffic prediction models forecast link speed along the corridor. However, operational traffic signal decisions and congestion prevention require **accurate forecasts of queue lengths and queue spillback risk across multi-step horizons (15, 30, 45, and 60 minutes)**.

This task trains and serves a multi-horizon **Quantile Gradient Boosted Trees model (XGBoost Regressor)** outputting 10th, 50th (median), and 90th percentile queue lengths ($\alpha \in \{0.10, 0.50, 0.90\}$). The pipeline integrates topological spatial lags from PostGIS network geometry, cyclic temporal encodings, and local weather context, accompanied by TreeSHAP feature attributions.

---

## 2. Feature Engineering & Model Architecture

### 2.1 Feature Vector Formulation
For each road segment link $L$ at timestamp $t$:

1. **Volume-to-Capacity Ratio ($V/C$):** $V/C_t = \frac{q_t}{C_{\text{link}}}$ (normalized demand).
2. **Topological Spatial Lags (PostGIS Graph):**
   - Immediate upstream link ($L_{-1}$): Speed $v_{-1, t}$, Density $k_{-1, t}$, Queue $Q_{-1, t}$.
   - Second-degree upstream link ($L_{-2}$): Speed $v_{-2, t}$, Density $k_{-2, t}$.
   - Downstream link ($L_{+1}$): Speed $v_{+1, t}$, Queue $Q_{+1, t}$ (essential for spillback detection).
3. **Temporal Moving Averages & Autoregressive Lags:**
   - $Q_{t-5\text{m}}$, $Q_{t-10\text{m}}$, $Q_{t-15\text{m}}$, $Q_{t-30\text{m}}$, $Q_{t-60\text{m}}$.
   - Rolling mean and rolling standard deviation over $60\text{m}$ window.
4. **Cyclic Diurnal & Day-of-Week Encodings:**
   $$\text{sin\_time} = \sin\left(\frac{2\pi \cdot m}{1440}\right), \quad \text{cos\_time} = \cos\left(\frac{2\pi \cdot m}{1440}\right)$$
   $$\text{day\_of\_week} \in \{0, \dots, 6\}$$
5. **Contextual Environmental Features:**
   - Rainfall intensity ($\text{mm/h}$), Visibility ($\text{km}$), Road surface wetness indicator.

### 2.2 Quantile Loss Function (Pinball Loss)
$$\mathcal{L}_\alpha(y, \hat{y}) = \max\left(\alpha (y - \hat{y}), \; (1 - \alpha)(\hat{y} - y)\right)$$
Trained with XGBoost objective `reg:quantileerror` for $\alpha \in \{0.10, 0.50, 0.90\}$.

### 2.3 Model Governance & Baseline Invariants (AGENTS.md)
- Strict chronological 80/10/10 split without random shuffling.
- Evaluated against Persistence Baseline ($Q_{t+h} = Q_t$) on the chronological holdout test set.
- Conformal confidence intervals and top-5 TreeSHAP feature attributions per inference.
- Population Stability Index (PSI) drift monitoring against training distribution baseline.

---

## 3. Data Contracts & API Schema

```json
{
  "segmentId": "SEG-NR-EB-01",
  "forecastHorizonMinutes": 30,
  "forecastTimestamp": "2026-09-25T16:50:00Z",
  "queueForecastMeters": {
    "q10": 42.0,
    "q50": 68.5,
    "q90": 115.0
  },
  "spillbackProbability": 0.28,
  "baselinePersistenceMeters": 55.0,
  "shapAttributions": [
    {"feature": "upstream_queue_L-1", "contribution": 18.4},
    {"feature": "volume_capacity_ratio", "contribution": 12.1},
    {"feature": "rainfall_intensity_mmh", "contribution": 6.8},
    {"feature": "sin_time", "contribution": 3.2},
    {"feature": "downstream_speed_L+1", "contribution": -5.1}
  ],
  "provenance": {
    "sourceMode": "PREDICTED",
    "modelId": "xgb-quantile-queue-v1.4",
    "evaluationMetrics": {"testMAE": 8.4, "testRMSE": 11.2, "baselineMAE": 16.5}
  }
}
```

---

## 4. Implementation Steps

1. **Feature Extraction Pipeline (`ml/pipelines/queue_feature_pipeline.py`):**
   - Query historical 15m aggregates from database.
   - Construct topological lag matrix ($L_{-1}, L_{+1}$) using PostGIS graph neighbor tables.
2. **Model Training Script (`ml/train_quantile_queue.py`):**
   - Fit XGBoost Quantile Regressors for $\alpha = 0.10, 0.50, 0.90$.
   - Compute Pinball loss, MAE, and RMSE vs persistence baseline on holdout test set.
   - Save artifacts to `ml/models/xgb_queue_quantile.json`.
3. **Inference & SHAP Explainer Service (`ml/services/queue_forecast_service.py`):**
   - Implement `predict_queue(segment_id: str, horizon_minutes: int) -> QueueForecast`.
   - Wrap with `shap.TreeExplainer` to extract top-5 positive and negative attributions.
4. **API Endpoint (`backend/api/v1/endpoints/forecasting.py`):**
   - Expose `GET /api/v1/forecasts/queue/{segment_id}`.
5. **Hermetic Test Suite (`tests/test_queue_forecasting.py`):**
   - Verify monotonic quantile ordering ($Q_{10} \le Q_{50} \le Q_{90}$).
   - Verify feature attribution outputs sum within reasonable margin of prediction.

---

## 5. Verification & Acceptance Criteria

- [ ] Model outperforms persistence baseline by at least 25% MAE reduction on holdout set.
- [ ] Quantile ordering is strictly preserved: $\hat{y}_{0.10} \le \hat{y}_{0.50} \le \hat{y}_{0.90}$.
- [ ] TreeSHAP produces top-5 attributions for every served prediction.
- [ ] Hermetic tests pass cleanly: `pytest tests/test_queue_forecasting.py`.
