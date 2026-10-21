"""
spat_adapter.py

Real-Time Signal Phase and Timing (SPaT) Controller Ingestion Adapter (TASK-08).
Parses high-frequency NTCIP 1202 and SAE J2735 signal state frames (1 to 10 Hz),
tracks active phase aspects and countdown timers, enforces freshness SLAs,
and archives phase transition history with strict state separation.
"""

from datetime import datetime, timezone
from enum import Enum
import json
import logging
import threading
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("digital_twin.services.spat_adapter")


class SignalColor(str, Enum):
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"
    FLASHING_YELLOW = "FLASHING_YELLOW"


class ControllerMode(str, Enum):
    PRETIMED = "PRETIMED"
    ACTUATED = "ACTUATED"
    COORDINATED = "COORDINATED"
    MANUAL = "MANUAL"
    EMERGENCY_PREEMPT = "EMERGENCY_PREEMPT"


class PhaseMovement(BaseModel):
    phase_id: int
    approach_id: str
    phase_name: str
    min_green_sec: float = 15.0
    allocated_green_sec: float = 25.0
    yellow_sec: float = 3.0
    all_red_sec: float = 2.0
    protected_turn: bool = True

    @property
    def total_stage_duration_sec(self) -> float:
        return self.allocated_green_sec + self.yellow_sec + self.all_red_sec


class SPaTPacket(BaseModel):
    """
    Validated inbound NTCIP 1202 / SAE J2735 normalized frame.
    """
    intersection_id: str = Field(..., description="Target intersection identifier or URN")
    timestamp: str = Field(..., description="Observation timestamp in ISO-8601 format")
    cycle_length_sec: int = Field(90, ge=40, le=240, description="Cycle time in seconds")
    elapsed_cycle_sec: float = Field(0.0, ge=0.0, description="Elapsed seconds within cycle")
    active_phase: int = Field(..., ge=1, le=8, description="Active signal phase ring (1-8)")
    active_phase_name: str = Field(..., description="Semantic approach name")
    phase_color: SignalColor = Field(..., description="Active aspect color")
    time_to_next_phase_sec: float = Field(..., ge=0.0, description="Remaining seconds in stage")
    preempt_status: str = Field("NONE", description="Emergency preemption status")
    controller_mode: ControllerMode = Field(ControllerMode.ACTUATED, description="Operating mode")
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Metadata provenance")

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp_format(cls, v: str) -> str:
        try:
            # Validate ISO format compatibility
            dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
            return dt.isoformat()
        except Exception:
            raise ValueError("Timestamp must be valid ISO-8601 string.")


class IntersectionSPaTState:
    """
    In-memory representation of an intersection real-time SPaT state.
    """
    def __init__(
        self,
        intersection_id: str,
        intersection_name: str,
        cycle_length_sec: int = 90,
        active_phase: int = 1,
        active_phase_name: str = "Major Arterial EB Through",
        phase_color: SignalColor = SignalColor.GREEN,
        time_to_next_phase_sec: float = 20.0,
        elapsed_cycle_sec: float = 0.0,
        controller_mode: ControllerMode = ControllerMode.ACTUATED,
        source_mode: str = "REPLAY",
        observed_at: Optional[str] = None
    ):
        self.intersection_id = intersection_id
        self.intersection_name = intersection_name
        self.cycle_length_sec = cycle_length_sec
        self.active_phase = active_phase
        self.active_phase_name = active_phase_name
        self.phase_color = phase_color
        self.time_to_next_phase_sec = time_to_next_phase_sec
        self.elapsed_cycle_sec = elapsed_cycle_sec
        self.controller_mode = controller_mode
        self.source_mode = source_mode
        self.observed_at = observed_at or datetime.now(timezone.utc).isoformat()
        self.last_heartbeat = datetime.now(timezone.utc)
        self.current_phase_start_time = datetime.now(timezone.utc)

    def evaluate_freshness(self, now: Optional[datetime] = None) -> Tuple[str, float]:
        """
        Evaluates SLA freshness threshold:
        latency <= 3.0s -> VALID
        3.0s < latency <= 10.0s -> STALE
        latency > 10.0s -> DISCONNECTED
        """
        curr = now or datetime.now(timezone.utc)
        latency_sec = max(0.0, (curr - self.last_heartbeat).total_seconds())
        if latency_sec <= 3.0:
            status = "VALID"
        elif latency_sec <= 10.0:
            status = "STALE"
        else:
            status = "DISCONNECTED"
        return status, latency_sec

    def to_dict(self, now: Optional[datetime] = None) -> Dict[str, Any]:
        freshness_status, latency_sec = self.evaluate_freshness(now)
        effective_source_mode = self.source_mode
        if freshness_status == "STALE":
            effective_source_mode = "STALE"

        return {
            "intersectionId": self.intersection_id,
            "intersectionName": self.intersection_name,
            "activePhase": self.active_phase,
            "activePhaseName": self.active_phase_name,
            "phaseColor": self.phase_color.value if isinstance(self.phase_color, SignalColor) else str(self.phase_color),
            "timeToNextPhaseSec": round(self.time_to_next_phase_sec, 1),
            "cycleLengthSec": self.cycle_length_sec,
            "elapsedCycleSec": round(self.elapsed_cycle_sec, 1),
            "controllerMode": self.controller_mode.value if isinstance(self.controller_mode, ControllerMode) else str(self.controller_mode),
            "freshnessStatus": freshness_status,
            "freshnessSeconds": round(latency_sec, 2),
            "observedAt": self.observed_at,
            "sourceMode": effective_source_mode,
            "provenance": {
                "sourceMode": effective_source_mode,
                "protocol": "SAE_J2735_SPAT",
                "qualityStatus": freshness_status,
                "freshnessThresholdSec": 3.0,
                "disconnectThresholdSec": 10.0
            }
        }


