# UI/UX Specification
## Digital Twin-Enabled Smart City Analytics Platform

> **Document status:** Baseline MVP experience specification  
> **Companion documents:** `PROJECT_CONTEXT.md`, `PRD.md`, `TECHNICAL_ARCHITECTURE.md`, `DATA_AND_ML_PLAN.md`  
> **Pilot study area:** Viman Nagar Chowk (Phoenix Mall) ↔ Somnath Nagar Chowk corridor, Pune  
> **Primary product users:** Municipal/city-governance teams, Smart City SPVs, ICCC teams, traffic-management agencies, urban planners, infrastructure departments, utility/energy teams, and environmental authorities  
> **Primary interface:** Authorized desktop-first city-operations and planning dashboard  
> **Design principle:** Make urban evidence understandable, traceable, and actionable without making simulated or predicted information look like verified live reality.

---

## 1. Purpose

This document defines the user experience, information architecture, interface requirements, visual rules, interaction patterns, and accessibility rules for the **Digital Twin-Enabled Smart City Analytics Platform**.

It ensures that the platform is designed for governance and operational decision support—not as a consumer navigation app, generic smart-city dashboard, or decorative 3D visualization.

The interface must help an authorized user move through a reliable decision-support sequence:

```text
Observe conditions
→ check source/freshness/quality
→ inspect trend and forecast
→ understand uncertainty and evidence
→ test an approved simulation scenario
→ compare consequences
→ review advisory recommendation
→ make or document a human decision outside the platform
```

---

## 2. UX goals

### 2.1 Primary goals

1. Provide a shared visual picture of the pilot corridor and its assets.
2. Make the difference between observed, replayed, simulated, and predicted information unmistakable.
3. Allow users to understand congestion, energy demand, environmental context, and system health quickly.
4. Enable a user to inspect the evidence behind a forecast or recommendation.
5. Allow authorized analysts to run predefined scenarios safely.
6. Make baseline versus intervention comparison clear and unbiased.
7. Support auditability through visible source, timestamp, model version, scenario version, and quality metadata.
8. Make core operations usable without requiring AI, GIS, or database expertise.

### 2.2 Secondary goals

- Present a polished, credible system for academic review, government innovation discussions, funding demos, and portfolio presentation.
- Preserve a clean path to optional 3D visualization.
- Support future expansion from the pilot corridor to wider districts and domains.

### 2.3 UX non-goals

- Consumer turn-by-turn navigation.
- Showing every possible metric at once.
- Making the interface look “AI-powered” through unnecessary visual effects.
- Treating a 3D city scene as proof of digital-twin functionality.
- Hiding uncertainty, missingness, or limitations to make results look stronger.
- Requiring users to understand raw MQTT, SQL, SUMO, or MLflow concepts.

---

## 3. User groups and experience needs

| User group | Primary task | UX need |
|---|---|---|
| Municipal/city-governance team | Review corridor evidence for policy/coordination | Clear high-level status, evidence traceability, understandable consequences |
| Smart City SPV / ICCC user | Monitor conditions, alerts, freshness, source health | Fast scanning, map state, alert triage, reliable timestamps |
| Traffic-management agency | Assess congestion and test traffic scenarios | Road-level details, forecast, queues/delay, KPI comparison |
| Urban/transport planner | Compare planning/intervention alternatives | Scenario inputs, baseline-vs-intervention results, trade-offs |
| Public works/infrastructure department | Understand stressed assets/corridor effects | Spatial context, event history, planned work/closure future extension |
| Energy/utility user | Assess demand and peak risk | Load trend, forecast, source/data quality, peak advisories |
| Environmental authority | Interpret weather/AQI context | Station source, threshold context, geographic caveat |
| System administrator | Monitor source, service, model, and run health | System health, freshness, failures, configuration status |
| Researcher/evaluator | Validate methodology and limitations | Provenance, model/scenario versions, metrics, reproducible evidence |

---

## 4. Product experience principles

### 4.1 Evidence before recommendation

A recommendation must never appear without accessible evidence.

Every recommendation view must provide:

- Trigger condition.
- Current/relevant observed value.
- Forecast or scenario value.
- Source mode.
- Timestamp.
- Data quality/confidence.
- Model/scenario version where relevant.
- Suggested action.
- Human-approval requirement.

### 4.2 Provenance is a first-class UI feature

The following labels are mandatory throughout the product:

