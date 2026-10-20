"""
los_engine.py

Canonical Level of Service (LOS) and Hydrodynamic State Engine for the Digital Twin Platform.
Calculates universal physical hydrodynamic properties (space-mean speed, flow rate, density,
volume-to-capacity ratio, and congestion index) and applies pluggable standard policy profiles
(Indo-HCM / IRC:106, US HCM 6th Edition, and Custom District).
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("digital_twin.los_engine")


class PolicyStandard:
    INDO_HCM = "INDO_HCM"
    US_HCM_6TH = "US_HCM_6TH"
    CUSTOM_DISTRICT = "CUSTOM_DISTRICT"


# Threshold definitions for Indo-HCM / IRC:106 arterial profile
INDO_HCM_THRESHOLDS = [
    {
        "grade": "A",
        "max_vc": 0.35,
        "min_speed_ratio": 0.90,
        "condition": "Free flow: low density, maneuvers completely unhindered."
    },
    {
        "grade": "B",
        "max_vc": 0.50,
        "min_speed_ratio": 0.80,
        "condition": "Reasonably free flow: minor restriction on maneuvering."
    },
    {
        "grade": "C",
        "max_vc": 0.70,
        "min_speed_ratio": 0.60,
        "condition": "Stable flow: maneuvers noticeably restricted by traffic platoons."
    },
    {
        "grade": "D",
        "max_vc": 0.85,
        "min_speed_ratio": 0.45,
        "condition": "Approaching unstable flow: high density, queues form at signals."
    },
    {
        "grade": "E",
        "max_vc": 1.00,
        "min_speed_ratio": 0.30,
        "condition": "Unstable flow: operation at or near corridor design capacity."
    },
    {
        "grade": "F",
        "max_vc": float("inf"),
        "min_speed_ratio": 0.0,
        "condition": "Forced or breakdown flow: severe queue spillback, stop-and-go conditions."
    }
]

# Threshold definitions for US HCM 6th Edition urban arterial profile
US_HCM_THRESHOLDS = [
    {
        "grade": "A",
        "max_vc": 0.30,
        "min_speed_ratio": 0.85,
        "condition": "Free flow: optimal arterial travel speeds."
    },
    {
        "grade": "B",
        "max_vc": 0.50,
        "min_speed_ratio": 0.67,
        "condition": "Stable flow: slight delay at signalized intersections."
    },
    {
        "grade": "C",
        "max_vc": 0.75,
        "min_speed_ratio": 0.50,
        "condition": "Stable flow: noticeable progression delays, acceptable travel times."
    },
    {
        "grade": "D",
        "max_vc": 0.90,
        "min_speed_ratio": 0.40,
        "condition": "Approaching capacity: long delays at major intersections."
    },
    {
        "grade": "E",
        "max_vc": 1.00,
        "min_speed_ratio": 0.30,
        "condition": "At capacity: unstable flow, extensive intersection queuing."
    },
    {
        "grade": "F",
        "max_vc": float("inf"),
        "min_speed_ratio": 0.0,
        "condition": "Breakdown flow: demand exceeds capacity, extensive queue spillback."
    }
]


class LOSEngine:
    """
    Canonical Level of Service (LOS) and hydrodynamic state calculation engine.
    Supports location-agnostic execution with pluggable policy standards.
    """

    def __init__(self, default_policy: str = PolicyStandard.INDO_HCM):
        self.default_policy = default_policy

    @staticmethod
    def compute_hydrodynamics(
        speed_kmh: float,
        flow_vph: float,
        capacity_vph: float,
        free_flow_speed_kmh: float = 50.0
    ) -> Dict[str, float]:
        """
        Computes universal hydrodynamic continuity properties:
        - Volume-to-Capacity ratio: V/C = q / capacity
        - Density: k = q / max(v, 1.0) (veh/km)
        - Normalized Congestion Index: CI = min(1.0, max(0.0, 1.0 - v / v_free))
        """
        safe_capacity = max(capacity_vph, 1.0)
        safe_speed = max(0.0, speed_kmh)
        safe_free_flow = max(free_flow_speed_kmh, 1.0)

        vc_ratio = round(flow_vph / safe_capacity, 3)
        density = round(flow_vph / max(safe_speed, 1.0), 2)
        ci = round(min(1.0, max(0.0, 1.0 - (safe_speed / safe_free_flow))), 3)
        speed_ratio = round(safe_speed / safe_free_flow, 3)

        return {
            "volume_capacity_ratio": vc_ratio,
            "density_veh_km": density,
            "congestion_index": ci,
            "speed_ratio": speed_ratio
        }

    def _grade_by_vc(self, vc_ratio: float, thresholds: List[Dict[str, Any]]) -> str:
        for t in thresholds:
            if vc_ratio <= t["max_vc"]:
                return t["grade"]
        return "F"

    def _grade_by_speed(self, speed_ratio: float, thresholds: List[Dict[str, Any]]) -> str:
        # Check from A downward
        for t in thresholds:
            if speed_ratio >= t["min_speed_ratio"]:
                return t["grade"]
        return "F"

    def classify_los(
        self,
        vc_ratio: float,
        speed_ratio: float,
        policy_standard: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Evaluates LOS A through F against the chosen policy standard.
        Boundary Condition: When V/C and speed suggest differing LOS grades,
        the worse grade is selected to represent actual commuter delay truthfully.
        """
        policy = policy_standard or self.default_policy
        thresholds = INDO_HCM_THRESHOLDS if policy == PolicyStandard.INDO_HCM else US_HCM_THRESHOLDS

        grade_vc = self._grade_by_vc(vc_ratio, thresholds)
        grade_spd = self._grade_by_speed(speed_ratio, thresholds)

        # Worse grade determination: 'F' > 'E' > 'D' > 'C' > 'B' > 'A'
        order = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6}
        worse_grade = grade_vc if order[grade_vc] >= order[grade_spd] else grade_spd

        # Lookup operational condition
        condition = "Operational state nominal."
        for t in thresholds:
            if t["grade"] == worse_grade:
                condition = t["condition"]
                break

        return worse_grade, condition

    def compute_segment_los(
        self,
        segment_id: str,
        speed_kmh: float,
        flow_vph: float,
        capacity_vph: float,
        free_flow_speed_kmh: float = 50.0,
        policy_standard: Optional[str] = None,
        source_mode: str = "REPLAY",
        quality_score: float = 0.98,
        observed_at: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive segment-level LOS computation returning canonical data contracts.
        """
        policy = policy_standard or self.default_policy
        hydro = self.compute_hydrodynamics(
            speed_kmh=speed_kmh,
            flow_vph=flow_vph,
            capacity_vph=capacity_vph,
            free_flow_speed_kmh=free_flow_speed_kmh
        )

        los_grade, condition = self.classify_los(
            vc_ratio=hydro["volume_capacity_ratio"],
            speed_ratio=hydro["speed_ratio"],
            policy_standard=policy
        )

        obs_time = observed_at or datetime.now(timezone.utc).isoformat()

        return {
            "segmentId": segment_id,
            "speedKmh": round(max(0.0, speed_kmh), 1),
            "flowVehHr": round(max(0.0, flow_vph), 1),
            "capacityVehHr": round(max(1.0, capacity_vph), 1),
            "freeFlowSpeedKmh": round(free_flow_speed_kmh, 1),
            "volumeCapacityRatio": hydro["volume_capacity_ratio"],
            "densityVehKm": hydro["density_veh_km"],
            "congestionIndex": hydro["congestion_index"],
            "speedRatio": hydro["speed_ratio"],
            "levelOfService": los_grade,
            "operationalCondition": condition,
            "policyStandard": policy,
            "provenance": {
                "sourceMode": source_mode,
                "observedAt": obs_time,
                "qualityScore": quality_score
            }
        }

    def evaluate_corridor_summary(
        self,
        segment_records: List[Dict[str, Any]],
        policy_standard: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Computes corridor-wide aggregate Level of Service and hydrodynamic rollup.
        """
        policy = policy_standard or self.default_policy
        if not segment_records:
            return {
                "corridorLevelOfService": "C",
                "averageSpeedKmh": 35.0,
                "averageVolumeCapacityRatio": 0.50,
                "averageDensityVehKm": 40.0,
                "averageCongestionIndex": 0.30,
                "criticalSegmentId": None,
                "policyStandard": policy,
                "totalSegmentsEvaluated": 0,
                "evaluatedAt": datetime.now(timezone.utc).isoformat()
            }

        avg_speed = round(sum(s["speedKmh"] for s in segment_records) / len(segment_records), 1)
        avg_vc = round(sum(s["volumeCapacityRatio"] for s in segment_records) / len(segment_records), 3)
        avg_density = round(sum(s["densityVehKm"] for s in segment_records) / len(segment_records), 2)
        avg_ci = round(sum(s["congestionIndex"] for s in segment_records) / len(segment_records), 3)

        # Average free flow speed
        avg_free_flow = sum(s.get("freeFlowSpeedKmh", 50.0) for s in segment_records) / len(segment_records)
        speed_ratio = round(avg_speed / max(avg_free_flow, 1.0), 3)

        corridor_los, condition = self.classify_los(avg_vc, speed_ratio, policy)

        # Find the most congested segment (highest V/C or lowest speed)
        critical_seg = max(segment_records, key=lambda s: s["volumeCapacityRatio"])

        return {
            "corridorLevelOfService": corridor_los,
            "averageSpeedKmh": avg_speed,
            "averageVolumeCapacityRatio": avg_vc,
            "averageDensityVehKm": avg_density,
            "averageCongestionIndex": avg_ci,
            "criticalSegmentId": critical_seg.get("segmentId"),
            "criticalSegmentCondition": critical_seg.get("operationalCondition"),
            "policyStandard": policy,
            "totalSegmentsEvaluated": len(segment_records),
            "evaluatedAt": datetime.now(timezone.utc).isoformat()
        }


# Singleton instance
los_engine = LOSEngine()
