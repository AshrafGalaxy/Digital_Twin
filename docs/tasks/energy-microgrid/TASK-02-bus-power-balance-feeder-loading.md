# Task 02: Electrical Bus Power Balance & Feeder Thermal Loading Engine

- **Task Identifier:** `TASK-02`
- **Domain:** Energy Management & Microgrid Optimization
- **Specification Reference:** [`ENERGY_MANAGEMENT.md`](../../FuturePlans/ENERGY_MANAGEMENT.md) Section 7.1
- **Component / Scope:** Backend & Telemetry
- **Priority:** High
- **Type:** Core Feature Implementation & Physical Validation

---

## 1. Context & Objective

In a physical distribution microgrid, distributed generation (Solar PV), storage (BESS), and dynamic loads (HVAC, EV chargers, lighting plug loads) continuously interact at the Point of Common Coupling (PCC) and distribution feeder buses.

This task implements the **Electrical Bus Power Balance & Feeder Thermal Loading Engine**. It computes live conservation of active and reactive power at each microgrid node, calculates technical distribution losses ($I^2 R$), and evaluates distribution branch ampacity thermal margins ($I_k(t) \le I_{\text{rated}, k}$) to alert grid operators to overload risks before breaker trips occur.

---

## 2. Mathematical Formulation & Physical Invariants

### 2.1 Conservation of Active & Reactive Power
At each electrical node / PCC bus at timestamp $t$:

$$\text{Active Power Balance: } P_{\text{grid}}(t) + P_{\text{pv}}(t) \pm P_{\text{bess}}(t) - \sum_{i=1}^{N} P_{\text{load}, i}(t) - P_{\text{loss}}(t) = 0$$

Where:
- $P_{\text{grid}}(t)$: Net power imported from or exported to the utility grid ($>0$: Import, $<0$: Export).
- $P_{\text{pv}}(t)$: Total instantaneous solar photovoltaic generation ($\text{kW}$).
- $P_{\text{bess}}(t) = P_{\text{bess,dis}}(t) - P_{\text{bess,ch}}(t)$: Net battery output ($>0$: Discharging, $<0$: Charging).
- $\sum P_{\text{load}, i}(t)$: Sum of building zone, HVAC chiller, EV charging, and auxiliary loads.
- $P_{\text{loss}}(t)$: Line and transformer technical losses:
  $$P_{\text{loss}}(t) = \sum_{k \in \text{Branches}} 3 \cdot I_k(t)^2 \cdot R_k$$

### 2.2 Feeder Thermal Loading & Ampacity Margin
For each distribution feeder branch $k$:
$$\text{Loading Ratio: } \mu_k(t) = \frac{I_k(t)}{I_{\text{rated}, k}}$$

Where:
- $I_k(t) = \frac{S_k(t)}{\sqrt{3} \cdot V_{\text{line}}(t)}$: Instantaneous RMS phase current.
- $I_{\text{rated}, k}$: Continuous thermal ampacity rating of cable/busbar (e.g. $630\text{ A}$ for $300\text{ mm}^2$ XLPE copper feeder).

**Thermal Status Evaluation:**
- $\mu_k < 0.75$: `NOMINAL` (Optimal operating zone)
- $0.75 \le \mu_k < 0.90$: `WARNING` (Elevated thermal loading)
- $\mu_k \ge 0.90$: `CRITICAL_OVERLOAD_RISK` (Trigger feeder shedding recommendation)

---

## 3. Data Contracts & API Schema

### Endpoint: `GET /api/v1/energy/power-balance`
```json
{
  "substationId": "SUB-VN-22KV-01",
  "timestamp": "2026-09-26T12:00:00Z",
  "pccGridImportKw": 1420.5,
  "solarGenerationKw": 380.0,
  "bessNetPowerKw": -150.0,
  "facilityTotalLoadKw": 1632.0,
  "technicalLossesKw": 18.5,
  "powerBalanceResidualKw": 0.0,
  "feeders": [
    {
      "feederId": "FDR-PHOENIX-MAIN-01",
      "currentAmps": 1840.2,
      "ratedCurrentAmps": 2200.0,
      "thermalLoadingRatio": 0.836,
      "status": "WARNING",
      "availableHeadroomKw": 258.0
    },
    {
      "feederId": "FDR-SOLITAIRE-01",
      "currentAmps": 920.0,
      "ratedCurrentAmps": 1600.0,
      "thermalLoadingRatio": 0.575,
      "status": "NOMINAL",
      "availableHeadroomKw": 485.0
    }
  ],
  "provenance": {
    "sourceMode": "LIVE",
    "solverMethod": "PHYSICAL_POWER_CONSERVATION",
    "qualityStatus": "VALID"
  }
}
```

---

## 4. Step-by-Step Implementation Guide

1. **Service Engine:** Implement `backend/services/power_balance_service.py` to calculate node-level power balance and branch loading ratios across registered feeders.
2. **Loss Calculation:** Model feeder impedance $R_k$ and reactance $X_k$ using cable parameters from `electrical_feeders`.
3. **Threshold & Alert Evaluator:** Trigger operational warnings when thermal capacity crosses $85\%$.
4. **API Integration:** Mount `GET /api/v1/energy/power-balance` and `GET /api/v1/energy/feeders/{id}/thermal-margin`.
5. **Automated Tests:** Add hermetic tests in `tests/test_power_balance.py` validating residual closure ($<0.1\text{ kW}$) and overload threshold alerts.

---

## 5. Architectural Invariants Checklist (`AGENTS.md`)
- [ ] **State Separation Invariant:** Power balance calculations are classified as `SIMULATION` or `PREDICTED` derived states and never overwrite raw meter readings.
- [ ] **Strict Non-Actuation:** Feeder overload warnings produce advisory recommendations; automated tripping remains under physical relay control.
- [ ] **Strictly Zero Emojis:** Zero emojis across API outputs, logs, and status badges.
