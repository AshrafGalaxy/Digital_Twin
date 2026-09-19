# Dataset Manifest: D-07 SUMO Corridor Simulation Stream

| Field | Detail |
|---|---|
| **Dataset ID** | D-07 |
| **Dataset Name** | Eclipse SUMO Viman Nagar–Somnath Nagar Microscopic Traffic Stream |
| **Source URL** | Generated locally via Eclipse SUMO + TraCI |
| **Access Date** | 2026-09-19 |
| **License / Terms** | Eclipse Public License 2.0 (EPL-2.0) |
| **Geographic Coverage** | Viman Nagar–Somnath Nagar Corridor Network (`study_area.geojson`) |
| **Temporal Coverage** | Controlled repeatable simulation epochs (morning peak 08:30-10:30, evening peak 17:30-20:00) |
| **Sampling Frequency** | 1-second simulation step, aggregated to 60-second detector intervals |
| **Fields & Units** | Step time ($s$), segment ID, vehicle count ($veh$), mean speed ($m/s \to km/h$), density ($veh/km$), queue length ($m$), delay ($s$) |
| **Locality Classification** | **SIMULATION** |
| **Intended Use** | Testing what-if intervention scenarios (e.g. dynamic signal splits at Viman Nagar Chowk), synthetic telemetry event generation |
| **Prohibited Claims** | **MANDATORY:** Must NEVER be described as field-observed vehicle measurements or empirical proof of commuter benefits. |
| **Known Limitations** | Driver behavioral models (Krauss car-following) are approximations; does not fully model Indian informal lane-sharing behavior without calibration. |
| **Privacy / Sensitivity** | Fully synthetic microsimulation; zero personal data. |
