# Design System
## Digital Twin-Enabled Smart City Analytics Platform

> **Document status:** Baseline visual and interaction implementation contract  
> **Companion documents:** `PROJECT_CONTEXT.md`, `PRD.md`, `TECHNICAL_ARCHITECTURE.md`, `DATA_AND_ML_PLAN.md`, `UI_UX_SPEC.md`, `ROADMAP.md`, `DELIVERABLES.md`  
> **Audience:** UI/UX agents, frontend agents, data-visualization agents, reviewers  
> **Design direction:** Civic infrastructure, urban operations intelligence, evidence-first decision support  
> **Core rule:** The interface must make information more trustworthy and understandable—not merely more visually impressive.

---

## 1. Purpose

This document is the visual and interaction implementation contract for the **Digital Twin-Enabled Smart City Analytics Platform**.

It defines the shared design tokens, themes, typography, spacing, layout, components, data-visualization rules, accessibility requirements, and anti-patterns that every frontend/UI contributor must follow.

This system exists to ensure the platform feels:

- Trustworthy.
- Civic and public-sector appropriate.
- Calm and analytical.
- Accessible.
- Evidence-oriented.
- Consistent across traffic, energy, environment, scenario, recommendation, and system-health views.

It does **not** define product behavior or screen information architecture; see `UI_UX_SPEC.md` for those requirements.

---

## 2. Design principles

### 2.1 Civic credibility

The product supports public-sector decision-making. It must feel dependable and intentional, not promotional, playful, or experimental.

Use:

- Neutral surfaces.
- Clear hierarchy.
- Calm primary color.
- Explicit labels.
- Direct language.
- Dense but readable data layouts.

Avoid:

- Trend-driven “AI” visual effects.
- Decorative futuristic imagery.
- Excessive gradients.
- Loud animations.
- Arbitrary color accents.

### 2.2 Evidence before aesthetics

A beautiful dashboard that hides provenance, uncertainty, stale data, or simulation assumptions is a failure.

Every relevant UI element must help a user answer:

- What is this value?
- When was it observed/generated?
- Where did it come from?
- Is it live, replayed, simulated, or predicted?
- How reliable/complete is it?
- What action, if any, is appropriate?

### 2.3 Progressive disclosure

Show operational meaning first, technical evidence second, raw metadata third.

```text
Operational summary
→ entity/corridor detail
→ forecast/scenario evidence
→ model/source/configuration metadata
```

Do not expose raw JSON, topic names, SQL concepts, or SUMO configuration to ordinary users by default.

### 2.4 Semantic restraint

Use one primary UI color. Reserve other colors for meaning: traffic state, provenance, warnings, errors, and data visualization.

Do not add colors merely to decorate cards or sections.

### 2.5 Accessible by default

No important status may rely on color alone. Every status must have text, and where appropriate an icon, pattern, line style, or shape.

### 2.6 Human-governed interaction

The UI is a decision-support interface. It must use language such as:

- Review.
- Inspect.
- Compare.
- Simulate.
- Evaluate.
- Acknowledge.
- Consider.

It must not imply autonomous public control through wording such as:

- Apply signal plan.
- Deploy intervention.
- Execute optimization.
- Control corridor.
- Automatically resolve congestion.

---

## 3. Visual direction

### 3.1 Selected style

```text
Style:        Civic infrastructure + urban operations intelligence
Mood:         Calm, credible, precise, analytical
Density:      Balanced, data-aware, not crowded
Primary UI:   Desktop-first operations dashboard
Primary map:  2D analytical map
3D role:      Optional presentation enhancement, never a core dependency
```

### 3.2 Reference qualities

The interface should resemble:

- A well-designed civic operations tool.
- A professional planning/engineering application.
- A trustworthy data-control workspace.
- A modern but restrained public-service dashboard.

It should not resemble:

- A crypto/Web3 dashboard.
- A gaming HUD.
- A marketing landing page.
- A generic glassmorphism SaaS template.
- A fictional “smart city of the future” animation.

### 3.3 Design language summary

```text
Neutral surfaces
+ deep teal primary actions
+ semantic colors reserved for data/status
+ crisp sans-serif typography
+ 4px spacing grid
+ small-to-medium radii
+ subtle borders
+ elevation only for overlays
+ visible provenance and uncertainty
```

---

## 4. Theme strategy

### 4.1 Required themes

The platform must support:

- Light theme.
- Dark theme.
- System-preference default.
- Manual user toggle.

Theme selection should remain in-memory for the prototype if browser storage is unavailable; persistent preference may be added when supported securely.

### 4.2 Theme rules

- Semantic meaning must remain consistent in light and dark themes.
- Do not reverse semantic red/amber/green meaning between themes.
- Text, map labels, chart axes, and status badges must pass contrast checks in both themes.
- Dark mode uses deep charcoal/blue-gray surfaces, not pure black.
- Light mode uses neutral white/light-gray surfaces, not bright saturated backgrounds.

