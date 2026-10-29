# Master Demo Handbook - Volume 2: Domain Engineering and Mathematical Foundations

## 1. Introduction: Why the Math Matters to the Judges

Judges and city stakeholders often ask: *"Is this just a pretty web dashboard, or is there real science and engineering running underneath?"*

This volume explains the physical laws, municipal standards, and mathematical formulations that power the digital twin. You do not need to memorize every equation, but knowing the concepts and plain-text formulas will give you complete authority during your demonstration.

---

## 2. Traffic Engineering and Arterial Mobility

### 2.1 The Fundamental Traffic Flow Equation (Greenshields Model)
Traffic behaves like a compressible fluid. The core equation connecting traffic volume, vehicle speed, and vehicle density is:

`q = k * v`

Where:
- `q` = Traffic Flow or Volume: The number of vehicles passing a sensor station per hour (vehicles/hour).
- `k` = Traffic Density: The concentration of vehicles packing the roadway (vehicles/kilometer).
- `v` = Space-Mean Speed: The average velocity of traffic moving along the corridor (km/h).

Under Greenshields model, as density increases, speed drops linearly:
`v = v_f * (1 - k / k_jam)`

Where:
- `v_f` = Free-Flow Speed: The speed when the road is completely empty (calibrated to 60 km/h on our arterial corridor).
- `k_jam` = Jam Density: The bumper-to-bumper standstill point where speed drops to zero (calibrated to 140 vehicles/km per lane).

The theoretical maximum capacity of any road segment occurs at critical density:
`q_max = (v_f * k_jam) / 4`
For a 3-lane arterial segment, this represents a saturation threshold of approximately 2100 to 2400 vehicles per hour per lane.

### 2.2 Level of Service (LOS): Indo-HCM vs US HCM Standards
Level of Service is the report card grade (from A to F) that traffic engineers assign to a road:

| LOS Grade | Traffic Condition | Driver Experience | Speed Range |
| :--- | :--- | :--- | :--- |
| **LOS A** | Free Flow | Completely unhindered; drivers choose their speed. | > 42 km/h |
| **LOS B** | Reasonably Free Flow | Manoeuvring is slightly restricted. | 38 - 42 km/h |
| **LOS C** | Stable Flow | Other vehicles noticeably affect driving. | 32 - 38 km/h |
| **LOS D** | Approaching Unstable | High density; small hiccups cause slowdowns. | 25 - 32 km/h |
| **LOS E** | Unstable Flow | Operating at maximum road capacity; stop-and-go waves. | 18 - 25 km/h |
| **LOS F** | Breakdown / Forced Flow | Gridlock; long queues spill back into upstream junctions. | < 18 km/h |

**The Indian Context (IRC:106 / Indo-HCM):**
Standard US highway manuals (US HCM 6th Edition) assume disciplined, homogeneous lane driving (mostly passenger cars). In Indian urban arterials, traffic is highly heterogeneous (two-wheelers, auto-rickshaws, buses, and cars weaving dynamically). 

Our platform includes a toggle for **Indo-HCM (IRC:106)**, which uses a dual-criteria evaluation factoring in both the Volume-to-Capacity ratio (`V/C`) and actual space-mean speed, reflecting real operating realities.

### 2.3 Webster Minimum Delay Signal Timing Optimization
When an intersection experiences heavy traffic, how should the signal timing change? The platform uses F.V. Webster classic formulation for optimum cycle time (`C_0`):

`C_0 = (1.5 * L + 5) / (1 - Y)`

Where:
- `L` = Total Lost Time per Cycle: The seconds lost during phase transitions (yellow change intervals and all-red clearance intervals, typically 12 to 16 seconds per cycle).
- `Y` = Sum of Critical Volume Ratios: `Y = y_1 + y_2 + ... + y_n`, where each `y_i = q_i / s_i` (ratio of actual approach volume `q_i` to saturation flow rate `s_i`).
- `C_0` = Optimum Cycle Length in seconds (bounded between 60s and 180s).

