# Task 07: Critical Infrastructure Structural Health Monitoring (SHM) Telemetry

- **Task Identifier:** `TASK-07`
- **Domain:** Intelligent Traffic Mobility & Adaptive Corridor Control
- **Specification Reference:** [`TRAFFIC_MANAGEMENT.md`](../../FuturePlans/TRAFFIC_MANAGEMENT.md) Section 10.1
- **Primary Assignee:** Engineer 1 (Backend & Telemetry)
- **Priority:** High
- **Type:** Sensor Telemetry & Ingestion Subsystem

---

## 1. Context & Objective

Arterial corridors such as Nagar Road carry high-volume heavy commercial vehicles (HCVs) across flyovers, elevated metro viaducts, and bridge decks (e.g., Ramwadi / Viman Nagar Flyover). High-frequency dynamic impact loads and chronic overloaded freight induce structural fatigue, micro-cracks, and bearing degradation.

This task builds the **Structural Health Monitoring (SHM) telemetry ingestion pipeline**. It processes continuous vibration, strain gauge, and Weigh-in-Motion (WIM) data streams, tracks girder deflection and resonant frequency shifts, and surfaces structural integrity alerts before micro-fatigue transitions into structural damage.

---

## 2. Sensor Modalities & Physical Invariants

### 2.1 Monitored Structural Metrics
1. **Tri-axial Accelerometers ($a_x, a_y, a_z$):** Structural vibration amplitude ($g$ or $\text{m/s}^2$) and Peak Particle Velocity ($\text{PPV}$ in $\text{mm/s}$).
2. **Resonant Frequency ($f_0$ in $\text{Hz}$):** Fundamental natural frequency of the bridge span derived via Fast Fourier Transform (FFT) peak analysis.
   $$\text{Stiffness Degradation: } \frac{\Delta f_0}{f_{0, \text{baseline}}} > 5.0\% \implies \text{Structural Fatigue Warning}$$
3. **Fiber-Optic Strain Gauges ($\mu\varepsilon$):** Microstrain along tension flanges:
   $$\epsilon \le 600\ \mu\varepsilon \quad (\text{Normal Operating Range})$$
   $$\epsilon > 800\ \mu\varepsilon \quad (\text{Elastic Yield Advisory Alert})$$
4. **Weigh-in-Motion (WIM) Axle Scales:** Detects overloaded freight vehicles exceeding the legal axle weight threshold ($>10.2\text{ tonnes}$ per single axle).

---

## 3. Data Contracts & Database Schema

### 3.1 Schema Migration (`backend/core/schema_migrator.py`)
```sql
CREATE TABLE IF NOT EXISTS shm_telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    structure_id TEXT NOT NULL,
    sensor_id TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    vibration_ppv_mms REAL NOT NULL,
    strain_microstrain REAL NOT NULL,
    resonant_freq_hz REAL NOT NULL,
    temperature_celsius REAL NOT NULL,
    hcv_axle_load_tonnes REAL,
    integrity_status TEXT NOT NULL, -- 'NOMINAL', 'ADVISORY_FATIGUE', 'ALERT_OVERLOAD'
    source_mode TEXT NOT NULL,
    quality_score REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_shm_struct_time ON shm_telemetry(structure_id, observed_at);
```

### 3.2 MQTT Ingestion Topic
`citytwin/v1/live/shm/flyover/STR-VN-FLY-01/telemetry`

```json
{
  "structureId": "STR-VN-FLY-01",
  "structureName": "Viman Nagar Corridor Flyover",
  "spanId": "SPAN-03-EB",
  "observedAt": "2026-09-25T16:35:00Z",
  "vibrationPPV": {"value": 3.42, "unit": "mm/s", "qualityScore": 0.99},
  "strain": {"value": 520.5, "unit": "microstrain", "qualityScore": 0.98},
  "resonantFreqHz": {"value": 4.12, "baselineHz": 4.25, "driftPct": -3.06},
  "ambientTempC": 28.5,
  "hcvAxleLoadTonnes": 11.4,
  "integrityStatus": "NOMINAL",
  "provenance": {
    "sourceMode": "LIVE",
    "sensorType": "FBG_OPTICAL_PIEZO"
  }
}
```

---

## 4. Implementation Steps

1. **Implement Ingestion Parser (`backend/services/shm_service.py`):**
   - Parse incoming MQTT payloads on `citytwin/v1/live/shm/#`.
   - Validate physical bounds: strain $-2000 \le \epsilon \le 3000\ \mu\varepsilon$, PPV $0 \le \text{PPV} \le 50\text{ mm/s}$.
   - Classify integrity status (`NOMINAL`, `ADVISORY_FATIGUE`, `ALERT_OVERLOAD`).
2. **Correlation with Corridor Congestion:**
   - Correlate extreme strain events with high traffic density ($k > 120\text{ veh/km}$) and WIM axle spikes.
3. **API Endpoints (`backend/api/v1/endpoints/shm.py`):**
   - `GET /api/v1/shm/structures` (list monitored bridges/flyovers).
   - `GET /api/v1/shm/structures/{id}/telemetry` (recent historical strain & vibration).
4. **Hermetic Test Suite (`tests/test_shm_service.py`):**
   - Test ingestion of normal reading.
   - Test alert trigger when $\epsilon > 800\ \mu\varepsilon$.
   - Test rejection of impossible physical readings (PPV $< 0$ or $> 100$).

---

## 5. Verification & Acceptance Criteria

- [ ] SHM records persist to `shm_telemetry` table with full provenance metadata.
- [ ] Fatigue and overload threshold alarms trigger accurately without false positives.
- [ ] Hermetic tests pass cleanly: `pytest tests/test_shm_service.py`.
