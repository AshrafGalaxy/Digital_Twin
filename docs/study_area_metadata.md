# Study Area Metadata: Viman Nagar–Somnath Nagar Corridor

> **Pilot Study Area:** Viman Nagar Chowk (Phoenix Marketcity) ↔ Somnath Nagar Chowk corridor, Nagar Road, Pune, Maharashtra, India  
> **Asset ID:** `urn:ngsi-ld:StudyArea:PUNE:VN-SN-CORRIDOR`  
> **Boundary Version:** 1.0.0  
> **Capture Date:** 2026-09-19  
> **Coordinate Reference System:** EPSG:4326 (WGS 84 geographic coordinates)

---

## 1. Geographic Extent & Bounding Box

| Parameter | Coordinate / Value | Description |
|---|---|---|
| **Western Boundary** | `73.9120° E` | West of Phoenix Marketcity / Ramwadi approach |
| **Eastern Boundary** | `73.9325° E` | East of Somnath Nagar Chowk towards Chandan Nagar |
| **Southern Boundary** | `18.5575° N` | Approach buffer south of Nagar Road (Wadgaon Sheri access) |
| **Northern Boundary** | `18.5665° N` | Approach buffer north of Nagar Road (Viman Nagar core access) |
| **Center Point** | `18.5615° N, 73.9220° E` | Nagar Road central corridor section |
| **Corridor Length** | ~1.25 km | Main arterial centerline length |

---

## 2. Core Infrastructure Assets

### 2.1 Primary Intersections
1. **Viman Nagar Chowk (`urn:ngsi-ld:Intersection:PUNE:VN-01`):**
   - Coordinates: `18.5602° N, 73.9168° E`
   - Configuration: 4-leg major signalized junction.
   - Legs: Nagar Road Eastbound, Nagar Road Westbound, Viman Nagar Road (North), Wadgaon Sheri Link (South).
   - Key Feature: Main access junction for Phoenix Marketcity commercial traffic.
2. **Somnath Nagar Chowk (`urn:ngsi-ld:Intersection:PUNE:SN-01`):**
   - Coordinates: `18.5630° N, 73.9280° E`
   - Configuration: 4-leg signalized junction.
   - Legs: Nagar Road Eastbound, Nagar Road Westbound, Somnath Nagar Road (North), Anand Park Road (South).

### 2.2 Arterial Road
- **Nagar Road (Pune–Ahmednagar Highway):** Divided 6-lane urban arterial (3 lanes each direction) carrying heavy mixed-traffic commuter flow, public transit buses (BRTS infrastructure along central median), and commercial vehicles.

---

## 3. Inclusion and Exclusion Rationale

### Included in Pilot Scope
- **Arterial Centerline Segments:** Direct connecting links between Viman Nagar Chowk and Somnath Nagar Chowk.
- **Immediate Approach Legs:** Up to 250m on north/south intersecting roads to accurately capture turning queues and signal delays.
- **Representative Energy Zone:** Phoenix Marketcity commercial footprint directly adjacent to Viman Nagar Chowk.

### Excluded from Initial Scope
- **Interior Residential Networks:** Dense interior residential lanes of Viman Nagar and Somnath Nagar to avoid unnecessary simulation complexity.
- **Airport Road / Gunjan Chowk:** Major junction further west, excluded to preserve two-junction pilot discipline.
- **Chandan Nagar Bypass:** Highway section further east past Somnath Nagar.

---

## 4. OSM Extraction Methodology
- Spatial data is retrieved from OpenStreetMap using the bounding box `[18.5575, 73.9120, 18.5665, 73.9325]`.
- Highway tags filtered: `primary`, `primary_link`, `secondary`, `secondary_link`, `tertiary`.
- Data extracted via Overpass API / OSMnx script (`scripts/extract_osm_corridor.py`).
