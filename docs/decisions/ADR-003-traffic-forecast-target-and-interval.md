# ADR-003: 15-Minute Traffic Forecast Target and Baselines

## Context and Problem Statement
In Phase 1, we must formalize the machine-learning forecast target, time aggregation interval, and evaluation baseline for corridor traffic forecasting per `ROADMAP.md` task `P1-11`.

## Decision Outcome
1. **Target Metric:** Average Corridor Speed (in km/h) per road segment, with derived Congestion Index:
   $$\text{Congestion Index} = \max\left(0, 1 - \frac{\text{Observed Speed}}{\text{Free Flow Speed}}\right)$$
2. **Aggregation Interval:** 5-minute sampling aggregated into 15-minute rolling modeling windows.
3. **Forecasting Horizon:** 15 minutes ahead ($t + 15\text{m}$).
4. **Primary Model:** Feature-engineered XGBoost Regressor.
5. **Mandatory Baselines:**
   - *Baseline 1 (Persistence):* $\hat{y}_{t+15} = y_t$.
   - *Baseline 2 (Historical Average):* Same day-of-week and same time-of-day mean speed over training history.
6. **Chronological Splitting:** Strictly chronological train (70%) / validation (15%) / test (15%) split. Random shuffling is strictly prohibited.
7. **Evaluation Metrics:** Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE).

## Locality & Data Limitations
Initial prototype model training utilizes the Pune Heterogeneous Traffic Count dataset (Mendeley Data) combined with SUMO corridor simulations. All outputs must clearly disclose that non-local Pune counts serve as contextual pre-training/validation rather than ground-truth corridor observations.