| Label | Meaning | Visual treatment |
|---|---|---|
| `LIVE` | Approved real sensor/API input | Solid status badge + timestamp |
| `REPLAY` | Historical data streamed for demonstration/testing | Solid status badge + replay indicator |
| `SIMULATION` | SUMO/synthetic scenario/generator output | Distinct badge + simulation icon/text |
| `PREDICTED` | ML forecast | Distinct badge + forecast horizon/interval |
| `STALE` | Data older than freshness threshold | Warning badge + last known time |
| `INVALID` | Failed validation/untrusted value | Error state; not styled as normal operational data |

**Rule:** Badge color cannot be the only communication mechanism. Every badge includes text and is supported by an icon/pattern where practical.

### 4.3 Decision support, not control

The interface uses verbs such as:

- Review.
- Inspect.
- Compare.
- Evaluate.
- Simulate.
- Consider.
- Acknowledge.

The interface must not use misleading operational-control language such as:

- Apply signal timing.
- Deploy route diversion.
- Activate restriction.
- Optimize city automatically.
- Execute intervention.

Instead, use:

> “Run simulated signal-timing scenario”

and:

> “Advisory only — human approval required before any external action.”

### 4.4 Progressive disclosure

The main operations screen must answer “what needs attention?” in seconds. Technical detail appears progressively:

```text
Overview map
→ selected asset/corridor detail
→ forecast/evidence
→ model/scenario details
→ raw/technical metadata
```

### 4.5 Map is the spatial anchor, not the only interface

The map provides location and state context. Charts, alerts, explanations, scenario results, and data-quality panels are equally important.

---

## 5. Information architecture

### 5.1 Primary navigation

```text
Operations
Traffic Analytics
Energy Analytics
Environment Context
Scenario Studio
Recommendations
System & Data Health
```

### 5.2 Navigation principles

- `Operations` is the default landing view.
- `Scenario Studio` is restricted to analyst/admin roles when access control is enabled.
- `Recommendations` presents advisory evidence, not a command queue.
- `System & Data Health` is visible to administrators/research users and may be summarized for operators.
- Navigation labels must be written in plain, government/operations-appropriate language.

### 5.3 Screen hierarchy

```text
Application shell
├── Operations
│   ├── Map overview
│   ├── Corridor summary
│   ├── Alerts/recommendations summary
│   └── Selected entity detail drawer
├── Traffic Analytics
│   ├── Segment forecast
│   ├── Trend/history
│   ├── Explanation/quality
│   └── Network/corridor context
├── Energy Analytics
│   ├── Building/zone load
│   ├── Forecast/peak advisory
│   └── Source/provenance
├── Environment Context
│   ├── Weather
│   ├── AQI/air-quality source
│   └── Threshold status/caveats
├── Scenario Studio
│   ├── Scenario template selection
│   ├── Assumption review
│   ├── Run progress
│   └── KPI comparison
├── Recommendations
│   ├── Advisory feed
│   ├── Evidence drill-down
│   └── Review/acknowledgement status
└── System & Data Health
    ├── Source freshness
    ├── Ingestion quality
    ├── Model status
    ├── Scenario-service status
    └── Audit/system events
```

---

## 6. Global application shell

### 6.1 Header

The header contains:

- Product title: **Digital Twin-Enabled Smart City Analytics Platform**.
- Pilot context subtitle: **Pune pilot corridor** or equivalent neutral pilot label.
- Environment badge: `Development`, `Demo`, or `Production-like demo`.
- Global source-mode summary: Live/replay/simulation/predicted counts where relevant.
- Current system-health indicator.
- Authenticated user/role menu.
- Optional dark/light mode control.

### 6.2 Global status bar

A compact status bar or panel must communicate:

```text
Data freshness: updated 18 seconds ago
Source mode: REPLAY + SIMULATION
Traffic model: traffic-xgb-v1
Energy model: energy-xgb-v1
Scenario service: available
```

Do not show raw implementation details by default. Allow a “details” expansion for advanced/research users.

### 6.3 Responsive behavior

- Desktop is the primary experience because operations maps, charts, and scenarios need visual space.
- Tablet is supported with stacked/condensed panels.
- Mobile provides a monitoring-focused experience: current conditions, alerts, simplified map, and read-only scenario results.
- Do not force dense scenario configuration workflows onto small screens.

---

## 7. Operations view

### 7.1 Purpose

