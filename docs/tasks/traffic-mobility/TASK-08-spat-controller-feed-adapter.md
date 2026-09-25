# Task 08: Real-Time Signal Phase and Timing (SPaT) Controller Ingestion Adapter

- **Task Identifier:** `TASK-08`
- **Domain:** Intelligent Traffic Mobility & Adaptive Corridor Control
- **Specification Reference:** [`TRAFFIC_MANAGEMENT.md`](../../FuturePlans/TRAFFIC_MANAGEMENT.md) Section 7.3
- **Primary Assignee:** Engineer 1 (Backend & Telemetry)
- **Priority:** High
- **Type:** Protocols & Field Controller Ingestion

---

## 1. Context & Objective

To provide accurate decision support, the digital twin must mirror the exact real-time phase states, active signal rings, and countdown timers of on-street traffic controllers (such as CoSiCoSt or NTCIP 1202 / SAE J2735 compliant field masters).

This task implements the **SPaT (Signal Phase and Timing) Ingestion Adapter**. The adapter ingests live or replayed high-frequency signal state broadcasts (1–10 Hz), maps controller phase bits to semantic corridor movements, tracks signal freshness against an strict SLA ($<3.0\text{s}$ timeout), and projects real-time signal heads into the digital twin state store.

---

## 2. Protocol Standards & Field Mapping

### 2.1 SAE J2735 / NTCIP 1202 Movement Mapping
Field controllers represent signal stages as numbered phase rings. The adapter maps these to corridor physical approach movements:

| Controller Phase | Intersection | Semantic Movement Name | Protected Turn? | Minimum Green ($g_{\min}$) |
|---|---|---|---|---|
| **Phase 1** | `INT-VN-01` | Nagar Road EB Through + Right | Protected | 25s |
| **Phase 2** | `INT-VN-01` | Nagar Road WB Through | Permissive | 30s |
| **Phase 3** | `INT-VN-01` | Viman Nagar Approach (Southbound) | Protected | 15s |
| **Phase 4** | `INT-VN-01` | Clover Park Approach (Northbound) | Protected | 12s |

### 2.2 Freshness & Stale Invariant
Under high-frequency telemetry, controller communication dropouts must be recognized immediately:
$$t_{\text{now}} - t_{\text{packet}} > 3.0\text{ s} \implies \text{Set status to } \mathbf{STALE}$$
$$t_{\text{now}} - t_{\text{packet}} > 10.0\text{ s} \implies \text{Set status to } \mathbf{DISCONNECTED} \text{ and trigger alert}$$

---

## 3. Data Contracts & Ingestion Payloads

MQTT Ingestion Topic:
`citytwin/v1/live/traffic/signals/INT-VN-01/spat`

Normalized Ingest Payload:
```json
{
  "intersectionId": "INT-VN-01",
  "timestamp": "2026-09-25T16:42:01.250Z",
  "cycleLengthSec": 90,
  "elapsedCycleSec": 42,
  "activePhase": 2,
  "activePhaseName": "Nagar Road WB Through",
  "phaseColor": "GREEN",
  "timeToNextPhaseSec": 18.0,
  "preemptStatus": "NONE",
  "controllerMode": "ACTUATED",
  "provenance": {
    "sourceMode": "LIVE",
    "protocol": "SAE_J2735_SPAT",
    "hardwareController": "CoSiCoSt-V4"
  }
}
```

---

## 4. Implementation Steps

1. **Implement Ingestion Parser (`backend/services/spat_adapter.py`):**
   - Implement `class SPaTAdapter`.
   - Parse raw SPaT payloads, validate timestamp, cycle sanity ($40\text{s} \le C \le 180\text{s}$), and phase colors (`RED`, `YELLOW`, `GREEN`, `FLASHING_YELLOW`).
   - Maintain in-memory active phase cache with last-seen heartbeat.
2. **Database Persistence:**
   - Write phase transition events into `signal_phase_history` table:
     `INSERT INTO signal_phase_history (intersection_id, phase_id, color, duration_sec, start_time, end_time, source_mode) ...`
3. **Stale Watchdog Daemon:**
   - If heartbeat exceeds $3.0\text{s}$, update `entity_current_state` provenance mode for the intersection to `STALE`.
4. **WebSocket & REST Broadcast:**
   - Stream SPaT updates to frontend via existing WebSocket channel `/ws/telemetry`.
   - Expose `GET /api/v1/intersections/{id}/spat` returning current active stage and countdown.
5. **Hermetic Test Suite (`tests/test_spat_adapter.py`):**
   - Test payload normalization.
   - Test watchdog timeout marking state as `STALE`.
   - Test valid phase transition logging.

---

## 5. Verification & Acceptance Criteria

- [ ] Ingestion parses SPaT messages at up to 10 Hz without thread blocking.
- [ ] Dropouts exceeding 3.0s accurately mark intersection state as `STALE`.
- [ ] No emojis in payload or logging.
- [ ] Hermetic tests pass cleanly: `pytest tests/test_spat_adapter.py`.
