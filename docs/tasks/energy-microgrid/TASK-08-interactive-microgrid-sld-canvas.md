# Task 08: Interactive Microgrid Single-Line Diagram (SLD) & Power Flow Canvas

- **Task Identifier:** `TASK-08`
- **Domain:** Energy Management & Microgrid Optimization
- **Specification Reference:** [`ENERGY_MANAGEMENT.md`](../../FuturePlans/ENERGY_MANAGEMENT.md) Section 4 & 11
- **Primary Assignee:** Engineer 5 (Frontend & Control Room UI)
- **Priority:** High
- **Type:** UI/UX & Geospatial Schematic Layer

---

## 1. Context & Objective

Microgrid operators and facility energy managers need an intuitive, real-time visual representation of electrical network topology that clearly displays generation, storage, and consumption across feeders.

Static tables and simple line charts fail to convey whether power is flowing into or out of the grid, which feeders are thermally stressed, or how the battery is interacting with rooftop solar.

This task builds the **Interactive Microgrid Single-Line Diagram (SLD) & Power Flow Canvas** (`MicrogridSLDCanvas.tsx`). It renders a dynamic SVG/HTML5 electrical schematic of the Point of Common Coupling (PCC), 22kV transformer, distribution feeders, solar PV arrays, BESS storage, and commercial facilities with animated energy flow particles and real-time thermal loading gauges.

---

## 2. Visual Architecture & Component Specification

### 2.1 Microgrid SLD Node Layout
- **Utility Grid Substation (PCC Node):** Shows active import/export ($P_{\text{grid}}$), voltage ($415\text{V}$), frequency ($50.0\text{Hz}$), and breaker status.
- **Rooftop Solar PV Array Node:** Displays live solar generation ($\text{kW}$), irradiance ($\text{W/m}^2$), and inverter efficiency.
- **BESS Battery Storage Node:** Displays battery State-of-Charge (SoC) radial gauge, charge/discharge mode, cell temperatures, and health status.
- **Commercial Facility Load Nodes:** Displays active kW demand, contract demand threshold marker, and power factor ($PF$).
- **EV Charging Station Node:** Displays total charging load and plugged vehicle count.

### 2.2 Dynamic Power Flow Particle Animation
- **Energy Direction Vectors:** SVG animated dashed strokes or particles indicating the physical direction of energy flow:
  - From Grid to Facility (Net Import): Slate/Indigo particles.
  - From Solar to Facility/Grid (Green Generation): Emerald particles.
  - From BESS to Facility (Discharging / Peak Shaving): Amber particles.
  - From Grid to BESS (Charging off-peak): Cyan particles.
- **Speed of Flow:** Particle animation speed scales proportionally with active power magnitude ($P_{\text{active}}$).

### 2.3 Feeder Thermal Loading Heat Indicators
- Distribution branch lines are color-coded based on the loading ratio $\mu_k = \frac{I_k}{I_{\text{rated}}}$:
  - $\mu < 0.70$: Deep Slate / Emerald (`#10B981`)
  - $0.70 \le \mu < 0.85$: Amber Warning (`#F59E0B`)
  - $\mu \ge 0.85$: Pulsing Rose Alert (`#F43F5E`)

### 2.4 Strict UI Invariants
- **Strictly No Emojis:** Use Lucide React vector icons (`Zap`, `BatteryCharging`, `Sun`, `Building2`, `ShieldAlert`, `Gauge`) exclusively.
- **Dark Control-Room Aesthetic:** Slate-950 backdrop (`#020617`), slate-900 panels (`#0F172A`), and crisp 1px borders.

---

## 3. Data Contracts & State Management

Receives live WebSocket energy packets from `/ws/telemetry`:
```typescript
export interface MicrogridTelemetryState {
  timestamp: string;
  gridImportKw: number;
  solarGenerationKw: number;
  bessPowerKw: number; // >0 discharging, <0 charging
  bessSoCPct: number;
  totalFacilityDemandKw: number;
  contractDemandLimitKw: number;
  frequencyHz: number;
  voltageV: number;
  feeders: Array<{
    feederId: string;
    feederName: string;
    currentAmps: number;
    thermalLoadingRatio: number;
    status: 'NOMINAL' | 'WARNING' | 'CRITICAL';
  }>;
  sourceMode: 'LIVE' | 'REPLAY' | 'SIMULATION';
}
```

---

## 4. Step-by-Step Implementation Guide

1. **Canvas Component:** Build `frontend/src/components/Microgrid/MicrogridSLDCanvas.tsx` using responsive SVG with viewBox scaling.
2. **Node Sub-Components:** Create `SubstationNode.tsx`, `SolarPVNode.tsx`, `BessNode.tsx`, and `FeederBranchLine.tsx`.
3. **Flow Particle CSS/SVG Animation:** Implement CSS stroke-dashoffset keyframe animations driven by live power signs.
4. **Integration with Energy View:** Mount the SLD canvas into `frontend/src/components/views/EnergyAnalyticsView.tsx`.
5. **Build Verification:** Run `npm run build` ensuring 0 TypeScript errors.

---

## 5. Architectural Invariants Checklist (`AGENTS.md`)
- [ ] **Strictly Zero Emojis:** Verify all nodes, gauges, tooltips, and toolbars use Lucide React icons or plain typography.
- [ ] **Mandatory Provenance Display:** Provenance badge clearly shows `sourceMode` and last update timestamp.
- [ ] **Clean Build:** `npm --prefix frontend run build` completes with 0 errors.
