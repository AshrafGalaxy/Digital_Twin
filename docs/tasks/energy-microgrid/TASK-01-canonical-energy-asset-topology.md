# Task 01: Canonical Electrical Network Topology & Multi-Asset Telemetry Engine

- **Task Identifier:** `TASK-01`
- **Domain:** Energy Management & Microgrid Optimization
- **Specification Reference:** [`ENERGY_MANAGEMENT.md`](../../FuturePlans/ENERGY_MANAGEMENT.md) Section 4, 5, 6
- **Component / Scope:** Backend & Telemetry
- **Priority:** High
- **Type:** Architectural Foundation & Telemetry Ingestion

---

## 1. Context & Objective

Currently, building energy telemetry is confined to a single static entity (`BLD-PHOENIX-01`) ingesting raw active power (`activePowerKw`) and power factor into SQLite.

In a production microgrid digital twin, electrical assets must be **modeled as discrete, interconnected network entities** (Substations, Distribution Feeders, Point of Common Coupling, Rooftop Solar PV Inverters, Battery Energy Storage Systems, Building Zones, and Smart EV Chargers).

This task implements the **Canonical Electrical Network Topology & Multi-Asset Telemetry Engine**. It provisions authoritative database schemas, registers physical electrical entities, and ingests multi-phase telemetry (active power $P$, reactive power $Q$, voltage $V$, current $I$, frequency $f$, power factor $PF$, and current unbalance) following the canonical MQTT hierarchy.

---

## 2. Topic Hierarchy & Canonical Telemetry Format

### 2.1 MQTT Ingestion Hierarchy
```text
citytwin/{environment}/{source_mode}/energy/{study_area}/{asset_type}/{asset_id}
```
**Example Topics:**
- Substation: `citytwin/v1/live/energy/pune-corridor/substation/SUB-VN-22KV-01`
- Smart Feeder: `citytwin/v1/live/energy/pune-corridor/feeder/FDR-PHOENIX-MAIN-01`
- Solar PV Inverter: `citytwin/v1/live/energy/pune-corridor/solar_inverter/INV-PHOENIX-ROOF-01`
- BESS: `citytwin/v1/live/energy/pune-corridor/bess/BESS-PHOENIX-500KWH-01`
- EV Charging Hub: `citytwin/v1/live/energy/pune-corridor/ev_hub/EVHUB-PHOENIX-01`

### 2.2 Canonical Multi-Phase Telemetry Event (NGSI-LD Inspired)
```json
{
  "id": "urn:energy:SmartMeter:pune-corridor:MTR-PHOENIX-01",
  "type": "EnergyMeter",
  "observedAt": "2026-09-26T12:00:00Z",
  "studyAreaId": "pune-corridor",
  "topologyVersion": "pune-electrical-v1",
  "activePower": {"value": 1420.5, "unit": "kW", "qualityScore": 0.99},
  "reactivePower": {"value": 290.2, "unit": "kvar", "qualityScore": 0.98},
  "apparentPower": {"value": 1449.8, "unit": "kVA", "qualityScore": 0.99},
  "voltage": {"value": 415.2, "unit": "V", "qualityScore": 0.99},
  "current": {"value": 2017.3, "unit": "A", "qualityScore": 0.98},
  "frequency": {"value": 50.02, "unit": "Hz", "qualityScore": 0.99},
  "powerFactor": {"value": 0.98, "unit": "1", "qualityScore": 0.99},
  "phaseUnbalancePct": {"value": 1.2, "unit": "%", "qualityScore": 0.95},
  "provenance": {"sourceMode": "LIVE", "gatewayId": "gw-modbus-substation-01"}
}
```

---

## 3. Database Schema & Data Contracts

Update `backend/core/schema_migrator.py` with multi-asset tables:

```sql
-- Electrical Topology Registry
CREATE TABLE IF NOT EXISTS electrical_substations (
    id TEXT PRIMARY KEY,
    study_area_id TEXT NOT NULL,
    name TEXT NOT NULL,
    primary_voltage_kv REAL NOT NULL DEFAULT 22.0,
    secondary_voltage_v REAL NOT NULL DEFAULT 415.0,
    transformer_capacity_kva REAL NOT NULL,
    pcc_latitude REAL NOT NULL,
    pcc_longitude REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS electrical_feeders (
    id TEXT PRIMARY KEY,
    substation_id TEXT REFERENCES electrical_substations(id),
    name TEXT NOT NULL,
    rated_current_amps REAL NOT NULL,
    voltage_nominal_v REAL NOT NULL DEFAULT 415.0,
    cable_type TEXT,
    length_meters REAL,
    linked_building_id TEXT,
    status TEXT NOT NULL DEFAULT 'ENERGIZED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS distributed_energy_assets (
    id TEXT PRIMARY KEY,
    feeder_id TEXT REFERENCES electrical_feeders(id),
    asset_type TEXT NOT NULL, -- 'SOLAR_PV', 'BESS', 'EV_CHARGER', 'HVAC_PLANT'
    name TEXT NOT NULL,
    rated_power_kw REAL NOT NULL,
    capacity_kwh REAL, -- For BESS
    controller_protocol TEXT NOT NULL DEFAULT 'MODBUS_TCP',
    location_coordinates TEXT NOT NULL,
    metadata TEXT NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS electrical_telemetry_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    observed_at TIMESTAMP NOT NULL,
    asset_id TEXT NOT NULL,
    source_mode TEXT NOT NULL,
    active_power_kw REAL NOT NULL,
    reactive_power_kvar REAL,
    voltage_v REAL,
    current_amps REAL,
    frequency_hz REAL,
    power_factor REAL,
    state_of_charge_pct REAL, -- For BESS
    temperature_celsius REAL,
    quality_status TEXT NOT NULL DEFAULT 'VALID',
    raw_payload TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_elec_telemetry ON electrical_telemetry_observations(asset_id, observed_at);
```

---

## 4. Step-by-Step Implementation Guide

1. **Schema Migration:** Add `electrical_substations`, `electrical_feeders`, `distributed_energy_assets`, and `electrical_telemetry_observations` to `backend/core/schema_migrator.py`.
2. **Pydantic Validation Models:** Implement `SmartMeterTelemetryEvent`, `BessTelemetryEvent`, and `SolarPvTelemetryEvent` in `backend/schemas/canonical.py`.
3. **Ingestion & Validation:** Extend `backend/ingestion/validator.py` to validate electrical engineering bounds (Voltage 360V–460V, Frequency 47.5Hz–52.5Hz, Power Factor 0.5–1.0).
4. **Topology REST Endpoints:** Create `backend/api/v1/endpoints/energy_topology.py` exposing:
   - `GET /api/v1/energy/substations`
   - `GET /api/v1/energy/feeders`
   - `GET /api/v1/energy/assets`
   - `GET /api/v1/energy/live-telemetry`
5. **Automated Unit Tests:** Add hermetic tests in `tests/test_energy_topology.py`.

---

## 5. Architectural Invariants Checklist (`AGENTS.md`)
- [ ] **State Separation Invariant:** Observed meter telemetry persists strictly to `electrical_telemetry_observations` and never overwrites forecasts or optimizer schedules.
- [ ] **Data Honesty:** Replayed benchmark facility meters are tagged `sourceMode="REPLAY"` and never labeled "live".
- [ ] **Strictly Zero Emojis:** Zero emojis in API errors, logs, or schema documentation.
- [ ] **Hermetic Testing:** Isolated test passes 100% via `pytest tests/test_energy_topology.py`.