---

## 5. Color system

### 5.1 Color philosophy

The system uses:

1. Neutral surfaces and text for most UI.
2. Deep teal as the single primary interactive color.
3. Semantic colors only for operational state and data meaning.
4. Accessible contrast in both themes.

### 5.2 Core light-theme tokens

```css
:root,
[data-theme="light"] {
  /* Surfaces */
  --color-bg: #F6F7F8;
  --color-surface: #FFFFFF;
  --color-surface-raised: #FBFCFD;
  --color-surface-subtle: #F1F5F4;
  --color-surface-selected: #E7F2F1;
  --color-overlay: rgba(24, 33, 47, 0.48);

  /* Text */
  --color-text: #18212F;
  --color-text-secondary: #536170;
  --color-text-muted: #6F7C8B;
  --color-text-faint: #8A97A5;
  --color-text-inverse: #F8FAFC;

  /* Structure */
  --color-border: #D9E0E6;
  --color-border-strong: #B9C5D0;
  --color-divider: #E5EAEE;

  /* Primary — civic teal */
  --color-primary: #006B6F;
  --color-primary-hover: #00565A;
  --color-primary-active: #00464A;
  --color-primary-subtle: #DDF0EF;
  --color-primary-focus: #0B8C91;

  /* Semantic status */
  --color-success: #177E5D;
  --color-success-subtle: #DDF3EA;
  --color-warning: #B86B00;
  --color-warning-subtle: #FFF1D6;
  --color-danger: #B42318;
  --color-danger-subtle: #FEE9E7;
  --color-invalid: #A61B3C;
  --color-invalid-subtle: #FCE7EE;
  --color-info: #1769AA;
  --color-info-subtle: #E4F0FA;

  /* Provenance */
  --color-live: #177E5D;
  --color-live-subtle: #DDF3EA;
  --color-replay: #4A6075;
  --color-replay-subtle: #E8EEF3;
  --color-simulation: #6E4AA5;
  --color-simulation-subtle: #EEE7F8;
  --color-predicted: #1769AA;
  --color-predicted-subtle: #E4F0FA;
  --color-stale: #B86B00;
  --color-stale-subtle: #FFF1D6;

  /* Data visualization */
  --color-traffic-low: #177E5D;
  --color-traffic-moderate: #B86B00;
  --color-traffic-high: #B42318;
  --color-traffic-unknown: #667085;
  --color-chart-observed: #006B6F;
  --color-chart-predicted: #1769AA;
  --color-chart-simulation: #6E4AA5;
  --color-chart-baseline: #667085;
}
```

### 5.3 Core dark-theme tokens

```css
[data-theme="dark"] {
  /* Surfaces */
  --color-bg: #111827;
  --color-surface: #18212F;
  --color-surface-raised: #202B3A;
  --color-surface-subtle: #16202D;
  --color-surface-selected: #173A3C;
  --color-overlay: rgba(2, 6, 23, 0.68);

  /* Text */
  --color-text: #F3F6F8;
  --color-text-secondary: #C6D0D9;
  --color-text-muted: #A9B6C3;
  --color-text-faint: #8190A0;
  --color-text-inverse: #18212F;

  /* Structure */
  --color-border: #334155;
  --color-border-strong: #4B5B70;
  --color-divider: #283649;

  /* Primary — civic teal */
  --color-primary: #3FB4B8;
  --color-primary-hover: #66C7C9;
  --color-primary-active: #8DDBDC;
  --color-primary-subtle: #173A3C;
  --color-primary-focus: #70D3D5;

  /* Semantic status */
  --color-success: #5FC79A;
  --color-success-subtle: #183E34;
  --color-warning: #F1AE4B;
  --color-warning-subtle: #4B3516;
  --color-danger: #F28B82;
  --color-danger-subtle: #4A2426;
  --color-invalid: #F49AB0;
  --color-invalid-subtle: #4D2434;
  --color-info: #73B7F0;
  --color-info-subtle: #1B3550;

  /* Provenance */
  --color-live: #5FC79A;
  --color-live-subtle: #183E34;
  --color-replay: #AFC0D0;
  --color-replay-subtle: #29394A;
  --color-simulation: #C5A6F5;
  --color-simulation-subtle: #372850;
  --color-predicted: #73B7F0;
  --color-predicted-subtle: #1B3550;
  --color-stale: #F1AE4B;
  --color-stale-subtle: #4B3516;

  /* Data visualization */
  --color-traffic-low: #5FC79A;
  --color-traffic-moderate: #F1AE4B;
  --color-traffic-high: #F28B82;
  --color-traffic-unknown: #9AAABC;
  --color-chart-observed: #3FB4B8;
  --color-chart-predicted: #73B7F0;
  --color-chart-simulation: #C5A6F5;
  --color-chart-baseline: #9AAABC;
}
```