The Operations view is the default dashboard. It answers:

- What is the current corridor status?
- Where are the stressed segments or alerts?
- What information is current versus replayed/simulated/predicted?
- What requires review?

### 7.2 Required layout

```text
┌─────────────────────────────────────────────────────────────────────┐
│ Header: Product · Pilot · Status · User                              │
├───────────────┬─────────────────────────────────────┬───────────────┤
│ Left panel    │ Main map                             │ Right panel   │
│ Filters       │ Road/intersection/sensor overlays    │ Corridor      │
│ Layer legend  │ Selected geometry and alerts         │ summary       │
│ Source mode   │                                     │ Alerts        │
│ Time context  │                                     │ Recommendations│
├───────────────┴─────────────────────────────────────┴───────────────┤
│ Bottom tray: selected entity trend / forecast / provenance           │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.3 Required map layers

| Layer | Description | Required |
|---|---|---:|
| Basemap | OSM-based base map | Yes |
| Pilot boundary | Versioned study-area polygon | Yes |
| Roads | Road-segment geometry | Yes |
| Traffic state | Speed/congestion styling by segment | Yes |
| Junctions | Intersection markers and status | Yes |
| Logical sensors | Source/health markers | Yes |
| Energy entity | Building/zone marker/polygon | Yes |
| Weather/AQI sources | Context station markers | Should |
| Forecast overlay | Future condition styling/pattern | Yes |
| Scenario overlay | Explicit simulation-only layer | Yes when scenario selected |
| Recommendations | Evidence-backed advisory markers | Yes |

### 7.4 Map interactions

| Interaction | Expected behavior |
|---|---|
| Click road segment | Open entity detail with current, history, forecast, source, quality |
| Click intersection | Show connected segments, status, scenario relevance |
| Click sensor | Show source mode, last event, quality/freshness, linked entity |
| Click recommendation | Open advisory evidence/detail panel |
| Toggle layer | Show/hide non-critical overlays without changing underlying data |
| Filter source mode | Filter/highlight `LIVE`, `REPLAY`, `SIMULATION`, `PREDICTED` data |
| Select time window | Update charts/overlays where supported; preserve source label |
| Reset view | Return to full pilot boundary |

### 7.5 Traffic symbology

Traffic state styling should use a consistent scale, for example:

| Condition | Suggested visual |
|---|---|
| Low congestion / high speed | Cool/neutral green-blue family + text/value on selection |
| Moderate congestion | Amber/orange family |
| High congestion | Red/magenta family with pattern/label support |
| Unknown/stale | Gray/dashed/striped line |
| Simulation overlay | Distinct outline or hatch/pattern plus `SIMULATION` label |
| Forecast overlay | Dashed/glow-free overlay or future-horizon marker, never identical to observed state |

Do not use neon glows, decorative 3D effects, or color-only semantics.

### 7.6 Corridor summary card

Required fields:

- Overall corridor state: normal / elevated / stressed / unknown.
- Number of affected road segments.
- Highest forecasted congestion/speed concern.
- Current dominant source mode.
- Last update time.
- Number of active advisories.
- Scenario status if one is running.

The summary must state whether it is based on observed, replayed, simulated, or predicted data.

---

## 8. Entity detail experience

### 8.1 Purpose

An entity detail drawer/panel explains a selected road, junction, sensor, energy zone, or environmental station without forcing users to navigate away from the map.

### 8.2 Mandatory entity detail sections

```text
1. Identity and location
2. Current state
3. Source/provenance and freshness
4. Trend/history
5. Forecast and uncertainty
6. Related assets
7. Alerts/recommendations
8. Technical evidence/details (expandable)
```

### 8.3 Road segment detail

Required fields:

- Segment name/ID.
- From/to intersection.
- Geometry or length where available.
- Current traffic metric and unit.
- Current source mode.
- Last observed time.
- Data-quality state.
- History chart.
- 15-minute forecast and interval.
- Model version.
- Feature explanation summary.
- Related sensor/source.
- Related recommendations/scenario results.

### 8.4 Energy entity detail

Required fields:

- Building/zone name/ID.
- Energy source type: measured/replayed/benchmark/synthetic.
- Current load/demand and unit.
- Historical trend.
- 60-minute forecast/interval.
- Peak threshold status.
- Model version.
- Source/provenance caveat.

### 8.5 Environmental station detail

Required fields:

- Station/source name.
- Geographic location.
- Metric(s) and units.
- Last observed time.
- Regional/corridor relevance caveat.
- Threshold status.
- Source mode.

---

## 9. Traffic analytics view

### 9.1 Purpose

Allow traffic-management, planning, and governance users to understand near-term mobility conditions, forecast quality, and contributing factors.

### 9.2 Required content

- Selected segment/intersection/corridor selector.
- Current traffic metric card.
- Historical trend chart.
- 15-minute forecast chart/marker.
- Forecast interval/uncertainty visualization.
- Baseline comparison summary for research/advanced view.
- Input quality/completeness indicator.
- Model version and source-data caveat.
- Feature importance/SHAP explanation summary.
- Link to relevant scenario template or completed scenario runs.

### 9.3 Forecast visualization rules

```text
Observed series: solid line
Forecast series: dashed line
Prediction interval: subdued translucent band
Stale/low-quality input: warning annotation
Simulation-generated input: SIMULATION badge near chart title
Replay-generated input: REPLAY badge near chart title
```

Never show predicted values as an extension of the solid observed line without a clear visual boundary.

### 9.4 Forecast explanation pattern

Use plain language before technical detail:

```text
Why this forecast?
- Recent congestion trend increased over the last 15 minutes.
- Current time falls within the configured peak-period pattern.
- Rainfall/temperature context contributed [if used].
- Input completeness: 95%.

