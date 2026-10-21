-- =========================================================
-- Digital Twin Database Initialization (PostgreSQL / Supabase)
-- Authoritative Schema: 29 Tables + PostGIS + TimescaleDB Resilience
-- =========================================================

-- PostGIS Spatial Extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- TimescaleDB Extension (Defensive Check for standard PostgreSQL / Supabase hosts)
DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'TimescaleDB extension not available on this host. Proceeding with standard PostgreSQL indexed tables.';
END $$;

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
    direction VARCHAR(32) NOT NULL,
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
    source_mode VARCHAR(32) NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metrics JSONB NOT NULL DEFAULT '{}',
    quality_status VARCHAR(32) NOT NULL DEFAULT 'VALID',
    freshness_seconds NUMERIC(8, 2) DEFAULT 0.0,
    CONSTRAINT chk_source_mode CHECK (source_mode IN ('LIVE', 'REPLAY', 'SIMULATION', 'PREDICTED', 'STALE', 'INVALID'))
);

-- 7. Traffic Observations
CREATE TABLE IF NOT EXISTS traffic_observations (
    id BIGSERIAL,
    observed_at TIMESTAMPTZ NOT NULL,
    sensor_id VARCHAR(128) NOT NULL,
    segment_id VARCHAR(128) NOT NULL,
    source_mode VARCHAR(32) NOT NULL,
    average_speed_kmh NUMERIC(6, 2),
    vehicle_flow_per_hour NUMERIC(8, 2),
    occupancy_percent NUMERIC(5, 2),
    queue_length_meters NUMERIC(8, 2),
    congestion_index NUMERIC(4, 3),
    quality_flag VARCHAR(32) NOT NULL DEFAULT 'VALID',
    raw_payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, observed_at)
);

DO $$
BEGIN
    PERFORM create_hypertable('traffic_observations', 'observed_at', if_not_exists => TRUE);
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Hypertable traffic_observations skipped.';
END $$;

CREATE INDEX IF NOT EXISTS idx_traffic_obs_segment_time ON traffic_observations (segment_id, observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_traffic_obs_sensor_time ON traffic_observations (sensor_id, observed_at DESC);

-- 8. Energy Observations
CREATE TABLE IF NOT EXISTS energy_observations (
    id BIGSERIAL,
    observed_at TIMESTAMPTZ NOT NULL,
    building_id VARCHAR(128) NOT NULL,
    source_mode VARCHAR(32) NOT NULL,
    active_power_kw NUMERIC(10, 2) NOT NULL,
    reactive_power_kvar NUMERIC(10, 2),
    power_factor NUMERIC(4, 3),
    energy_consumption_kwh NUMERIC(12, 2),
    quality_flag VARCHAR(32) NOT NULL DEFAULT 'VALID',
    raw_payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, observed_at)
);

DO $$
BEGIN
    PERFORM create_hypertable('energy_observations', 'observed_at', if_not_exists => TRUE);
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Hypertable energy_observations skipped.';
END $$;

CREATE INDEX IF NOT EXISTS idx_energy_obs_building_time ON energy_observations (building_id, observed_at DESC);

-- 9. Environment Observations
CREATE TABLE IF NOT EXISTS environment_observations (
    id BIGSERIAL,
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
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, observed_at)
);

DO $$
BEGIN
    PERFORM create_hypertable('environment_observations', 'observed_at', if_not_exists => TRUE);
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Hypertable environment_observations skipped.';
END $$;

