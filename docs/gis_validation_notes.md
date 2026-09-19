# GIS Validation Notes: Viman Nagar–Somnath Nagar Corridor

> **Asset ID:** `urn:ngsi-ld:StudyArea:PUNE:VN-SN-CORRIDOR`  
> **Target Network:** Nagar Road (Pune–Ahmednagar Highway), Viman Nagar Chowk ↔ Somnath Nagar Chowk  
> **Date:** 2026-09-19  
> **Status:** Validated Pilot Asset Baseline

---

## 1. Arterial Cross-Section & Lane Assumptions

### Nagar Road (Main Arterial)
- **Geometry:** Divided multi-lane urban highway with physical central median.
- **Lanes:** 3 lanes Eastbound (`SEG-NR-EB-01`, `SEG-NR-EB-02`, `SEG-NR-EB-03`) and 3 lanes Westbound (`SEG-NR-WB-01`, `SEG-NR-WB-02`, `SEG-NR-WB-03`).
- **Median & BRTS Infrastructure:** Dedicated central bus lane reservation (Rainbow BRTS corridor). For the MVP micro-simulation, the median is treated as a physical barrier preventing mid-block U-turns, with BRTS transit sharing the left/median reservation under mixed traffic assumptions.
- **Speed Limit:** 50 km/h regulatory speed limit; calibrated free-flow speed of 45–48 km/h.

---

## 2. Intersection Geometry & Turning Restrictions

### Viman Nagar Chowk (`urn:ngsi-ld:Intersection:PUNE:VN-01`)
- **North Leg (Viman Nagar Road):** 2 lanes undivided approaching south toward Nagar Road. Serves heavy two-wheeler and auto-rickshaw traffic from Symbiosis / residential sectors.
- **Turn Restrictions:**
  - Nagar Road Eastbound: Through movement permitted; Left turn into Viman Nagar Road permitted; Right turn into southern commercial lane restricted during peak hours (enforced via physical bollards / traffic police).
  - Viman Nagar Road Northbound: Left turn onto Nagar Road Eastbound permitted; Right turn onto Nagar Road Westbound regulated by dedicated signal phase.

### Somnath Nagar Chowk (`urn:ngsi-ld:Intersection:PUNE:SN-01`)
- **North Leg (Somnath Nagar Road):** 2 lanes approaching south.
- **South Leg (Anand Park / Wadgaon Sheri Link):** 2 lanes approaching north.
- **Turn Restrictions:**
  - Heavy left and right turning movements into Somnath Nagar interior residential areas; standard 3-phase signal plan with shared right-turn lanes.

---

## 3. OpenStreetMap Limitations and Corrections Applied

| Feature | Raw OSM Status | Digital Twin Curated Correction |
|---|---|---|
| **Lane Counts** | Often tagged generically as `lanes=2` or missing | Corrected to 3 arterial lanes each direction based on ground surveys and satellite verification. |
| **BRTS Median** | Inconsistent separator barrier tagging | Explicitly modeled as divided dual-carriageway with separated Eastbound and Westbound LineStrings. |
| **Mall Entry / Exit** | Fragmented service road tagging | Modeled as discrete access nodes linked to Viman Nagar Chowk. |
| **Signal Locations** | Mapped as single nodes without approach links | Expanded into logical intersection asset with 4 linked approach legs and 10 detector zones. |