Technical details
- Model: traffic-xgb-v1
- Forecast horizon: 15 minutes
- Top features: speed_lag_5m, rolling_speed_15m, hour_of_day
```

Avoid saying the model “knows” or “decides.” Use “forecast indicates,” “model estimate,” or “evidence suggests.”

---

## 10. Energy analytics view

### 10.1 Purpose

Allow energy/utility/facility stakeholders to review representative demand, identify possible peaks, and understand data limitations.

### 10.2 Required content

- Entity/zone selector.
- Current demand card and unit.
- Source label: measured/replay/benchmark/synthetic.
- Historical load chart.
- 60-minute forecast with interval.
- Peak threshold marker.
- Advisory card if threshold exceeded.
- Weather/context feature display where relevant.
- Model version and top explanatory factors.

### 10.3 Energy integrity rule

If the energy source is benchmark/replay/synthetic, the view must include a persistent but non-intrusive statement:

> “This pilot energy stream is [replayed benchmark/synthetic] data and is not a measured meter feed from the Pune pilot corridor.”

---

## 11. Environment context view

### 11.1 Purpose

Provide environmental context, not a falsely precise localized environmental diagnosis.

### 11.2 Required content

- Weather summary: temperature, humidity, precipitation/wind where available.
- Air-quality/AQI card with station name/source.
- Observation time and freshness.
- Threshold status.
- Geographic relevance/caveat.
- Trend chart where history is available.

### 11.3 Required caveat

When using regional station data, show:

> “This reading is sourced from a Pune monitoring station and may not represent micro-level conditions at the pilot corridor.”

---

## 12. Scenario Studio

### 12.1 Purpose

Scenario Studio allows authorized users to compare approved mobility interventions in a safe simulated environment.

It must feel like an evidence workspace, not a control console.

### 12.2 Access

- Viewer: may view completed scenario results.
- Analyst: may run approved templates within allowed parameters.
- Administrator: may configure templates/thresholds where supported.

### 12.3 Scenario flow

```text
Choose scenario template
→ review purpose, assumptions, limits, and input configuration
→ confirm simulation-only execution
→ start run
→ monitor progress/status
→ inspect baseline vs intervention KPI comparison
→ review result caveats
→ optionally open/create advisory record
```

### 12.4 Scenario template selection

Each scenario card must show:

- Scenario name.
- Plain-language purpose.
- Intervention type.
- Variables that may change.
- Variables held constant.
- Network and demand version.
- Expected KPI outputs.
- Simulation-only label.
- Estimated run duration if known.

Example card text:

```text
Signal timing adjustment
Purpose: Evaluate whether a configured phase-duration change reduces simulated
queue length and delay at the selected junction during a defined demand period.

