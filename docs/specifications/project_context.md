# Project Context & Corridor Pilot Scope
## Digital Twin-Enabled Smart City Analytics Platform

> **Corridor Pilot:** Viman Nagar Chowk (Phoenix Marketcity) ↔ Somnath Nagar Chowk, Nagar Road, Pune, Maharashtra  
> **Geographic Extent:** `[18.5575° N, 73.9120° E]` to `[18.5665° N, 73.9325° E]` | Length: ~1.25 km arterial centerline  
> **Key Municipal Stakeholders:** Pune Municipal Corporation (PMC), Pune Traffic Police, Urban Infrastructure SPVs

---

## 1. Municipal Problem Statement

The Pune-Ahmednagar highway (Nagar Road) through Viman Nagar is a vital multi-modal arterial experiencing:
1. **Severe Peak-Hour Congestion:** Heavy morning and evening surges between IT parks (Kalyani Nagar / Kharadi) and residential sectors.
2. **Commercial Traffic Friction:** High inbound and outbound vehicle queues at Phoenix Marketcity access junctions.
3. **Fragmented Municipal Data:** Traffic police, transit operators (PMPML BRTS), environmental agencies, and utilities operate isolated datasets without a unified operational picture.
4. **Lack of Pre-Implementation Simulation:** Signal timing adjustments are frequently made reactively in the field without predictive impact analysis.

---

## 2. Platform Mission & Solution

The Digital Twin-Enabled Smart City Analytics Platform delivers an integrated decision-support environment that:
- Maintains a real-time digital replica of corridor road segments, signalized junctions, and commercial facilities.
- Predicts 15-minute traffic speeds and 60-minute commercial power demand using calibrated XGBoost models.
- Enables safe "what-if" micro-simulation of adaptive signal interventions via Eclipse SUMO before field deployment.
- Recommends human-governed advisory actions with clear provenance, uncertainty bounds, and transparent evidence.

---

## 3. Pilot Boundary & Infrastructure Assets

### 3.1 Road Network
- **Nagar Road:** Divided 6-lane urban highway (3 lanes Eastbound, 3 lanes Westbound) with dedicated Rainbow BRTS central median reservations.
- **Speed Limit:** 50 km/h regulatory limit; 45–48 km/h calibrated free-flow speed.

### 3.2 Signalized Intersections
- **Viman Nagar Chowk (`INT-VN-01`):** Major 4-leg junction connecting Nagar Road with Viman Nagar core and Phoenix Marketcity.
- **Somnath Nagar Chowk (`INT-SN-01`):** 4-leg junction serving residential commuter access to Somnath Nagar and Wadgaon Sheri.

### 3.3 Commercial Energy Entity
- **Phoenix Marketcity (`BLD-PHOENIX-01`):** Large-scale retail and entertainment facility with 4,500 kVA sanctioned electrical load, serving as the representative building digital twin entity.
