# Urban Environmental Quality & Atmospheric Monitoring

## 1. Purpose

This domain is a reusable environmental digital twin for a city, district, campus, or industrial area. It combines air-quality, meteorological, noise, and contextual data to provide monitored conditions, regulatory-index calculations, spatial estimates, forecasts, and safe operational advice.

The platform is **location-agnostic in software design**, not zero-setup. Every Study Area configures its applicable regulations, sensor network, local meteorology, topography, source inventory, health-alert authority, and approved intervention policies.

## 2. Scope

The domain covers ambient air pollutants, microclimate, acoustic noise, sensor quality, environmental forecasting, exposure-risk mapping, and cross-domain recommendations.

Core capabilities:

- Monitor PM2.5, PM10, NO2, SO2, CO, O3, and other locally required pollutants.
- Ingest temperature, humidity, wind, rainfall, pressure, solar radiation, and available boundary-layer data.
- Monitor configured noise indicators such as Leq, Lday, Levening, and Lnight.
- Compute the locally applicable air-quality index using an explicit, versioned regulatory method.
- Estimate pollution fields between stations, forecast pollutant levels for 1 to 24 hours, and communicate uncertainty.
- Detect sensor faults, drift, missing data, and disagreement between reference and low-cost devices.
- Issue evidence-based health, traffic, building, dust-control, or operational recommendations through approved authority workflows.

Initial exclusions: replacing statutory reference monitoring, issuing legal public-health orders without authority approval, proving source attribution without a validated emissions inventory, and unrestricted automatic control of traffic, HVAC, or misting equipment.

## 3. Operating Modes

| Mode | Function | Intervention permission |
|---|---|---|
| Observe | Collect, validate, store, and visualize environmental data | None |
| Advise | Forecast conditions and recommend alerts or mitigation | None |
| Supervised response | Submit approved notices or local dust-control actions for operator approval | Approved action only |
| Bounded automation | Run pre-approved, low-risk local equipment inside strict limits | Restricted and auditable |
| Fallback | Suppress central action after uncertainty or fault | Local manual/approved control only |

Statutory monitoring agencies, health authorities, building operators, traffic authorities, and local safety systems remain authoritative within their responsibilities.

## 4. Architecture

```text
Reference stations / Low-cost sensors / Weather stations / Noise meters / Context feeds
        │  MQTT, HTTPS, OPC UA, or approved secure gateway
        ▼
Protocol Adapters and Validation
        ▼
Canonical Environmental Entities and Geospatial Registry
        ├──────────────────┬──────────────────┐
        ▼                  ▼                  ▼
Time-series observations  GIS grid/topography  Error/DLQ store
TimescaleDB               PostGIS/raster       ingestion_errors
        └──────────────────┴──────────────────┘
                           ▼
AQI rules, calibration, spatial estimates, forecasting, policy checks
                           ▼
Operator dashboard, uncertainty maps, recommendation queue, approved response workflow
```

Non-overwriting records are retained as:

- `observed`: validated sensor and external-source measurements.
- `derived`: AQI, calibrated readings, interpolation, exposure, and quality outputs.
- `predicted`: pollutant, noise, and meteorological forecasts.
- `scenario`: dispersion or intervention analysis outputs.
- `recommendation`: proposed response, evidence, reviewer decision, and expiry.
- `command`: approved, sent, acknowledged, verified, failed, expired, or rolled-back local actions.

## 5. Location Onboarding

The core platform is portable because sensor types, AQI methods, maps, rules, and models are configured rather than hardcoded. Each new Study Area requires:

| Layer | Required local configuration |
|---|---|
| Regulation | Applicable AQI method, pollutant averaging periods, breakpoints, noise zones, reporting and retention rules |
| Sensor network | Station location, inlet height, sensor type, calibration status, maintenance plan, ownership, and reference-station linkage |
| Geography | Boundary, land use, elevation, terrain, street canyons, sensitive receptors, and grid resolution |
| Context | Weather source, seasonal events, construction, traffic, industry, waste burning, dust, and other known emission sources |
| Governance | Health-alert authority, public-message approval, intervention owner, escalation path, and local safety limits |
| Calibration | Local historical data, collocation records, forecast validation, and model acceptance thresholds |

