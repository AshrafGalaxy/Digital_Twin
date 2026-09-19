# Architecture Decision Records (ADRs)

This directory contains the immutable record of significant architectural and technical design decisions for the **Digital Twin**, following the ADR pattern.

## Index of Decisions

| ADR ID | Title | Status | Decided On | Scope |
|---|---|---|---|---|
| [ADR-001](ADR-001-modular-monolith-architecture.md) | Adoption of Modular Monolith Architecture | Accepted | 2026-09-19 | Core Platform / Backend |
| [ADR-002](ADR-002-state-separation-and-provenance.md) | Provenance Taxonomy and Multi-Class State Separation | Accepted | 2026-09-19 | Ingestion, Storage & UI |
| [ADR-003](ADR-003-traffic-forecast-target-and-interval.md) | 15-Minute Traffic Forecast Target and Baselines | Accepted | 2026-09-19 | Machine Learning & Analytics |
| [ADR-004](ADR-004-initial-simulation-scenario.md) | Viman Nagar Chowk Signal Intervention Scenario | Accepted | 2026-09-19 | SUMO Simulation & TraCI |

---

## Decision Protocol
Any change to core technical stack, study-area boundary, database engine, or safety boundary requires a documented ADR before code implementation (per [AGENTS.md](../../AGENTS.md)).
