"""
spatial.py

Pydantic schemas for the Spatial Fidelity Foundation (Phase 8A).
Binds PostGIS real-world coordinates, SUMO simulation IDs, lane geometries,
traffic signals, building zones, and sensors into a versioned spatial registry.
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class LaneSpatialModel(BaseModel):
    laneIndex: int = Field(..., description="0-based lane index (0 is innermost or curbside per standard)")
    sumoLaneId: str = Field(..., description="SUMO lane identifier (e.g. edge_0)")
    type: str = Field(default="THROUGH", description="Lane function: CURBSIDE, THROUGH, MEDIAN_OVERTAKING")
    widthMeters: float = Field(default=3.5, description="Physical lane width in meters")
    offsetMeters: float = Field(default=0.0, description="Lateral offset from road centerline in meters")


class RoadSegmentSUMOMap(BaseModel):
    segmentId: str = Field(..., description="Canonical URN of the road segment")
    sumoEdgeId: str = Field(..., description="SUMO network edge ID")
    name: str = Field(..., description="Human readable corridor name")
    direction: str = Field(..., description="EASTBOUND, WESTBOUND, NORTHBOUND, SOUTHBOUND")
    fromJunction: Optional[str] = Field(None, description="Origin junction/node ID")
    toJunction: Optional[str] = Field(None, description="Destination junction/node ID")
    lengthMeters: float = Field(..., description="Segment length in meters")
    laneCount: int = Field(..., ge=1, description="Total travel lanes")
    speedLimitKmh: float = Field(..., description="Design speed limit")
    osmHighway: str = Field(default="primary", description="OSM highway tag classification")
    coordinates: List[List[float]] = Field(..., description="Linestring coordinates [[lng, lat], ...]")
    lanes: List[LaneSpatialModel] = Field(default_factory=list, description="Per-lane spatial specifications")


class IntersectionSUMOMap(BaseModel):
    intersectionId: str = Field(..., description="Canonical URN of the intersection")
    sumoJunctionId: str = Field(..., description="SUMO network junction ID")
    name: str = Field(..., description="Junction name")
    controlType: str = Field(default="SIGNALIZED", description="SIGNALIZED, PRIORITY, ROUNDABOUT")
    coordinates: List[float] = Field(..., description="Center point coordinates [lng, lat]")
    cycleTimeSec: int = Field(default=120, description="Signal cycle length in seconds")
    phasesCount: int = Field(default=4, description="Total active signal phases")
    approachEdges: List[str] = Field(default_factory=list, description="Approach edge IDs")
    departureEdges: List[str] = Field(default_factory=list, description="Departure edge IDs")
    tlsProgramId: Optional[str] = Field(None, description="Associated traffic light program ID")


class SignalGroupMap(BaseModel):
    groupId: str = Field(..., description="Signal group identifier")
    name: str = Field(..., description="Descriptive movement name")
    approachEdge: str = Field(..., description="Approach edge controlled by this signal group")
    sumoLinks: List[int] = Field(default_factory=list, description="SUMO link indices in TLS state string")
    stopLineCoordinate: List[float] = Field(..., description="Stop line 3D placement [lng, lat]")
    headingDegrees: float = Field(default=0.0, description="Azimuth angle facing approaching traffic")
    greenDurationSec: int = Field(..., description="Green phase duration in seconds")
    yellowDurationSec: int = Field(default=3, description="Yellow clearance duration in seconds")


class SignalControllerSUMOMap(BaseModel):
    controllerId: str = Field(..., description="Canonical URN of the signal controller")
    intersectionId: str = Field(..., description="Governed intersection URN")
    sumoTlsId: str = Field(..., description="SUMO traffic light logic ID")
    cycleTimeSec: int = Field(default=120, description="Total cycle length")
    signalGroups: List[SignalGroupMap] = Field(default_factory=list, description="Signal groups / movements")


class BuildingZoneSpatialMap(BaseModel):
    buildingId: str = Field(..., description="Canonical URN of the building entity")
    name: str = Field(..., description="Commercial building name")
    category: str = Field(default="COMMERCIAL_RETAIL")
    grossFloorAreaSqm: float = Field(..., description="Total building floor area")
    contractDemandKw: float = Field(..., description="Peak sanctioned electrical demand")
    heightMeters: float = Field(default=28.0, description="Physical building height for 3D extrusion")
    buildingLevels: int = Field(default=6, description="Above-ground floor count")
    modelFidelityLevel: str = Field(default="B2", description="B1 footprint extrusion, B2 curated, B3 photorealistic")
    roofType: str = Field(default="FLAT_COMMERCIAL")
    colorTint: str = Field(default="#2A4B54")
    centroid: List[float] = Field(..., description="Building centroid [lng, lat]")
    footprintPolygon: List[List[float]] = Field(..., description="Closed polygon coordinates [[lng, lat], ...]")


class SensorSpatialMap(BaseModel):
    sensorId: str = Field(..., description="Canonical sensor URN")
    name: str = Field(..., description="Sensor designation")
    segmentId: Optional[str] = Field(None, description="Linked road segment if traffic sensor")
    sumoEdgeId: Optional[str] = Field(None, description="Linked SUMO edge ID if traffic sensor")
    direction: str = Field(default="EASTBOUND")
    coordinates: List[float] = Field(..., description="Physical sensor position [lng, lat]")
    elevationMeters: float = Field(default=1.5, description="Mounting height above ground")
    sensorType: str = Field(default="INDUCTIVE_LOOP_EMULATION")
    samplingIntervalSec: int = Field(default=60)


class ScenarioGeometryMap(BaseModel):
    scenarioTemplateId: str = Field(..., description="SCEN-BASE-01 or SCEN-INT-01")
    name: str = Field(..., description="Scenario descriptive name")
    corridorEdgeIds: List[str] = Field(default_factory=list)
    junctionIds: List[str] = Field(default_factory=list)


class SpatialRegistryCatalog(BaseModel):
    registryVersion: str = Field(default="1.0.0")
    crs: str = Field(default="EPSG:4326")
    studyAreaId: str = Field(...)
    name: str = Field(...)
    boundaryCoordinates: List[List[float]]
    roadSegmentMappings: List[RoadSegmentSUMOMap]
    intersectionMappings: List[IntersectionSUMOMap]
    signalControllers: List[SignalControllerSUMOMap]
    buildingZoneMappings: List[BuildingZoneSpatialMap]
    sensorMappings: List[SensorSpatialMap]
    scenarioGeometryMappings: List[ScenarioGeometryMap]
    urbanTreeMappings: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    secondaryStreetMappings: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


class SpatialEntityResolution(BaseModel):
    entityId: str
    entityType: str
    spatialFound: bool
    sumoEquivalentId: Optional[str] = None
    coordinates: Optional[Any] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
