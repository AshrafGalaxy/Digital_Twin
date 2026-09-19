# Dataset Manifest: D-02 OSMnx Network Model

| Field | Detail |
|---|---|
| **Dataset ID** | D-02 |
| **Dataset Name** | OSMnx Viman Nagar Corridor Graph Representation |
| **Source URL** | https://github.com/gboeing/osmnx |
| **Access Date** | 2026-09-19 |
| **License / Terms** | MIT License |
| **Geographic Coverage** | Viman Nagar–Somnath Nagar corridor bounding box |
| **Temporal Coverage** | Derived from current OpenStreetMap network |
| **Sampling Frequency** | Static network extract |
| **Fields & Units** | Nodes (lat/lon, elevation, junction attributes), Directed Edges (length in meters, highway tag, lane count, speed limit, geometry) |
| **Locality Classification** | **PILOT_LOCAL** |
| **Intended Use** | Topological network graph verification, routing distances, and intermediate input to SUMO `netconvert` |
| **Prohibited Claims** | Does not guarantee real-time road conditions, current physical closures, or dynamic construction diversions. |
| **Known Limitations** | Dependent on underlying OSM completeness; elevation data interpolated where missing. |
| **Privacy / Sensitivity** | Open-source algorithmic graph; contains zero personal data. |
