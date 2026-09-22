"""
test_spatial_registry.py

Comprehensive test suite verifying Phase 8A: Spatial Fidelity Foundation.
Validates:
1. Master spatial registry catalog integrity and schema adherence.
2. 100% spatial mapping coverage across PostGIS, SUMO edges/lanes/junctions, signals, and buildings.
3. FastAPI endpoints: /api/v1/spatial/registry, /corridor-3d, /layers/{layer}, /resolve/{id}, /signals, /buildings.
4. Database persistence and automated seeding of spatial mapping tables.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.spatial_registry_service import spatial_service
from backend.core.database import persistence_manager
from sqlalchemy import text

client = TestClient(app)


def test_spatial_catalog_structure():
    """Verify the spatial registry catalog loads with all required Phase 8A entities."""
    cat = spatial_service.catalog
    assert cat.registryVersion == "1.0.0"
    assert cat.crs == "EPSG:4326"
    assert cat.studyAreaId == "urn:ngsi-ld:StudyArea:PUNE:VN-SN-CORRIDOR"
    assert len(cat.boundaryCoordinates) >= 4

    # 10 Road Segments mapped to SUMO edges
    assert len(cat.roadSegmentMappings) == 10
    # 2 Intersections mapped to SUMO junctions
    assert len(cat.intersectionMappings) == 2
    # 2 Signal Controllers with signal groups
    assert len(cat.signalControllers) == 2
    # Building Zones (Phoenix Marketcity and corridor landmarks) with 3D heights
    assert len(cat.buildingZoneMappings) >= 1
    # 5 Sensors
    assert len(cat.sensorMappings) == 5
    # 2 Scenario Geometries
    assert len(cat.scenarioGeometryMappings) == 2


def test_spatial_100_percent_mapping_coverage():
    """
    Verify 100% mapping coverage: every PostGIS road segment, intersection,
    building, and sensor maps to valid simulation / spatial entities without orphans.
    """
    cat = spatial_service.catalog

    expected_edges = [
        "SEG-NR-EB-01", "SEG-NR-EB-02", "SEG-NR-EB-03",
        "SEG-NR-WB-01", "SEG-NR-WB-02", "SEG-NR-WB-03",
        "SEG-VN-NB-01", "SEG-VN-SB-01",
        "SEG-SN-NB-01", "SEG-SN-SB-01",
    ]
    registered_edges = [seg.sumoEdgeId for seg in cat.roadSegmentMappings]
    for e in expected_edges:
        assert e in registered_edges, f"SUMO edge {e} missing from spatial registry"

    # Verify each edge has valid lanes with lateral offsets
    for seg in cat.roadSegmentMappings:
        assert len(seg.lanes) == seg.laneCount
        assert len(seg.coordinates) >= 2
        for idx, lane in enumerate(seg.lanes):
            assert lane.laneIndex == idx
            assert lane.sumoLaneId.startswith(seg.sumoEdgeId)
            assert lane.widthMeters > 0

    # Intersections
    registered_junctions = {inter.sumoJunctionId: inter for inter in cat.intersectionMappings}
    assert "VN-01" in registered_junctions
    assert "SN-01" in registered_junctions
    assert registered_junctions["VN-01"].phasesCount == 4
    assert registered_junctions["SN-01"].phasesCount == 3

    # Signal Groups
    vn_tsc = next(c for c in cat.signalControllers if c.sumoTlsId == "VN-01")
    assert len(vn_tsc.signalGroups) == 4
    for sg in vn_tsc.signalGroups:
        assert len(sg.stopLineCoordinate) == 2
        assert len(sg.sumoLinks) > 0
        assert sg.greenDurationSec > 0


def test_building_height_and_energy_spatial_fidelity():
    """Verify Phoenix Marketcity building footprint, height, and levels for 3D extrusion."""
    cat = spatial_service.catalog
    bld = cat.buildingZoneMappings[0]

    assert bld.buildingId == "urn:ngsi-ld:BuildingZone:PUNE:BLD-PHOENIX-01"
    assert bld.category == "COMMERCIAL_RETAIL"
    assert bld.grossFloorAreaSqm == 110000.0
    assert bld.heightMeters == 28.0
    assert bld.buildingLevels == 6
    assert bld.modelFidelityLevel == "B2"
    assert len(bld.footprintPolygon) >= 4


def test_api_get_spatial_registry():
    """Test GET /api/v1/spatial/registry returns 200 and schema validates."""
    response = client.get("/api/v1/spatial/registry")
    assert response.status_code == 200
    data = response.json()

    assert data["registryVersion"] == "1.0.0"
    assert len(data["roadSegmentMappings"]) == 10
    assert len(data["intersectionMappings"]) == 2
    assert len(data["signalControllers"]) == 2
    assert len(data["buildingZoneMappings"]) >= 1
    assert len(data["sensorMappings"]) == 5


def test_api_get_corridor_3d_geojson():
    """Test GET /api/v1/spatial/corridor-3d returns a valid Cesium-ready FeatureCollection."""
    response = client.get("/api/v1/spatial/corridor-3d")
    assert response.status_code == 200
    data = response.json()

    assert data["type"] == "FeatureCollection"
    assert "crs" in data
    assert "metadata" in data
    assert data["metadata"]["corridorLengthKm"] == 1.8
    assert len(data["features"]) > 20

    layers = {f["properties"]["layer"] for f in data["features"]}
    assert "study_area" in layers
    assert "buildings" in layers
    assert "roads" in layers
    assert "intersections" in layers
    assert "signals" in layers
    assert "sensors" in layers

    # Check building extrusion properties
    bld_feat = next(f for f in data["features"] if f["properties"]["layer"] == "buildings")
    assert bld_feat["properties"]["heightMeters"] == 28.0
    assert bld_feat["properties"]["buildingLevels"] == 6

    # Check signal head stopline properties
    sig_feat = next(f for f in data["features"] if f["properties"]["layer"] == "signals")
    assert "headingDegrees" in sig_feat["properties"]
    assert "sumoLinks" in sig_feat["properties"]


def test_api_get_spatial_layer_filtering():
    """Test GET /api/v1/spatial/layers/{layer} correctly filters features."""
    for layer in ["buildings", "roads", "intersections", "signals", "sensors"]:
        response = client.get(f"/api/v1/spatial/layers/{layer}")
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) > 0
        for feat in data["features"]:
            assert feat["properties"]["layer"] == layer

    # Invalid layer returns 400
    bad_resp = client.get("/api/v1/spatial/layers/invalid_layer_name")
    assert bad_resp.status_code == 400


def test_api_resolve_spatial_entity():
    """Test GET /api/v1/spatial/resolve/{id} resolves road segment, intersection, and building."""
    # 1. Resolve road segment
    resp_seg = client.get("/api/v1/spatial/resolve/urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01")
    assert resp_seg.status_code == 200
    seg_data = resp_seg.json()
    assert seg_data["spatialFound"] is True
    assert seg_data["sumoEquivalentId"] == "SEG-NR-EB-01"
    assert seg_data["properties"]["laneCount"] == 3

    # Short form ID resolution
    resp_short = client.get("/api/v1/spatial/resolve/SEG-NR-EB-01")
    assert resp_short.status_code == 200
    assert resp_short.json()["sumoEquivalentId"] == "SEG-NR-EB-01"

    # 2. Resolve intersection
    resp_int = client.get("/api/v1/spatial/resolve/urn:ngsi-ld:Intersection:PUNE:VN-01")
    assert resp_int.status_code == 200
    int_data = resp_int.json()
    assert int_data["spatialFound"] is True
    assert int_data["sumoEquivalentId"] == "VN-01"
    assert int_data["properties"]["phasesCount"] == 4

    # 3. Resolve building
    resp_bld = client.get("/api/v1/spatial/resolve/urn:ngsi-ld:BuildingZone:PUNE:BLD-PHOENIX-01")
    assert resp_bld.status_code == 200
    bld_data = resp_bld.json()
    assert bld_data["spatialFound"] is True
    assert bld_data["properties"]["heightMeters"] == 28.0

    # 4. Unknown entity returns 404
    resp_none = client.get("/api/v1/spatial/resolve/nonexistent_entity_xyz")
    assert resp_none.status_code == 404


def test_building_entity_resolution_isolation_and_aliases():
    """Verify Phoenix aliases resolve strictly to Phoenix and non-Phoenix buildings do not false-match."""
    # Canonical Building URN
    res_can = spatial_service.resolve_entity("urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01")
    assert res_can.spatialFound is True
    assert "PHOENIX" in res_can.entityId.upper()

    # Short form ID
    res_short = spatial_service.resolve_entity("BLD-PHOENIX-01")
    assert res_short.spatialFound is True
    assert "PHOENIX" in res_short.entityId.upper()

    # Non-existent building must not resolve to Phoenix
    res_other = spatial_service.resolve_entity("BLD-NONEXISTENT-99")
    assert res_other.spatialFound is False

    # Resolution via API
    resp_alias = client.get("/api/v1/spatial/resolve/urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01")
    assert resp_alias.status_code == 200
    assert resp_alias.json()["spatialFound"] is True


from backend.core.schema_migrator import init_db_schema


@pytest.mark.asyncio
async def test_database_spatial_tables_persistence():
    """Verify that spatial mapping tables are seeded and queryable in SQLite / PostgreSQL."""
    init_res = await init_db_schema()
    assert init_res["status"] == "INITIALIZED"

    async with persistence_manager.session_factory() as session:
        # Segments
        res_seg = await session.execute(text("SELECT COUNT(*) FROM spatial_road_segment_map"))
        assert (res_seg.scalar() or 0) >= 10

        # Intersections
        res_int = await session.execute(text("SELECT COUNT(*) FROM spatial_intersection_map"))
        assert (res_int.scalar() or 0) >= 2

        # Signals
        res_sig = await session.execute(text("SELECT COUNT(*) FROM spatial_signal_controller_map"))
        assert (res_sig.scalar() or 0) >= 2

        # Buildings
        res_bld = await session.execute(text("SELECT COUNT(*) FROM spatial_building_zone_map"))
        assert (res_bld.scalar() or 0) >= 1

        # Sensors
        res_sns = await session.execute(text("SELECT COUNT(*) FROM spatial_sensor_map"))
        assert (res_sns.scalar() or 0) >= 5