# Canonical phase movement definitions for reference intersections
CANONICAL_INTERSECTION_PHASES: Dict[str, List[PhaseMovement]] = {
    "urn:ngsi-ld:Intersection:PUNE:INT-VN-01": [
        PhaseMovement(phase_id=1, approach_id="APP-NR-EB", phase_name="Nagar Road EB Through + Right", min_green_sec=20.0, allocated_green_sec=25.0, yellow_sec=3.0, all_red_sec=2.0, protected_turn=True),
        PhaseMovement(phase_id=2, approach_id="APP-NR-WB", phase_name="Nagar Road WB Through", min_green_sec=20.0, allocated_green_sec=30.0, yellow_sec=3.0, all_red_sec=2.0, protected_turn=False),
        PhaseMovement(phase_id=3, approach_id="APP-VN-SB", phase_name="Viman Nagar Southbound Approach", min_green_sec=12.0, allocated_green_sec=15.0, yellow_sec=3.0, all_red_sec=2.0, protected_turn=True),
        PhaseMovement(phase_id=4, approach_id="APP-VN-NB", phase_name="Clover Park Northbound Approach", min_green_sec=10.0, allocated_green_sec=10.0, yellow_sec=3.0, all_red_sec=2.0, protected_turn=True),
    ],
    "urn:ngsi-ld:Intersection:PUNE:INT-SN-01": [
        PhaseMovement(phase_id=1, approach_id="APP-SN-EB", phase_name="Nagar Road EB Approach to Somnath", min_green_sec=20.0, allocated_green_sec=28.0, yellow_sec=3.0, all_red_sec=2.0, protected_turn=True),
        PhaseMovement(phase_id=2, approach_id="APP-SN-WB", phase_name="Nagar Road WB Approach from Somnath", min_green_sec=20.0, allocated_green_sec=28.0, yellow_sec=3.0, all_red_sec=2.0, protected_turn=False),
        PhaseMovement(phase_id=3, approach_id="APP-SN-NB", phase_name="Somnath Nagar Northbound Approach", min_green_sec=12.0, allocated_green_sec=14.0, yellow_sec=3.0, all_red_sec=2.0, protected_turn=True),
        PhaseMovement(phase_id=4, approach_id="APP-SN-SB", phase_name="Somnath Nagar Southbound Approach", min_green_sec=10.0, allocated_green_sec=11.0, yellow_sec=3.0, all_red_sec=2.0, protected_turn=True),
    ]
}


