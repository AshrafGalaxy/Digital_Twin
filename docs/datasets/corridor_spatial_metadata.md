# Corridor Spatial Metadata & GIS Validation

> **Pilot Study Area:** Viman Nagar Chowk (Phoenix Marketcity) ↔ Somnath Nagar Chowk corridor, Nagar Road, Pune, Maharashtra, India  
> **Asset ID:** `urn:ngsi-ld:StudyArea:PUNE:VN-SN-CORRIDOR`  
> **CRS:** EPSG:4326 (WGS 84)  
> **Boundary Extent:** South: 18.5575° N, West: 73.9120° E, North: 18.5665° N, East: 73.9325° E  
> **Corridor Length:** ~1.25 km arterial centerline

---

## 1. Primary Intersections & Road Network

### 1.1 Viman Nagar Chowk (`urn:ngsi-ld:Intersection:PUNE:VN-01`)
- **Coordinates:** `18.5602° N, 73.9168° E`
- **Configuration:** 4-leg major signalized junction (Nagar Road EB, WB, Viman Nagar Road North, Wadgaon Sheri Link South). Main access junction for Phoenix Marketcity traffic.
- **Cycle & Phases:** 120s cycle time, 4 phases.

### 1.2 Somnath Nagar Chowk (`urn:ngsi-ld:Intersection:PUNE:SN-01`)
- **Coordinates:** `18.5630° N, 73.9280° E`
- **Configuration:** 4-leg signalized junction (Nagar Road EB, WB, Somnath Nagar Road North, Anand Park Link South).
- **Cycle & Phases:** 90s cycle time, 3 phases.

### 1.3 Nagar Road Arterial Segments
- Divided 6-lane urban highway with physical central median (3 lanes EB: `SEG-NR-EB-01..03`; 3 lanes WB: `SEG-NR-WB-01..03`).
- Regulatory speed limit: 50 km/h; calibrated free-flow: 45–48 km/h. Capacity: 3,600 veh/hr per direction.

---

## 2. GIS Corrections Applied to OpenStreetMap

| Feature | Raw OSM Status | Digital Twin Curated Correction |
|---|---|---|
| **Lane Counts** | Often tagged generically as `lanes=2` or missing | Corrected to 3 arterial lanes each direction based on ground verification. |
| **BRTS Median** | Inconsistent separator barrier tagging | Explicitly modeled as divided dual-carriageway with separated EB and WB LineStrings. |
| **Commercial Entry** | Fragmented service road tagging | Modeled as discrete access nodes linked to Viman Nagar Chowk. |
| **Signal Locations** | Single nodes without approach links | Expanded into logical intersection assets with 4 linked approach legs and detector zones. |

---

## 3. Scope Boundary Rationale
- **Included:** Nagar Road arterial corridor between junctions, immediate approach legs (up to 250m), Phoenix Marketcity energy zone.
- **Excluded:** Dense interior residential lanes, Airport Road / Gunjan Chowk (further west), Chandan Nagar Bypass (further east).