The active environmental context includes station health, calibration version, active data source, weather quality, source inventory version, local alert policy, and uncertainty. Every index, map, forecast, and recommendation records the configuration version used.

## 6. Data and Quality Controls

### 6.1 Inputs

| Source | Primary measurements |
|---|---|
| Reference monitoring station | Regulatory-grade pollutant concentrations and instrument status |
| Low-cost sensor node | Particle/gas readings, temperature, humidity, device diagnostics |
| Meteorological station or provider | Wind, temperature, humidity, pressure, rainfall, solar radiation, visibility, and boundary-layer data where available |
| Noise station | Configured A-weighted or equivalent noise metrics, quality status, and local zone |
| Context feeds | Traffic state, roadworks, construction, fire/smoke notices, industrial status, and planned events where approved |

Topic format:

```text
citytwin/{environment}/{source_mode}/environment/{study_area}/{device_type}/{device_id}
```

Example:

```text
citytwin/prod/live/environment/central-zone/air-sensor/pm-node-01
```

### 6.2 Canonical Air-Quality Event

```json
{
  "id": "urn:environment:AirQualityStation:central-zone-02",
  "type": "AirQualityObserved",
  "observedAt": "2026-09-25T16:30:00Z",
  "studyAreaId": "central-zone",
  "configurationVersion": "environment-central-v8",
  "pm25": {"value": 78.4, "unit": "ug/m3", "qualityScore": 0.97},
  "pm10": {"value": 142.1, "unit": "ug/m3", "qualityScore": 0.95},
  "no2": {"value": 45.2, "unit": "ug/m3", "qualityScore": 0.93},
  "temperature": {"value": 29.1, "unit": "degC", "qualityScore": 0.99},
  "relativeHumidity": {"value": 61.0, "unit": "%", "qualityScore": 0.99},
  "windSpeed": {"value": 2.3, "unit": "m/s", "qualityScore": 0.96},
  "provenance": {"sourceMode": "LIVE", "gatewayId": "gw-environment-01"}
}
```

All timestamps are stored in UTC; local reporting windows use the Study Area timezone.

Validation checks source identity, schema, units, timestamps, duplicate/late events, instrument status, calibration validity, physical plausibility, humidity/temperature limits, cross-sensor consistency, station location, and maintenance state. Invalid or degraded readings are retained with a reason but excluded from statutory or automated outputs.

### 6.3 Sensor Calibration & Drift Correction

Reference-grade instruments (BAM, UV fluorescence) are the authoritative baseline for official reporting. Low-cost electrochemical and optical sensors experience thermal drift and humidity swelling artifacts. Telemetry is calibrated online via an empirical multi-variable transfer function before canonical persistence:

$$\hat{C}_{\text{calibrated}} = \beta_0 + \beta_1 C_{\text{raw}} + \beta_2 \cdot T + \beta_3 \cdot \left(\frac{RH^2}{100 - RH}\right)$$

Where parameters $\beta$ are calibrated using reference-grade collocated CAAQMS stations. The platform tracks calibration version, collocation period, sensor age, drift, and expiration date.

## 7. Indices, Maps, and Models

### 7.1 Statutory Air Quality Index (AQI) Computation

AQI is calculated using piecewise linear interpolation against statutory pollutant concentration breakpoints:

$$I_p = \frac{I_{\text{high}} - I_{\text{low}}}{C_{\text{high}} - C_{\text{low}}} (C_p - C_{\text{low}}) + I_{\text{low}}$$

Where:
* $C_p$: The truncated 24-hour (or statutory rolling window) average concentration of pollutant $p$.
* $C_{\text{low}}, C_{\text{high}}$: Statutory concentration breakpoints enclosing $C_p$.
* $I_{\text{low}}, I_{\text{high}}$: Corresponding index breakpoint values.

The composite AQI follows the statutory worst-case maximum principle:

$$AQI = \max_{p \in \{\text{PM}_{2.5}, \text{PM}_{10}, \text{NO}_2, \text{SO}_2, \text{CO}, \text{O}_3, \text{NH}_3\}} (I_p)$$

### 7.2 Atmospheric Dispersion Modeling (Steady-State Gaussian Plume)

