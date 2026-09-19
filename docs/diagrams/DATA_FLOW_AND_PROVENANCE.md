# Data Flow and Provenance Separation Diagram
## Digital Twin-Enabled Smart City Analytics Platform

> **Document Status:** Provenance Architecture Contract (Deliverable `D-12`)  
> **Core Architecture Invariant:** Observed, Predicted, and Simulated states are strictly separated data classes.  
> Forecasts and scenario simulations **never overwrite** authoritative ground-truth observations.

---

```mermaid
flowchart TD
    subgraph INCOMING["1. Data Ingestion Stream"]
        RAW_TEL["Raw Corridor Telemetry<br/>(Sensors / Building Meters)"]
        SOURCE_MODE{"Source Mode<br/>Classification"}
    end

    subgraph OBSERVED_TIER["2. Authoritative Observed Twin State (System of Record)"]
        direction TB
        LIVE_REC["LIVE Observation<br/>(Timestamp: t, Quality: VALID)"]
        REPLAY_REC["REPLAY Observation<br/>(Historical Replay Timestamp: t)"]
        CURR_STATE[("entity_current_state<br/>(Authoritative Ground Truth)")]
    end

    subgraph PREDICTED_TIER["3. Predictive ML Forecast Stream (Isolated)"]
        direction TB
        FEAT_PIPE["Chronological Feature Pipeline<br/>(Lags, Rolling Stats, Cyclical Time)<br/>*Zero Future Leakage*"]
        XGB_INF["XGBoost Inference Engine<br/>• Point Prediction<br/>• p10/p90 Interval Bounds"]
        FORECAST_REC["ForecastRecord<br/>• Provenance: PREDICTED<br/>• Horizon: +15m / +60m<br/>• Model: traffic-xgb-v1 / energy-xgb-v1"]
    end

    subgraph SIMULATION_TIER["4. Microscopic Scenario Simulation (Isolated)"]
        direction TB
        SCEN_PARAM["Approved Scenario Template<br/>(SCEN-BASE-01 / SCEN-INT-01)<br/>• Parameter Sliders (+5s .. +25s)<br/>• Seed: 42"]
        SUMO_SIM["SUMO Microscopic / Kinematic Engine<br/>• Centerline Car-Following<br/>• Arterial Signal Plan Evaluation"]
        SCEN_REC["ScenarioRunResult<br/>• Provenance: SIMULATION<br/>• Comparative KPI Deltas<br/>• Non-Deployable Disclaimer"]
    end

    subgraph GOVERNANCE_TIER["5. Decision Support & Advisory Governance"]
        direction TB
        RULE_ENG["Deterministic Rule Engine<br/>(Evaluates Observed + Predicted + Scenario Evidence)"]
        ADVISORY["AdvisoryRecommendation<br/>• Status: ACTIVE ➔ REVIEW ➔ ACKNOWLEDGED<br/>• Traceable Evidence Links<br/>• humanApprovalRequired: TRUE<br/>• No External Actuation"]
        HUMAN["Human Municipal / Facility Decision-Maker<br/>(Authorizes Actions Outside Platform)"]
    end

    %% Data flow links
    RAW_TEL --> SOURCE_MODE
    SOURCE_MODE -->|Field Telemetry| LIVE_REC
    SOURCE_MODE -->|Archival Stream| REPLAY_REC

    LIVE_REC --> CURR_STATE
    REPLAY_REC --> CURR_STATE

    CURR_STATE ==>|Historical Lags at t| FEAT_PIPE
    FEAT_PIPE --> XGB_INF
    XGB_INF --> FORECAST_REC

    SCEN_PARAM --> SUMO_SIM
    SUMO_SIM --> SCEN_REC

    CURR_STATE -.->|Evidence Link| RULE_ENG
    FORECAST_REC -.->|Predictive Evidence| RULE_ENG
    SCEN_REC -.->|Scenario KPI Evidence| RULE_ENG

    RULE_ENG --> ADVISORY
    ADVISORY ==>|Advisory Inspection| HUMAN
    HUMAN -.->|Manual Field Action Outside Twin| RAW_TEL

    %% Strict Prohibitions (Dotted Red Lines)
    FORECAST_REC -.x|FORBIDDEN: Overwrite Current State| CURR_STATE
    SCEN_REC -.x|FORBIDDEN: Overwrite Current State| CURR_STATE
    ADVISORY -.x|FORBIDDEN: Autonomous Physical Actuation| RAW_TEL

    classDef forbidden stroke:#EF4444,stroke-width:2px,stroke-dasharray: 5 5,color:#EF4444;
    classDef observed fill:#0F4C5C,color:#fff,stroke:#38BDF8;
    classDef predicted fill:#6366F1,color:#fff,stroke:#818CF8;
    classDef simulation fill:#F59E0B,color:#fff,stroke:#FBBF24;
    classDef governance fill:#10B981,color:#fff,stroke:#34D399;

    class LIVE_REC,REPLAY_REC,CURR_STATE observed;
    class FORECAST_REC,XGB_INF,FEAT_PIPE predicted;
    class SCEN_REC,SUMO_SIM,SCEN_PARAM simulation;
    class ADVISORY,RULE_ENG governance;
```

---

## Provenance State Invariants

1. **State Isolation:** The authoritative current state table (`entity_current_state`) is strictly updated by validated observations (`LIVE` or `REPLAY`).
2. **Forecast Separation:** Predictions produced by `traffic-xgb-v1` and `energy-xgb-v1` are classified exclusively as `PREDICTED`. They are queried independently via `/api/v1/forecasts/*` and never overwrite sensor records.
3. **Scenario Separation:** SUMO scenario runs generate synthetic what-if projections labeled `SIMULATION`. They are stored in `scenario_runs` and evaluated side-by-side in `Scenario Studio`.
4. **Advisory Governance:** Recommendations emitted by the rule engine carry explicit links to the evidence (`sourceMode`, timestamp, model version, and threshold) and require municipal sign-off.
5. **Zero External Actuation:** No platform endpoint sends control packets to traffic lights, building controllers, or field infrastructure.
