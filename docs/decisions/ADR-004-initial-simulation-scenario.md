# ADR-004: Initial Simulation Scenario Design (Viman Nagar Chowk Signal Optimization)

## Context and Problem Statement
Per Phase 1 (`P1-12`) and Deliverable D-07, we must select and define the first microscopic simulation scenario for Eclipse SUMO before developing the TraCI execution wrapper. The goal is to provide a concrete, realistic what-if mobility intervention that can be tested against a calibrated baseline without risk to real infrastructure.

## Decision Outcome
The initial scenario focuses on **Evening Peak Signal Split Optimization at Viman Nagar Chowk (`urn:ngsi-ld:Intersection:PUNE:VN-01`)**.

### Baseline Configuration (`SCEN-BASE-01`)
- **Simulation Time Window:** 18:00 to 19:30 (evening commuter rush).
- **Signal Control:** Fixed-time 4-phase signal with 120-second cycle length:
  - Phase 1 (Nagar Road EB): 35s Green
  - Phase 2 (Nagar Road WB): 35s Green
  - Phase 3 (Viman Nagar Road NB): 25s Green
  - Phase 4 (Commercial / Mall Access link): 15s Green
  - Inter-green / All-Red buffers: 2.5s per phase.
- **Observed Problem:** Heavy spillback queues on Nagar Road EB approaching Phoenix Mall due to mall turn conflicts and high through-traffic volume.

### Intervention Configuration (`SCEN-INT-01`)
- **Intervention Type:** Dynamic signal green-split re-allocation based on queue lengths.
- **Parameters:**
  - Dynamic extension of Nagar Road EB green time up to +15s (from 35s to 50s) when upstream detector `urn:ngsi-ld:TrafficSensor:PUNE:DS-VN-EB-01` detects occupancy > 70%.
  - Cycle length maintained at 120s by proportionally reducing minor approach phases.
- **Evaluation KPIs:**
  1. Average Delay per Vehicle (seconds).
  2. 95th-percentile Queue Length (meters) on Segment `SEG-NR-EB-01`.
  3. Total Corridor Throughput (vehicles/hour).
  4. Travel Time along Arterial Centerline (seconds).

## Governance Invariant
All simulation outputs from this scenario must be tagged with `SIMULATION` provenance and presented in the Scenario Studio comparative table. They are purely advisory and cannot actuate real physical signal controllers.
