# Task 09: Building Floorplate 3D/2D Thermal Comfort & Occupancy Density Visualizer

- **Task Identifier:** `TASK-09`
- **Domain:** Energy Management & Microgrid Optimization
- **Specification Reference:** [`ENERGY_MANAGEMENT.md`](../../FuturePlans/ENERGY_MANAGEMENT.md) Section 7.2, 7.3, 11
- **Primary Assignee:** Engineer 5 (Frontend & Control Room UI)
- **Priority:** Medium
- **Type:** UI/UX & Thermal Zone Heatmap

---

## 1. Context & Objective

HVAC optimization algorithms command thermostat adjustments and setback modes across multiple building zones. However, facility managers cannot blindly trust automated setbacks without real-time visibility into **indoor thermal comfort and spatial occupancy levels**.

This task develops the **Building Floorplate Thermal Comfort & Occupancy Density Visualizer** (`ThermalComfortHeatmap.tsx`). It renders a 2D/isometric zone map of the facility, color-coding each zone by indoor temperature relative to ASHRAE 55 comfort bounds, displaying live PIR/CO2 occupancy badges, and highlighting zones currently operating under energy-saving setbacks.

---

## 2. Visual Architecture & Component Specification

### 2.1 Zone Heatmap Color Encoding
Each building zone polygon is dynamically shaded based on its temperature deviation from nominal setpoint:
- **Under-Cooled / Cold Drift ($T_{\text{in}} < 22.0^\circ\text{C}$):** Cyan / Blue tint (`#06B6D4`).
- **Optimal Comfort Zone ($22.0^\circ\text{C} \le T_{\text{in}} \le 24.5^\circ\text{C}$):** Emerald / Slate tint (`#10B981`).
- **Acceptable Eco Drift ($24.5^\circ\text{C} < T_{\text{in}} \le 26.5^\circ\text{C}$):** Amber tint (`#F59E0B`).
- **Thermal Discomfort Violation ($T_{\text{in}} > 26.5^\circ\text{C}$):** Rose / Crimson warning (`#EF4444`).

### 2.2 Occupancy & Air Quality Badge Overlay
- Displays live zone occupants count (from PIR footfall sensors).
- Displays indoor air quality: NDIR $\text{CO}_2$ concentration in ppm (green $<800\text{ ppm}$, amber $800–1200\text{ ppm}$, red $>1200\text{ ppm}$).
- **Setback Pill:** When occupancy drops $<10\%$ and dynamic setback activates, displays a clean vector badge: `SETBACK ACTIVE (+2.5°C)` with energy reduction gauge.

### 2.3 Strict Aesthetic Rules
- **Zero Emojis:** Use Lucide React vector icons (`Thermometer`, `Users`, `Wind`, `Leaf`, `AlertCircle`).
- **Clean Responsive Layout:** Grid cards with hover cards showing detailed 2R-2C thermal model parameters.

---

## 3. Data Contracts & State Types

```typescript
export interface BuildingZoneThermalState {
  zoneId: string;
  zoneName: string;
  floor: number;
  currentTempC: number;
  setpointTempC: number;
  ambientTempC: number;
  hvacMode: 'COMFORT' | 'PRE_COOLING' | 'DYNAMIC_SETBACK' | 'UNOCCUPIED';
  occupantCount: number;
  co2Ppm: number;
  coolingKwTh: number;
  ashrae55Compliant: boolean;
}
```

---

## 4. Step-by-Step Implementation Guide

1. **Component Design:** Build `frontend/src/components/Energy/ThermalComfortHeatmap.tsx`.
2. **Zone Card Component:** Create `ZoneThermalCard.tsx` with temperature progress bar and comfort status pill.
3. **Interactive Floor Selector:** Add floor tabs (e.g. Ground Floor Retail, 1st Floor Atrium, 2nd Floor Food Court).
4. **WebSocket Wire-up:** Subscribe to zone telemetry frames streamed from backend.
5. **Typecheck & Build:** Validate `npm --prefix frontend run build` completes cleanly.

---

## 5. Architectural Invariants Checklist (`AGENTS.md`)
- [ ] **Zero Emojis:** Completely verify no emoji characters exist in components, labels, or tooltips.
- [ ] **State Separation Invariant:** Displayed simulation states are clearly tagged as `SIMULATION` or `PREDICTED`.
- [ ] **Clean Build:** 0 TypeScript / build errors.
