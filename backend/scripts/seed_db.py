"""
seed_db.py

Populates PostgreSQL / PostGIS with the initial authoritative corridor spatial assets,
intersections, road segments, sensors, and representative building zones.

Usage:
    python backend/scripts/seed_db.py
"""

import json
import logging
import sys
from pathlib import Path
from sqlalchemy import create_engine, text

# Set up paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def seed_database(connection_string: str):
    logging.info("Connecting to database: %s", connection_string.split("@")[-1])
    engine = create_engine(connection_string)

    with engine.begin() as conn:
        # 1. Seed Study Area
        study_area_file = DATA_DIR / "study_area.geojson"
        if study_area_file.exists():
            logging.info("Seeding study area from %s", study_area_file)
            with open(study_area_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                feature = data["features"][0]
                props = feature["properties"]
                geom_json = json.dumps(feature["geometry"])
                
                conn.execute(text("""
                    INSERT INTO study_areas (
                        id, name, city, state, country, primary_highway,
                        corridor_length_km, boundary_version, crs, geom
                    ) VALUES (
                        :id, :name, :city, :state, :country, :primary_highway,
                        :corridor_length_km, :boundary_version, :crs,
                        ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326)
                    ) ON CONFLICT (id) DO UPDATE SET
                        geom = EXCLUDED.geom,
                        name = EXCLUDED.name
                """), {
                    "id": props["id"],
                    "name": props["name"],
                    "city": props["city"],
                    "state": props["state"],
                    "country": props["country"],
                    "primary_highway": props["primaryHighway"],
                    "corridor_length_km": props["corridorLengthKm"],
                    "boundary_version": props["boundaryVersion"],
                    "crs": props["crs"],
                    "geom": geom_json
                })
        
        # 2. Seed Corridor Assets (Intersections & Road Segments)
        corridor_file = DATA_DIR / "samples" / "corridor_assets.json"
        if corridor_file.exists():
            logging.info("Seeding intersections and road segments from %s", corridor_file)
            with open(corridor_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                study_area_id = data.get("studyAreaId")

                # Intersections
                for item in data.get("intersections", []):
                    point_geom = json.dumps({"type": "Point", "coordinates": item["coordinates"]})
                    conn.execute(text("""
                        INSERT INTO intersections (
                            id, study_area_id, name, control_type,
                            cycle_time_sec, phases_count, geom, properties
                        ) VALUES (
                            :id, :study_area_id, :name, :control_type,
                            :cycle_time_sec, :phases_count,
                            ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326), :properties
                        ) ON CONFLICT (id) DO UPDATE SET
                            geom = EXCLUDED.geom,
                            cycle_time_sec = EXCLUDED.cycle_time_sec
                    """), {
                        "id": item["id"],
                        "study_area_id": study_area_id,
                        "name": item["name"],
                        "control_type": item.get("controlType", "SIGNALIZED"),
                        "cycle_time_sec": item.get("cycleTimeSec", 120),
                        "phases_count": item.get("phases", 4),
                        "geom": point_geom,
                        "properties": json.dumps({"connectedSegments": item.get("connectedSegments", [])})
                    })

                # Road Segments
                for seg in data.get("roadSegments", []):
                    line_geom = json.dumps({"type": "LineString", "coordinates": seg["coordinates"]})
                    conn.execute(text("""
                        INSERT INTO road_segments (
                            id, study_area_id, name, direction, from_intersection,
                            to_intersection, length_meters, lane_count, speed_limit_kmh,
                            free_flow_speed_kmh, capacity_veh_per_hour, osm_highway, geom
                        ) VALUES (
                            :id, :study_area_id, :name, :direction, :from_intersection,
                            :to_intersection, :length_meters, :lane_count, :speed_limit_kmh,
                            :free_flow_speed_kmh, :capacity_veh_per_hour, :osm_highway,
                            ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326)
                        ) ON CONFLICT (id) DO UPDATE SET
                            geom = EXCLUDED.geom,
                            speed_limit_kmh = EXCLUDED.speed_limit_kmh
                    """), {
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

        # 3. Seed Sensors
        sensor_file = DATA_DIR / "samples" / "sensor_registry.json"
        if sensor_file.exists():
            logging.info("Seeding sensors from %s", sensor_file)
            with open(sensor_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                study_area_id = data.get("studyAreaId")
                for s in data.get("sensors", []):
                    point_geom = json.dumps({"type": "Point", "coordinates": s["coordinates"]})
                    conn.execute(text("""
                        INSERT INTO sensors (
                            id, study_area_id, name, linked_segment_id, direction,
                            sensor_type, supported_source_modes, sampling_interval_sec,
                            freshness_threshold_sec, geom, properties
                        ) VALUES (
                            :id, :study_area_id, :name, :linked_segment_id, :direction,
                            :sensor_type, :supported_source_modes, :sampling_interval_sec,
                            :freshness_threshold_sec,
                            ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326), :properties
                        ) ON CONFLICT (id) DO UPDATE SET
                            freshness_threshold_sec = EXCLUDED.freshness_threshold_sec
                    """), {
                        "id": s["id"],
                        "study_area_id": study_area_id,
                        "name": s["name"],
                        "linked_segment_id": s["linkedSegmentId"],
                        "direction": s["direction"],
                        "sensor_type": s["sensorType"],
                        "supported_source_modes": s["supportedSourceModes"],
                        "sampling_interval_sec": s["samplingIntervalSec"],
                        "freshness_threshold_sec": s["freshnessThresholdSec"],
                        "geom": point_geom,
                        "properties": json.dumps({"metrics": s.get("metrics", [])})
                    })

        # 4. Seed Building Zone
        energy_file = DATA_DIR / "samples" / "energy_assets.json"
        if energy_file.exists():
            logging.info("Seeding building zone from %s", energy_file)
            with open(energy_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                study_area_id = data.get("studyAreaId")
                for b in data.get("entities", []):
                    point_geom = json.dumps(b["location"])
                    conn.execute(text("""
                        INSERT INTO building_zones (
                            id, study_area_id, name, category, gross_floor_area_sqm,
                            occupancy_type, sanctioned_load_kva, contract_demand_kw,
                            geom, properties
                        ) VALUES (
                            :id, :study_area_id, :name, :category, :gross_floor_area_sqm,
                            :occupancy_type, :sanctioned_load_kva, :contract_demand_kw,
                            ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326), :properties
                        ) ON CONFLICT (id) DO UPDATE SET
                            gross_floor_area_sqm = EXCLUDED.gross_floor_area_sqm
                    """), {
                        "id": b["id"],
                        "study_area_id": study_area_id,
                        "name": b["name"],
                        "category": b.get("category", "COMMERCIAL_RETAIL"),
                        "gross_floor_area_sqm": b["grossFloorAreaSqMeters"],
                        "occupancy_type": b.get("occupancyType"),
                        "sanctioned_load_kva": b.get("electricalConnection", {}).get("sanctionedLoadKVA"),
                        "contract_demand_kw": b.get("electricalConnection", {}).get("contractDemandKW"),
                        "geom": point_geom,
                        "properties": json.dumps(b.get("baselineMetrics", {}))
                    })

    logging.info("Database seeding successfully completed!")

if __name__ == "__main__":
    db_url = "postgresql://postgres:postgres@localhost:5432/digital_twin"
    if len(sys.argv) > 1:
        db_url = sys.argv[1]
    seed_database(db_url)