This is a simulation. It does not change any real signal.
```

### 12.5 Scenario configuration

The MVP should expose only safe, bounded, predefined parameters:

- Demand profile selection.
- Approved signal plan variant.
- Approved turn restriction toggle.
- Seed selection/default.
- Time window.

Do not expose raw SUMO files, unrestricted scripts, or infrastructure-control parameters in the general UI.

### 12.6 Run progress states

| Status | UI behavior |
|---|---|
| Queued | Show pending state, request time |
| Preparing | Show network/input validation stage |
| Running baseline | Show clear progress text; do not imply result yet |
| Running intervention | Show clear progress text |
| Computing KPIs | Show comparison preparation state |
| Completed | Enable results/comparison |
| Failed | Explain failure safely and offer technical reference for authorized users |

### 12.7 Scenario result comparison

Use a side-by-side comparison table plus visual indicators.

| KPI | Baseline | Intervention | Delta | Interpretation |
|---|---:|---:|---:|---|
| Average travel time | value | value | ± value | Improved/worse/unchanged in simulation |
| Average delay | value | value | ± value | Improved/worse/unchanged in simulation |
| Queue length | value | value | ± value | Improved/worse/unchanged in simulation |
| Throughput | value | value | ± value | Improved/worse/unchanged in simulation |

Every result must show:

```text
SIMULATION
Network version: ...
Demand input: ...
Seed: ...
Run time: ...
```

### 12.8 Scenario result language

Use:

- “In this simulated scenario…”
- “The intervention reduced simulated average delay by…”
- “This result depends on the network and demand assumptions.”

Do not use:

- “This will reduce actual Pune traffic by…”
- “Deploy this signal plan.”
- “Guaranteed improvement.”

---

## 13. Recommendations view

### 13.1 Purpose

Recommendations are an evidence-backed advisory queue for authorized review.

### 13.2 Advisory card anatomy

```text
[Severity / type] [ADVISORY] [PREDICTED / SIMULATION / LIVE]
Title: Forecasted congestion risk on Segment X
Time: Generated at ... · target time ...

Why it appeared:
- Forecast congestion index: 0.71
- Configured threshold: 0.70
- Input completeness: 95%
- Data source: REPLAY / SIMULATION / LIVE

Suggested next step:
Review the approved signal-timing scenario.

Evidence: Forecast · Model version · Scenario result (if present)
[Inspect evidence] [Mark reviewed]

