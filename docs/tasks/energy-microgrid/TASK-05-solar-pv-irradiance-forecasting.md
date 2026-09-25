# Task 05: Solar PV Generation & Irradiance Physical Forecasting Engine

- **Task Identifier:** `TASK-05`
- **Domain:** Energy Management & Microgrid Optimization
- **Specification Reference:** [`ENERGY_MANAGEMENT.md`](../../FuturePlans/ENERGY_MANAGEMENT.md) Section 8.2
- **Component / Scope:** Machine Learning
- **Priority:** High
- **Type:** Physical Modeling & Renewable Analytics

---

## 1. Context & Objective

Microgrid energy cost optimization requires accurate foreknowledge of local rooftop solar photovoltaic generation ($\hat{P}_{\text{pv}}$) to schedule battery charging and avoid peak grid demand charges.

Solar generation fluctuates dramatically based on solar zenith angle, cloud cover, and ambient temperature (which derates silicon cell efficiency).

This task implements the **Solar PV Generation & Irradiance Physical Forecasting Engine**. It ingests Global Horizontal Irradiance ($\text{GHI}$ in $\text{W/m}^2$) and weather forecasts, computes plane-of-array irradiance, models cell temperature thermal derating ($[1 - \gamma (T_{\text{cell}} - 25)]$)), and detects operational underperformance (soiling or inverter clipping) by comparing physical yield with expected capacity.

---

## 2. Mathematical Formulation & Architecture

### 2.1 Physical Photovoltaic Power Output Model
$$\hat{P}_{\text{pv}}(t) = \eta_{\text{sys}} \cdot A_{\text{pv}} \cdot \text{GHI}(t) \cdot \left[1 - \gamma (T_{\text{cell}}(t) - 25.0)\right]$$

Where:
- $\eta_{\text{sys}}$: Overall system efficiency accounting for dust soiling, wiring losses, and inverter conversion ($0.16 \le \eta \le 0.20$).
- $A_{\text{pv}}$: Effective photovoltaic collector area ($\text{m}^2$, e.g. $2,400\text{ m}^2$ on commercial mall rooftops).
- $\text{GHI}(t)$: Global Horizontal Irradiance ($\text{W/m}^2$, from numerical weather forecasts or satellite feeds).
- $\gamma$: Cell thermal power derating coefficient (typically $0.004 / ^\circ\text{C} = 0.40\% / ^\circ\text{C}$).
- $T_{\text{cell}}(t)$: Operating PV cell temperature estimated via King / Sandia formula:
  $$T_{\text{cell}}(t) = T_{\text{amb}}(t) + \text{GHI}(t) \cdot e^{-a - b \cdot v_{\text{wind}}}$$
  (Where $a \approx 3.56, b \approx 0.075$).

### 2.2 Solar Generation Underperformance Anomaly Detector
The engine compares measured inverter power ($P_{\text{pv, measured}}$) against expected physical power ($\hat{P}_{\text{pv}}$):

$$\text{Performance Ratio: } PR(t) = \frac{P_{\text{pv, measured}}(t)}{\hat{P}_{\text{pv}}(t)}$$

- $PR(t) \ge 0.85$: `NOMINAL`
- $0.65 \le PR(t) < 0.85$: `SOILING_OR_DEGRADATION_WARNING` (Trigger panel washing advisory)
- $PR(t) < 0.65$: `INVERTER_OR_STRING_FAULT` (Trigger field maintenance work order)

---

## 3. Data Contracts & Database Schema

```sql
CREATE TABLE IF NOT EXISTS solar_pv_arrays (
    id TEXT PRIMARY KEY,
    facility_id TEXT NOT NULL,
    inverter_id TEXT NOT NULL,
    collector_area_sqm REAL NOT NULL,
    nominal_efficiency REAL NOT NULL DEFAULT 0.185,
    thermal_derating_coeff REAL NOT NULL DEFAULT 0.004,
    tilt_degrees REAL NOT NULL DEFAULT 18.0,
    azimuth_degrees REAL NOT NULL DEFAULT 180.0, -- True South
    rated_peak_power_kw REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS solar_pv_forecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    array_id TEXT REFERENCES solar_pv_arrays(id),
    forecast_generated_at TIMESTAMP NOT NULL,
    target_timestamp TIMESTAMP NOT NULL,
    expected_power_kw REAL NOT NULL,
    ghi_w_per_sqm REAL NOT NULL,
    cell_temperature_c REAL NOT NULL,
    source_mode TEXT NOT NULL DEFAULT 'PREDICTED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 4. Step-by-Step Implementation Guide

1. **Physical Engine Implementation:** Build `backend/services/solar_forecast_service.py` implementing the GHI irradiance and cell temperature derating physics.
2. **Solar Performance Monitoring:** Evaluate live Performance Ratio ($PR$) to detect panel soiling or partial string failures.
3. **Multi-Horizon Forecast API:** Mount `GET /api/v1/energy/solar/{array_id}/forecast` delivering 15m to 24h solar generation curves.
4. **Automated Tests:** Add hermetic tests in `tests/test_solar_forecast.py` asserting zero generation during nighttime hours ($\text{GHI}=0$) and correct thermal derating under high ambient heat.

---

## 5. Architectural Invariants Checklist (`AGENTS.md`)
- [ ] **State Separation Invariant:** Solar generation predictions are stored separately from physical inverter telemetry.
- [ ] **Data Honesty:** Numerical weather irradiance predictions are never tagged as real-time physical sensor readings.
- [ ] **Strictly Zero Emojis:** Zero emojis in code, logs, and frontend displays.
