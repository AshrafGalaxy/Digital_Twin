"""
arterial_coordinator.py

Arterial Two-Way Green Wave Progression and Offset Optimizer Engine (TASK-03).
Calculates nominal progression offset, downstream queue clearance wave adjustment,
and bidirectional coordination efficiency subject to queue storage safety invariants.
"""

from datetime import datetime, timezone
import logging
import math
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, ConfigDict, Field

from backend.services.spatial_registry_service import spatial_service, SpatialRegistryService

logger = logging.getLogger("digital_twin.arterial_coordinator")


class ProgressionRequest(BaseModel):
    """
    Input request schema for arterial green wave progression offset calculation.
    Supports both snake_case and camelCase field aliases.
    """
    model_config = ConfigDict(populate_by_name=True)

    corridor_id: str = Field(default="CORRIDOR-NAGAR-ROAD", alias="corridorId", description="Corridor identifier")
    upstream_intersection_id: str = Field(..., alias="upstreamIntersectionId", description="Upstream intersection ID")
    downstream_intersection_id: str = Field(..., alias="downstreamIntersectionId", description="Downstream intersection ID")
    common_cycle_sec: int = Field(default=90, alias="commonCycleSec", ge=30, le=240, description="Common coordinated cycle length in seconds")
    downstream_queue_m: float = Field(default=0.0, alias="downstreamQueueMeters", ge=0.0, description="Downstream residual queue length in meters")
    progression_speed_kmh: float = Field(default=40.0, alias="progressionSpeedKmh", gt=0.0, le=120.0, description="Target design progression speed in km/h")
    distance_meters: Optional[float] = Field(default=None, alias="distanceMeters", gt=0.0, description="Optional explicit link distance override in meters")
    reverse_queue_m: float = Field(default=0.0, alias="reverseQueueMeters", ge=0.0, description="Reverse direction residual queue in meters")
    forward_weight: float = Field(default=0.5, alias="forwardWeight", ge=0.0, le=1.0, description="Weight for forward direction progression")
    reverse_weight: float = Field(default=0.5, alias="reverseWeight", ge=0.0, le=1.0, description="Weight for reverse direction progression")
    dissipation_speed_mps: float = Field(default=5.0, alias="dissipationSpeedMps", gt=0.0, description="Backward queue clearance wave dissipation speed in m/s")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True)


class ProgressionOffsetResult(BaseModel):
    """
    Standardized result for arterial green wave progression offset calculations.
    Maintains explicit separation between nominal, adjusted, and bidirectional metrics.
    """
    model_config = ConfigDict(populate_by_name=True)

    corridorId: str = Field(..., description="Corridor identifier")
    upstreamIntersectionId: str = Field(..., description="Upstream intersection identifier")
    downstreamIntersectionId: str = Field(..., description="Downstream intersection identifier")
    distanceMeters: float = Field(..., description="Link center-line distance in meters")
    commonCycleSec: int = Field(..., description="Common coordinated cycle length in seconds")
    progressionSpeedKmh: float = Field(..., description="Target progression speed in km/h")
    progressionSpeedMps: float = Field(..., description="Progression speed converted to m/s")
    nominalTravelTimeSec: float = Field(..., description="Nominal unconstrained travel time in seconds")
    nominalOffsetSec: float = Field(..., description="Nominal green wave offset in seconds")
    downstreamQueueMeters: float = Field(..., description="Residual downstream queue length in meters")
    effectiveDistanceMeters: float = Field(..., description="Effective link travel distance after queue deduction")
    effectiveTravelTimeSec: float = Field(..., description="Travel time to reach the back of the queue")
    dissipationSpeedMps: float = Field(default=5.0, description="Backward queue clearance wave speed in m/s")
    queueClearanceTimeSec: float = Field(..., description="Time required for downstream queue to dissipate")
    adjustedOffsetSec: float = Field(..., description="Queue clearance adjusted progression offset in seconds")
    coordinationMode: str = Field(..., description="Operational coordination mode: PROGRESSION_ACTIVE or QUEUE_FLUSH_REQUIRED")
    queueStorageRatio: float = Field(..., description="Downstream queue storage occupancy ratio Q / d")
    safetyStatus: str = Field(..., description="Safety validation envelope status")
    progressionSuspended: bool = Field(..., description="Whether progression is suspended due to spillback risk")
    forwardOffsetSec: float = Field(..., description="Ideal forward progression offset in seconds")
    reverseOffsetSec: float = Field(..., description="Ideal reverse progression offset in seconds")
    optimalCompromiseOffsetSec: float = Field(..., description="Optimal two-way compromise offset in seconds")
    forwardWeight: float = Field(default=0.5, description="Relative priority weight assigned to forward direction")
    reverseWeight: float = Field(default=0.5, description="Relative priority weight assigned to reverse direction")
    forwardEfficiency: float = Field(..., description="Forward progression efficiency between 0.0 and 1.0")
    reverseEfficiency: float = Field(..., description="Reverse progression efficiency between 0.0 and 1.0")
    bidirectionalEfficiency: float = Field(..., description="Composite weighted two-way progression efficiency between 0.0 and 1.0")
    bandwidthEfficiencyPct: float = Field(..., description="Progression bandwidth efficiency percentage")
    safetyAdvisory: str = Field(..., description="Advisory message for operators and controllers")
    advisoryStatus: str = Field(default="REQUIRES_HUMAN_APPROVAL", description="Governance compliance status")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Standardized provenance metadata")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True)