Human approval required. No physical action is performed by this platform.
```

### 13.3 Recommendation severity

Use a small, clearly defined set:

| Severity | Meaning |
|---|---|
| Informational | Context or trend worth reviewing |
| Attention | Threshold crossed; operator/planner review suggested |
| High attention | Significant modeled/observed concern requiring prompt human review |

Do not use “critical” unless a well-defined, validated safety rule exists. The MVP should normally use `Informational` and `Attention`.

### 13.4 Review lifecycle

```text
New → Viewed → Reviewed → Linked to scenario/decision note → Closed
```

Original evidence must remain immutable even after review status changes.

---

## 14. System and data health view

### 14.1 Purpose

Give technical administrators, research users, and authorized operations users a trustworthy view of platform reliability without exposing unnecessary implementation complexity by default.

### 14.2 Required health cards

| Card | Required fields |
|---|---|
| Data sources | Source name, mode, last update, freshness, validation success/failure count |
| Ingestion | Events accepted/rejected/duplicate; latest error summary |
| Twin state | Current entity count, stale entities, latest state update |
| Models | Active model version, last inference, status, recent metrics link |
| Scenario service | Availability, last run, current run status, failures |
| Database | Ready/degraded status, last backup/export indicator if implemented |
| API | Health/readiness state |

### 14.3 Detail behavior

- Operators see clear status: healthy / attention / unavailable.
- Administrators may expand to technical event details.
- Research users may export health/quality evidence for evaluation.

---

## 15. Visual design system

### 15.1 Art direction

**Direction:** Civic infrastructure + analytical clarity.

The visual tone should feel:

- Trustworthy.
- Calm.
- Precise.
- Professional.
- Public-sector appropriate.
- Research credible.
- Modern without looking like a generic “AI smart city” template.

Avoid:

- Neon-purple/blue gradients.
- Decorative glowing city grids.
- Futuristic “hologram” visuals.
- Excessive glassmorphism.
- Random 3D shapes.
- Overuse of badges/colors.
- Overly rounded SaaS-card aesthetics.

### 15.2 Recommended palette

Use neutral surfaces with a restrained deep teal/blue primary for navigation and interactive emphasis. Reserve multiple hues primarily for semantic map/data states.

| Token | Suggested intent |
|---|---|
| Background | Warm/cool neutral, low distraction |
| Surface | White/light neutral in light mode; deep charcoal in dark mode |
| Primary | Deep teal or city-blue for action/focus |
| Traffic low | Teal/green-blue |
| Traffic moderate | Amber |
| Traffic high | Red/magenta with accessible label/pattern |
| Simulation | Purple or slate pattern with explicit label |
| Prediction | Blue dashed/outlined treatment |
| Warning/stale | Amber + timestamp |
| Error/invalid | Red + text/icon |

### 15.3 Typography

Use a highly legible sans-serif UI font. Prefer:

- **Primary:** Satoshi, Inter, Source Sans 3, or IBM Plex Sans.
- **Data/numeric:** tabular figures enabled where available.

Rules:

- Body text minimum: 16px equivalent.
- Buttons/navigation minimum: 14px equivalent.
- Secondary labels minimum: 12px equivalent.
- Use sentence case for labels.
- Use title case sparingly for headings.
- Avoid condensed/decorative type in operational views.

### 15.4 Spacing and density

- Use a 4px spacing system.
- Dashboard density should be balanced: enough information for operations, enough whitespace for confidence.
- Panels should use consistent padding and alignment.
- Avoid cramming charts, cards, and KPIs into one view.
- Keep primary map interactions within one main scroll context on desktop.

### 15.5 Borders and elevation

- Prefer subtle neutral 1px borders or surface contrast.
- Use shadows only to indicate elevated drawers/modals/popovers.
- Avoid colored side borders on cards.
- Use consistent corner radius; denser controls use smaller radius than panels.

---

## 16. Component specifications

### 16.1 Provenance badge

Required component props:

```text
mode: LIVE | REPLAY | SIMULATION | PREDICTED | STALE | INVALID
size: compact | standard
showIcon: boolean
showTimestamp: boolean
```

Must:

- Include text, not color only.
- Be keyboard/screen-reader readable.
- Use consistent meaning globally.

### 16.2 Data-quality indicator

Required states:

- Valid.
- Suspect.
- Stale.
- Missing.
- Invalid.

Display:

```text
Data quality: Valid (95% input completeness)
Last observed: 14:05 IST
```

### 16.3 KPI card

Must show:

- Metric name and unit.
- Current value or scenario value.
- Context/time range.
- Delta/trend only if comparison basis is clear.
- Source mode or scenario label.

Do not show a green upward arrow for every increase: an increase may be bad for congestion, energy, or AQI.

### 16.4 Chart component

Must support:

- Time axis with time zone/format.
- Units.
- Source/provenance label.
- Observed vs forecast distinction.
- Interval band if available.
- Data-quality/stale gaps.
- Tooltip with full timestamp/value/source.
- Accessible text summary or table fallback where feasible.

### 16.5 Alert/recommendation card

Must show:

- Type/severity.
- Provenance.
- Timestamp.
- Plain-language title.
- Evidence summary.
- Suggested next action.
- Human approval statement.
- Evidence drill-down action.

### 16.6 Scenario result table

Must:

- Compare baseline/intervention values side by side.
- Show delta with unit and direction.
- Use plain interpretation text.
- Show run metadata.
- Provide export/copy option later if useful.

---

## 17. Interaction and feedback rules

### 17.1 Loading states

Use contextual skeletons for:

- Map asset layers.
- Entity detail drawer.
- Charts.
- Scenario results.
- Health cards.

Do not use a full-screen spinner for routine panel loading.

### 17.2 Empty states

Every empty state must explain:

- What data would appear here.
- Why it is unavailable.
- What action is possible.

Examples:

```text
No current traffic observations
The selected source has not published a valid update in the configured freshness window.
View last known state or switch to replay/simulation mode.
```

```text
No completed scenario yet
Select an approved scenario template to create a simulated baseline-versus-intervention comparison.
```

### 17.3 Error states

Use specific, actionable messages:

```text
Scenario run could not complete
The simulator returned an error before KPI comparison. The run configuration and logs are available to authorized users.
```

Avoid vague messages such as “Something went wrong.”

### 17.4 Confirmation patterns

Confirm only actions that affect data/configuration or begin expensive computation:

- Run scenario.
- Change threshold/configuration.
- Clear/re-import data.
- Archive model/run.

A scenario confirmation must include:

```text
This will run a simulation only.
No real traffic signal, road rule, or city service will be changed.
```

### 17.5 Motion

- Use short, functional transitions for drawers, tabs, and loading completion.
- Avoid animated vehicles or moving heatmaps in the main operational dashboard if they reduce clarity.
- Respect reduced-motion preference.
- Optional 3D demo may animate simulated vehicles, but must label them as simulation.

---

## 18. Accessibility requirements

### 18.1 Minimum requirements

- Keyboard-navigable navigation, controls, map alternatives, drawers, and scenario actions.
- Visible focus indicators.
- WCAG AA contrast for text and key controls.
- Status not communicated by color alone.
- Text alternatives for map status and charts where practical.
- Icons accompanied by labels/tooltips/accessible names.
- Reduced-motion support.
- Minimum 44×44px touch target for primary controls on touch devices.

### 18.2 Map accessibility fallback

Maps are difficult for screen readers. Provide a synchronized list/table view for key map information:

- Road segment name.
- Current state.
- Forecast state.
- Source mode.
- Freshness.
- Active advisory.

### 18.3 Chart accessibility fallback

Each chart must offer:

- Text summary.
- Latest value and forecast summary.
- Downloadable/copyable table later if feasible.
- Explicit observed vs predicted explanation.

---

## 19. Optional 3D visualization specification

### 19.1 Role

The optional 3D view is a **presentation and spatial-comprehension enhancement**, not the primary operational UI and not a system dependency.

### 19.2 Approved use cases

- Demonstrate the physical context of the pilot corridor.
- Overlay simulated vehicle paths.
- Show road congestion as custom overlays.
- Display asset/sensor locations.
- Show selected scenario results.
- Present traffic/energy/environment state as overlays on a city scene.

### 19.3 Technical approach

```text
CesiumJS client
  ├── Reads same backend APIs/WebSocket events as 2D dashboard
  ├── Renders custom entities/overlays owned by this project
  └── May use approved 3D basemap source