### 5.4 Color usage rules

| Color family | Allowed use | Prohibited use |
|---|---|---|
| Primary teal | Primary actions, active nav, focus, selected state | Decorative gradients, traffic severity, unrelated card accents |
| Green/teal success | Valid/healthy/live/low congestion where legend confirms | Generic “good-looking” highlight |
| Amber | Attention, stale data, moderate congestion, review required | Primary CTA color |
| Red | High attention, high congestion, error, invalid data | Decorative emphasis or routine metadata |
| Purple | Simulation only | Generic feature/category color |
| Blue | Prediction/forecast/information | Primary action when teal is available |
| Gray/slate | Replay, unknown, unavailable, baseline | Hiding important warnings |

### 5.5 Color accessibility rules

- Normal body text must meet a minimum 4.5:1 contrast ratio against its background.
- Large text and key non-text controls/boundaries must meet at least 3:1 contrast ratio.
- Focus indicator must be visible with at least 3:1 contrast against adjacent colors.
- Color cannot be the only means of conveying a status, provenance, trend, or severity.
- Every chart/map color needs a legend, label, pattern, line style, shape, or accessible tooltip.

These rules follow WCAG 2.2 guidance, including color-use and contrast requirements. See [WCAG 2.2](https://www.w3.org/TR/WCAG22/), [W3C quick reference](https://www.w3.org/WAI/WCAG22/quickref/), and [USWDS color guidance](https://designsystem.digital.gov/design-tokens/color/overview/).

---

## 6. Provenance and status styles

### 6.1 Mandatory provenance component

Every data-facing screen must use a shared `ProvenanceBadge` component.

| Mode | Label | Icon concept | Color token | Additional encoding |
|---|---|---|---|---|
| Live | `LIVE` | Radio/activity | `--color-live` | Solid dot + timestamp |
| Replay | `REPLAY` | History/rotate | `--color-replay` | Replay/history icon |
| Simulation | `SIMULATION` | Flask/route | `--color-simulation` | Pattern/hatch where mapped |
| Predicted | `PREDICTED` | Chart/arrow | `--color-predicted` | Dashed line/future horizon |
| Stale | `STALE` | Clock | `--color-stale` | Last-known timestamp |
| Invalid | `INVALID` | Alert octagon | `--color-invalid` | Error description |

### 6.2 Badge requirements

```text
Minimum height: 24px
Text size: 12px minimum
Padding: 4px vertical / 8px horizontal
Radius: full/pill only for status badges
Icon-text gap: 4px
Text: mandatory
Tooltip: required if terminology needs explanation
```

### 6.3 Example markup concept

```text
[ icon ] PREDICTED · 15 min ahead
[ icon ] SIMULATION · scenario-run-004
[ icon ] REPLAY · source recorded 12 Jun 2025
[ icon ] STALE · last update 18 min ago
```

Never show a badge that only says “Active” or “Current” when the provenance type is relevant.

---

## 7. Typography

### 7.1 Font selection

Use one primary sans-serif family across the product.

```css
--font-body: 'Satoshi', 'Inter', 'Segoe UI', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
--font-display: 'Satoshi', 'Inter', 'Segoe UI', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
```

**Primary choice:** Satoshi.  
**Fallback:** Inter, then platform/system fonts.

Rationale:

- Clear at dashboard/UI sizes.
- Strong numeral readability.
- Professional but not generic or decorative.
- Works for dense tables, controls, charts, and documentation-like panels.
- One family reduces visual noise and loading complexity.

### 7.2 Numeric typography

Use tabular numbers for all metrics, timestamps, IDs, KPIs, table values, chart labels, and scenario comparisons.

```css
.numeric,
.kpi-value,
table,
.metric-value {
  font-variant-numeric: tabular-nums lining-nums;
}
```

### 7.3 Type scale

| Token | Suggested size | Weight | Usage |
|---|---:|---:|---|
| `--text-xs` | 12px | 500 | Metadata, status, chart labels, badges |
| `--text-sm` | 14px | 500–600 | Buttons, nav, table cells, form labels |
| `--text-base` | 16px | 400 | Body text, descriptions, default readable content |
| `--text-lg` | 18px | 600 | Panel/section headings |
| `--text-xl` | 20–24px | 650 | Page-level section title |
| `--text-page-title` | 28–32px | 650–700 | Single page title only |
| `--text-kpi` | 24–32px | 650–700 | Key metric values only |

### 7.4 Typography rules

- No visible text below 12px.
- Use 16px as minimum standard body text.
- Keep dashboard page titles at 32px maximum.
- Use sentence case for labels, navigation, actions, and table headings where practical.
- Use one heading hierarchy; do not use multiple display styles.
- Do not use all caps for long labels. Small all-caps may be used for short provenance/status badges only.
- Avoid excessive bold text; use weight to establish hierarchy, not to decorate every label.
- Do not use decorative display fonts, condensed fonts, or serif headline fonts in operational UI.

### 7.5 Writing style tokens

Use clear, neutral, evidence-aware copy.

| Preferred | Avoid |
|---|---|
| Forecast indicates | AI decided |
| Simulated result | Real-world result |
| Advisory | Command/order |
| Review scenario | Apply intervention |
| Source mode | Data truth |
| Input completeness | Certain prediction |
| Estimated impact | Guaranteed improvement |
| Human approval required | Automated governance |

---

## 8. Spacing system

### 8.1 Base unit

All layout spacing must derive from a 4px base unit.

```css
:root {
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;
}
```

### 8.2 Usage rules

| Context | Allowed spacing |
|---|---|
| Icon-to-label gap | 4px or 8px |
| Tight control/field group gap | 8px |
| Label-to-input gap | 8px |
| Form field group gap | 16px |
| Button group gap | 8px |
| Card internal gap | 12px or 16px |
| Standard panel padding | 16px |
| Major panel/drawer padding | 20px or 24px |
| Grid gap | 16px |
| Section gap | 24px or 32px |
| Page outer padding | 24px desktop, 16px smaller screens |

### 8.3 Spacing prohibitions

- Do not use arbitrary values such as 13px, 18px, 22px, or 27px unless a documented visual exception exists.
- Do not use uneven padding inside comparable components.
- Do not compress text/charts merely to fit more cards above the fold.
- Do not use the same large gap between every element; hierarchy must shape spacing.

---

## 9. Layout and grid

### 9.1 Desktop application shell

The product is desktop-first because corridor operations, map analysis, and scenario comparison require spatial width.

```text
┌─────────────────────────────────────────────────────────────────────┐
│ Global header                                                        │
├──────────────┬──────────────────────────────────────┬───────────────┤
│ Navigation   │ Main work surface                     │ Context panel │
│ 240–280px    │ Map / analytics / scenario workspace  │ 320–400px     │
├──────────────┴──────────────────────────────────────┴───────────────┤
│ Optional bottom analysis tray / selected entity trend               │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.2 Grid

Use a 12-column grid for content-heavy desktop views.

| Area | Suggested allocation |
|---|---|
| Persistent navigation | Fixed 240–280px or 2 columns |
| Main map/workspace | 6–7 columns |
| Context/detail panel | 3–4 columns |
| Full-width chart/table | 12 columns |
| Two related panels | 6 + 6 columns |
| Summary/KPI strip | Auto-fit, minimum 220px per item |

### 9.3 Responsive breakpoints

| Breakpoint | Behavior |
|---|---|
| `≥ 1280px` | Persistent nav, map + context panel, optional bottom tray |
| `1024–1279px` | Narrower nav/panel; map remains dominant |
| `768–1023px` | Collapsible nav; context becomes drawer/stacked panel |
| `480–767px` | Single-column monitoring view; map and cards stacked |
| `< 480px` | Read-first/mobile monitoring; limit scenario configuration complexity |

### 9.4 Layout rules

- The map is the dominant surface in Operations view.
- Do not make all content equal card sizes.
- Use full-width space for scenario comparisons and long trend charts.
- Keep persistent navigation minimal and role-appropriate.
- On small screens, collapse complex scenario controls into step-based panels or provide read-only access.
- Do not hide provenance/status to gain screen space.

---

## 10. Surface, border, radius, and shadow system

### 10.1 Surface hierarchy

```text
App background
→ standard surface
→ raised surface/drawer
→ selected/active surface
→ overlay/modal surface
```

Use surface contrast first; use borders second; use shadows only where elevation is meaningful.

### 10.2 Border tokens

```css
--border-subtle: 1px solid var(--color-border);
--border-strong: 1px solid var(--color-border-strong);
```

Rules:

- Use 1px borders in almost all cases.
- Use 2px only for keyboard focus, selected data/interaction state, or deliberate emphasis.
- Do not use thick colored left borders on cards.
- Do not use dark-gray borders on light surfaces or light-gray borders on dark surfaces without tokens.

### 10.3 Radius tokens

```css
:root {
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-full: 9999px;
}
```

| Element | Radius |
|---|---|
| Buttons, inputs, compact controls | 6px |
| Cards/panels | 8px |
| Drawers/modals/large containers | 12px |
| Status badges | Full/pill |
| Map markers | Depends on marker, but avoid decorative blobs |

### 10.4 Shadow tokens

```css
:root {
  --shadow-sm: 0 1px 2px rgba(24, 33, 47, 0.06);
  --shadow-md: 0 8px 20px rgba(24, 33, 47, 0.10);
  --shadow-lg: 0 16px 40px rgba(24, 33, 47, 0.16);
}

[data-theme="dark"] {
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.22);
  --shadow-md: 0 8px 20px rgba(0, 0, 0, 0.30);
  --shadow-lg: 0 16px 40px rgba(0, 0, 0, 0.42);
}
```

Use shadows only for:

- Drawers.
- Modals.
- Popovers.
- Floating panels over map.
- Dragged/reordered components if introduced later.

Do not use shadows as decoration on every card.

---

## 11. Component system

### 11.1 Button hierarchy

| Button type | Use | Visual treatment |
|---|---|---|
| Primary | One primary action in a local context | Solid primary teal, high contrast text |
| Secondary | Supporting action | Neutral surface + border, primary/neutral text |
| Tertiary/ghost | Low-emphasis action | Text/icon, minimal background |
| Danger | Destructive/configuration action only | Danger token, confirmation required |
| Icon-only | Compact map/table action | Icon + aria-label + tooltip |

Rules:

- Do not use gradient buttons.
- Buttons have 44px minimum touch target where used on touch devices.
- Avoid more than one equally strong primary button in a panel.
- Scenario start button must include simulation-only confirmation context.

### 11.2 Button sizing

```text
Small:    32px height — compact table/toolbar only
Medium:   40px height — default dashboard control
Large:    44px height — primary panel action/touch-friendly action
```

### 11.3 Form controls

All inputs, selects, toggles, date/time selectors, and sliders must include:

- Visible label.
- Help text when context is non-obvious.
- Required/optional state where applicable.
- Inline validation/error message.
- Focus-visible state.
- Disabled reason where disabled controls could confuse users.

Scenario forms must use bounded inputs and plain-language explanations. Do not expose raw SUMO config fields to ordinary users.

### 11.4 Navigation

- Use text labels plus icons where helpful.
- Active nav uses primary-subtle surface plus primary text/icon; do not rely only on a thin color indicator.
- Navigation supports keyboard focus and current-page semantics.
- Mobile uses a compact navigation pattern; avoid five layers of hidden menus.

### 11.5 Cards and panels

Cards are containers for meaningful groups, not default decoration.

Required structure:

```text
Panel heading
Optional status/provenance
Primary content/value
Supporting detail or action
```

Rules:

- Standard panel padding: 16px.
- Major panel padding: 20–24px.
- Border: subtle neutral.
- No colored side border.
- No icon-in-circle decoration unless it communicates actual semantic status.
- Use panel headings sparingly and make each panel answer one question.

### 11.6 KPI cards

Required content:

- Metric name.
- Current/scenario value.
- Unit.
- Context/time period.
- Source mode or scenario label.
- Change/delta only where comparison baseline is clear.

Do not use upward green arrows universally. For congestion, energy demand, AQI, queue length, or delay, increases may be undesirable.

### 11.7 Drawers and modals

Use a drawer for context-preserving asset details. Use a modal for confirmation or isolated configuration only.

Required drawer elements:

- Clear title and entity/status context.
- Close action.
- Scrollable internal content without scrolling the entire app unnecessarily.
- Provenance/freshness near the top.

Required modal elements:

- Title.
- Consequence/summary.
- Confirm and cancel actions.
- Keyboard escape/close behavior.

### 11.8 Tables

Rules:

- Use tabular numerals.
- Include units in headers.
- Use sticky header for long lists where useful.
- Include sorting/filter state indicators.
- Include source mode/provenance column when mixed data classes exist.
- Preserve readability rather than squeezing columns on mobile; horizontal scrolling is allowed.
- Avoid zebra stripes if surface/border hierarchy already makes rows clear; if used, keep contrast subtle.

### 11.9 Tooltips

Use tooltips for icon-only controls and abbreviated technical terms. Do not hide essential instructions solely in tooltips.

### 11.10 Loading, empty, and error states

Every async/data-dependent component must have:

```text
Loading → skeleton matching final structure
Empty   → explanation + available next action
Error   → specific reason + safe retry/action
Stale   → last-known value + time + source issue context
```

Never show only “No data” or “Error.”

---

## 12. Data visualization system

### 12.1 General principles

- Data visualization must clarify, not decorate.
- Use a maximum of a few semantic hues per chart.
- Keep observed, predicted, baseline, and simulated series visually distinct.
- Always show units, time context, source mode, and legend.
- Use labels/tooltips for exact values.
- Avoid chart types that obscure comparison.

Material Design accessibility guidance also recommends careful color use, labels, and redundant visual encodings for data visualization. See [Material Design data visualization accessibility guidance](https://m3.material.io/blog/data-visualization-accessibility).

### 12.2 Line chart rules

| Series type | Visual rule |
|---|---|
| Observed | Solid line, `--color-chart-observed` |
| Predicted | Dashed line, `--color-chart-predicted` |
| Prediction interval | Low-opacity band around prediction |
| Simulation | Solid/dash-dot purple line plus `SIMULATION` legend label |
| Baseline | Gray/slate dotted line |
| Missing/stale interval | Gap or gray hatched interval; do not interpolate silently |

### 12.3 Bar chart rules

Use for:

- Baseline vs intervention KPI comparisons.
- Scenario deltas.
- Category counts.
- Feature importance.

Rules:

- Baseline: neutral/slate.
- Intervention: primary teal or semantic result color only with context.
- Simulation label visible above/below chart.
- Negative/positive performance direction must be explained in text; red/green alone is insufficient.

### 12.4 Area chart rules

Use only for:

- Prediction intervals.
- Cumulative volume/demand when appropriate.

Use low-opacity fills. Avoid stacked areas when categories are difficult to compare.

### 12.5 Avoid

- Pie/donut charts for time-series or operational comparisons.
- 3D charts.
- Rainbow color scales.
- Dual-axis charts unless unavoidable and clearly explained.
- More than four series in one core chart without interaction/filtering.
- Animated chart transitions that distort perceived values.

### 12.6 Forecast chart anatomy

```text
Title: Traffic forecast — Segment 001
Subtitle: REPLAY input · Updated 14:05 IST · 15 min horizon