class CorridorCoordinationPlan(BaseModel):
    """
    Corridor-wide coordination plan covering multiple sequential junctions.
    """
    model_config = ConfigDict(populate_by_name=True)

    corridorId: str = Field(..., description="Corridor identifier")
    corridorName: str = Field(..., description="Descriptive corridor name")
    generatedAt: str = Field(..., description="ISO 8601 generation timestamp")
    commonCycleSec: int = Field(..., description="Common cycle length in seconds")
    progressionSpeedKmh: float = Field(..., description="Progression design speed in km/h")
    totalLengthMeters: float = Field(..., description="Total coordinated corridor length in meters")
    intersections: List[str] = Field(..., description="Ordered list of coordinated intersection IDs")
    links: List[ProgressionOffsetResult] = Field(..., description="List of progression offset results for consecutive links")
    networkBidirectionalEfficiency: float = Field(..., description="Overall corridor two-way efficiency between 0.0 and 1.0")
    networkBandwidthEfficiencyPct: float = Field(..., description="Overall corridor bandwidth efficiency percentage")
    overallSafetyStatus: str = Field(..., description="Corridor-wide safety status")
    coordinationMode: str = Field(..., description="Corridor-wide coordination mode")
    advisoryStatus: str = Field(default="REQUIRES_HUMAN_APPROVAL", description="Governance compliance status")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Standardized provenance metadata")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True)


def _circular_deviation(offset1: float, offset2: float, cycle: float) -> float:
    """Calculates the minimum circular deviation between two offsets on a cycle."""
    diff = abs(offset1 - offset2) % cycle
    return min(diff, cycle - diff)


def _directional_efficiency(offset: float, target_offset: float, cycle: float) -> float:
    """Calculates progression efficiency for a given target offset."""
    dev = _circular_deviation(offset, target_offset, cycle)
    return max(0.0, 1.0 - (2.0 * dev / cycle))


def _haversine_distance(coord1: List[float], coord2: List[float]) -> float:
    """Calculates geodesic distance in meters between two [lng, lat] coordinate pairs."""
    lng1, lat1 = coord1[0], coord1[1]
    lng2, lat2 = coord2[0], coord2[1]
    earth_radius_m = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return earth_radius_m * c


