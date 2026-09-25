# Task 09: Deck.gl 3D Animated Signal Head & Lane Queue Visualizer

- **Task Identifier:** `TASK-09`
- **Domain:** Intelligent Traffic Mobility & Adaptive Corridor Control
- **Specification Reference:** [`TRAFFIC_MANAGEMENT.md`](../../FuturePlans/TRAFFIC_MANAGEMENT.md) Section 7.3 & 11.2
- **Primary Assignee:** Engineer 5 (Frontend & GIS Visualization)
- **Priority:** High
- **Type:** UI/UX & Geospatial Deck.gl Layer

---

## 1. Context & Objective

Traffic engineers and municipal dispatchers need an intuitive, high-fidelity visual representation of corridor junctions. Static 2D pins fail to convey real-time phase transitions, remaining green countdowns, or lane-level queue accumulations.

This task develops a **Deck.gl custom overlay layer** for the Digital Twin Map (`frontend/src/components/Map.tsx`). It renders 3D physical signal poles with animated signal heads (Red/Yellow/Green with circular countdown timers), extruded lane queue volumes, and bus stop crowd density indicators, updating smoothly via WebSocket streams.

---

## 2. Visual Architecture & Component Design

### 2.1 3D Signal Head Overlay (`SignalHeadLayer.tsx`)
- Renders at junction coordinates (`INT-VN-01`: $[73.9168, 18.5583]$, `INT-SN-01`: $[73.9247, 18.5612]$).
- Displays approach-specific signal aspects:
  - Solid high-contrast circular lamps (Luminous green `#10B981`, Warning amber `#F59E0B`, Stop red `#EF4444`).
  - Circular SVG progress ring indicating remaining phase seconds (countdown ring).
  - Approach movement label tag (e.g. `EB Through`, `VN Southbound`) with high legibility.

### 2.2 Lane Queue Volume Extrusion (`LaneQueueLayer.tsx`)
- Reads road segment queue length ($Q_{\text{meters}}$) and Volume-to-Capacity ratio ($V/C$).
- Renders an extruded 3D polygon along the approach lane centerline:
  - Height proportional to queue length ($h = Q_{\text{meters}} \times 0.5\text{ m}$).
  - Color graded:
    - $V/C < 0.60$: `#06B6D4` (Cyan / Free Flow)
    - $0.60 \le V/C < 0.85$: `#F59E0B` (Amber / Dense Platoon)
    - $V/C \ge 0.85$: `#F43F5E` (Rose / Severe Queue Spillback Risk)

### 2.3 Transit Bus Stop Crowd Radius
- Renders pulsating circle radius around bus stops scaled to passenger waiting density ($D_{\text{stop}}$):
  - Normal ($< 1.0\text{ pax/m}^2$): Subtle emerald halo.
  - Surge ($> 2.5\text{ pax/m}^2$): Flashing amber perimeter with passenger count badge.

### 2.4 Strict UI Invariants
- **Strictly No Emojis**: Use vector iconography (Lucide React `Navigation`, `Clock`, `Bus`, `ShieldAlert`) or clean typographic badges.
- **Dark Mode Aesthetic**: Match existing Slate/Cyan control room theme (`#0F172A` background, `#1E293B` surfaces).

---

## 3. Data Contracts & State Management

Receives live WebSocket frames from `/ws/telemetry`:
```typescript
interface SPaTState {
  intersectionId: string;
  activePhase: number;
  activePhaseName: string;
  phaseColor: 'RED' | 'YELLOW' | 'GREEN' | 'FLASHING_YELLOW';
  timeToNextPhaseSec: number;
  elapsedCycleSec: number;
  cycleLengthSec: number;
}
```

---

## 4. Implementation Steps

1. **Create Signal Head Layer (`frontend/src/components/map/layers/SignalHeadLayer.tsx`):**
   - Implement Deck.gl `IconLayer` or custom `CompositeLayer`.
   - Embed HTML/SVG overlays using Deck.gl `HtmlOverlay` or Canvas renderer for crisp countdown text.
2. **Create Lane Queue Layer (`frontend/src/components/map/layers/LaneQueueLayer.tsx`):**
   - Implement `PathLayer` / `PolygonLayer` with 3D extrusion (`extruded: true`, `getElevation`).
3. **Integrate into Twin Map (`frontend/src/components/Map.tsx`):**
   - Wire SPaT state into Map layers list.
   - Add layer toggle control in the Map toolbar ("Signal Heads", "Lane Queues", "Transit Stops").
4. **Build Verification:**
   - Run `npm run build` to ensure 0 TypeScript or JSX bundling errors.

---

## 5. Verification & Acceptance Criteria

- [ ] Signal lamps animate color changes in real-time without flickering.
- [ ] Phase countdown text counts down smoothly towards zero.
- [ ] Extruded queue height accurately scales with reported queue length.
- [ ] Layer toggle cleanly mounts/unmounts layers.
- [ ] Clean build with 0 TypeScript errors (`npm run build`).