Observed series: solid teal
Forecast series: dashed blue
Interval: blue transparent band
Baseline: dotted slate line

Footer:
Model: traffic-xgb-v1
Input completeness: 95%
Limitation: initial model evaluation uses non-local Pune intersection data
```

---

## 13. Map visualization system

### 13.1 Map role

The map is the operational spatial anchor. It is not a decorative background.

Required map elements:

- Study-area boundary.
- Road segments.
- Intersections.
- Selected-asset state.
- Traffic condition overlay.
- Sensor/source markers.
- Energy entity marker/polygon.
- Optional environment station markers.
- Forecast and scenario overlays.
- Visible legend.
- Time/provenance context.

### 13.2 Basemap rules

- Use a neutral, low-saturation basemap.
- Basemap should not compete with traffic/state overlays.
- Ensure road labels remain legible under overlay lines.
- Follow OpenStreetMap/tile-provider attribution requirements.
- Do not use satellite imagery by default; it can obscure data overlays and increase visual noise.

### 13.3 Traffic-state map encoding

| State | Color | Line/pattern | Additional requirement |
|---|---|---|---|
| Low congestion | Traffic low token | Solid | Visible legend |
| Moderate congestion | Traffic moderate token | Solid | Visible legend |
| High congestion | Traffic high token | Solid, thicker on selection | Value available on hover/select |
| Predicted state | Prediction blue | Dashed/offset overlay | `PREDICTED` label and horizon |
| Simulation result | Simulation purple | Hatch/dash/overlay | `SIMULATION` label and run ID |
| Stale/unknown | Gray/slate | Dashed/striped | Last update displayed |
| Invalid | Invalid token | Hidden from normal overlay or explicit error marker | Never rendered as normal state |

### 13.4 Road line widths

Suggested logical line widths:

```text
Base road:                  3–4px
Traffic overlay:            4–6px
Selected road:              6–8px
Predicted/simulation overlay: add pattern/dash, not only more thickness
```

Adapt to zoom level; do not let overlays cover all basemap context.

### 13.5 Marker rules

- Use distinct shapes/icons for intersection, sensor, building/energy, environment station, and recommendation.
- Include accessible label/tooltip.
- Cluster only when density requires it; MVP corridor likely should not need clustering.
- Avoid decorative pin styles or emoji markers.

### 13.6 Map legend

The legend must always be accessible and include:

- Traffic scale.
- Predicted/simulation encoding.
- Source-mode badge meaning.
- Unknown/stale encoding.
- Unit/context where needed.

Never require the user to remember color meaning from another page.

---

## 14. Scenario and recommendation visualization

### 14.1 Scenario workspace visual hierarchy

```text
Scenario title and SIMULATION label
→ assumptions and input version
→ run status
→ baseline vs intervention KPIs
→ delta interpretation
→ caveats and evidence links
→ optional advisory creation/review
```

### 14.2 Baseline vs intervention comparison

Use a table as the primary comparison format because users need exact values. Charts may supplement it.

| KPI | Baseline | Intervention | Delta | Interpretation |
|---|---:|---:|---:|---|
| Average travel time | value | value | ± value | Simulated change |
| Average delay | value | value | ± value | Simulated change |
| Queue length | value | value | ± value | Simulated change |
| Throughput | value | value | ± value | Simulated change |

Always show:

```text
SIMULATION
Network version: ...
Demand version: ...
Seed: ...
Run completed: ...
```

### 14.3 Recommendation visual rules

Recommendation cards must be visually serious but not alarming by default.

| Severity | Intended use | Styling |
|---|---|---|
| Informational | Context/trend review | Neutral/info styling |
| Attention | Threshold crossed, review advised | Amber attention styling |
| High attention | Major modeled/observed concern | Red styling; must include evidence and no automatic action |

Do not introduce “critical” status in MVP unless a formally justified operational safety rule exists.

---

## 15. Interaction states

### 15.1 Required states for interactive controls

Every button, input, tab, toggle, map marker, interactive card, and link needs:

```text
Default
Hover
Active/pressed
Focus-visible
Disabled
Loading (if action starts async work)
Error (where operation can fail)
```

### 15.2 Focus-visible style

```css
:focus-visible {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
  border-radius: var(--radius-sm);
}
```

Focus must remain visible on both light and dark surfaces.

### 15.3 Hover and active rules

- Hover changes must be subtle and fast.
- Do not rely on hover-only information; touch users need equivalent tap/focus behavior.
- Use active/pressed state for immediate feedback.
- Non-interactive cards should not gain click-like hover shadows.

### 15.4 Motion rules

- Use 150–200ms transitions for controls, drawers, and overlays.
- Use `ease-out` or equivalent natural easing.
- Do not animate critical numbers in a way that delays comprehension.
- Do not use decorative looping animation in operational screens.
- Respect `prefers-reduced-motion`; disable non-essential transitions/animation.

---

## 16. Accessibility requirements

### 16.1 Core requirements

The design must support WCAG 2.2 AA-oriented implementation practices.

- Text contrast: at least 4.5:1 for normal text.
- Large text: at least 3:1.
- UI components/focus boundaries: at least 3:1 where applicable.
- Keyboard operation for all key controls.
- Visible focus state.
- No color-only meaning.
- Semantic HTML first; ARIA only where native semantics are insufficient.
- Screen-reader names for icon-only controls.
- Reduced-motion support.
- Minimum 44×44px touch targets for primary touch controls.

Relevant resources:

- [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- [WCAG 2.2 Quick Reference](https://www.w3.org/WAI/WCAG22/quickref/)
- [Understanding use of color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html)
- [Understanding contrast minimum](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)

### 16.2 Map accessibility fallback

Interactive maps are not sufficient on their own. Provide a synchronized list/table for core operational information:

- Asset name/ID.
- Current status/value/unit.
- Source mode.
- Last update/freshness.
- Forecast summary.
- Active recommendation.

### 16.3 Chart accessibility fallback

Every chart must provide:

- Clear title and visible unit.
- Text summary of latest/current/forecast values.
- Legend and source mode.
- Tooltip with full timestamp/value/unit/provenance.
- Optional table/download alternative when feasible.

### 16.4 Error and status accessibility

- Errors must be textually described, not just colored red.
- `aria-live` may be used for important asynchronous scenario/alert updates, but avoid excessive announcements.
- Do not use auto-dismissing toasts for important errors or outcomes; show inline/contextual state.

---

## 17. Loading, empty, stale, and error states

### 17.1 Loading

Use skeletons that match final content structure.

```text
Map: neutral map/overlay loading indicator without blocking navigation
Card: label skeleton + value skeleton + metadata skeleton
Chart: chart-area skeleton + legend placeholder
Drawer: title + status + content skeleton
```

### 17.2 Empty state

Each empty state must contain:

1. What belongs here.
2. Why it is not available.
3. A safe next action where possible.

Example:

```text
No completed scenario
Run an approved simulation template to compare baseline and intervention KPIs.
```

### 17.3 Stale state

Example:

```text
STALE
Last valid update: 14:05 IST
No valid source update has arrived within the configured freshness window.
```

A stale value may remain visible as last-known state, but it must never be styled as current/healthy data.

### 17.4 Error state

Example:

```text
Scenario run could not complete
The simulation service stopped before KPI comparison. Configuration and diagnostic logs are available to authorized users.
```

Avoid generic “Something went wrong.”

---

## 18. Design anti-patterns

### 18.1 Never use

- Purple-to-blue AI gradients.
- Neon city-grid backgrounds.
- Decorative holograms.
- Random glowing orbs/blobs.
- Gradient buttons.
- 3D charts.
- Rainbow data scales.
- Icons in colored circles used only as decoration.
- Thick colored side borders on cards.
- Huge marketing-style hero headings inside dashboard views.
- Excessive rounded/bubbly UI.
- Centered content everywhere.
- Low-contrast tiny metadata.
- Status communicated only by color.
- Simulation data styled exactly like observed data.
- Generic copy such as “Unlock the power of smart cities.”
- “AI decided” language.
- Fake real-time motion or vehicle animation without clear simulation label.

### 18.2 Avoid unless justified

- Glassmorphism/backdrop blur.
- Gradients anywhere other than a subtle, non-semantic chart/visualization use.
- Dense multi-series charts.
- Dual-axis charts.
- Floating action buttons that obscure map data.
- Automatic chart animation.
- Full-screen modal workflows for tasks that could remain contextual.
- Decorative imagery in operations screens.

---

## 19. Required component inventory

The frontend must establish these reusable components before building many screens.

| Component | Required variants/states |
|---|---|
| App shell | Light/dark, desktop/tablet/mobile |
| Navigation item | Default, active, hover, focus, disabled |
| Button | Primary, secondary, ghost, danger, icon-only, loading, disabled |
| Input/select | Default, focus, error, disabled, help text |
| Provenance badge | Live, replay, simulation, predicted, stale, invalid |
| Quality indicator | Valid, suspect, stale, missing, invalid |
| KPI card | Current, scenario, unavailable, loading |
| Panel/card | Standard, selected, warning, loading |
| Map legend | Traffic/provenance/scenario states |
| Entity detail drawer | Road, intersection, energy, environment, loading/error |
| Time-series chart | Observed, forecast, simulation, baseline, interval, empty/error |
| Scenario comparison table | Baseline, intervention, delta, metadata |
| Recommendation card | Informational, attention, high attention, reviewed |
| Health card | Healthy, attention, unavailable |
| Empty state | Data, scenario, forecast, recommendations |
| Error state | API, source, model, scenario failure |
| Confirmation modal | Scenario run, configuration action |
| Toast/inline status | Non-critical success/background update only |

---

## 20. Implementation checklist for frontend agents

Before a UI feature is marked done:

### Visual consistency

- [ ] Uses design tokens, not arbitrary colors/sizes.
- [ ] Uses Satoshi/approved fallback typography.
- [ ] Uses 4px spacing scale.
- [ ] Uses approved radius/border/shadow values.
- [ ] Supports light and dark theme.

### Data integrity

- [ ] Displays unit, timestamp, provenance, and quality where relevant.
- [ ] Clearly differentiates observed, predicted, replayed, and simulated data.
- [ ] Does not hide data limitations.
- [ ] Does not use color alone for data status.

### Interaction quality

- [ ] Has loading, empty, error, stale, and unavailable states.
- [ ] Has focus-visible/keyboard behavior.
- [ ] Has mobile/tablet fallback behavior.
- [ ] Does not depend on hover-only information.
- [ ] Uses correct advisory/simulation language.

### Accessibility

- [ ] Meets contrast requirements.
- [ ] Labels icon-only buttons.
- [ ] Provides chart/map fallback or textual summary.
- [ ] Respects reduced motion.
- [ ] Uses semantic elements and correct heading order.

---

## 21. Recommended CSS token starter

```css
:root {
  --font-body: 'Satoshi', 'Inter', 'Segoe UI', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
  --font-display: var(--font-body);

  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.5rem;
  --text-page-title: 2rem;
  --text-kpi: 2rem;

  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-10: 2.5rem;
  --space-12: 3rem;
  --space-16: 4rem;

  --radius-sm: 0.375rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
  --radius-full: 9999px;

  --transition-fast: 150ms ease-out;
  --transition-standard: 180ms ease-out;
}

