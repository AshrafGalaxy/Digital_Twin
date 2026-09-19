# ADR-001: Adoption of Modular Monolith Architecture

## Context and Problem Statement
The digital twin project models a constrained corridor (2 intersections, 8–15 road segments) with low-to-moderate event throughput. Designing an early microservices architecture with distributed context brokers (e.g., FIWARE Orion-LD) and streaming engines (e.g., Apache Kafka/Flink) introduces operational overhead, network latency, distributed transaction complexity, and debugging friction.

## Decision Drivers
- Need for high reproducibility on a single laptop or modest VM.
- Strict requirement for academic and research evaluation integrity.
- Clear module boundaries (Ingestion, Twin Core, Simulation, ML/Rules) with shared domain models.
- Rapid developer iteration without managing multiple container lifecycles.

## Considered Options
1. Distributed Microservices with Kafka and Orion-LD.
2. Serverless event-driven architecture.
3. FastAPI Modular Monolith with internal event buses and Postgres/TimescaleDB.

## Decision Outcome
Chosen option: **Option 3 — FastAPI Modular Monolith**.
The backend is structured into distinct, cohesive Python modules:
- `ingestion/` (MQTT consumers, schema validation)
- `twin_core/` (entity state projection, REST/WebSocket APIs)
- `simulation/` (TraCI wrappers, SUMO scenario runner)
- `ml/` (inference engines, feature generators)
- `rules/` (advisory decision engine)

Communication within the application occurs via typed memory interfaces and Postgres transactions; external communication uses standard REST and WebSockets.

## Consequences
- **Positive:** Single deployment target, simplified transactional consistency, straightforward automated testing.
- **Negative:** Horizontal scaling of individual modules requires code separation if throughput increases beyond single-node capacity.
- **Mitigation:** Clear interface boundaries allow any module to be decoupled into a standalone microservice later without architectural rewrites.