```

### 19.4 Google Photorealistic 3D Tiles rules

If selected:

- Treat Google tiles as a visual basemap only.
- Configure billing/API keys/attribution/terms correctly.
- Do not extract geometry, train ML from imagery, perform prohibited analysis, or use offline content in violation of policy.
- Keep MapLibre 2D fully usable when Google tiles are unavailable.
- Clearly label custom simulated vehicles/state overlays as `SIMULATION`.

Resources:

- [Google Photorealistic 3D Tiles](https://developers.google.com/maps/documentation/tile/3d-tiles)
- [Google Map Tiles API policies](https://developers.google.com/maps/documentation/tile/policies)
- [CesiumJS](https://cesium.com/platform/cesiumjs/)

---

## 20. Screen-level acceptance criteria

### 20.1 Operations view

- [ ] Displays study-area boundary and core road/intersection layers.
- [ ] Shows current traffic overlay with visible legend.
- [ ] Allows entity selection.
- [ ] Shows provenance and freshness.
- [ ] Shows active recommendations.
- [ ] Does not confuse forecast/simulation with observed state.

### 20.2 Traffic analytics

- [ ] Shows current/historical/forecast traffic data.
- [ ] Forecast visually differs from observed data.
- [ ] Shows horizon, unit, interval/quality, and model version.
- [ ] Shows source-locality limitation where relevant.
- [ ] Provides explanation summary.

### 20.3 Energy analytics

- [ ] Shows load history and 60-minute forecast.
- [ ] Shows energy source type prominently.
- [ ] Shows peak threshold/advisory when applicable.
- [ ] Does not imply a benchmark/synthetic source is local measured meter data.

### 20.4 Scenario Studio

- [ ] Restricts selection to predefined templates.
- [ ] Shows simulation-only confirmation.
- [ ] Shows run progress and failure state.
- [ ] Shows baseline/intervention KPI comparison.
- [ ] Shows network/input/seed/run metadata.
- [ ] Labels all output as simulation.

### 20.5 Recommendations

- [ ] Shows advisory status, evidence, quality, and human-approval requirement.
- [ ] Allows drill-down to forecast/scenario evidence.
- [ ] Does not present recommendation as automatic action.
- [ ] Preserves original evidence when review state changes.

### 20.6 System & Data Health

- [ ] Shows source freshness and validation health.
- [ ] Shows model/scenario service status.
- [ ] Provides understandable degraded/unavailable states.
- [ ] Does not expose secrets or sensitive configuration values.

---

## 21. Design research and testing plan

### 21.1 Usability questions

Test whether a representative user can:

1. Identify the corridor’s current state.
2. Tell whether a value is simulated, replayed, live, or predicted.
3. Find the cause/evidence behind a recommendation.
4. Read a traffic forecast and uncertainty interval.
5. Run or review a permitted scenario.
6. Interpret whether the intervention improved or worsened simulated KPIs.
7. Understand that no real city action is taken by the platform.

### 21.2 Suggested test tasks

| Task | Success criterion |
|---|---|
| Find highest-congestion road segment | User identifies segment and source mode correctly |
| Explain a forecast | User identifies forecast horizon, interval/quality, and evidence |
| Review energy state | User identifies whether source is measured/replay/synthetic |
| Run scenario | User understands it is simulation only before confirming |
| Compare scenario results | User correctly identifies KPI change and caveat |
| Review advisory | User finds trigger/evidence and understands human approval requirement |

### 21.3 Measures

- Task completion rate.
- Time to find key evidence.
- Provenance comprehension.
- Scenario-result interpretation accuracy.
- Qualitative clarity/trust feedback.
- Accessibility issues found.

---

## 22. Implementation guidance

### 22.1 Frontend technology

| Concern | Choice |
|---|---|
| Framework | React + TypeScript + Vite |
| Map | MapLibre GL JS |
| Charts | Recharts, ECharts, or equivalent accessible chart library |
| Data fetching | Typed REST client + WebSocket event client |
| State | Lightweight local/query state; avoid unnecessary global complexity |
| Styling | CSS variables/design tokens; responsive layout |
| Icons | Lucide or another accessible consistent icon set |

### 22.2 Suggested frontend feature modules

```text
src/
  app/
  api/
  components/
  design-system/
  features/
    operations-map/
    entity-detail/
    traffic-analytics/
    energy-analytics/
    environment-context/
    scenario-studio/
    recommendations/
    system-health/
  hooks/
  types/
  utils/