-- 10. Model Versions Registry
CREATE TABLE IF NOT EXISTS model_versions (
    id VARCHAR(128) PRIMARY KEY,
    domain VARCHAR(64) NOT NULL,
    algorithm VARCHAR(128) NOT NULL,
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
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
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
    domain VARCHAR(64) NOT NULL,
    urgency VARCHAR(32) NOT NULL DEFAULT 'MEDIUM',
    title VARCHAR(255) NOT NULL,
    rationale TEXT NOT NULL,
    advisory_action TEXT NOT NULL,
    evidence JSONB NOT NULL,
    human_approval_required BOOLEAN NOT NULL DEFAULT TRUE,
    review_status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
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

-- 19. Continuous 15m Aggregates (P4-B)
CREATE TABLE IF NOT EXISTS traffic_15m_aggregates (
    bucket_15m TIMESTAMPTZ NOT NULL,
    segment_id VARCHAR(128) NOT NULL,
    sample_count INTEGER NOT NULL DEFAULT 1,
    avg_speed_kmh NUMERIC(6, 2) NOT NULL,
    p85_speed_kmh NUMERIC(6, 2),
    total_flow_veh NUMERIC(10, 2) NOT NULL,
    avg_occupancy_percent NUMERIC(5, 2) NOT NULL,
    avg_queue_length_meters NUMERIC(8, 2) NOT NULL,
    max_queue_length_meters NUMERIC(8, 2) NOT NULL,
    avg_congestion_index NUMERIC(4, 3) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (bucket_15m, segment_id)
);
CREATE INDEX IF NOT EXISTS idx_traffic_15m_seg_time ON traffic_15m_aggregates (segment_id, bucket_15m DESC);

-- 20. Spatial Road Segment Map (Phase 8A)
CREATE TABLE IF NOT EXISTS spatial_road_segment_map (
    segment_id VARCHAR(128) PRIMARY KEY,
    sumo_edge_id VARCHAR(128) NOT NULL,
    name VARCHAR(255) NOT NULL,
    direction VARCHAR(32) NOT NULL,
    from_junction VARCHAR(128),
    to_junction VARCHAR(128),
    length_meters NUMERIC(8, 2) NOT NULL,
    lane_count INTEGER NOT NULL,
    speed_limit_kmh NUMERIC(5, 2) NOT NULL,
    osm_highway VARCHAR(64) DEFAULT 'primary',
    coordinates JSONB NOT NULL,
    lanes_json JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_spatial_road_sumo_edge ON spatial_road_segment_map(sumo_edge_id);

-- 21. Spatial Intersection Map (Phase 8A)
CREATE TABLE IF NOT EXISTS spatial_intersection_map (
    intersection_id VARCHAR(128) PRIMARY KEY,
    sumo_junction_id VARCHAR(128) NOT NULL,
    name VARCHAR(255) NOT NULL,
    control_type VARCHAR(64) NOT NULL DEFAULT 'SIGNALIZED',
    coordinates JSONB NOT NULL,
    cycle_time_sec INTEGER DEFAULT 120,
    phases_count INTEGER DEFAULT 4,
    approach_edges JSONB NOT NULL DEFAULT '[]',
    departure_edges JSONB NOT NULL DEFAULT '[]',
    tls_program_id VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_spatial_inter_sumo_junc ON spatial_intersection_map(sumo_junction_id);

-- 22. Spatial Signal Controller Map (Phase 8A)
CREATE TABLE IF NOT EXISTS spatial_signal_controller_map (
    controller_id VARCHAR(128) PRIMARY KEY,
    intersection_id VARCHAR(128) NOT NULL,
    sumo_tls_id VARCHAR(128) NOT NULL,
    cycle_time_sec INTEGER DEFAULT 120,
    signal_groups_json JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_spatial_signal_tls ON spatial_signal_controller_map(sumo_tls_id);

-- 23. Spatial Building Zone Map (Phase 8A)
CREATE TABLE IF NOT EXISTS spatial_building_zone_map (
    building_id VARCHAR(128) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(64) NOT NULL DEFAULT 'COMMERCIAL_RETAIL',
    gross_floor_area_sqm NUMERIC(10, 2) NOT NULL,
    contract_demand_kw NUMERIC(10, 2) NOT NULL,
    height_meters NUMERIC(6, 2) NOT NULL DEFAULT 28.0,
    building_levels INTEGER NOT NULL DEFAULT 6,
    model_fidelity_level VARCHAR(32) NOT NULL DEFAULT 'B2',
    roof_type VARCHAR(64) DEFAULT 'FLAT_COMMERCIAL',
    color_tint VARCHAR(32) DEFAULT '#2A4B54',
    centroid JSONB NOT NULL,
    footprint_polygon JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 24. Spatial Sensor Map (Phase 8A)
CREATE TABLE IF NOT EXISTS spatial_sensor_map (
    sensor_id VARCHAR(128) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    segment_id VARCHAR(128),
    sumo_edge_id VARCHAR(128),
    direction VARCHAR(32) NOT NULL DEFAULT 'EASTBOUND',
    coordinates JSONB NOT NULL,
    elevation_meters NUMERIC(6, 2) DEFAULT 1.5,
    sensor_type VARCHAR(64) NOT NULL,
    sampling_interval_sec INTEGER DEFAULT 60,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 25. Spatial Scenario Geometry Map (Phase 8A)
CREATE TABLE IF NOT EXISTS spatial_scenario_geometry_map (
    scenario_template_id VARCHAR(128) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    corridor_edge_ids JSONB NOT NULL DEFAULT '[]',
    junction_ids JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 26. Segment Level of Service History (TASK-01)
CREATE TABLE IF NOT EXISTS segment_los_history (
    id BIGSERIAL PRIMARY KEY,
    segment_id VARCHAR(128) NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    volume_capacity_ratio NUMERIC(6, 4) NOT NULL,
    density_veh_km NUMERIC(8, 2) NOT NULL,
    congestion_index NUMERIC(4, 3) NOT NULL,
    los_grade VARCHAR(8) NOT NULL,
    operational_condition VARCHAR(128) NOT NULL,
    policy_standard VARCHAR(64) NOT NULL DEFAULT 'INDO_HCM',
    source_mode VARCHAR(32) NOT NULL DEFAULT 'REPLAY',
    quality_score NUMERIC(4, 3) NOT NULL DEFAULT 0.98,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_segment_los_hist ON segment_los_history (segment_id, observed_at DESC);

-- 27. Signal Timing Recommendations (TASK-02)
CREATE TABLE IF NOT EXISTS timing_recommendations (
    id VARCHAR(128) PRIMARY KEY,
    intersection_id VARCHAR(128) NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL,
    target_cycle_sec INTEGER NOT NULL,
    baseline_cycle_sec INTEGER NOT NULL,
    total_lost_time_sec INTEGER NOT NULL,
    critical_flow_ratio_y NUMERIC(6, 4) NOT NULL,
    phases_json JSONB NOT NULL,
    baseline_delay_sec_veh NUMERIC(8, 2) NOT NULL,
    optimal_delay_sec_veh NUMERIC(8, 2) NOT NULL,
    estimated_delay_reduction_sec NUMERIC(8, 2) NOT NULL,
    estimated_delay_reduction_pct NUMERIC(6, 2) NOT NULL,
    max_saturation NUMERIC(6, 4) NOT NULL,
    pedestrian_invariant_verified BOOLEAN NOT NULL DEFAULT TRUE,
    source_mode VARCHAR(32) NOT NULL DEFAULT 'PREDICTED',
    quality_status VARCHAR(32) NOT NULL DEFAULT 'VALID',
    applied_status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_timing_rec_int ON timing_recommendations (intersection_id, generated_at DESC);

-- 28. Signal Phase History (TASK-08 / SPaT Controller Ingestion)
CREATE TABLE IF NOT EXISTS signal_phase_history (
    id BIGSERIAL PRIMARY KEY,
    intersection_id VARCHAR(128) NOT NULL,
    phase_id INTEGER NOT NULL,
    phase_name VARCHAR(128) NOT NULL,
    color VARCHAR(32) NOT NULL,
    duration_sec NUMERIC(8, 2) NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    source_mode VARCHAR(32) NOT NULL DEFAULT 'REPLAY',
    quality_status VARCHAR(32) NOT NULL DEFAULT 'VALID',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_signal_phase_hist ON signal_phase_history (intersection_id, start_time DESC);

-- 29. Advisory Audit Log (TASK-10 / Human-in-the-Loop Operator Authorization)
CREATE TABLE IF NOT EXISTS advisory_audit_log (
    id BIGSERIAL PRIMARY KEY,
    audit_id VARCHAR(128) UNIQUE NOT NULL,
    recommendation_id VARCHAR(128) NOT NULL,
    target_entity_id VARCHAR(255) NOT NULL,
    action_type VARCHAR(64) NOT NULL,
    previous_status VARCHAR(32) NOT NULL,
    new_status VARCHAR(32) NOT NULL,
    authorized_by VARCHAR(128) NOT NULL,
    badge_id VARCHAR(64),
    shift_id VARCHAR(64),
    justification_notes TEXT,
    dispatch_order_id VARCHAR(64),
    dispatch_payload_json JSONB NOT NULL,
    tamper_evident_hash VARCHAR(128) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_advisory_audit_rec ON advisory_audit_log (recommendation_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_advisory_audit_time ON advisory_audit_log (created_at DESC);

-- 30. Canonical Electrical Network Nodes (Energy TASK-01)
CREATE TABLE IF NOT EXISTS energy_network_nodes (
    node_id VARCHAR(128) PRIMARY KEY,
    study_area_id VARCHAR(128) REFERENCES study_areas(id),
    name VARCHAR(255) NOT NULL,
    node_type VARCHAR(64) NOT NULL,
    parent_node_id VARCHAR(128) REFERENCES energy_network_nodes(node_id),
    nominal_voltage_kv NUMERIC(6, 2) NOT NULL,
    rated_capacity_kva NUMERIC(10, 2) NOT NULL,
    rated_current_amps NUMERIC(8, 2) NOT NULL,
    phase_count INTEGER NOT NULL DEFAULT 3,
    coordinates JSONB,
    properties JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_energy_nodes_parent ON energy_network_nodes (parent_node_id);
CREATE INDEX IF NOT EXISTS idx_energy_nodes_type ON energy_network_nodes (node_type);

-- 31. Multi-Asset Electrical Telemetry (Energy TASK-01)
CREATE TABLE IF NOT EXISTS energy_asset_telemetry (
    id BIGSERIAL PRIMARY KEY,
    asset_id VARCHAR(128) NOT NULL REFERENCES energy_network_nodes(node_id),
    observed_at TIMESTAMPTZ NOT NULL,
    source_mode VARCHAR(32) NOT NULL DEFAULT 'SIMULATION',
    active_power_kw NUMERIC(10, 2) NOT NULL,
    reactive_power_kvar NUMERIC(10, 2) NOT NULL,
    apparent_power_kva NUMERIC(10, 2) NOT NULL,
    power_factor NUMERIC(4, 3) NOT NULL,
    voltage_v NUMERIC(8, 2) NOT NULL,
    current_a NUMERIC(8, 2) NOT NULL,
    frequency_hz NUMERIC(5, 2) NOT NULL DEFAULT 50.00,
    voltage_unbalance_pct NUMERIC(5, 2) NOT NULL DEFAULT 0.50,
    current_unbalance_pct NUMERIC(5, 2) NOT NULL DEFAULT 1.20,
    device_metrics_json JSONB NOT NULL DEFAULT '{}',
    quality_status VARCHAR(32) NOT NULL DEFAULT 'VALID',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_energy_telemetry_asset_time ON energy_asset_telemetry (asset_id, observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_energy_telemetry_obs ON energy_asset_telemetry (observed_at DESC);

-- 32. Access Inquiries
CREATE TABLE IF NOT EXISTS access_inquiries (
    id VARCHAR(128) PRIMARY KEY,
    organization VARCHAR(255) NOT NULL,
    work_email VARCHAR(255) NOT NULL,
    contact_name VARCHAR(150) NOT NULL,
    jurisdiction VARCHAR(200) NOT NULL,
    domain VARCHAR(150) NOT NULL DEFAULT 'Integrated Multi-Domain Digital Twin',
    infrastructure_scale VARCHAR(100) DEFAULT '1-10 Intersections / Corridors',
    message TEXT DEFAULT '',
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    assigned_role VARCHAR(64) DEFAULT 'Municipal Analyst',
    reviewed_by VARCHAR(128),
    reviewed_at TIMESTAMPTZ,
    rejection_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_inquiries_status ON access_inquiries (status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_inquiries_email ON access_inquiries (work_email);

-- 33. Magic Access Tokens
CREATE TABLE IF NOT EXISTS magic_access_tokens (
    token VARCHAR(128) PRIMARY KEY,
    inquiry_id VARCHAR(128) REFERENCES access_inquiries(id),
    email VARCHAR(255) NOT NULL,
    contact_name VARCHAR(150) NOT NULL,
    assigned_role VARCHAR(64) NOT NULL DEFAULT 'Municipal Analyst',
    department VARCHAR(150) NOT NULL DEFAULT 'Agency Operations',
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    expires_at TIMESTAMPTZ NOT NULL,
    redeemed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_magic_tokens_status ON magic_access_tokens (status, expires_at);
CREATE INDEX IF NOT EXISTS idx_magic_tokens_email ON magic_access_tokens (email);


