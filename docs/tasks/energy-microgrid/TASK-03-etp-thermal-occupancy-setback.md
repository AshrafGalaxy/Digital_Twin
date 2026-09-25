# Task 03: 2R-2C ETP Building Thermal Network & Dynamic Occupancy Setback Engine

- **Task Identifier:** `TASK-03`
- **Domain:** Energy Management & Microgrid Optimization
- **Specification Reference:** [`ENERGY_MANAGEMENT.md`](../../FuturePlans/ENERGY_MANAGEMENT.md) Section 7.2 & 7.3
- **Primary Assignee:** Engineer 2 (Simulation & Thermal Physics)
- **Priority:** High
- **Type:** Microscopic Thermal Modeling & Demand Flexibility

---

## 1. Context & Objective

Commercial buildings (such as Phoenix Marketcity or Solitaire Business Hub) spend up to $60\%$ of total electricity on central HVAC chillers. Flattening grid peak demand requires shifting HVAC cooling loads (pre-cooling during low-tariff hours and shedding during peak pricing).

However, uncoordinated thermostat adjustments risk violating **occupant thermal comfort standards (ASHRAE 55)** or wasting energy in unoccupied zones.

This task implements the **2R-2C Equivalent Thermal Parameter (ETP) Network & Dynamic Occupancy Setback Engine**. It simulates indoor air and building envelope thermal dynamics, evaluates zone thermal inertia, and integrates live occupancy sensing (PIR footfall and CO2 concentrations) to command automated dynamic setbacks ($\pm 2.5^\circ\text{C}$ drift) in under-utilized zones without sacrificing occupant comfort.

---

## 2. Mathematical Formulation & Architecture

### 2.1 Lumped-Capacitance 2R-2C ETP Network
The thermal state of building zone $z$ is modeled via coupled first-order differential equations:

$$\frac{dT_{\text{in}}}{dt} = \frac{1}{R_1 C_{\text{in}}} (T_{\text{amb}} - T_{\text{in}}) + \frac{1}{R_2 C_{\text{in}}} (T_{\text{envelope}} - T_{\text{in}}) + \frac{\dot{Q}_{\text{hvac}} + \dot{Q}_{\text{internal}}}{C_{\text{in}}}$$

$$\frac{dT_{\text{envelope}}}{dt} = \frac{1}{R_2 C_{\text{envelope}}} (T_{\text{in}} - T_{\text{envelope}})$$

Where:
- $T_{\text{in}}(t)$: Indoor zone air temperature ($^\circ\text{C}$).
- $T_{\text{amb}}(t)$: Ambient outdoor air temperature ($^\circ\text{C}$, from live weather API / campus station).
- $T_{\text{envelope}}(t)$: Internal building envelope wall and slab temperature ($^\circ\text{C}$).
- $C_{\text{in}}, C_{\text{envelope}}$: Thermal capacitance of zone indoor air volume and structural concrete thermal mass ($\text{kJ/}^\circ\text{C}$).
- $R_1, R_2$: Thermal resistances representing window glazing/infiltration and building envelope boundary ($^\circ\text{C/kW}$).
- $\dot{Q}_{\text{hvac}}$: Chiller/fan-coil thermal extraction rate ($\text{kW}_{\text{th}}$).
- $\dot{Q}_{\text{internal}} = q_{\text{occupant}} \cdot N_{\text{occ}} + P_{\text{lighting}} + P_{\text{plug}}$: Internal dynamic sensible heat gains.

### 2.2 ASHRAE 55 Thermal Comfort Envelope
The optimizer maintains indoor temperature within the statutory comfort envelope during occupied operating hours:
$$T_{\text{setpoint}} - 1.0^\circ\text{C} \le T_{\text{in}}(t) \le T_{\text{setpoint}} + 1.0^\circ\text{C} \quad (23.0^\circ\text{C} \le T_{\text{in}} \le 25.0^\circ\text{C})$$

### 2.3 Dynamic Occupancy Setback Policy (§7.3)
When zone occupancy density $\rho_{\text{occ}} < 0.10$ ($\text{occupants/m}^2$ derived from PIR/CO2 sensors):
1. Expand allowable temperature drift band: $T_{\text{setpoint, setback}} = T_{\text{setpoint}} + 2.5^\circ\text{C}$ (up to $27.0^\circ\text{C}$).
2. Throttle Variable Air Volume (VAV) terminal dampers to minimum ventilation ($30\%$).
3. Return zone to comfort band 20 minutes prior to scheduled re-occupancy.

---

## 3. Database Schema & Data Contracts

```sql
CREATE TABLE IF NOT EXISTS building_thermal_zones (
    id TEXT PRIMARY KEY,
    building_id TEXT NOT NULL,
    zone_name TEXT NOT NULL,
    floor_number INTEGER NOT NULL,
    floor_area_sqm REAL NOT NULL,
    thermal_capacitance_cin REAL NOT NULL, -- kJ/°C
    thermal_capacitance_cenv REAL NOT NULL,
    thermal_resistance_r1 REAL NOT NULL, -- °C/kW
    thermal_resistance_r2 REAL NOT NULL,
    chiller_cooling_cop REAL NOT NULL DEFAULT 4.2,
    nominal_setpoint_c REAL NOT NULL DEFAULT 24.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS zone_occupancy_telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zone_id TEXT REFERENCES building_thermal_zones(id),
    observed_at TIMESTAMP NOT NULL,
    occupant_count INTEGER NOT NULL,
    co2_ppm REAL NOT NULL,
    occupancy_density_pax_sqm REAL NOT NULL,
    hvac_mode TEXT NOT NULL, -- 'COMFORT', 'PRE_COOLING', 'SETBACK_ECO'
    current_temp_c REAL NOT NULL,
    source_mode TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 4. Step-by-Step Implementation Guide

1. **Thermal Model Implementation:** Write `backend/services/building_thermal_service.py` with Runge-Kutta 4th-order (RK4) integration for the 2R-2C ETP state equations.
2. **Occupancy Ingestion Hook:** Ingest PIR footfall and zone CO2 readings over `citytwin/v1/live/energy/building/{bld}/zone/{zone}/occupancy`.
3. **Pre-Cooling Simulator:** Model pre-cooling potential during low-tariff hours (00:00–06:00 IST) to shave afternoon peak chiller power.
4. **REST Endpoints:** Expose `GET /api/v1/energy/zones/{id}/thermal-state` and `POST /api/v1/energy/zones/{id}/simulate-precooling`.
5. **Automated Tests:** Add hermetic tests in `tests/test_building_thermal.py`.

---

## 5. Architectural Invariants Checklist (`AGENTS.md`)
- [ ] **State Separation Invariant:** Zone thermal state projections are saved in simulation schemas, keeping physical BMS sensor records isolated.
- [ ] **Data Honesty:** Synthetic 2R-2C thermal simulations are clearly marked with `sourceMode="SIMULATION"`.
- [ ] **Strictly Zero Emojis:** Zero emojis in code, logs, and frontend status indicators.