For point and localized line sources (e.g., arterial road segment idling emissions or industrial exhausts), downwind concentration fields are modeled dynamically:

$$C(x, y, z) = \frac{Q}{2\pi u \sigma_y \sigma_z} \exp\left( -\frac{y^2}{2\sigma_y^2} \right) \left[ \exp\left( -\frac{(z - H)^2}{2\sigma_z^2} \right) + \exp\left( -\frac{(z + H)^2}{2\sigma_z^2} \right) \right]$$

Where:
* $Q$: Continuous emission mass release rate ($\text{g/s}$).
* $u$: Surface wind speed at effective release height $H$ ($\text{m/s}$).
* $y, z$: Crosswind and vertical spatial coordinates relative to source centerline.
* $\sigma_y, \sigma_z$: Atmospheric dispersion coefficients parameterised by downwind distance $x$ and Pasquill-Gifford atmospheric stability classes (A through F) derived from solar radiation and wind speed.

### 7.3 Dynamic Spatial Interpolation (Wind-Weighted IDW)

For spatial visualization across zones lacking dense physical sensors, real-time concentrations are estimated onto a discrete PostGIS mesh via Inverse Distance Weighting (IDW) with wind directional weighting:

$$\hat{Z}(s_0) = \sum_{i=1}^{N} \lambda_i Z(s_i), \quad \lambda_i = \frac{d_{i0}^{-\alpha} \cdot (1 + \cos(\theta_i))}{\sum_{j=1}^{N} d_{j0}^{-\alpha} \cdot (1 + \cos(\theta_j))}$$

Where $\theta_i$ represents the alignment angle between the station-to-target vector and the prevailing wind vector.

### 7.4 Forecasting & Meteorological Feature Engineering

Quantile gradient boosted trees forecast $\text{PM}_{2.5}$ and $\text{PM}_{10}$ for 1 to 24 hours ($\alpha \in \{0.10, 0.50, 0.90\}$).

Features include:
* **Wind Vector Decomposition:** Converting polar wind data into orthogonal Cartesian components:
  $$u_{\text{wind}} = -v \cdot \sin(\theta), \quad v_{\text{wind}} = -v \cdot \cos(\theta)$$
* **Atmospheric Ventilation Coefficient (VC):**
  $$VC = \text{PBLH} \cdot u_{\text{wind}}$$
  Where $\text{PBLH}$ is the Planetary Boundary Layer Height (m), representing the vertical mixing volume for surface pollutants.
* **Thermal Inversion Index:** Vertical temperature gradient indicator ($\Delta T = T_{\text{surface}} - T_{\text{upper}}$), capturing ground-level pollution trapping during nighttime radiative cooling cycles.
* **Traffic Proxy Features:** Real-time and forecasted volume-to-capacity ($V/C$) ratios and average traffic speeds from adjacent corridor segments.
* **Autoregressive Lags:** Lags at $t-1\text{h}$, $t-2\text{h}$, $t-3\text{h}$, $t-6\text{h}$, $t-12\text{h}$, and $t-24\text{h}$.

## 8. Alerts, Mitigation, and Inter-Twin Orchestration

### 8.1 Recommendations and Exposure Alerts

The platform generates:
- Authority-approved public exposure advisories and Variable Message Sign (VMS) health warnings.
- Suspected sensor drift, calibration anomalies, or localized emission flares.
- Cross-domain traffic and building operational recommendations.

### 8.2 Localized Particulate Suppression Actuation

Anti-smog water mist cannons may be triggered around sensitive receptor zones (schools, hospitals, transit plazas) subject to strict meteorological interlocks:

```text
               Environmental Setpoints
[Twin State Engine] ──────────────► [Safety & Meteorological Interlock]
                                                   │
                                         Valid?    ├──► Reject: Suppress Spray
                                                   │
                                                   ▼
                                      [Actuator Industrial Gateway]
                                                   │
                                                   ▼ (Modbus-TCP / LoRaWAN)
                                      [Anti-Smog Mist Cannons / VMS]
                                                   │
                                                   ▼
                                      [Aerosol Reduction Response]
                                                   │
                                                   ▼
                                      [Downwind Concentration Delta]
```

