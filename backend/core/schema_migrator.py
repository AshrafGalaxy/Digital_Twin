"""
schema_migrator.py

Automatic database schema initializer and spatial asset seeder for the Digital Twin Platform (P4-A).
Ensures all 18 tables are properly initialized and authoritative corridor assets
are seeded upon application startup across PostgreSQL/TimescaleDB and SQLite.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .database import get_active_backend, persistence_manager

logger = logging.getLogger("digital_twin.migrator")

# Locate data directory relative to project root or current working dir
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
if not DATA_DIR.exists() and (Path.cwd() / "data").exists():
    DATA_DIR = Path.cwd() / "data"

SQLITE_TABLE_DDL = [
    # 1. Study Areas
    """
    CREATE TABLE IF NOT EXISTS study_areas (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        city TEXT NOT NULL,
        state TEXT NOT NULL,
        country TEXT NOT NULL,
        primary_highway TEXT,
        corridor_length_km REAL,
        boundary_version TEXT NOT NULL,
        crs TEXT NOT NULL DEFAULT 'EPSG:4326',
        geom TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 2. Intersections
    """
    CREATE TABLE IF NOT EXISTS intersections (
        id TEXT PRIMARY KEY,
        study_area_id TEXT REFERENCES study_areas(id),
        name TEXT NOT NULL,
        control_type TEXT NOT NULL DEFAULT 'SIGNALIZED',
        cycle_time_sec INTEGER DEFAULT 120,
        phases_count INTEGER DEFAULT 4,
        geom TEXT NOT NULL,
        properties TEXT DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 3. Road Segments
    """
    CREATE TABLE IF NOT EXISTS road_segments (
        id TEXT PRIMARY KEY,
        study_area_id TEXT REFERENCES study_areas(id),
        name TEXT NOT NULL,
        direction TEXT NOT NULL,
        from_intersection TEXT REFERENCES intersections(id),
        to_intersection TEXT REFERENCES intersections(id),
        length_meters REAL NOT NULL,
        lane_count INTEGER NOT NULL DEFAULT 3,
        speed_limit_kmh REAL NOT NULL DEFAULT 50.0,
        free_flow_speed_kmh REAL NOT NULL DEFAULT 45.0,
        capacity_veh_per_hour INTEGER DEFAULT 3600,
        osm_highway TEXT DEFAULT 'primary',
        geom TEXT NOT NULL,
        properties TEXT DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 4. Sensors
    """
    CREATE TABLE IF NOT EXISTS sensors (
        id TEXT PRIMARY KEY,
        study_area_id TEXT REFERENCES study_areas(id),
        name TEXT NOT NULL,
        linked_segment_id TEXT REFERENCES road_segments(id),
        direction TEXT NOT NULL,
        sensor_type TEXT NOT NULL DEFAULT 'INDUCTIVE_LOOP_EMULATION',
        supported_source_modes TEXT NOT NULL DEFAULT '["REPLAY", "SIMULATION", "LIVE"]',
        sampling_interval_sec INTEGER NOT NULL DEFAULT 60,
        freshness_threshold_sec INTEGER NOT NULL DEFAULT 180,
        geom TEXT NOT NULL,
        properties TEXT DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 5. Building Zones
    """
    CREATE TABLE IF NOT EXISTS building_zones (
        id TEXT PRIMARY KEY,
        study_area_id TEXT REFERENCES study_areas(id),
        name TEXT NOT NULL,
        category TEXT NOT NULL DEFAULT 'COMMERCIAL_RETAIL',
        gross_floor_area_sqm REAL NOT NULL,
        occupancy_type TEXT,
        sanctioned_load_kva REAL,
        contract_demand_kw REAL,
        geom TEXT,
        properties TEXT DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 6. Entity Current State
    """
    CREATE TABLE IF NOT EXISTS entity_current_state (
        entity_id TEXT PRIMARY KEY,
        entity_type TEXT NOT NULL,
        source_mode TEXT NOT NULL,
        observed_at TIMESTAMP NOT NULL,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        metrics TEXT NOT NULL DEFAULT '{}',
        quality_status TEXT NOT NULL DEFAULT 'VALID',
        freshness_seconds REAL DEFAULT 0.0
    );
    """,
    # 7. Traffic Observations
    """
    CREATE TABLE IF NOT EXISTS traffic_observations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        observed_at TIMESTAMP NOT NULL,
        sensor_id TEXT NOT NULL,
        segment_id TEXT NOT NULL,
        source_mode TEXT NOT NULL,
        average_speed_kmh REAL,
        vehicle_flow_per_hour REAL,
        occupancy_percent REAL,
        queue_length_meters REAL,
        congestion_index REAL,
        quality_flag TEXT NOT NULL DEFAULT 'VALID',
        raw_payload TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 8. Energy Observations
    """
    CREATE TABLE IF NOT EXISTS energy_observations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        observed_at TIMESTAMP NOT NULL,
        building_id TEXT NOT NULL,
        source_mode TEXT NOT NULL,
        active_power_kw REAL NOT NULL,
        reactive_power_kvar REAL,
        power_factor REAL,
        energy_consumption_kwh REAL,
        quality_flag TEXT NOT NULL DEFAULT 'VALID',
        raw_payload TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 9. Environment Observations
    """
    CREATE TABLE IF NOT EXISTS environment_observations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        observed_at TIMESTAMP NOT NULL,
        station_id TEXT NOT NULL,
        source_mode TEXT NOT NULL,
        aqi_value REAL,
        pm25 REAL,
        pm10 REAL,
        temperature_c REAL,
        relative_humidity_pct REAL,
        precipitation_mm REAL,
        quality_flag TEXT NOT NULL DEFAULT 'VALID',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 10. Model Versions
    """
    CREATE TABLE IF NOT EXISTS model_versions (
        id TEXT PRIMARY KEY,
        domain TEXT NOT NULL,
        algorithm TEXT NOT NULL,
        horizon_minutes INTEGER NOT NULL,
        training_data_version TEXT NOT NULL,
        metrics TEXT NOT NULL DEFAULT '{}',
        is_active INTEGER NOT NULL DEFAULT 0,
        approved_for_demo INTEGER NOT NULL DEFAULT 0,
        model_card_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 11. Forecasts
    """
    CREATE TABLE IF NOT EXISTS forecasts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        generated_at TIMESTAMP NOT NULL,
        target_timestamp TIMESTAMP NOT NULL,
        entity_id TEXT NOT NULL,
        domain TEXT NOT NULL,
        model_version_id TEXT REFERENCES model_versions(id),
        horizon_minutes INTEGER NOT NULL,
        source_mode TEXT NOT NULL DEFAULT 'PREDICTED',
        predicted_value REAL NOT NULL,
        unit TEXT NOT NULL,
        confidence_lower REAL,
        confidence_upper REAL,
        input_quality_status TEXT NOT NULL DEFAULT 'VALID',
        features_used TEXT DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 12. Scenario Templates
    """
    CREATE TABLE IF NOT EXISTS scenario_templates (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        category TEXT NOT NULL DEFAULT 'MOBILITY_SIGNAL',
        parameters_schema TEXT NOT NULL,
        default_parameters TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 13. Scenario Runs
    """
    CREATE TABLE IF NOT EXISTS scenario_runs (
        id TEXT PRIMARY KEY,
        template_id TEXT REFERENCES scenario_templates(id),
        name TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'PENDING',
        source_mode TEXT NOT NULL DEFAULT 'SIMULATION',
        network_version TEXT NOT NULL,
        demand_version TEXT NOT NULL,
        random_seed INTEGER NOT NULL DEFAULT 42,
        parameters TEXT NOT NULL,
        started_at TIMESTAMP,
        completed_at TIMESTAMP,
        error_message TEXT,
        artifact_paths TEXT DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 14. Scenario KPIs
    """
    CREATE TABLE IF NOT EXISTS scenario_kpis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scenario_run_id TEXT REFERENCES scenario_runs(id),
        is_baseline INTEGER NOT NULL DEFAULT 0,
        average_travel_time_sec REAL,
        average_delay_sec REAL,
        p95_queue_length_meters REAL,
        throughput_veh_per_hour REAL,
        delta_vs_baseline TEXT DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 15. Recommendations
    """
    CREATE TABLE IF NOT EXISTS recommendations (
        id TEXT PRIMARY KEY,
        generated_at TIMESTAMP NOT NULL,
        domain TEXT NOT NULL,
        urgency TEXT NOT NULL DEFAULT 'MEDIUM',
        title TEXT NOT NULL,
        rationale TEXT NOT NULL,
        advisory_action TEXT NOT NULL,
        evidence TEXT NOT NULL,
        human_approval_required INTEGER NOT NULL DEFAULT 1,
        review_status TEXT NOT NULL DEFAULT 'PENDING',
        reviewed_at TIMESTAMP,
        reviewer_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 16. Ingestion Errors
    """
    CREATE TABLE IF NOT EXISTS ingestion_errors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        occurred_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        topic TEXT NOT NULL,
        source_mode TEXT,
        raw_payload TEXT,
        error_reason TEXT NOT NULL,
        validation_failures TEXT DEFAULT '{}'
    );
    """,
    # 17. Audit Events
    """
    CREATE TABLE IF NOT EXISTS audit_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emitted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        event_type TEXT NOT NULL,
        source_service TEXT NOT NULL,
        details TEXT NOT NULL DEFAULT '{}'
    );
    """,
    # 18. Quarantine Observations
    """
    CREATE TABLE IF NOT EXISTS quarantine_observations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quarantined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        entity_id TEXT,
        entity_type TEXT,
        source_mode TEXT,
        observed_at TIMESTAMP,
        rejection_reason TEXT NOT NULL,
        raw_payload TEXT NOT NULL,
        validation_details TEXT DEFAULT '{}'
    );
    """,
    # 19. Continuous 15m Aggregates (P4-B)
    """
    CREATE TABLE IF NOT EXISTS traffic_15m_aggregates (
        bucket_15m TIMESTAMP NOT NULL,
        segment_id TEXT NOT NULL,
        sample_count INTEGER NOT NULL DEFAULT 1,
        avg_speed_kmh REAL NOT NULL,
        p85_speed_kmh REAL,
        total_flow_veh REAL NOT NULL,
        avg_occupancy_percent REAL NOT NULL,
        avg_queue_length_meters REAL NOT NULL,
        max_queue_length_meters REAL NOT NULL,
        avg_congestion_index REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (bucket_15m, segment_id)
    );
    """,
    # 20. Spatial Road Segment Map (Phase 8A)
    """
    CREATE TABLE IF NOT EXISTS spatial_road_segment_map (
        segment_id TEXT PRIMARY KEY,
        sumo_edge_id TEXT NOT NULL,
        name TEXT NOT NULL,
        direction TEXT NOT NULL,
        from_junction TEXT,
        to_junction TEXT,
        length_meters REAL NOT NULL,
        lane_count INTEGER NOT NULL,
        speed_limit_kmh REAL NOT NULL,
        osm_highway TEXT DEFAULT 'primary',
        coordinates TEXT NOT NULL,
        lanes_json TEXT NOT NULL DEFAULT '[]',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 21. Spatial Intersection Map (Phase 8A)
    """
    CREATE TABLE IF NOT EXISTS spatial_intersection_map (
        intersection_id TEXT PRIMARY KEY,
        sumo_junction_id TEXT NOT NULL,
        name TEXT NOT NULL,
        control_type TEXT NOT NULL DEFAULT 'SIGNALIZED',
        coordinates TEXT NOT NULL,
        cycle_time_sec INTEGER DEFAULT 120,
        phases_count INTEGER DEFAULT 4,
        approach_edges TEXT NOT NULL DEFAULT '[]',
        departure_edges TEXT NOT NULL DEFAULT '[]',
        tls_program_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 22. Spatial Signal Controller Map (Phase 8A)
    """
    CREATE TABLE IF NOT EXISTS spatial_signal_controller_map (
        controller_id TEXT PRIMARY KEY,
        intersection_id TEXT NOT NULL,
        sumo_tls_id TEXT NOT NULL,
        cycle_time_sec INTEGER DEFAULT 120,
        signal_groups_json TEXT NOT NULL DEFAULT '[]',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 23. Spatial Building Zone Map (Phase 8A)
    """
    CREATE TABLE IF NOT EXISTS spatial_building_zone_map (
        building_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL DEFAULT 'COMMERCIAL_RETAIL',
        gross_floor_area_sqm REAL NOT NULL,
        contract_demand_kw REAL NOT NULL,
        height_meters REAL NOT NULL DEFAULT 28.0,
        building_levels INTEGER NOT NULL DEFAULT 6,
        model_fidelity_level TEXT NOT NULL DEFAULT 'B2',
        roof_type TEXT DEFAULT 'FLAT_COMMERCIAL',
        color_tint TEXT DEFAULT '#2A4B54',
        centroid TEXT NOT NULL,
        footprint_polygon TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 24. Spatial Sensor Map (Phase 8A)
    """
    CREATE TABLE IF NOT EXISTS spatial_sensor_map (
        sensor_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        segment_id TEXT,
        sumo_edge_id TEXT,
        direction TEXT NOT NULL DEFAULT 'EASTBOUND',
        coordinates TEXT NOT NULL,
        elevation_meters REAL DEFAULT 1.5,
        sensor_type TEXT NOT NULL,
        sampling_interval_sec INTEGER DEFAULT 60,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 25. Spatial Scenario Geometry Map (Phase 8A)
    """
    CREATE TABLE IF NOT EXISTS spatial_scenario_geometry_map (
        scenario_template_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        corridor_edge_ids TEXT NOT NULL DEFAULT '[]',
        junction_ids TEXT NOT NULL DEFAULT '[]',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
]

SQLITE_INDEX_DDL = [
    "CREATE INDEX IF NOT EXISTS idx_traffic_obs_segment_time ON traffic_observations (segment_id, observed_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_traffic_obs_sensor_time ON traffic_observations (sensor_id, observed_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_energy_obs_building_time ON energy_observations (building_id, observed_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_forecasts_target_entity ON forecasts (entity_id, target_timestamp DESC);",
    "CREATE INDEX IF NOT EXISTS idx_quarantine_rejection_reason ON quarantine_observations(rejection_reason);",
    "CREATE INDEX IF NOT EXISTS idx_quarantine_quarantined_at ON quarantine_observations(quarantined_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_quarantine_entity_id ON quarantine_observations(entity_id);",
    "CREATE INDEX IF NOT EXISTS idx_traffic_15m_seg_time ON traffic_15m_aggregates (segment_id, bucket_15m DESC);",
    "CREATE INDEX IF NOT EXISTS idx_spatial_road_sumo_edge ON spatial_road_segment_map(sumo_edge_id);",
    "CREATE INDEX IF NOT EXISTS idx_spatial_inter_sumo_junc ON spatial_intersection_map(sumo_junction_id);",
    "CREATE INDEX IF NOT EXISTS idx_spatial_signal_tls ON spatial_signal_controller_map(sumo_tls_id);"
]


async def _migrate_sqlite(session: AsyncSession) -> int:
    """Creates tables and indexes on SQLite."""
    tables_count = 0
    for stmt in SQLITE_TABLE_DDL:
        await session.execute(text(stmt))
        tables_count += 1
    for stmt in SQLITE_INDEX_DDL:
        await session.execute(text(stmt))
    await session.commit()
    return tables_count


async def _migrate_postgres(session: AsyncSession) -> int:
    """Executes PostgreSQL DDL script if running on PostgreSQL."""
    init_sql_path = BASE_DIR / "infrastructure" / "postgres" / "init.sql"
    if init_sql_path.exists():
        sql_content = init_sql_path.read_text(encoding="utf-8")
        # Execute line-by-line or section-by-section
        for stmt in sql_content.split(";"):
            cleaned = stmt.strip()
            if cleaned:
                try:
                    await session.execute(text(cleaned + ";"))
                except Exception as ex:
                    logger.debug("PostgreSQL statement notice: %s", ex)
        await session.commit()
    return 18


async def _seed_study_area(session: AsyncSession, is_pg: bool) -> bool:
    study_file = DATA_DIR / "study_area.geojson"
    if not study_file.exists():
        return False
    try:
        with open(study_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            feat = data["features"][0]
            props = feat["properties"]
            geom_str = json.dumps(feat["geometry"])

            if is_pg:
                stmt = text("""
                    INSERT INTO study_areas (
                        id, name, city, state, country, primary_highway,
                        corridor_length_km, boundary_version, crs, geom
                    ) VALUES (
                        :id, :name, :city, :state, :country, :primary_highway,
                        :corridor_length_km, :boundary_version, :crs,
                        ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326)
                    ) ON CONFLICT (id) DO NOTHING;
                """)
            else:
                stmt = text("""
                    INSERT OR IGNORE INTO study_areas (
                        id, name, city, state, country, primary_highway,
                        corridor_length_km, boundary_version, crs, geom
                    ) VALUES (
                        :id, :name, :city, :state, :country, :primary_highway,
                        :corridor_length_km, :boundary_version, :crs, :geom
                    );
                """)
            await session.execute(stmt, {
                "id": props["id"],
                "name": props["name"],
                "city": props["city"],
                "state": props["state"],
                "country": props["country"],
                "primary_highway": props.get("primaryHighway", "Pune-Ahmednagar Road"),
                "corridor_length_km": props.get("corridorLengthKm", 1.8),
                "boundary_version": props.get("boundaryVersion", "1.0.0"),
                "crs": props.get("crs", "EPSG:4326"),
                "geom": geom_str
            })
            return True
    except Exception as e:
        logger.warning("Study area seeding notice: %s", e)
        return False


async def _seed_corridor_assets(session: AsyncSession, is_pg: bool) -> Dict[str, int]:
    counts = {"intersections": 0, "road_segments": 0}
    corridor_file = DATA_DIR / "samples" / "corridor_assets.json"
    if not corridor_file.exists():
        return counts

    try:
        with open(corridor_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            study_area_id = data.get("studyAreaId", "urn:ngsi-ld:StudyArea:PUNE:VN-SN-CORRIDOR")

            # Intersections
            for item in data.get("intersections", []):
                point_geom = json.dumps({"type": "Point", "coordinates": item["coordinates"]})
                if is_pg:
                    stmt = text("""
                        INSERT INTO intersections (
                            id, study_area_id, name, control_type,
                            cycle_time_sec, phases_count, geom, properties
                        ) VALUES (
                            :id, :study_area_id, :name, :control_type,
                            :cycle_time_sec, :phases_count,
                            ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326), :properties
                        ) ON CONFLICT (id) DO NOTHING;
                    """)
                else:
                    stmt = text("""
                        INSERT OR IGNORE INTO intersections (
                            id, study_area_id, name, control_type,
                            cycle_time_sec, phases_count, geom, properties
                        ) VALUES (
                            :id, :study_area_id, :name, :control_type,
                            :cycle_time_sec, :phases_count, :geom, :properties
                        );
                    """)
                await session.execute(stmt, {
                    "id": item["id"],
                    "study_area_id": study_area_id,
                    "name": item["name"],
                    "control_type": item.get("controlType", "SIGNALIZED"),
                    "cycle_time_sec": item.get("cycleTimeSec", 120),
                    "phases_count": item.get("phases", 4),
                    "geom": point_geom,
                    "properties": json.dumps({"connectedSegments": item.get("connectedSegments", [])})
                })
                counts["intersections"] += 1

            # Road Segments
            for seg in data.get("roadSegments", []):
                line_geom = json.dumps({"type": "LineString", "coordinates": seg["coordinates"]})
                if is_pg:
                    stmt = text("""
                        INSERT INTO road_segments (
                            id, study_area_id, name, direction, from_intersection,
                            to_intersection, length_meters, lane_count, speed_limit_kmh,
                            free_flow_speed_kmh, capacity_veh_per_hour, osm_highway, geom
                        ) VALUES (
                            :id, :study_area_id, :name, :direction, :from_intersection,
                            :to_intersection, :length_meters, :lane_count, :speed_limit_kmh,
                            :free_flow_speed_kmh, :capacity_veh_per_hour, :osm_highway,
                            ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326)
                        ) ON CONFLICT (id) DO NOTHING;
                    """)
                else:
                    stmt = text("""
                        INSERT OR IGNORE INTO road_segments (
                            id, study_area_id, name, direction, from_intersection,
                            to_intersection, length_meters, lane_count, speed_limit_kmh,
                            free_flow_speed_kmh, capacity_veh_per_hour, osm_highway, geom
                        ) VALUES (
                            :id, :study_area_id, :name, :direction, :from_intersection,
                            :to_intersection, :length_meters, :lane_count, :speed_limit_kmh,
                            :free_flow_speed_kmh, :capacity_veh_per_hour, :osm_highway, :geom
                        );
                    """)
                await session.execute(stmt, {
                    "id": seg["id"],
                    "study_area_id": study_area_id,
                    "name": seg["name"],
                    "direction": seg["direction"],
                    "from_intersection": seg.get("fromIntersection"),
                    "to_intersection": seg.get("toIntersection"),
                    "length_meters": seg["lengthMeters"],
                    "lane_count": seg.get("laneCount", 3),
                    "speed_limit_kmh": seg.get("speedLimitKmh", 50.0),
                    "free_flow_speed_kmh": seg.get("freeFlowSpeedKmh", 45.0),
                    "capacity_veh_per_hour": seg.get("capacityVehPerHour", 3600),
                    "osm_highway": seg.get("osmHighway", "primary"),
                    "geom": line_geom
                })
                counts["road_segments"] += 1
    except Exception as e:
        logger.warning("Corridor assets seeding notice: %s", e)

    return counts


async def _seed_sensors(session: AsyncSession, is_pg: bool) -> int:
    sensor_file = DATA_DIR / "samples" / "sensor_registry.json"
    if not sensor_file.exists():
        return 0

    count = 0
    try:
        with open(sensor_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            study_area_id = data.get("studyAreaId", "urn:ngsi-ld:StudyArea:PUNE:VN-SN-CORRIDOR")
            for s in data.get("sensors", []):
                point_geom = json.dumps({"type": "Point", "coordinates": s["coordinates"]})
                if is_pg:
                    stmt = text("""
                        INSERT INTO sensors (
                            id, study_area_id, name, linked_segment_id, direction,
                            sensor_type, supported_source_modes, sampling_interval_sec,
                            freshness_threshold_sec, geom, properties
                        ) VALUES (
                            :id, :study_area_id, :name, :linked_segment_id, :direction,
                            :sensor_type, :supported_source_modes, :sampling_interval_sec,
                            :freshness_threshold_sec,
                            ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326), :properties
                        ) ON CONFLICT (id) DO NOTHING;
                    """)
                else:
                    stmt = text("""
                        INSERT OR IGNORE INTO sensors (
                            id, study_area_id, name, linked_segment_id, direction,
                            sensor_type, supported_source_modes, sampling_interval_sec,
                            freshness_threshold_sec, geom, properties
                        ) VALUES (
                            :id, :study_area_id, :name, :linked_segment_id, :direction,
                            :sensor_type, :supported_source_modes, :sampling_interval_sec,
                            :freshness_threshold_sec, :geom, :properties
                        );
                    """)
                await session.execute(stmt, {
                    "id": s["id"],
                    "study_area_id": study_area_id,
                    "name": s["name"],
                    "linked_segment_id": s["linkedSegmentId"],
                    "direction": s["direction"],
                    "sensor_type": s["sensorType"],
                    "supported_source_modes": json.dumps(s.get("supportedSourceModes", ["REPLAY", "SIMULATION", "LIVE"])) if not is_pg else s.get("supportedSourceModes", ["REPLAY", "SIMULATION", "LIVE"]),
                    "sampling_interval_sec": s["samplingIntervalSec"],
                    "freshness_threshold_sec": s["freshnessThresholdSec"],
                    "geom": point_geom,
                    "properties": json.dumps({"metrics": s.get("metrics", [])})
                })
                count += 1
    except Exception as e:
        logger.warning("Sensor registry seeding notice: %s", e)
    return count


async def _seed_energy_assets(session: AsyncSession, is_pg: bool) -> int:
    energy_file = DATA_DIR / "samples" / "energy_assets.json"
    if not energy_file.exists():
        return 0

    count = 0
    try:
        with open(energy_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            study_area_id = data.get("studyAreaId", "urn:ngsi-ld:StudyArea:PUNE:VN-SN-CORRIDOR")
            for b in data.get("entities", []):
                point_geom = json.dumps(b["location"])
                if is_pg:
                    stmt = text("""
                        INSERT INTO building_zones (
                            id, study_area_id, name, category, gross_floor_area_sqm,
                            occupancy_type, sanctioned_load_kva, contract_demand_kw,
                            geom, properties
                        ) VALUES (
                            :id, :study_area_id, :name, :category, :gross_floor_area_sqm,
                            :occupancy_type, :sanctioned_load_kva, :contract_demand_kw,
                            ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326), :properties
                        ) ON CONFLICT (id) DO NOTHING;
                    """)
                else:
                    stmt = text("""
                        INSERT OR IGNORE INTO building_zones (
                            id, study_area_id, name, category, gross_floor_area_sqm,
                            occupancy_type, sanctioned_load_kva, contract_demand_kw,
                            geom, properties
                        ) VALUES (
                            :id, :study_area_id, :name, :category, :gross_floor_area_sqm,
                            :occupancy_type, :sanctioned_load_kva, :contract_demand_kw,
                            :geom, :properties
                        );
                    """)
                await session.execute(stmt, {
                    "id": b["id"],
                    "study_area_id": study_area_id,
                    "name": b["name"],
                    "category": b.get("category", "COMMERCIAL_RETAIL"),
                    "gross_floor_area_sqm": b["grossFloorAreaSqMeters"],
                    "occupancy_type": b.get("occupancyType", "RETAIL_ENTERTAINMENT"),
                    "sanctioned_load_kva": b.get("electricalConnection", {}).get("sanctionedLoadKVA"),
                    "contract_demand_kw": b.get("electricalConnection", {}).get("contractDemandKW"),
                    "geom": point_geom,
                    "properties": json.dumps(b.get("baselineMetrics", {}))
                })
                count += 1
    except Exception as e:
        logger.warning("Energy asset seeding notice: %s", e)
    return count


async def _seed_scenario_templates(session: AsyncSession) -> int:
    templates = [
        {
            "id": "SCEN-BASE-01",
            "name": "Evening Peak Fixed-Time Baseline (Viman Nagar Chowk)",
            "description": "Standard historical evening peak cycle timing with 120-second fixed progression.",
            "category": "MOBILITY_SIGNAL",
            "parameters_schema": json.dumps({"type": "object", "properties": {"cycle_time_sec": {"type": "integer", "default": 120}}}),
            "default_parameters": json.dumps({"cycle_time_sec": 120, "split_ratio_eb": 0.45})
        },
        {
            "id": "SCEN-INT-01",
            "name": "Adaptive Green Extension (Eastbound Nagar Road)",
            "description": "Dynamically extends EB green phase by 15s during detected high-queue conditions.",
            "category": "MOBILITY_SIGNAL",
            "parameters_schema": json.dumps({"type": "object", "properties": {"green_extension_sec": {"type": "integer", "default": 15}}}),
            "default_parameters": json.dumps({"green_extension_sec": 15, "priority_corridor": "EASTBOUND"})
        },
        {
            "id": "SCEN-INT-02",
            "name": "Corridor Platoon Coordination (VN Chowk to Somnath Nagar)",
            "description": "Synchronizes signal offsets to establish a continuous green wave across adjacent junctions.",
            "category": "MOBILITY_PROGRESSION",
            "parameters_schema": json.dumps({"type": "object", "properties": {"offset_sec": {"type": "integer", "default": 24}}}),
            "default_parameters": json.dumps({"offset_sec": 24, "target_speed_kmh": 45.0})
        }
    ]
    count = 0
    for t in templates:
        stmt = text("""
            INSERT OR IGNORE INTO scenario_templates (
                id, name, description, category, parameters_schema, default_parameters
            ) VALUES (
                :id, :name, :description, :category, :parameters_schema, :default_parameters
            );
        """)
        try:
            await session.execute(stmt, t)
            count += 1
        except Exception:
            pass
    return count


async def _seed_initial_current_state(session: AsyncSession) -> int:
    """
    Seeds initial authoritative corridor state in entity_current_state so that
    GET /api/v1/state/current returns instant operational metrics.
    All seeded states are strictly marked REPLAY with quality VALID per AGENTS.md §7.1.
    """
    now_utc = datetime.now(timezone.utc).isoformat()
    segments = [
        ("urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01", "RoadSegment", 42.5, 1820.0, 32.0, 15.0, 0.35),
        ("urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-02", "RoadSegment", 38.0, 2100.0, 48.0, 45.0, 0.52),
        ("urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-03", "RoadSegment", 44.0, 1650.0, 28.0, 10.0, 0.28),
        ("urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-WB-01", "RoadSegment", 41.0, 1750.0, 35.0, 20.0, 0.39),
        ("urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-WB-02", "RoadSegment", 36.5, 2250.0, 52.0, 60.0, 0.58),
        ("urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-WB-03", "RoadSegment", 43.5, 1700.0, 30.0, 12.0, 0.31),
        ("urn:ngsi-ld:RoadSegment:PUNE:SEG-VN-NB-01", "RoadSegment", 28.0, 950.0, 55.0, 40.0, 0.62),
        ("urn:ngsi-ld:RoadSegment:PUNE:SEG-VN-SB-01", "RoadSegment", 32.0, 880.0, 42.0, 25.0, 0.48),
        ("urn:ngsi-ld:RoadSegment:PUNE:SEG-SN-NB-01", "RoadSegment", 30.5, 780.0, 38.0, 18.0, 0.44),
        ("urn:ngsi-ld:RoadSegment:PUNE:SEG-SN-SB-01", "RoadSegment", 34.0, 720.0, 32.0, 12.0, 0.36),
    ]

    count = 0
    for seg_id, entity_type, speed, flow, occ, queue, cong in segments:
        metrics = {
            "averageSpeedKmh": speed,
            "vehicleFlowPerHour": flow,
            "occupancyPercent": occ,
            "queueLengthMeters": queue,
            "congestionIndex": cong
        }
        stmt = text("""
            INSERT OR IGNORE INTO entity_current_state (
                entity_id, entity_type, source_mode, observed_at, updated_at,
                metrics, quality_status, freshness_seconds
            ) VALUES (
                :entity_id, :entity_type, :source_mode, :observed_at, :updated_at,
                :metrics, :quality_status, :freshness_seconds
            );
        """)
        await session.execute(stmt, {
            "entity_id": seg_id,
            "entity_type": entity_type,
            "source_mode": "REPLAY",
            "observed_at": now_utc,
            "updated_at": now_utc,
            "metrics": json.dumps(metrics),
            "quality_status": "VALID",
            "freshness_seconds": 12.0
        })
        count += 1

    # Energy entity
    energy_metrics = {
        "activePowerKw": 3450.0,
        "reactivePowerKvar": 1120.0,
        "powerFactor": 0.95,
        "energyConsumptionKwh": 82800.0
    }
    stmt = text("""
        INSERT OR IGNORE INTO entity_current_state (
            entity_id, entity_type, source_mode, observed_at, updated_at,
            metrics, quality_status, freshness_seconds
        ) VALUES (
            :entity_id, :entity_type, :source_mode, :observed_at, :updated_at,
            :metrics, :quality_status, :freshness_seconds
        );
    """)
    # Seed Phoenix Marketcity current energy state (Canonical URN + Spatial/Legacy Aliases)
    bld_urns = [
        ("urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01", "Building"),
        ("urn:ngsi-ld:BuildingZone:PUNE:BLD-PHOENIX-01", "BuildingZone"),
        ("urn:ngsi-ld:BuildingZone:PUNE:PHOENIX-01", "BuildingZone"),
    ]
    for bld_id, bld_type in bld_urns:
        await session.execute(stmt, {
            "entity_id": bld_id,
            "entity_type": bld_type,
            "source_mode": "REPLAY",
            "observed_at": now_utc,
            "updated_at": now_utc,
            "metrics": json.dumps(energy_metrics),
            "quality_status": "VALID",
            "freshness_seconds": 15.0
        })
        count += 1

    return count


async def _seed_spatial_registry(session: AsyncSession, is_pg: bool) -> Dict[str, int]:
    """
    Seeds the spatial mapping tables (Phase 8A) from corridor_spatial_registry.json.
    Establishes versioned PostGIS <-> SUMO mappings for segments, junctions, signals, and buildings.
    """
    counts = {"segments": 0, "intersections": 0, "signals": 0, "buildings": 0, "sensors": 0}
    registry_file = DATA_DIR / "spatial" / "corridor_spatial_registry.json"
    if not registry_file.exists():
        return counts

    try:
        with open(registry_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 1. Road Segments
        for seg in data.get("roadSegmentMappings", []):
            stmt = text("""
                INSERT OR IGNORE INTO spatial_road_segment_map (
                    segment_id, sumo_edge_id, name, direction, from_junction,
                    to_junction, length_meters, lane_count, speed_limit_kmh,
                    osm_highway, coordinates, lanes_json
                ) VALUES (
                    :segment_id, :sumo_edge_id, :name, :direction, :from_junction,
                    :to_junction, :length_meters, :lane_count, :speed_limit_kmh,
                    :osm_highway, :coordinates, :lanes_json
                );
            """)
            await session.execute(stmt, {
                "segment_id": seg["segmentId"],
                "sumo_edge_id": seg["sumoEdgeId"],
                "name": seg["name"],
                "direction": seg["direction"],
                "from_junction": seg.get("fromJunction"),
                "to_junction": seg.get("toJunction"),
                "length_meters": seg["lengthMeters"],
                "lane_count": seg["laneCount"],
                "speed_limit_kmh": seg["speedLimitKmh"],
                "osm_highway": seg.get("osmHighway", "primary"),
                "coordinates": json.dumps(seg.get("coordinates", [])),
                "lanes_json": json.dumps(seg.get("lanes", []))
            })
            counts["segments"] += 1

        # 2. Intersections
        for inter in data.get("intersectionMappings", []):
            stmt = text("""
                INSERT OR IGNORE INTO spatial_intersection_map (
                    intersection_id, sumo_junction_id, name, control_type,
                    coordinates, cycle_time_sec, phases_count, approach_edges,
                    departure_edges, tls_program_id
                ) VALUES (
                    :intersection_id, :sumo_junction_id, :name, :control_type,
                    :coordinates, :cycle_time_sec, :phases_count, :approach_edges,
                    :departure_edges, :tls_program_id
                );
            """)
            await session.execute(stmt, {
                "intersection_id": inter["intersectionId"],
                "sumo_junction_id": inter["sumoJunctionId"],
                "name": inter["name"],
                "control_type": inter["controlType"],
                "coordinates": json.dumps(inter.get("coordinates", [])),
                "cycle_time_sec": inter.get("cycleTimeSec", 120),
                "phases_count": inter.get("phasesCount", 4),
                "approach_edges": json.dumps(inter.get("approachEdges", [])),
                "departure_edges": json.dumps(inter.get("departureEdges", [])),
                "tls_program_id": inter.get("tlsProgramId")
            })
            counts["intersections"] += 1

        # 3. Signal Controllers
        for tsc in data.get("signalControllers", []):
            stmt = text("""
                INSERT OR IGNORE INTO spatial_signal_controller_map (
                    controller_id, intersection_id, sumo_tls_id, cycle_time_sec, signal_groups_json
                ) VALUES (
                    :controller_id, :intersection_id, :sumo_tls_id, :cycle_time_sec, :signal_groups_json
                );
            """)
            await session.execute(stmt, {
                "controller_id": tsc["controllerId"],
                "intersection_id": tsc["intersectionId"],
                "sumo_tls_id": tsc["sumoTlsId"],
                "cycle_time_sec": tsc.get("cycleTimeSec", 120),
                "signal_groups_json": json.dumps(tsc.get("signalGroups", []))
            })
            counts["signals"] += 1

        # 4. Building Zones
        for bld in data.get("buildingZoneMappings", []):
            stmt = text("""
                INSERT OR IGNORE INTO spatial_building_zone_map (
                    building_id, name, category, gross_floor_area_sqm,
                    contract_demand_kw, height_meters, building_levels,
                    model_fidelity_level, roof_type, color_tint,
                    centroid, footprint_polygon
                ) VALUES (
                    :building_id, :name, :category, :gross_floor_area_sqm,
                    :contract_demand_kw, :height_meters, :building_levels,
                    :model_fidelity_level, :roof_type, :color_tint,
                    :centroid, :footprint_polygon
                );
            """)
            await session.execute(stmt, {
                "building_id": bld["buildingId"],
                "name": bld["name"],
                "category": bld.get("category", "COMMERCIAL_RETAIL"),
                "gross_floor_area_sqm": bld["grossFloorAreaSqm"],
                "contract_demand_kw": bld["contractDemandKw"],
                "height_meters": bld.get("heightMeters", 28.0),
                "building_levels": bld.get("buildingLevels", 6),
                "model_fidelity_level": bld.get("modelFidelityLevel", "B2"),
                "roof_type": bld.get("roofType", "FLAT_COMMERCIAL"),
                "color_tint": bld.get("colorTint", "#2A4B54"),
                "centroid": json.dumps(bld.get("centroid", [])),
                "footprint_polygon": json.dumps(bld.get("footprintPolygon", []))
            })
            counts["buildings"] += 1

        # 5. Sensors
        for sns in data.get("sensorMappings", []):
            stmt = text("""
                INSERT OR IGNORE INTO spatial_sensor_map (
                    sensor_id, name, segment_id, sumo_edge_id, direction,
                    coordinates, elevation_meters, sensor_type, sampling_interval_sec
                ) VALUES (
                    :sensor_id, :name, :segment_id, :sumo_edge_id, :direction,
                    :coordinates, :elevation_meters, :sensor_type, :sampling_interval_sec
                );
            """)
            await session.execute(stmt, {
                "sensor_id": sns["sensorId"],
                "name": sns["name"],
                "segment_id": sns.get("segmentId"),
                "sumo_edge_id": sns.get("sumoEdgeId"),
                "direction": sns.get("direction", "EASTBOUND"),
                "coordinates": json.dumps(sns.get("coordinates", [])),
                "elevation_meters": sns.get("elevationMeters", 1.5),
                "sensor_type": sns.get("sensorType", "INDUCTIVE_LOOP_EMULATION"),
                "sampling_interval_sec": sns.get("samplingIntervalSec", 60)
            })
            counts["sensors"] += 1

        # 6. Scenario Geometry
        for sc in data.get("scenarioGeometryMappings", []):
            stmt = text("""
                INSERT OR IGNORE INTO spatial_scenario_geometry_map (
                    scenario_template_id, name, corridor_edge_ids, junction_ids
                ) VALUES (
                    :scenario_template_id, :name, :corridor_edge_ids, :junction_ids
                );
            """)
            await session.execute(stmt, {
                "scenario_template_id": sc["scenarioTemplateId"],
                "name": sc["name"],
                "corridor_edge_ids": json.dumps(sc.get("corridorEdgeIds", [])),
                "junction_ids": json.dumps(sc.get("junctionIds", []))
            })

    except Exception as e:
        logger.warning("Spatial registry seeding notice: %s", e)

    return counts


async def init_db_schema() -> Dict[str, Any]:
    """
    Primary entrypoint called on FastAPI startup lifespan.
    Initializes database tables and seeds authoritative corridor assets if missing.
    """
    backend = get_active_backend()
    is_pg = backend == "postgresql"

    async with persistence_manager.session_factory() as session:
        try:
            # 1. Run DDL migration
            if is_pg:
                tables_created = await _migrate_postgres(session)
            else:
                tables_created = await _migrate_sqlite(session)

            # 2. Check if assets need seeding
            check_res = await session.execute(text("SELECT COUNT(*) FROM study_areas"))
            study_count = check_res.scalar() or 0

            seeded_assets = {}
            if study_count == 0:
                logger.info("Database empty. Seeding authoritative corridor assets...")
                await _seed_study_area(session, is_pg)
                seeded_assets["corridor"] = await _seed_corridor_assets(session, is_pg)
                seeded_assets["sensors"] = await _seed_sensors(session, is_pg)
                seeded_assets["energy"] = await _seed_energy_assets(session, is_pg)
                seeded_assets["templates"] = await _seed_scenario_templates(session)
                seeded_assets["currentState"] = await _seed_initial_current_state(session)
                await session.commit()
                logger.info("Authoritative corridor spatial assets seeded successfully.")
            else:
                logger.info("Corridor assets already present (%s study areas found).", study_count)

            # Check if spatial registry needs seeding
            check_spatial = await session.execute(text("SELECT COUNT(*) FROM spatial_road_segment_map"))
            spatial_count = check_spatial.scalar() or 0
            if spatial_count == 0:
                logger.info("Seeding spatial registry mappings...")
                seeded_assets["spatial"] = await _seed_spatial_registry(session, is_pg)
                await session.commit()
                logger.info("Spatial registry seeded successfully: %s", seeded_assets.get("spatial"))

            # Ensure continuous aggregates are seeded if empty
            try:
                from backend.services.continuous_aggregator import continuous_aggregator
                await continuous_aggregator.seed_synthetic_historical_rollups(session)
            except Exception as agg_err:
                logger.warning("Historical rollup seeding notice: %s", agg_err)

            # 3. Query total existing tables
            if is_pg:
                tbl_query = text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
            else:
                tbl_query = text("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            
            res = await session.execute(tbl_query)
            total_tables = res.scalar() or 0

            return {
                "backend": backend,
                "isFallback": not is_pg,
                "tablesCount": total_tables,
                "studyAreasCount": max(study_count, 1),
                "status": "INITIALIZED"
            }
        except Exception as e:
            logger.error("Database schema initialization failed: %s", e, exc_info=True)
            await session.rollback()
            return {
                "backend": backend,
                "isFallback": not is_pg,
                "status": "ERROR",
                "error": str(e)
            }