class SPaTAdapter:
    """
    Core SPaT Controller Ingestion and Normalization Engine.
    Manages in-memory state, transition detection, freshness SLA,
    database history persistence, and simulation tick generators.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._states: Dict[str, IntersectionSPaTState] = {}
        self._init_default_states()

    def _init_default_states(self):
        with self._lock:
            # Seed default intersections
            self._states["urn:ngsi-ld:Intersection:PUNE:INT-VN-01"] = IntersectionSPaTState(
                intersection_id="urn:ngsi-ld:Intersection:PUNE:INT-VN-01",
                intersection_name="Viman Nagar Chowk",
                cycle_length_sec=90,
                active_phase=1,
                active_phase_name="Nagar Road EB Through + Right",
                phase_color=SignalColor.GREEN,
                time_to_next_phase_sec=25.0,
                elapsed_cycle_sec=5.0,
                controller_mode=ControllerMode.ACTUATED,
                source_mode="SIMULATION"
            )
            self._states["urn:ngsi-ld:Intersection:PUNE:INT-SN-01"] = IntersectionSPaTState(
                intersection_id="urn:ngsi-ld:Intersection:PUNE:INT-SN-01",
                intersection_name="Somnath Nagar Chowk",
                cycle_length_sec=90,
                active_phase=2,
                active_phase_name="Nagar Road WB Approach from Somnath",
                phase_color=SignalColor.GREEN,
                time_to_next_phase_sec=18.0,
                elapsed_cycle_sec=35.0,
                controller_mode=ControllerMode.ACTUATED,
                source_mode="SIMULATION"
            )

    def get_current_spat(self, intersection_id: str, now: Optional[datetime] = None) -> IntersectionSPaTState:
        """
        Retrieves the current SPaT state for an intersection, resolving by exact ID or URN suffix.
        """
        with self._lock:
            state = self._states.get(intersection_id)
            if not state:
                # Suffix lookup
                for k, v in self._states.items():
                    if k.endswith(intersection_id) or intersection_id in k:
                        state = v
                        break

            if not state:
                # Dynamic initialization for new/unregistered intersection
                state = IntersectionSPaTState(
                    intersection_id=intersection_id,
                    intersection_name=f"Intersection {intersection_id}",
                    cycle_length_sec=90,
                    active_phase=1,
                    active_phase_name="Approach Movement 1",
                    phase_color=SignalColor.GREEN,
                    time_to_next_phase_sec=20.0,
                    source_mode="SIMULATION"
                )
                self._states[intersection_id] = state

            return state

    async def ingest_packet(
        self,
        raw_payload: Dict[str, Any],
        session: Optional[AsyncSession] = None
    ) -> IntersectionSPaTState:
        """
        Normalizes and ingests a raw SPaT packet.
        Validates schema, checks phase transitions, archives to signal_phase_history,
        and updates in-memory live state and entity_current_state.
        """
        packet = SPaTPacket(**raw_payload)
        now_dt = datetime.now(timezone.utc)
        parsed_obs_dt = datetime.fromisoformat(packet.timestamp.replace("Z", "+00:00"))

        with self._lock:
            current_state = self._states.get(packet.intersection_id)
            if not current_state:
                current_state = IntersectionSPaTState(
                    intersection_id=packet.intersection_id,
                    intersection_name=f"Intersection {packet.intersection_id}",
                    cycle_length_sec=packet.cycle_length_sec
                )
                self._states[packet.intersection_id] = current_state

            is_first_packet = not getattr(current_state, "_packet_received", False)
            current_state._packet_received = True

            # Detect phase transition only after initial packet calibration
            phase_transitioned = not is_first_packet and (
                current_state.active_phase != packet.active_phase or
                current_state.phase_color != packet.phase_color
            )

            prev_phase = current_state.active_phase
            prev_phase_name = current_state.active_phase_name
            prev_color = current_state.phase_color
            prev_start = current_state.current_phase_start_time

            # Update state attributes
            current_state.cycle_length_sec = packet.cycle_length_sec
            current_state.elapsed_cycle_sec = packet.elapsed_cycle_sec
            current_state.active_phase = packet.active_phase
            current_state.active_phase_name = packet.active_phase_name
            current_state.phase_color = packet.phase_color
            current_state.time_to_next_phase_sec = packet.time_to_next_phase_sec
            current_state.controller_mode = packet.controller_mode
            current_state.source_mode = packet.provenance.get("sourceMode", "LIVE")
            current_state.observed_at = packet.timestamp
            current_state.last_heartbeat = now_dt

            if phase_transitioned or is_first_packet:
                current_state.current_phase_start_time = parsed_obs_dt

        # If phase transitioned and DB session provided, log transition to signal_phase_history
        if phase_transitioned and session is not None:
            duration_sec = max(0.5, (parsed_obs_dt - prev_start).total_seconds())
            try:
                hist_stmt = text("""
                    INSERT INTO signal_phase_history (
                        intersection_id, phase_id, phase_name, color,
                        duration_sec, start_time, end_time, source_mode, quality_status
                    ) VALUES (
                        :intersection_id, :phase_id, :phase_name, :color,
                        :duration_sec, :start_time, :end_time, :source_mode, 'VALID'
                    )
                """)
                await session.execute(hist_stmt, {
                    "intersection_id": packet.intersection_id,
                    "phase_id": prev_phase,
                    "phase_name": prev_phase_name,
                    "color": prev_color.value if isinstance(prev_color, SignalColor) else str(prev_color),
                    "duration_sec": round(duration_sec, 2),
                    "start_time": prev_start.isoformat(),
                    "end_time": parsed_obs_dt.isoformat(),
                    "source_mode": current_state.source_mode
                })

                # Update entity_current_state for the intersection
                upsert_entity = text("""
                    INSERT INTO entity_current_state (
                        entity_id, entity_type, source_mode, observed_at,
                        updated_at, metrics, quality_status, freshness_seconds
                    ) VALUES (
                        :entity_id, 'TrafficSignal', :source_mode, :observed_at,
                        :updated_at, :metrics, 'VALID', 0.0
                    )
                    ON CONFLICT (entity_id) DO UPDATE SET
                        entity_type = 'TrafficSignal',
                        source_mode = EXCLUDED.source_mode,
                        observed_at = EXCLUDED.observed_at,
                        updated_at = EXCLUDED.updated_at,
                        metrics = EXCLUDED.metrics,
                        quality_status = 'VALID',
                        freshness_seconds = 0.0;
                """)
                metrics_payload = {
                    "activePhase": packet.active_phase,
                    "activePhaseName": packet.active_phase_name,
                    "phaseColor": packet.phase_color.value,
                    "timeToNextPhaseSec": packet.time_to_next_phase_sec,
                    "cycleLengthSec": packet.cycle_length_sec,
                    "controllerMode": packet.controller_mode.value
                }
                await session.execute(upsert_entity, {
                    "entity_id": packet.intersection_id,
                    "source_mode": current_state.source_mode,
                    "observed_at": packet.timestamp,
                    "updated_at": now_dt.isoformat(),
                    "metrics": json.dumps(metrics_payload)
                })

                await session.commit()
            except Exception as db_err:
                logger.warning("Could not persist SPaT phase transition to DB: %s", db_err)

        return current_state

    def generate_synthetic_tick(
        self,
        intersection_id: str,
        elapsed_delta_sec: float = 1.0,
        source_mode: str = "SIMULATION",
        **kwargs: Any
    ) -> IntersectionSPaTState:
        """
        Advances the virtual signal phase cycle for an intersection in simulation/replay modes.
        Computes stage intervals: Green -> Yellow -> All-Red -> Next Stage Green.
        """
        step_delta = kwargs.get("elapsed_seconds_delta", elapsed_delta_sec)
        phases = CANONICAL_INTERSECTION_PHASES.get(intersection_id)
        if not phases:
            # Match by suffix
            for k, v in CANONICAL_INTERSECTION_PHASES.items():
                if k.endswith(intersection_id) or intersection_id in k:
                    phases = v
                    break

        if not phases:
            # Generic 4-phase fallback
            phases = [
                PhaseMovement(phase_id=1, approach_id="APP-EB", phase_name="Eastbound Major Approach", allocated_green_sec=25.0),
                PhaseMovement(phase_id=2, approach_id="APP-WB", phase_name="Westbound Major Approach", allocated_green_sec=25.0),
                PhaseMovement(phase_id=3, approach_id="APP-NB", phase_name="Northbound Minor Approach", allocated_green_sec=15.0),
                PhaseMovement(phase_id=4, approach_id="APP-SB", phase_name="Southbound Minor Approach", allocated_green_sec=15.0),
            ]

        total_cycle = sum(p.total_stage_duration_sec for p in phases)

        with self._lock:
            state = self._states.get(intersection_id)
            if not state:
                state = IntersectionSPaTState(
                    intersection_id=intersection_id,
                    intersection_name=f"Intersection {intersection_id}",
                    cycle_length_sec=int(total_cycle),
                    source_mode=source_mode
                )
                self._states[intersection_id] = state

            # Advance elapsed cycle
            new_elapsed = (state.elapsed_cycle_sec + step_delta) % total_cycle
            state.elapsed_cycle_sec = new_elapsed
            state.cycle_length_sec = int(total_cycle)
            state.source_mode = source_mode
            now_dt = datetime.now(timezone.utc)
            state.observed_at = now_dt.isoformat()
            state.last_heartbeat = now_dt

            # Determine which phase and aspect corresponds to new_elapsed
            cumulative_t = 0.0
            found_phase = phases[0]
            aspect = SignalColor.GREEN
            countdown = 5.0

            for p in phases:
                green_end = cumulative_t + p.allocated_green_sec
                yellow_end = green_end + p.yellow_sec
                stage_end = yellow_end + p.all_red_sec

                if cumulative_t <= new_elapsed < stage_end:
                    found_phase = p
                    if new_elapsed < green_end:
                        aspect = SignalColor.GREEN
                        countdown = green_end - new_elapsed
                    elif new_elapsed < yellow_end:
                        aspect = SignalColor.YELLOW
                        countdown = yellow_end - new_elapsed
                    else:
                        aspect = SignalColor.RED
                        countdown = stage_end - new_elapsed
                    break

                cumulative_t = stage_end

            state.active_phase = found_phase.phase_id
            state.active_phase_name = found_phase.phase_name
            state.phase_color = aspect
            state.time_to_next_phase_sec = max(0.5, countdown)

            return state


# Global singleton instance
spat_adapter = SPaTAdapter()