Once `C_0` is computed, green time is allocated proportionally to the critical approaches:
`g_i = (y_i / Y) * (C_0 - L)`

**Green Wave Coordination:**
To coordinate multiple intersections along Nagar Road (e.g. from Viman Nagar Chowk to Somnath Nagar Chowk, spaced 1.8 km apart), the system calculates an offset delay:
`Offset_seconds = Distance_meters / (Progression_Speed_kmh * 0.2778)`
This allows a platoon of vehicles departing the first green light to arrive at the second intersection just as its signal turns green, minimizing arterial stops.

---

## 3. Electrical and Energy Microgrid Engineering

The corridor includes major commercial hubs (such as Phoenix Marketcity, Solitaire Business Hub, and Hyatt Regency) connected to a 22kV primary municipal distribution substation.

### 3.1 Three-Phase Alternating Current (AC) Power Balance
Commercial facilities and distribution feeders operate on 3-phase AC power. The fundamental electrical relationships calculated by our backend are:

- **Active Power (P):** The real, usable power doing physical work (running air conditioning chillers, lighting, elevators).
  `P = sqrt(3) * V_LL * I_L * cos(phi)` (measured in kilowatts, kW)

- **Reactive Power (Q):** The power sustained by inductive electromagnetic fields (large AC motors, compressors, transformers).
  `Q = sqrt(3) * V_LL * I_L * sin(phi)` (measured in kilovolt-amperes reactive, kVAR)

- **Apparent Power (S):** The total vector sum of power delivered through utility cables.
  `S = sqrt(3) * V_LL * I_L = sqrt(P^2 + Q^2)` (measured in kilovolt-amperes, kVA)

- **Power Factor (PF):** The efficiency ratio of real power to apparent power:
  `PF = P / S = cos(phi)`
  Municipal utilities penalize commercial customers if the power factor drops below 0.95. Our platform monitors power factor continuously (calibrated between 0.96 and 0.98).

### 3.2 Kirchhoff Conservation of Energy Law
Within the corridor microgrid, energy cannot disappear. The electrical balance at any moment must obey:

`P_grid + P_solar + P_bess = P_loads + P_losses`

Where:
- `P_grid` = Net power imported from the primary 22kV utility grid.
- `P_solar` = On-site rooftop solar photovoltaic generation (active during daylight hours).
- `P_bess` = Power from the Battery Energy Storage System (positive when discharging to support the grid, negative when charging from surplus solar).
- `P_loads` = Aggregate commercial power consumed by the facilities.
- `P_losses` = Technical distribution line and transformer core losses (typically 2 to 4 percent).

### 3.3 Feeder Thermal Ampacity and Transformer Headroom
Every underground distribution cable and transformer has a maximum current rating (`I_rated`) before conductor insulation begins to degrade from heat.

- **Ampacity Utilization:**
  `Utilization_% = (I_measured / I_rated) * 100%`

- **Available Electrical Headroom:**
  `Headroom_kW = sqrt(3) * V_LL * (I_rated - I_measured) * PF`

If utilization exceeds 85%, the platform raises an `ELEVATED` advisory. If it exceeds 95%, it triggers a `CRITICAL_OVERLOAD` risk warning, prompting a commercial demand response recommendation.

---

## 4. Environmental Science and Air Quality Monitoring

### 4.1 Air Quality Index (AQI) Calculation
The platform monitors ambient air quality from Continuous Ambient Air Quality Monitoring Stations (CAAQMS). AQI is calculated using linear piecewise interpolation based on official CPCB (Central Pollution Control Board, India) standards:

`I = ((I_hi - I_lo) / (BP_hi - BP_lo)) * (C - BP_lo) + I_lo`

Where:
- `C` = Monitored pollutant concentration (e.g. 24-hour average PM2.5 in micrograms per cubic meter).
- `BP_hi`, `BP_lo` = The concentration breakpoint category boundaries containing `C`.
- `I_hi`, `I_lo` = The corresponding AQI index boundaries.