Actuation Rules:
```text
IF PM10_observed >= 250 ug/m3
AND Wind_Speed <= 3.0 m/s
AND Relative_Humidity <= 80%
AND Precipitation == 0.0 mm
THEN:
  Trigger Anti-Smog Water Mist Cannon (Zone ID)
  Set Duty Cycle: 10 minutes run / 5 minutes rest
  Set Swivel Arc: 120 degrees upwind
```

Safety Invariants:
1. **Humidity Lockout:** Spray locks out if ambient relative humidity $>85\%$ to prevent localized ground ponding and slip hazards.
2. **Wind Speed Cutoff:** Spray locks out if wind speed $>5.0\text{ m/s}$ ($18\text{ km/h}$) to prevent mist drift into passing vehicular traffic.
3. **Audit Logging:** Every automated activation, duration timer, and suppression event is registered into the immutable `actuation_log` table with geographical and environmental provenance tokens.

### 8.3 Cross-Domain Inter-Twin Orchestration

1. **Traffic Domain Nexus:** When predicted AQI exceeds "Severe" ($>400$) along an arterial canyon, the twin automatically dispatches a prioritized advisory to the Traffic Scenario Engine to restrict Heavy Commercial Vehicles (HCV) and alter signal timing splits to clear stationary idling queues.
2. **Energy/Building Domain Nexus:** When ambient $\text{PM}_{2.5} > 150\ \mu\text{g/m}^3$, the twin issues BACnet signals to commercial building HVAC management systems to reduce outdoor air intake dampers from $20\%$ to $5\%$, running internal filtration cycles while modulating chiller setpoints to avoid occupant discomfort.

### 8.4 Command Lifecycle and Safety

```text
Proposed → Evidence and policy validated → Operator/authority approved → Sent
→ Gateway acknowledged → Field response verified → Completed, failed, expired, or rolled back
```

The platform blocks local action when measurements are stale, calibration is invalid, uncertainty is high, weather conditions are unsuitable, a device is faulted, a safety policy fails, or communication is unhealthy. On failure, central action stops and local equipment remains under approved local/manual control.

## 9. Privacy, Security, and Governance

Environmental data must use authenticated encrypted connections, device identities, least-privilege roles, network segmentation for operational devices, command authorization, credential rotation, and tamper-evident audit records.

Keep traceable histories of sensor calibration, maintenance, configuration/rule versions, AQI calculations, map and forecast versions, alerts, public-message approvals, recommendations, interventions, acknowledgments, overrides, and failures.

Noise monitoring must follow the local legal purpose, retention, access, and zoning rules. The platform does not use audio for speech surveillance or identity tracking.

## 10. Rollout and Acceptance

1. **Foundation:** configure regulations, Study Area boundary, sensors, reference data, geography, source context, roles, and security.
2. **Read-only monitoring:** validate telemetry, data quality, calibration status, dashboards, and regulatory-index calculations.
3. **Analytics:** deploy uncertainty maps, forecasts, sensor-drift detection, noise reporting, and source/context investigation workflows.
4. **Decision support:** produce authority-reviewed health, dust-control, traffic, and building recommendations.
5. **Supervised pilot:** test bounded local dust-suppression or approved communications with full logs and response verification.
6. **Bounded automation:** enable only after measured effectiveness, safety testing, policy approval, and reliable fallback behavior.

Minimum readiness requirements:

- The applicable regulatory method, pollutant averaging rules, and authority workflow are configured and verified.
- Critical sensors have known calibration and maintenance status; low-cost readings have explicit uncertainty.
- Maps, forecasts, and scenarios disclose confidence and limitations.
- Any intervention has a named owner, approved safety limits, water/energy/resource controls, and rollback path.
- Every action is authenticated, time-limited, logged, acknowledged, and field-verified.

## 11. Open Configuration Decisions

- Target environment: city, campus, industrial zone, construction corridor, or sensitive-receptor area.
- Applicable AQI/noise standards, reporting authority, and public-alert workflow.
- Available reference stations, low-cost sensor types, weather feeds, and maintenance capacity.
- Required pollutants, averaging periods, map resolution, forecast horizons, and retention policies.
- Approved source inventories and contextual feeds.
- Which responses are advisory only and which approved local assets may enter supervised or bounded automation.
