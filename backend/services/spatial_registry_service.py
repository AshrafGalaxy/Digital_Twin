"""
spatial_registry_service.py

Service layer for the Spatial Fidelity Foundation (Phase 8A).
Loads the authoritative corridor spatial registry, provides entity cross-referencing
between PostGIS and SUMO, and generates GeoJSON for 2D/3D visualization layers.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.schemas.spatial import (
    SpatialRegistryCatalog,
    SpatialEntityResolution,
    RoadSegmentSUMOMap,
    IntersectionSUMOMap,
    SignalControllerSUMOMap,
    BuildingZoneSpatialMap,
    SensorSpatialMap,
)

logger = logging.getLogger("digital_twin.spatial_service")


class SpatialRegistryService:
    def __init__(self, registry_path: Optional[Path] = None):
        self.registry_path = registry_path or self._resolve_registry_path()
        self._catalog: Optional[SpatialRegistryCatalog] = None
        self._raw_data: Optional[Dict[str, Any]] = None
        self._load()

    def _resolve_registry_path(self) -> Path:
        candidates = [
            Path(__file__).resolve().parents[2] / "data" / "spatial" / "corridor_spatial_registry.json",
            Path.cwd() / "data" / "spatial" / "corridor_spatial_registry.json",
            Path("data/spatial/corridor_spatial_registry.json"),
        ]
        for p in candidates:
            if p.exists():
                return p
        return candidates[0]

    def _load(self) -> None:
        if not self.registry_path.exists():
            logger.error("Spatial registry file not found at %s", self.registry_path)
            return
        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                self._raw_data = json.load(f)
                self._catalog = SpatialRegistryCatalog(**self._raw_data)
                logger.info(
                    "Loaded spatial registry v%s: %d segments, %d junctions, %d controllers, %d buildings",
                    self._catalog.registryVersion,
                    len(self._catalog.roadSegmentMappings),
                    len(self._catalog.intersectionMappings),
                    len(self._catalog.signalControllers),
                    len(self._catalog.buildingZoneMappings),
                )
        except Exception as e:
            logger.error("Failed to parse spatial registry JSON: %s", e)
            raise

    @property
    def catalog(self) -> SpatialRegistryCatalog:
        if not self._catalog:
            self._load()
        return self._catalog

    def get_catalog_dict(self) -> Dict[str, Any]:
        return self._raw_data or {}

    def resolve_entity(self, entity_id: str) -> SpatialEntityResolution:
        """
        Resolves an entity identifier to its PostGIS coordinates, SUMO equivalent ID,
        and spatial attributes. Handles both URN and short-form IDs.
        """
        norm_id = entity_id.strip()
        cat = self.catalog

        # Check Road Segments
        for seg in cat.roadSegmentMappings:
            if norm_id in (seg.segmentId, seg.sumoEdgeId) or norm_id.endswith(seg.sumoEdgeId):
                return SpatialEntityResolution(
                    entityId=seg.segmentId,
                    entityType="RoadSegment",
                    spatialFound=True,
                    sumoEquivalentId=seg.sumoEdgeId,
                    coordinates=seg.coordinates,
                    properties={
                        "name": seg.name,
                        "direction": seg.direction,
                        "lengthMeters": seg.lengthMeters,
                        "laneCount": seg.laneCount,
                        "speedLimitKmh": seg.speedLimitKmh,
                        "osmHighway": seg.osmHighway,
                        "lanes": [l.model_dump() for l in seg.lanes],
                    },
                )

        # Check Intersections
        for inter in cat.intersectionMappings:
            if norm_id in (inter.intersectionId, inter.sumoJunctionId) or norm_id.endswith(inter.sumoJunctionId):
                return SpatialEntityResolution(
                    entityId=inter.intersectionId,
                    entityType="Intersection",
                    spatialFound=True,
                    sumoEquivalentId=inter.sumoJunctionId,
                    coordinates=inter.coordinates,
                    properties={
                        "name": inter.name,
                        "controlType": inter.controlType,
                        "cycleTimeSec": inter.cycleTimeSec,
                        "phasesCount": inter.phasesCount,
                        "approachEdges": inter.approachEdges,
                        "departureEdges": inter.departureEdges,
                        "tlsProgramId": inter.tlsProgramId,
                    },
                )

        # Check Buildings
        for bld in cat.buildingZoneMappings:
            if norm_id in (bld.buildingId, "BLD-PHOENIX-01") or "PHOENIX" in norm_id.upper():
                return SpatialEntityResolution(
                    entityId=bld.buildingId,
                    entityType="BuildingZone",
                    spatialFound=True,
                    sumoEquivalentId=None,
                    coordinates=bld.centroid,
                    properties={
                        "name": bld.name,
                        "category": bld.category,
                        "grossFloorAreaSqm": bld.grossFloorAreaSqm,
                        "contractDemandKw": bld.contractDemandKw,
                        "heightMeters": bld.heightMeters,
                        "buildingLevels": bld.buildingLevels,
                        "modelFidelityLevel": bld.modelFidelityLevel,
                        "footprintPolygon": bld.footprintPolygon,
                    },
                )

        # Check Sensors
        for sns in cat.sensorMappings:
            if norm_id in (sns.sensorId, sns.name) or (sns.sumoEdgeId and norm_id.endswith(sns.sumoEdgeId)):
                return SpatialEntityResolution(
                    entityId=sns.sensorId,
                    entityType="Sensor",
                    spatialFound=True,
                    sumoEquivalentId=sns.sumoEdgeId,
                    coordinates=sns.coordinates,
                    properties={
                        "name": sns.name,
                        "segmentId": sns.segmentId,
                        "sensorType": sns.sensorType,
                        "direction": sns.direction,
                        "elevationMeters": sns.elevationMeters,
                    },
                )

        # Not found
        return SpatialEntityResolution(
            entityId=entity_id,
            entityType="Unknown",
            spatialFound=False,
            sumoEquivalentId=None,
            coordinates=None,
            properties={},
        )

    def get_corridor_3d_geojson(self) -> Dict[str, Any]:
        """
        Produces a consolidated 3D GeoJSON FeatureCollection optimized for CesiumJS ingestion.
        Includes extruded building geometries, road segments with lane properties,
        stop-line 3D signal points with azimuth, and sensor markers.
        """
        features: List[Dict[str, Any]] = []
        cat = self.catalog

        # 1. Study Area Polygon
        features.append({
            "type": "Feature",
            "id": cat.studyAreaId,
            "geometry": {
                "type": "Polygon",
                "coordinates": [cat.boundaryCoordinates],
            },
            "properties": {
                "layer": "study_area",
                "entityType": "StudyArea",
                "name": cat.name,
                "crs": cat.crs,
            },
        })

        # 2. Buildings (Polygons with 3D extrusion heights)
        for bld in cat.buildingZoneMappings:
            features.append({
                "type": "Feature",
                "id": bld.buildingId,
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [bld.footprintPolygon],
                },
                "properties": {
                    "layer": "buildings",
                    "entityType": "BuildingZone",
                    "name": bld.name,
                    "heightMeters": bld.heightMeters,
                    "buildingLevels": bld.buildingLevels,
                    "modelFidelityLevel": bld.modelFidelityLevel,
                    "colorTint": bld.colorTint,
                    "roofType": bld.roofType,
                    "grossFloorAreaSqm": bld.grossFloorAreaSqm,
                    "contractDemandKw": bld.contractDemandKw,
                },
            })

        # 3. Road Segments (LineStrings with lane counts & direction)
        for seg in cat.roadSegmentMappings:
            features.append({
                "type": "Feature",
                "id": seg.segmentId,
                "geometry": {
                    "type": "LineString",
                    "coordinates": seg.coordinates,
                },
                "properties": {
                    "layer": "roads",
                    "entityType": "RoadSegment",
                    "sumoEdgeId": seg.sumoEdgeId,
                    "name": seg.name,
                    "direction": seg.direction,
                    "laneCount": seg.laneCount,
                    "lengthMeters": seg.lengthMeters,
                    "speedLimitKmh": seg.speedLimitKmh,
                    "osmHighway": seg.osmHighway,
                    "lanes": [l.model_dump() for l in seg.lanes],
                },
            })

        # 4. Intersections (Points with junction control metadata)
        for inter in cat.intersectionMappings:
            features.append({
                "type": "Feature",
                "id": inter.intersectionId,
                "geometry": {
                    "type": "Point",
                    "coordinates": inter.coordinates,
                },
                "properties": {
                    "layer": "intersections",
                    "entityType": "Intersection",
                    "sumoJunctionId": inter.sumoJunctionId,
                    "name": inter.name,
                    "controlType": inter.controlType,
                    "cycleTimeSec": inter.cycleTimeSec,
                    "phasesCount": inter.phasesCount,
                    "tlsProgramId": inter.tlsProgramId,
                },
            })

        # 5. Signal Controllers & Signal Heads (Points at stop lines with azimuth)
        for tsc in cat.signalControllers:
            for sg in tsc.signalGroups:
                features.append({
                    "type": "Feature",
                    "id": f"{tsc.controllerId}:{sg.groupId}",
                    "geometry": {
                        "type": "Point",
                        "coordinates": sg.stopLineCoordinate,
                    },
                    "properties": {
                        "layer": "signals",
                        "entityType": "SignalHead",
                        "controllerId": tsc.controllerId,
                        "intersectionId": tsc.intersectionId,
                        "groupId": sg.groupId,
                        "name": sg.name,
                        "approachEdge": sg.approachEdge,
                        "headingDegrees": sg.headingDegrees,
                        "sumoLinks": sg.sumoLinks,
                        "greenDurationSec": sg.greenDurationSec,
                        "yellowDurationSec": sg.yellowDurationSec,
                    },
                })

        # 6. Sensors (Points with elevation & metric)
        for sns in cat.sensorMappings:
            features.append({
                "type": "Feature",
                "id": sns.sensorId,
                "geometry": {
                    "type": "Point",
                    "coordinates": sns.coordinates,
                },
                "properties": {
                    "layer": "sensors",
                    "entityType": "Sensor",
                    "name": sns.name,
                    "sensorType": sns.sensorType,
                    "segmentId": sns.segmentId,
                    "sumoEdgeId": sns.sumoEdgeId,
                    "direction": sns.direction,
                    "elevationMeters": sns.elevationMeters,
                    "samplingIntervalSec": sns.samplingIntervalSec,
                },
            })

        # 7. Urban Tree Canopies (Points with canopy diameter & height)
        for tree in getattr(cat, "urbanTreeMappings", []) or []:
            features.append({
                "type": "Feature",
                "id": tree.get("treeId", "TREE-01"),
                "geometry": {
                    "type": "Point",
                    "coordinates": tree.get("coordinates", [73.918, 18.561]),
                },
                "properties": {
                    "layer": "trees",
                    "entityType": "UrbanTreeCanopy",
                    "species": tree.get("species", "Gulmohar / Neem"),
                    "heightMeters": tree.get("heightMeters", 7.0),
                    "canopyDiameterMeters": tree.get("canopyDiameterMeters", 5.0),
                },
            })

        # 8. Secondary & Connector Streets (LineStrings with highway types)
        for st in getattr(cat, "secondaryStreetMappings", []) or []:
            features.append({
                "type": "Feature",
                "id": st.get("streetId", "SEC-01"),
                "geometry": {
                    "type": "LineString",
                    "coordinates": st.get("coordinates", []),
                },
                "properties": {
                    "layer": "secondary_streets",
                    "entityType": "SecondaryStreet",
                    "name": st.get("name", "Connector"),
                    "highwayType": st.get("highwayType", "residential"),
                },
            })

        return {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
            "metadata": {
                "registryVersion": cat.registryVersion,
                "totalFeatures": len(features),
                "corridorLengthKm": 1.8,
                "studyArea": cat.studyAreaId,
            },
            "features": features,
        }

    def get_layer_geojson(self, layer: str) -> Dict[str, Any]:
        """Filters the 3D GeoJSON package by specific layer."""
        full_collection = self.get_corridor_3d_geojson()
        target_layer = layer.lower().strip()
        filtered = [
            f for f in full_collection["features"]
            if f["properties"].get("layer", "").lower() == target_layer
        ]
        return {
            "type": "FeatureCollection",
            "crs": full_collection["crs"],
            "metadata": {
                "layer": target_layer,
                "count": len(filtered),
            },
            "features": filtered,
        }


# Global singleton instance
spatial_service = SpatialRegistryService()
