-- =========================================================
-- Digital Twin Database Initialization
-- Extensions: PostGIS (spatial) + TimescaleDB (time-series)
-- =========================================================

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- 1. Study Areas
CREATE TABLE IF NOT EXISTS study_areas (
    id VARCHAR(128) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    primary_highway VARCHAR(255),
    corridor_length_km NUMERIC(6, 2),
    boundary_version VARCHAR(32) NOT NULL,
    crs VARCHAR(32) NOT NULL DEFAULT 'EPSG:4326',
    geom GEOMETRY(Polygon, 4326),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Intersections
CREATE TABLE IF NOT EXISTS intersections (
    id VARCHAR(128) PRIMARY KEY,
    study_area_id VARCHAR(128) REFERENCES study_areas(id),
    name VARCHAR(255) NOT NULL,
    control_type VARCHAR(64) NOT NULL DEFAULT 'SIGNALIZED',
    cycle_time_sec INTEGER DEFAULT 120,
    phases_count INTEGER DEFAULT 4,
    geom GEOMETRY(Point, 4326) NOT NULL,
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Road Segments
CREATE TABLE IF NOT EXISTS road_segments (
    id VARCHAR(128) PRIMARY KEY,
    study_area_id VARCHAR(128) REFERENCES study_areas(id),
    name VARCHAR(255) NOT NULL,
    direction VARCHAR(32) NOT NULL, -- EASTBOUND, WESTBOUND, NORTHBOUND, SOUTHBOUND
    from_intersection VARCHAR(128) REFERENCES intersections(id),
    to_intersection VARCHAR(128) REFERENCES intersections(id),
    length_meters NUMERIC(8, 2) NOT NULL,
    lane_count INTEGER NOT NULL DEFAULT 3,
    speed_limit_kmh NUMERIC(5, 2) NOT NULL DEFAULT 50.0,
    free_flow_speed_kmh NUMERIC(5, 2) NOT NULL DEFAULT 45.0,
    capacity_veh_per_hour INTEGER DEFAULT 3600,
    osm_highway VARCHAR(64) DEFAULT 'primary',
    geom GEOMETRY(LineString, 4326) NOT NULL,
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. Sensors (Logical Traffic Detector Stations)
CREATE TABLE IF NOT EXISTS sensors (
    id VARCHAR(128) PRIMARY KEY,
    study_area_id VARCHAR(128) REFERENCES study_areas(id),
    name VARCHAR(255) NOT NULL,
    linked_segment_id VARCHAR(128) REFERENCES road_segments(id),
    direction VARCHAR(32) NOT NULL,
    sensor_type VARCHAR(64) NOT NULL DEFAULT 'INDUCTIVE_LOOP_EMULATION',
    supported_source_modes TEXT[] NOT NULL DEFAULT ARRAY['REPLAY', 'SIMULATION', 'LIVE'],
    sampling_interval_sec INTEGER NOT NULL DEFAULT 60,
    freshness_threshold_sec INTEGER NOT NULL DEFAULT 180,
    geom GEOMETRY(Point, 4326) NOT NULL,
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. Building Zones (Energy Entities)
CREATE TABLE IF NOT EXISTS building_zones (
    id VARCHAR(128) PRIMARY KEY,
    study_area_id VARCHAR(128) REFERENCES study_areas(id),
    name VARCHAR(255) NOT NULL,
    category VARCHAR(64) NOT NULL DEFAULT 'COMMERCIAL_RETAIL',
    gross_floor_area_sqm NUMERIC(10, 2) NOT NULL,
    occupancy_type VARCHAR(128),
    sanctioned_load_kva NUMERIC(10, 2),
    contract_demand_kw NUMERIC(10, 2),
    geom GEOMETRY(Geometry, 4326),
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. Authoritative Twin Current State (ONLY updated by LIVE and REPLAY observations)
CREATE TABLE IF NOT EXISTS entity_current_state (
    entity_id VARCHAR(128) PRIMARY KEY,
    entity_type VARCHAR(64) NOT NULL,
    source_mode VARCHAR(32) NOT NULL, -- LIVE, REPLAY, SIMULATION (marked explicit)
    observed_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metrics JSONB NOT NULL DEFAULT '{}',
    quality_status VARCHAR(32) NOT NULL DEFAULT 'VALID', -- VALID, STALE, DEGRADED, INVALID
    freshness_seconds NUMERIC(8, 2) DEFAULT 0.0,
    CONSTRAINT chk_source_mode CHECK (source_mode IN ('LIVE', 'REPLAY', 'SIMULATION', 'PREDICTED', 'STALE', 'INVALID'))
);

-- 7. Traffic Observations (TimescaleDB Hypertable)
CREATE TABLE IF NOT EXISTS traffic_observations (
    observed_at TIMESTAMPTZ NOT NULL,
    sensor_id VARCHAR(128) NOT NULL,
    segment_id VARCHAR(128) NOT NULL,
    source_mode VARCHAR(32) NOT NULL,
    average_speed_kmh NUMERIC(6, 2),
    vehicle_flow_per_hour NUMERIC(8, 2),
    occupancy_percent NUMERIC(5, 2),
    queue_length_meters NUMERIC(8, 2),
    congestion_index NUMERIC(4, 3), -- 0.000 to 1.000
    quality_flag VARCHAR(32) NOT NULL DEFAULT 'VALID',
    raw_payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
SELECT create_hypertable('traffic_observations', 'observed_at', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_traffic_obs_segment_time ON traffic_observations (segment_id, observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_traffic_obs_sensor_time ON traffic_observations (sensor_id, observed_at DESC);

-- 8. Energy Observations (TimescaleDB Hypertable)
CREATE TABLE IF NOT EXISTS energy_observations (
    observed_at TIMESTAMPTZ NOT NULL,
    building_id VARCHAR(128) NOT NULL,
    source_mode VARCHAR(32) NOT NULL,
    active_power_kw NUMERIC(10, 2) NOT NULL,
    reactive_power_kvar NUMERIC(10, 2),
    power_factor NUMERIC(4, 3),
    energy_consumption_kwh NUMERIC(12, 2),
    quality_flag VARCHAR(32) NOT NULL DEFAULT 'VALID',
    raw_payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
SELECT create_hypertable('energy_observations', 'observed_at', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_energy_obs_building_time ON energy_observations (building_id, observed_at DESC);

-- 9. Environment Observations (TimescaleDB Hypertable)
CREATE TABLE IF NOT EXISTS environment_observations (
    observed_at TIMESTAMPTZ NOT NULL,
    station_id VARCHAR(128) NOT NULL,
    source_mode VARCHAR(32) NOT NULL,
    aqi_value NUMERIC(6, 2),
    pm25 NUMERIC(6, 2),
    pm10 NUMERIC(6, 2),
    temperature_c NUMERIC(5, 2),
    relative_humidity_pct NUMERIC(5, 2),
    precipitation_mm NUMERIC(6, 2),
    quality_flag VARCHAR(32) NOT NULL DEFAULT 'VALID',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
SELECT create_hypertable('environment_observations', 'observed_at', if_not_exists => TRUE);

-- 10. Model Versions Registry
CREATE TABLE IF NOT EXISTS model_versions (
    id VARCHAR(128) PRIMARY KEY,
    domain VARCHAR(64) NOT NULL, -- TRAFFIC, ENERGY
    algorithm VARCHAR(128) NOT NULL, -- XGBoost, Persistence, HistoricalAverage
    horizon_minutes INTEGER NOT NULL,
    training_data_version VARCHAR(128) NOT NULL,
    metrics JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    approved_for_demo BOOLEAN NOT NULL DEFAULT FALSE,
    model_card_path VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 11. Forecasts (Segregated from Ground Truth Observations)
CREATE TABLE IF NOT EXISTS forecasts (
    id BIGSERIAL PRIMARY KEY,
    generated_at TIMESTAMPTZ NOT NULL,
    target_timestamp TIMESTAMPTZ NOT NULL,
    entity_id VARCHAR(128) NOT NULL,
    domain VARCHAR(64) NOT NULL,
    model_version_id VARCHAR(128) REFERENCES model_versions(id),
    horizon_minutes INTEGER NOT NULL,
    source_mode VARCHAR(32) NOT NULL DEFAULT 'PREDICTED',
    predicted_value NUMERIC(10, 2) NOT NULL,
    unit VARCHAR(32) NOT NULL,
    confidence_lower NUMERIC(10, 2),
    confidence_upper NUMERIC(10, 2),
    input_quality_status VARCHAR(32) NOT NULL DEFAULT 'VALID',
    features_used JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_forecasts_target_entity ON forecasts (entity_id, target_timestamp DESC);

-- 12. Scenario Templates
CREATE TABLE IF NOT EXISTS scenario_templates (
    id VARCHAR(128) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(64) NOT NULL DEFAULT 'MOBILITY_SIGNAL',
    parameters_schema JSONB NOT NULL,
    default_parameters JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 13. Scenario Runs (Segregated from Live State)
CREATE TABLE IF NOT EXISTS scenario_runs (
    id VARCHAR(128) PRIMARY KEY,
    template_id VARCHAR(128) REFERENCES scenario_templates(id),
    name VARCHAR(255) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING', -- PENDING, RUNNING, COMPLETED, FAILED
    source_mode VARCHAR(32) NOT NULL DEFAULT 'SIMULATION',
    network_version VARCHAR(64) NOT NULL,
    demand_version VARCHAR(64) NOT NULL,
    random_seed INTEGER NOT NULL DEFAULT 42,
    parameters JSONB NOT NULL,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    artifact_paths JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 14. Scenario KPIs (Comparative Metrics)
CREATE TABLE IF NOT EXISTS scenario_kpis (
    id BIGSERIAL PRIMARY KEY,
    scenario_run_id VARCHAR(128) REFERENCES scenario_runs(id),
    is_baseline BOOLEAN NOT NULL DEFAULT FALSE,
    average_travel_time_sec NUMERIC(8, 2),
    average_delay_sec NUMERIC(8, 2),
    p95_queue_length_meters NUMERIC(8, 2),
    throughput_veh_per_hour NUMERIC(8, 2),
    delta_vs_baseline JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 15. Advisory Recommendations (Decision Support, Advisory Only)
CREATE TABLE IF NOT EXISTS recommendations (
    id VARCHAR(128) PRIMARY KEY,
    generated_at TIMESTAMPTZ NOT NULL,
    domain VARCHAR(64) NOT NULL, -- TRAFFIC, ENERGY
    urgency VARCHAR(32) NOT NULL DEFAULT 'MEDIUM', -- LOW, MEDIUM, HIGH, CRITICAL
    title VARCHAR(255) NOT NULL,
    rationale TEXT NOT NULL,
    advisory_action TEXT NOT NULL,
    evidence JSONB NOT NULL, -- Linked forecast IDs, sensor IDs, scenario comparison
    human_approval_required BOOLEAN NOT NULL DEFAULT TRUE,
    review_status VARCHAR(32) NOT NULL DEFAULT 'PENDING', -- PENDING, ACKNOWLEDGED, REJECTED
    reviewed_at TIMESTAMPTZ,
    reviewer_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 16. Ingestion Errors & Dead Letter Audit Table
CREATE TABLE IF NOT EXISTS ingestion_errors (
    id BIGSERIAL PRIMARY KEY,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    topic VARCHAR(255) NOT NULL,
    source_mode VARCHAR(32),
    raw_payload JSONB,
    error_reason VARCHAR(255) NOT NULL,
    validation_failures JSONB DEFAULT '{}'
);

-- 17. Audit Events
CREATE TABLE IF NOT EXISTS audit_events (
    id BIGSERIAL PRIMARY KEY,
    emitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type VARCHAR(128) NOT NULL,
    source_service VARCHAR(128) NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'
);

-- 18. Formal Quarantine Observations Dead-Letter Queue (P3-B)
CREATE TABLE IF NOT EXISTS quarantine_observations (
    id BIGSERIAL PRIMARY KEY,
    quarantined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    entity_id VARCHAR(255),
    entity_type VARCHAR(64),
    source_mode VARCHAR(32),
    observed_at TIMESTAMPTZ,
    rejection_reason VARCHAR(255) NOT NULL,
    raw_payload JSONB NOT NULL,
    validation_details JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_quarantine_rejection_reason ON quarantine_observations(rejection_reason);
CREATE INDEX IF NOT EXISTS idx_quarantine_quarantined_at ON quarantine_observations(quarantined_at DESC);
CREATE INDEX IF NOT EXISTS idx_quarantine_entity_id ON quarantine_observations(entity_id);