```

### 22.3 Frontend data contracts

The frontend must consume typed contracts for:

- Study area/asset geometry.
- Current entity state.
- Historical observations.
- Forecasts.
- Recommendations.
- Scenario templates/runs/KPIs.
- Data health.
- WebSocket events.

No component should infer provenance from color or endpoint name. It must use explicit API fields.

---

## 23. Content and microcopy rules

### 23.1 Preferred wording

| Use | Avoid |
|---|---|
| Forecast indicates | AI knows / AI decided |
| Simulated result | Real-world outcome |
| Advisory | Command / order |
| Review scenario | Apply intervention |
| Data source | Truth source |
| Input completeness | Model certainty, unless statistically valid |
| Estimated impact | Guaranteed improvement |
| Human approval required | Automatically optimized |

### 23.2 Required disclaimer patterns

For non-local traffic model:

> “Initial model evaluation uses publicly available Pune intersection data. It does not establish measured accuracy for the pilot corridor.”

For synthetic/replayed energy:

> “This energy stream is replayed benchmark/synthetic data and is not a measured local meter feed.”

For environment station:

> “This environmental reading is station-based regional context and may not represent micro-level conditions at the pilot corridor.”

For scenario:

> “Simulation only. Results depend on documented network, demand, and signal assumptions; no real infrastructure is changed.”

---

## 24. Deferred UX capabilities

| Capability | Why deferred | Trigger |
|---|---|---|
| Citizen-facing public portal | Requires public communication, accessibility, and data-governance design | Stable validated government workflow |
| Full mobile operations app | Desktop workflow is primary | Confirmed field-user need |
| Public reporting/export portal | Needs policy, redaction, and governance review | Authorized data-sharing plan |
| Collaborative annotation/workflow | Requires multi-user permissions/audit detail | Multiple operational users confirmed |
| Full 3D navigation experience | Not required for core decision support | 2D workflow complete and 3D adds clear value |
| Natural-language assistant | Risks unclear/incorrect policy interpretation | Validated governance and retrieval controls |

---

## 25. Final UX statement

> The interface for the Digital Twin-Enabled Smart City Analytics Platform is a government-oriented urban decision-support dashboard. It uses the map as a shared spatial context while ensuring that every forecast, scenario output, recommendation, source, and limitation is visible and inspectable. The design supports human-governed decisions: it helps authorized city users observe, understand, compare, and review evidence, but it never disguises simulation as reality or automation as governance.
