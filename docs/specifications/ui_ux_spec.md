# UI/UX Operational Specification
## Digital Twin-Enabled Smart City Analytics Platform

> **Status:** Authoritative UI Layout & User Experience Specification  
> **Layout Model:** 12-Column Responsive Application Shell (Desktop-First with Tablet/Mobile Support)  
> **Core Pattern:** 2D Map-Centric Operations Canvas with Contextual Drawers & Tabular Views

---

## 1. Application Shell Structure

```text
+---------------------------------------------------------------------------------------+
| HEADER: Project Title | Corridor Badge | Source Mode | Clock | Theme Toggle | Health  |
+---------------------------------------------------------------------------------------+
| NAVIGATION TABS: [1. Map Operations] [2. Traffic] [3. Energy] [4. Scenarios] [5. Health]
+---------------------------------------------------------------------------------------+
|                                                                                       |
|   MAIN OPERATIONAL VIEWPORT (MapLibre 2D Canvas or Data Analytics View)              |
|                                                                                       |
|   +------------------------------------+  +---------------------------------------+   |
|   | FLOATING OVERLAY: Corridor Metrics |  | CONTEXT DRAWER: Road Segment Detail   |   |
|   | - Average Speed: 38.2 km/h         |  | - Current State (Replay)              |   |
|   | - Flow: 1,840 veh/h                |  | - 15-min Forecast: 32.1 km/h (80% CI) |   |
|   | - Provenance: REPLAY               |  | - TreeSHAP Top Features               |   |
|   +------------------------------------+  +---------------------------------------+   |
+---------------------------------------------------------------------------------------+
| STATUS BAR: Database Backend (PostgreSQL/SQLite) | Streamer Active | WebSocket: Online|
+---------------------------------------------------------------------------------------+
```

---

## 2. Core Functional Views

### 2.1 Map Operations View (`MapOperationsView.tsx`)
- **Center Canvas:** Full-viewport MapLibre GL 2D map centered on Viman Nagar (`[73.9220, 18.5615]`, zoom 15.2).
- **Interactive Layers:** 10 road segments with speed-coded colors, 2 signalized intersections with phase indicators, Phoenix Marketcity building footprint.
- **Selection Interaction:** Clicking any segment or intersection opens the slide-out [`EntityDetailDrawer`](file:///c:/Users/Ashraf/Desktop/AIDT/AI%20Digital%20Twin%20Project/frontend/src/components/EntityDetailDrawer.tsx).

### 2.2 Traffic Analytics View (`TrafficAnalyticsView.tsx`)
- Displays continuous 15-minute rollups from `traffic_15m_aggregates`.
- Compares hourly volume trends, peak-hour congestion indices, and p85 speed percentiles.
- Accessible fallback table provided for all chart data.

### 2.3 Scenario Studio View (`ScenarioStudioView.tsx`)
- Parameter configuration for approved scenario templates (`SCEN-BASE-01` vs `SCEN-INT-01`).
- Side-by-side KPI comparison card:
  - Average travel time delta (%)
  - Delay reduction delta (%)
  - Queue length reduction delta (%)
  - Throughput delta (%)
- Advisory human verification warning: *Simulations are for comparative planning evaluation and do not trigger physical signal changes.*

### 2.4 Energy Analytics View (`EnergyAnalyticsView.tsx`)
- Commercial building active power (kW) tracking for Phoenix Marketcity.
- 60-minute ahead XGBoost power forecast with 80%/90% confidence bands.
- Peak demand threshold warning when load exceeds 4,800 kW.

### 2.5 System Health View (`SystemHealthView.tsx`)
- Multi-storage database status and active persistence engine (`postgresql` vs `sqlite`).
- In-process telemetry streamer controls (Start, Stop, Pause, Single Tick, Interval slider).
- Dead-letter quarantine table viewer with rejection reason codes.

---

## 3. Mandatory UI States

Every data-dependent component must implement:
1. **Loading:** Subtle skeleton placeholder matching component dimensions.
2. **Empty:** Actionable message indicating no data found with guidance.
3. **Error:** Non-cryptic error card with retry button.
4. **Stale:** Warning banner with elapsed seconds if data exceeds freshness threshold.
5. **Valid:** Authoritative display with explicit `ProvenanceBadge`.