**AQI Categories:**
- 0 to 50: Good (Green)
- 51 to 100: Satisfactory (Light Green)
- 101 to 200: Moderate (Amber)
- 201 to 300: Poor (Orange)
- 301 to 400: Very Poor (Red)
- 401+: Severe (Maroon)

The overall reported AQI is dictated by the **determining pollutant** (the specific pollutant resulting in the highest sub-index, which in arterial traffic corridors is almost always PM2.5 or PM10).

### 4.2 Statistical Anomaly Detection (Isolation Forest)
To distinguish normal rush-hour emissions from sudden industrial discharges or sensor malfunctions, the backend runs a scikit-learn **Isolation Forest** coupled with dynamic Z-score evaluation:

`Z = (PM25 - mu) / sigma`

Where `mu` is the rolling diurnal expected baseline and `sigma` is the standard deviation. A reading with `|Z| > 2.0` or an anomalous tree isolation path score is flagged immediately as a candidate anomaly for environmental investigation.

---

## 5. Machine Learning, Conformal Prediction, and Explainability

### 5.1 Multi-Horizon XGBoost Forecasting
Forecasting traffic velocity and commercial electricity consumption is performed by an **XGBoost (Extreme Gradient Boosting)** regressor.

**Feature Engineering:**
The model does not simply look at the last number. It constructs a multi-dimensional feature vector:
1. **Historical Lag Features:** Readings from `t - 15m`, `t - 30m`, `t - 45m`, and `t - 60m`.
2. **Cyclical Diurnal Time Features:** Hour of day mapped into continuous sine and cosine waves:
   `sin_hour = sin(2 * pi * hour / 24)`
   `cos_hour = cos(2 * pi * hour / 24)`
   This avoids artificial discontinuities between 23:59 and 00:00.
3. **Day of Week Features:** Capturing workday rush-hour vs weekend leisure traffic patterns.

### 5.2 Conformal Prediction: Why It Matters
Most AI systems output a single number (e.g. "speed will be 32 km/h"). In municipal governance, a single number without an uncertainty bound is dangerous. Traditional statistical models output a plus-or-minus Gaussian bell curve, but real-world traffic data is skewed and non-Gaussian.

Our platform uses **Split Conformal Prediction**:
1. On a chronological calibration dataset, we calculate the non-conformity errors:
   `alpha_i = |y_actual - y_predicted|`
2. For a desired confidence level (e.g. 80% or 90%), we determine the empirical quantile `q_(1-alpha)` of these residuals.
3. The model outputs a mathematically guaranteed prediction band:
   `[y_predicted - q, y_predicted + q]`

This guarantees that the actual observed value will fall inside the shaded band with at least 80% or 90% mathematical certainty, regardless of the underlying distribution.

### 5.3 Explainable AI with TreeSHAP
City commissioners and traffic police officers will not trust a "black box" neural network.

Our platform integrates **TreeSHAP (SHapley Additive exPlanations)**. For every single forecast, it computes the exact contribution of each input feature:
`f(x) = base_value + sum(shap_value_i)`

When an operator looks at a speed drop forecast, the UI shows the **Top-5 Feature Attributions**:
- Feature 1: Recent 15-minute speed trend (-4.2 km/h impact)
- Feature 2: Evening peak hour multiplier (-3.8 km/h impact)
- Feature 3: Upstream intersection queue length (-1.5 km/h impact)
- Feature 4: Day of week (+0.8 km/h stability)

The operator can clearly see **why** the model made its prediction.

### 5.4 Data Drift Monitoring (Population Stability Index)
Over weeks and months, city traffic patterns shift (e.g. construction begins or holiday season starts). The platform monitors data drift using the **Population Stability Index (PSI)**:

`PSI = sum((Actual_% - Expected_%) * ln(Actual_% / Expected_%))`

- `PSI < 0.10`: **STABLE** (Model remains accurate and well-calibrated).
- `0.10 <= PSI < 0.25`: **WARNING** (Moderate distribution shift; retrain scheduled).
- `PSI >= 0.25`: **DRIFT** (Significant environmental shift; model alerts operator to recalibrate).

