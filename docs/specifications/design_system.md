# Design System Specification
## Digital Twin-Enabled Smart City Analytics Platform

> **Status:** Authoritative Frontend Design System & UI Token Standard  
> **Aesthetic Archetype:** Civic Decision-Support Infrastructure (evidence-focused, clear contrast, zero gimmicks)  
> **Accessibility Compliance:** WCAG 2.2 AA (minimum 4.5:1 text contrast, strictly $\ge$ 12px typography)

---

## 1. Dual-Theme Color Token System

| Token | Light Mode (`[data-theme="light"]`) | Dark Mode (`[data-theme="dark"]`) | Purpose |
|---|---|---|---|
| `--color-primary` | `#006B6F` (Deep Teal) | `#3FB4B8` (Electric Teal) | Primary interactive actions, active tabs |
| `--color-primary-hover` | `#005255` | `#5EC4C8` | Button and link hover states |
| `--color-primary-focus` | `rgba(0, 107, 111, 0.4)` | `rgba(63, 180, 184, 0.5)` | 2px accessible keyboard focus rings |
| `--color-bg` | `#F8F9FA` | `#0D1117` | Canvas root background |
| `--color-surface` | `#FFFFFF` | `#161B22` | Cards, drawers, popups, table rows |
| `--color-border` | `#E5E7EB` | `#30363D` | 1px clean container borders |
| `--color-text-primary` | `#111827` | `#F0F6FC` | Headings, primary metrics, table text |
| `--color-text-secondary`| `#4B5563` | `#8B949E` | Secondary descriptions, timestamps |

---

## 2. Provenance & Semantic Status Tokens

All dynamic data in the UI must display an explicit provenance badge utilizing these token pairs:

| Mode | Text / Border Token | Background Subtle Token | Meaning & Context |
|---|---|---|---|
| **`LIVE`** | `--color-live: #0F9D58` | `--color-live-subtle: rgba(15, 157, 88, 0.12)` | Real-time sensor feed from corridor |
| **`REPLAY`** | `--color-replay: #1A73E8` | `--color-replay-subtle: rgba(26, 115, 232, 0.12)` | Historical recorded time-series |
| **`SIMULATION`**| `--color-sim: #8E24AA` | `--color-sim-subtle: rgba(142, 36, 170, 0.12)` | SUMO behavioral simulation output |
| **`PREDICTED`** | `--color-pred: #D97706` | `--color-pred-subtle: rgba(217, 119, 6, 0.12)` | XGBoost 15m/60m ahead ML prediction |
| **`STALE`** | `--color-stale: #B45309` | `--color-stale-subtle: rgba(180, 83, 9, 0.12)` | Feed exceeds freshness threshold |
| **`INVALID`** | `--color-invalid: #D93025`| `--color-invalid-subtle: rgba(217, 48, 37, 0.12)` | Rejected by validation quarantine |

---

## 3. Typography & Numerical Encodings

### 3.1 Font Stack
- **Primary Body & Headings:** `Satoshi, Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`
- **Monospace & Code:** `JetBrains Mono, "Fira Code", monospace`

### 3.2 Tabular Numerals Requirement
All metrics, KPI displays, timestamps, coordinates, and scenario comparison tables must enforce:
```css
font-variant-numeric: tabular-nums lining-nums;
```

### 3.3 Type Scale & Minimum Bounds
- Strictly **no text under 12px** across any view, drawer, or map label.
- `--text-xs: 0.75rem (12px)`
- `--text-sm: 0.875rem (14px)`
- `--text-base: 1rem (16px)`
- `--text-lg: 1.125rem (18px)`
- `--text-xl: 1.5rem (24px)`
- `--text-kpi: 2rem (32px)`

---

## 4. Spacing Scale (4px Base)

- `--space-1: 4px` | `--space-2: 8px` | `--space-3: 12px` | `--space-4: 16px`
- `--space-5: 20px` | `--space-6: 24px` | `--space-8: 32px` | `--space-12: 48px`

---

## 5. UI Components & Interaction States

1. **Buttons:** Fixed heights (32px compact, 40px standard, 44px touch-accessible). Zero gradient fills.
2. **Provenance Badges:** Reusable [`ProvenanceBadge.tsx`](file:///c:/Users/Ashraf/Desktop/AIDT/AI%20Digital%20Twin%20Project/frontend/src/components/ProvenanceBadge.tsx), `min-height: 24px`, `font-size: 12px`, full pill radius (`--radius-full`).
3. **Map Visualization:** MapLibre GL 2D vector basemap, dynamic road segment widths (4px normal, 6px selected), intersection markers with cycle status.
4. **Accessible Focus Rings:** `outline: 2px solid var(--color-primary-focus); outline-offset: 2px;` on all interactive controls.
5. **Reduced Motion:** `@media (prefers-reduced-motion: reduce)` disables non-essential animations.
