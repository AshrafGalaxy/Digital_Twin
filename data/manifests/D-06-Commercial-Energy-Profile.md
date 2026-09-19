# Dataset Manifest: D-06 Commercial Energy Demand Profile

| Field | Detail |
|---|---|
| **Dataset ID** | D-06 |
| **Dataset Name** | Phoenix Marketcity Commercial Zone Calibrated Energy Demand Profile |
| **Source URL** | Internal project benchmark derivative / Open energy benchmarks |
| **Access Date** | 2026-09-19 |
| **License / Terms** | Academic / Prototype Open Derivative |
| **Geographic Coverage** | Phoenix Marketcity zone, Viman Nagar, Pune |
| **Temporal Coverage** | 15-minute time series spanning typical seasonal and weekly cycles |
| **Sampling Frequency** | 15-minute intervals |
| **Fields & Units** | Timestamp (UTC), Active Power Demand ($kW$), Reactive Power ($kVAR$), Power Factor, HVAC Load Ratio |
| **Locality Classification** | **BENCHMARK_SYNTHETIC** |
| **Intended Use** | Training and testing the 60-minute ahead XGBoost building energy forecasting pipeline |
| **Prohibited Claims** | **MANDATORY:** Must NEVER be claimed as official, private, or real-time smart meter feeds from MSEDCL (Maharashtra State Electricity Distribution Co.) or Phoenix Marketcity mall management. |
| **Known Limitations** | Calibrated mathematical model based on floor area ($115,000 m^2$) and commercial load profiles, not sub-metered ground truth. |
| **Privacy / Sensitivity** | Synthetic aggregate non-residential commercial model; contains no private customer or residential records. |