class ArterialProgressionCoordinator:
    """
    Arterial Two-Way Green Wave Progression and Offset Optimizer Engine.
    Implements:
    1. Nominal offset: theta = (d / v_prog) mod C in [0, C - 1] (or [0, C) float).
    2. Downstream queue clearance wave adjustment:
       d_eff = max(0, d - Q)
       t_eff = d_eff / v_prog
       t_clearance = Q / v_dissipation (v_dissipation = 5.0 m/s = 18 km/h)
       theta_adjusted = (t_eff - t_clearance) mod C in [0, C).
    3. Safety invariant:
       If Q / d > 0.65, set coordinationMode to 'QUEUE_FLUSH_REQUIRED',
       safetyStatus to 'QUEUE_SPILLBACK_RISK', and suspend progression.
       If Q / d <= 0.65, set coordinationMode to 'PROGRESSION_ACTIVE'
       and safetyStatus to 'ENVELOPE_VERIFIED'.
    4. Two-way bidirectional coordination efficiency weighting forward and reverse directions.
    5. Inter-junction distance resolution via spatial registry service / database topology with fallback to geometry.
    """

    DEFAULT_DISSIPATION_SPEED_MPS: float = 5.0
    QUEUE_STORAGE_SAFETY_THRESHOLD: float = 0.65
    FALLBACK_REFERENCE_DISTANCE_METERS: float = 850.0
    FALLBACK_GENERIC_DISTANCE_METERS: float = 800.0

    def __init__(self, registry_service: Optional[SpatialRegistryService] = None):
        self.spatial_service = registry_service or spatial_service

    @staticmethod
    def _normalize_node_id(identifier: Optional[str]) -> str:
        """Normalizes an intersection or junction identifier to a canonical key."""
        if not identifier:
            return ""
        cleaned = str(identifier).strip()
        if cleaned.startswith("urn:ngsi-ld:Intersection:"):
            cleaned = cleaned.replace("urn:ngsi-ld:Intersection:", "")
        if cleaned.startswith("PUNE:"):
            cleaned = cleaned.replace("PUNE:", "")
        if cleaned.startswith("INT-"):
            cleaned = cleaned[4:]
        return cleaned.upper()

    def resolve_link_distance(
        self,
        upstream_id: str,
        downstream_id: str,
        corridor_id: Optional[str] = None
    ) -> float:
        """
        Resolves the center-line distance between two signalized intersections.
        Resolution order:
        1. Exact segment match in spatial registry catalog (fromJunction, toJunction).
        2. Reverse segment match in spatial registry catalog (toJunction, fromJunction).
        3. Connected intersection departure and approach edge lookup.
        4. Geodesic Haversine distance between intersection coordinates.
        5. Reference corridor fallback (850.0m for Nagar Road pilot) or generic fallback (800.0m).
        """
        if not upstream_id or not downstream_id:
            raise ValueError("Upstream and downstream intersection identifiers must be non-empty strings.")

        up_norm = self._normalize_node_id(upstream_id)
        down_norm = self._normalize_node_id(downstream_id)

        if up_norm == down_norm:
            return 0.0

        try:
            cat = self.spatial_service.catalog
        except Exception as e:
            logger.warning("Spatial registry catalog unavailable during distance resolution: %s", e)
            cat = None

        if cat:
            # Step 1 & 2: Direct or reverse road segment mapping lookup
            for seg in cat.roadSegmentMappings:
                seg_from = self._normalize_node_id(seg.fromJunction)
                seg_to = self._normalize_node_id(seg.toJunction)
                if (seg_from == up_norm and seg_to == down_norm) or (seg_from == down_norm and seg_to == up_norm):
                    logger.debug("Resolved link distance %.1fm from segment %s", seg.lengthMeters, seg.segmentId)
                    return float(seg.lengthMeters)

            # Step 3: Intersection entity resolution and approach/departure edge intersection
            up_res = self.spatial_service.resolve_entity(upstream_id)
            down_res = self.spatial_service.resolve_entity(downstream_id)

            if up_res.spatialFound and down_res.spatialFound:
                up_dep = set(up_res.properties.get("departureEdges", []))
                down_app = set(down_res.properties.get("approachEdges", []))
                common_edges = up_dep.intersection(down_app)
                if common_edges:
                    edge_id = next(iter(common_edges))
                    for seg in cat.roadSegmentMappings:
                        if seg.sumoEdgeId == edge_id or seg.segmentId.endswith(edge_id):
                            logger.debug("Resolved link distance %.1fm via connected edge %s", seg.lengthMeters, edge_id)
                            return float(seg.lengthMeters)

                # Step 4: Geodesic Haversine distance between intersection coordinates
                if up_res.coordinates and down_res.coordinates:
                    calc_dist = _haversine_distance(up_res.coordinates, down_res.coordinates)
                    if calc_dist > 10.0:
                        logger.debug("Resolved link distance %.1fm via Haversine geometry", calc_dist)
                        return round(calc_dist, 1)

        # Step 5: Corridor specific fallback
        corr_upper = (corridor_id or "").upper()
        if "NAGAR" in corr_upper or (up_norm in ("VN-01", "SN-01") and down_norm in ("VN-01", "SN-01")):
            return self.FALLBACK_REFERENCE_DISTANCE_METERS

        return self.FALLBACK_GENERIC_DISTANCE_METERS

    @staticmethod
    def compute_bidirectional_efficiency(
        forward_target_offset: float,
        reverse_target_offset: float,
        common_cycle_sec: float,
        forward_weight: float = 0.5,
        reverse_weight: float = 0.5
    ) -> Tuple[float, float, float, float, float]:
        """
        Calculates the two-way progression efficiency and determines the optimal compromise offset.
        Returns:
            Tuple of (optimal_compromise_offset, forward_eff, reverse_eff, weighted_bidi_eff, pct_eff)
        """
        cycle = float(common_cycle_sec)
        w_sum = forward_weight + reverse_weight
        if w_sum <= 0.0:
            w_fwd = 0.5
            w_rev = 0.5
        else:
            w_fwd = forward_weight / w_sum
            w_rev = reverse_weight / w_sum

        fwd_target = forward_target_offset % cycle
        rev_target = reverse_target_offset % cycle

        # Candidates for optimal offset: target offsets, circular midpoints, and integer seconds
        candidates = [
            fwd_target,
            rev_target,
            ((fwd_target + rev_target) / 2.0) % cycle,
            ((fwd_target + rev_target + cycle) / 2.0) % cycle,
        ]
        # Include integer seconds on cycle to ensure coverage
        step = max(1, int(cycle // 90))
        for s in range(0, int(cycle), step):
            candidates.append(float(s))

        best_offset = fwd_target
        best_score = -1.0
        best_fwd_eff = 0.0
        best_rev_eff = 0.0

        for cand in candidates:
            cand_norm = cand % cycle
            eff_f = _directional_efficiency(cand_norm, fwd_target, cycle)
            eff_r = _directional_efficiency(cand_norm, rev_target, cycle)
            score = w_fwd * eff_f + w_rev * eff_r
            if score > best_score:
                best_score = score
                best_offset = cand_norm
                best_fwd_eff = eff_f
                best_rev_eff = eff_r

        best_score = max(0.0, min(1.0, best_score))
        return (
            round(best_offset, 2),
            round(best_fwd_eff, 4),
            round(best_rev_eff, 4),
            round(best_score, 4),
            round(best_score * 100.0, 1),
        )

    def calculate_progression_offset(
        self,
        upstream_intersection_id: Optional[Union[str, ProgressionRequest]] = None,
        downstream_intersection_id: Optional[str] = None,
        common_cycle_sec: int = 90,
        downstream_queue_m: float = 0.0,
        progression_speed_kmh: float = 40.0,
        distance_meters: Optional[float] = None,
        corridor_id: str = "CORRIDOR-NAGAR-ROAD",
        forward_weight: float = 0.5,
        reverse_weight: float = 0.5,
        reverse_queue_m: float = 0.0,
        dissipation_speed_mps: float = 5.0,
        request: Optional[ProgressionRequest] = None,
        **kwargs: Any
    ) -> ProgressionOffsetResult:
        """
        Calculates optimal progression offsets between sequential signalized junctions.
        Accepts either a ProgressionRequest object or explicit parameters.
        """
        # Unpack ProgressionRequest if passed as first parameter or keyword argument
        if isinstance(upstream_intersection_id, ProgressionRequest):
            req = upstream_intersection_id
        elif request is not None:
            req = request
        else:
            up_id = str(upstream_intersection_id or kwargs.get("upstream_id") or "")
            down_id = str(downstream_intersection_id or kwargs.get("downstream_id") or "")
            cycle = int(kwargs.get("common_cycle", common_cycle_sec))
            queue_m = float(kwargs.get("downstream_queue", downstream_queue_m))
            speed = float(kwargs.get("speed_kmh", progression_speed_kmh))
            dist = distance_meters if distance_meters is not None else kwargs.get("distance_m")
            corr = str(kwargs.get("corridor", corridor_id))
            w_fwd = float(kwargs.get("forward_weight", forward_weight))
            w_rev = float(kwargs.get("reverse_weight", reverse_weight))
            rev_q = float(kwargs.get("reverse_queue_m", reverse_queue_m))
            diss_speed = float(kwargs.get("dissipation_speed_mps", dissipation_speed_mps))

            req = ProgressionRequest(
                corridor_id=corr,
                upstream_intersection_id=up_id,
                downstream_intersection_id=down_id,
                common_cycle_sec=cycle,
                downstream_queue_m=queue_m,
                progression_speed_kmh=speed,
                distance_meters=float(dist) if dist is not None else None,
                reverse_queue_m=rev_q,
                forward_weight=w_fwd,
                reverse_weight=w_rev,
                dissipation_speed_mps=diss_speed,
            )

        # 1. Distance resolution
        if req.distance_meters is not None and req.distance_meters > 0.0:
            link_distance_m = float(req.distance_meters)
        else:
            link_distance_m = self.resolve_link_distance(
                upstream_id=req.upstream_intersection_id,
                downstream_id=req.downstream_intersection_id,
                corridor_id=req.corridor_id,
            )

        # Guard against degenerate zero/negative link distance
        if link_distance_m <= 0.0:
            link_distance_m = self.FALLBACK_GENERIC_DISTANCE_METERS

        cycle_sec = float(req.common_cycle_sec)
        v_prog_mps = float(req.progression_speed_kmh) / 3.6
        if v_prog_mps <= 0.0:
            raise ValueError("Progression speed must be greater than zero.")

        # 2. Nominal progression travel time and offset: theta = (d / v_prog) mod C in [0, C)
        nominal_travel_time_sec = link_distance_m / v_prog_mps
        nominal_offset_sec = nominal_travel_time_sec % cycle_sec

        # 3. Downstream queue clearance wave adjustment:
        #    d_eff = max(0, d - Q)
        #    t_eff = d_eff / v_prog
        #    t_clearance = Q / v_dissipation with v_dissipation = 5.0 m/s
        #    theta_adjusted = (t_eff - t_clearance) mod C in [0, C)
        effective_distance_m = max(0.0, link_distance_m - float(req.downstream_queue_m))
        effective_travel_time_sec = effective_distance_m / v_prog_mps
        v_dissipation = float(req.dissipation_speed_mps) if req.dissipation_speed_mps > 0.0 else self.DEFAULT_DISSIPATION_SPEED_MPS
        queue_clearance_time_sec = float(req.downstream_queue_m) / v_dissipation

        raw_adjusted_offset = (effective_travel_time_sec - queue_clearance_time_sec) % cycle_sec
        if raw_adjusted_offset < 0.0:
            raw_adjusted_offset += cycle_sec

        # 4. Safety invariant check:
        #    If Q / d > 0.65, set coordinationMode to 'QUEUE_FLUSH_REQUIRED',
        #    safetyStatus to 'QUEUE_SPILLBACK_RISK', and suspend progression.
        #    If Q / d <= 0.65, set coordinationMode to 'PROGRESSION_ACTIVE'
        #    and safetyStatus to 'ENVELOPE_VERIFIED'.
        queue_storage_ratio = float(req.downstream_queue_m) / link_distance_m
        if queue_storage_ratio > self.QUEUE_STORAGE_SAFETY_THRESHOLD:
            coordination_mode = "QUEUE_FLUSH_REQUIRED"
            safety_status = "QUEUE_SPILLBACK_RISK"
            progression_suspended = True
            safety_advisory = (
                "Downstream queue storage ratio exceeds 0.65 threshold. "
                "Green wave progression suspended. Upstream metering and queue-flush protocol required."
            )
        else:
            coordination_mode = "PROGRESSION_ACTIVE"
            safety_status = "ENVELOPE_VERIFIED"
            progression_suspended = False
            safety_advisory = (
                "Downstream queue storage ratio is within verified safety envelope (<= 0.65). "
                "Green wave progression active."
            )

        # 5. Reverse direction offset calculation
        effective_distance_rev_m = max(0.0, link_distance_m - float(req.reverse_queue_m))
        effective_travel_time_rev_sec = effective_distance_rev_m / v_prog_mps
        queue_clearance_rev_sec = float(req.reverse_queue_m) / v_dissipation
        raw_rev_travel = (effective_travel_time_rev_sec - queue_clearance_rev_sec) % cycle_sec
        if raw_rev_travel < 0.0:
            raw_rev_travel += cycle_sec
        reverse_target_offset = (cycle_sec - raw_rev_travel) % cycle_sec

        # 6. Two-way bidirectional coordination efficiency
        opt_offset, fwd_eff, rev_eff, bidi_eff, bidi_pct = self.compute_bidirectional_efficiency(
            forward_target_offset=raw_adjusted_offset,
            reverse_target_offset=reverse_target_offset,
            common_cycle_sec=cycle_sec,
            forward_weight=req.forward_weight,
            reverse_weight=req.reverse_weight,
        )

        if progression_suspended:
            bidi_eff = 0.0
            bidi_pct = 0.0
            fwd_eff = 0.0
            rev_eff = 0.0

        now_iso = datetime.now(timezone.utc).isoformat()
        provenance = {
            "sourceMode": "PREDICTED",
            "calculatedAt": now_iso,
            "timestamp": now_iso,
            "qualityScore": 1.0,
            "sourceDetail": "ArterialProgressionCoordinator",
            "method": "Modified Webster-Bandwidth Offset Optimization",
            "advisoryCompliance": "REQUIRES_HUMAN_APPROVAL",
        }

        return ProgressionOffsetResult(
            corridorId=req.corridor_id,
            upstreamIntersectionId=req.upstream_intersection_id,
            downstreamIntersectionId=req.downstream_intersection_id,
            distanceMeters=round(link_distance_m, 1),
            commonCycleSec=int(req.common_cycle_sec),
            progressionSpeedKmh=round(float(req.progression_speed_kmh), 1),
            progressionSpeedMps=round(v_prog_mps, 3),
            nominalTravelTimeSec=round(nominal_travel_time_sec, 2),
            nominalOffsetSec=round(nominal_offset_sec, 2),
            downstreamQueueMeters=round(float(req.downstream_queue_m), 1),
            effectiveDistanceMeters=round(effective_distance_m, 1),
            effectiveTravelTimeSec=round(effective_travel_time_sec, 2),
            dissipationSpeedMps=round(v_dissipation, 1),
            queueClearanceTimeSec=round(queue_clearance_time_sec, 2),
            adjustedOffsetSec=round(raw_adjusted_offset, 2),
            coordinationMode=coordination_mode,
            queueStorageRatio=round(queue_storage_ratio, 4),
            safetyStatus=safety_status,
            progressionSuspended=progression_suspended,
            forwardOffsetSec=round(raw_adjusted_offset, 2),
            reverseOffsetSec=round(reverse_target_offset, 2),
            optimalCompromiseOffsetSec=opt_offset,
            forwardWeight=round(req.forward_weight, 2),
            reverseWeight=round(req.reverse_weight, 2),
            forwardEfficiency=fwd_eff,
            reverseEfficiency=rev_eff,
            bidirectionalEfficiency=bidi_eff,
            bandwidthEfficiencyPct=bidi_pct,
            safetyAdvisory=safety_advisory,
            advisoryStatus="REQUIRES_HUMAN_APPROVAL",
            provenance=provenance,
        )

    def compute_corridor_coordination_plan(
        self,
        corridor_id: str = "CORRIDOR-NAGAR-ROAD",
        common_cycle_sec: int = 90,
        progression_speed_kmh: float = 40.0,
        intersections: Optional[List[str]] = None,
        downstream_queues: Optional[Dict[str, float]] = None,
        forward_weight: float = 0.5,
        reverse_weight: float = 0.5,
    ) -> CorridorCoordinationPlan:
        """
        Computes a comprehensive two-way progression coordination plan across all
        coordinated intersections along an arterial corridor.
        """
        # Resolve corridor intersection sequence
        if not intersections:
            corr_upper = corridor_id.upper()
            if "NAGAR" in corr_upper or "VN-SN" in corr_upper:
                nodes = ["INT-VN-01", "INT-SN-01"]
                corridor_name = "Nagar Road Arterial Reference Corridor"
            else:
                # Dynamic discovery from catalog
                try:
                    cat = self.spatial_service.catalog
                    nodes = [inter.sumoJunctionId for inter in cat.intersectionMappings]
                except Exception:
                    nodes = ["INT-VN-01", "INT-SN-01"]
                corridor_name = f"Arterial Corridor {corridor_id}"
        else:
            nodes = list(intersections)
            corridor_name = f"Coordinated Corridor {corridor_id}"

        queues = downstream_queues or {}
        links: List[ProgressionOffsetResult] = []
        total_length_m = 0.0

        for i in range(len(nodes) - 1):
            up = nodes[i]
            down = nodes[i + 1]
            q_m = float(queues.get(down, 0.0))
            link_res = self.calculate_progression_offset(
                upstream_intersection_id=up,
                downstream_intersection_id=down,
                common_cycle_sec=common_cycle_sec,
                downstream_queue_m=q_m,
                progression_speed_kmh=progression_speed_kmh,
                corridor_id=corridor_id,
                forward_weight=forward_weight,
                reverse_weight=reverse_weight,
            )
            links.append(link_res)
            total_length_m += link_res.distanceMeters

        # Overall corridor safety status and mode
        any_suspended = any(lnk.progressionSuspended for lnk in links)
        if any_suspended:
            overall_safety = "QUEUE_SPILLBACK_RISK"
            coordination_mode = "QUEUE_FLUSH_REQUIRED"
            network_efficiency = 0.0
            network_pct = 0.0
        else:
            overall_safety = "ENVELOPE_VERIFIED"
            coordination_mode = "PROGRESSION_ACTIVE"
            if links:
                network_efficiency = round(sum(lnk.bidirectionalEfficiency for lnk in links) / len(links), 4)
                network_pct = round(sum(lnk.bandwidthEfficiencyPct for lnk in links) / len(links), 1)
            else:
                network_efficiency = 1.0
                network_pct = 100.0

        now_iso = datetime.now(timezone.utc).isoformat()
        provenance = {
            "sourceMode": "PREDICTED",
            "calculatedAt": now_iso,
            "timestamp": now_iso,
            "qualityScore": 1.0,
            "sourceDetail": "ArterialProgressionCoordinator",
            "coordinationType": "Corridor Two-Way Arterial Green Wave",
            "advisoryCompliance": "REQUIRES_HUMAN_APPROVAL",
        }

        return CorridorCoordinationPlan(
            corridorId=corridor_id,
            corridorName=corridor_name,
            generatedAt=datetime.now(timezone.utc).isoformat(),
            commonCycleSec=common_cycle_sec,
            progressionSpeedKmh=progression_speed_kmh,
            totalLengthMeters=round(total_length_m, 1),
            intersections=nodes,
            links=links,
            networkBidirectionalEfficiency=network_efficiency,
            networkBandwidthEfficiencyPct=network_pct,
            overallSafetyStatus=overall_safety,
            coordinationMode=coordination_mode,
            advisoryStatus="REQUIRES_HUMAN_APPROVAL",
            provenance=provenance,
        )


# Exported singleton instance and canonical module aliases
arterial_coordinator = ArterialProgressionCoordinator()