*, *::before, *::after {
  box-sizing: border-box;
}

html {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}

body {
  min-height: 100dvh;
  margin: 0;
  font-family: var(--font-body);
  font-size: var(--text-base);
  line-height: 1.5;
  color: var(--color-text);
  background: var(--color-bg);
}

button, input, select, textarea {
  font: inherit;
}

.numeric {
  font-variant-numeric: tabular-nums lining-nums;
}

:focus-visible {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

The light/dark color token blocks in Sections 5.2 and 5.3 must be included with this starter when implementation begins.

---

## 22. Design-system governance

### 22.1 Change rules

Do not change the following without updating this file and documenting the reason:

- Primary color/palette semantics.
- Provenance color/label meaning.
- Typography family/size floor.
- Spacing base scale.
- Accessibility requirements.
- Map encoding rules.
- Observed/predicted/simulated chart styles.

### 22.2 Component contribution rule

Before introducing a new visual component, check whether an existing component can support the requirement through a variant.

A new component must specify:

- Purpose.
- States.
- Token use.
- Accessibility behavior.
- Responsive behavior.
- Empty/loading/error behavior if data-driven.

### 22.3 Final design-system statement

> The Digital Twin-Enabled Smart City Analytics Platform uses a restrained civic-operations design system: neutral surfaces, a deep teal primary interaction color, semantic status colors, Satoshi-based typography, a 4px spacing grid, accessible data visualizations, and mandatory provenance indicators. Every interface must make the difference between live, replayed, simulated, and predicted data obvious. Design choices exist to support trustworthy urban governance—not to make the platform look artificially futuristic.
