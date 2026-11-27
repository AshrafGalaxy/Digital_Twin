"""
energy_topology_service.py

Canonical Electrical Network Topology & Multi-Asset Telemetry Engine (Energy TASK-01).
Provides electrical distribution graph modeling, 3-phase AC power physics calculations,
diurnal solar generation modeling, BESS dispatch dynamics, EV charging simulation,
and corridor-wide microgrid power flow analytics.
"""

import asyncio
import json
import logging
import math
import random
import threading
import zoneinfo
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.database import AsyncSessionLocal, get_active_backend

logger = logging.getLogger("digital_twin.energy")


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Safely coerces untyped or heterogeneous dictionary values to float with explicit type narrowing."""
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        try:
            return float(val)
        except ValueError:
            return default
    return default


def get_local_civil_datetime(
    dt: Optional[datetime] = None,
    tz_name: Optional[str] = None
) -> datetime:
    """
    Converts a datetime to the local civil datetime for the study area.
    If dt is None, uses datetime.now(timezone.utc).
    If dt is naive, assumes UTC.
    Uses zoneinfo.ZoneInfo(tz_name or settings.STUDY_AREA_TIMEZONE) with fallback to
    timezone(timedelta(minutes=settings.CORRIDOR_UTC_OFFSET_MINUTES)).
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    target_tz_str = tz_name or settings.STUDY_AREA_TIMEZONE
    try:
        target_tz = zoneinfo.ZoneInfo(target_tz_str)
    except Exception as e:
        logger.warning(
            "Failed to load ZoneInfo for %s, falling back to CORRIDOR_UTC_OFFSET_MINUTES: %s",
            target_tz_str,
            e
        )
        target_tz = timezone(timedelta(minutes=settings.CORRIDOR_UTC_OFFSET_MINUTES))

    return dt.astimezone(target_tz)


def get_local_decimal_hour(
    dt: Optional[datetime] = None,
    tz_name: Optional[str] = None
) -> float:
    """
    Computes decimal hour of day (0.0 to 24.0) from the local civil datetime.
    """
    local_dt = get_local_civil_datetime(dt, tz_name)
    return local_dt.hour + local_dt.minute / 60.0 + local_dt.second / 3600.0 + local_dt.microsecond / 3600000000.0


class EnergyTopologyService:
    """
    Manages the multi-asset electrical distribution topology graph,
    real-time 3-phase AC power physics synthesis, and microgrid telemetry streaming.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._bess_soc_pct: float = 78.5
        self._ev_active_plugs: int = 6
        self._last_tick_time: datetime = datetime.now(timezone.utc)

    def get_local_civil_datetime(
        self,
        dt: Optional[datetime] = None,
        tz_name: Optional[str] = None
    ) -> datetime:
        return get_local_civil_datetime(dt, tz_name)

    def get_local_decimal_hour(
        self,
        dt: Optional[datetime] = None,
        tz_name: Optional[str] = None
    ) -> float:
        return get_local_decimal_hour(dt, tz_name)

    def calculate_ac_physics(
        self,
        active_power_kw: float,
        reactive_power_kvar: float,
        nominal_voltage_v: float,
        phase_count: int = 3
    ) -> Dict[str, float]:
        """
        Calculates 3-phase AC electrical properties:
        S = sqrt(P^2 + Q^2)
        PF = abs(P / S)
        I = (S * 1000) / (sqrt(3) * V)
        """
        p = active_power_kw
        q = reactive_power_kvar
        v = max(1.0, nominal_voltage_v)

        s = math.sqrt(p * p + q * q)
        pf = abs(p / s) if s > 1e-4 else 1.0
        pf = min(1.0, max(0.0, pf))

        if phase_count == 3:
            current_a = (s * 1000.0) / (math.sqrt(3.0) * v)
        else:
            current_a = (s * 1000.0) / v

        return {
            "activePowerKw": round(p, 2),
            "reactivePowerKvar": round(q, 2),
            "apparentPowerKva": round(s, 2),
            "powerFactor": round(pf, 3),
            "voltageV": round(v, 2),
            "currentA": round(current_a, 2)
        }

    def calculate_3phase_unbalance(
        self,
        active_power_kw: float,
        reactive_power_kvar: float,
        nominal_voltage_v: float,
        phase_count: int = 3
    ) -> Dict[str, Any]:
        """
        Calculates per-phase voltages, currents, and standard NEMA Voltage/Current
        Unbalance Rates (VUR/CUR).
        Guarantees that identical electrical inputs produce strictly identical,
        deterministic unbalance percentages without random noise.
        """
        if phase_count != 3:
            s = math.sqrt(active_power_kw**2 + reactive_power_kvar**2)
            v = max(1.0, nominal_voltage_v)
            i = (s * 1000.0) / v
            return {
                "voltageUnbalancePct": 0.0,
                "currentUnbalancePct": 0.0,
                "phaseVoltagesV": [round(v, 2)],
                "phaseCurrentsA": [round(i, 2)]
            }

        p_total = active_power_kw
        q_total = reactive_power_kvar
        v_nom = max(1.0, nominal_voltage_v)
        s_total = math.sqrt(p_total**2 + q_total**2)

        # Realistic deterministic network phase allocation shares:
        # Phase A: 33.8% active, 33.5% reactive
        # Phase B: 32.9% active, 33.2% reactive
        # Phase C: 33.3% active, 33.3% reactive
        shares_p = [0.338, 0.329, 0.333]
        shares_q = [0.335, 0.332, 0.333]

        phase_voltages: List[float] = []
        phase_currents: List[float] = []

        # Line-to-neutral nominal voltage: V_ln = V_ll / sqrt(3)
        v_ln_nom = v_nom / math.sqrt(3.0)

        # Slight deterministic impedance drop factors per phase
        v_drop_factors = [0.008, 0.012, 0.006]

        for idx in range(3):
            p_phi = p_total * shares_p[idx]
            q_phi = q_total * shares_q[idx]
            s_phi = math.sqrt(p_phi**2 + q_phi**2)

            # Line drop proportional to phase loading
            load_factor = (s_phi / max(0.1, s_total / 3.0)) if s_total > 1e-4 else 1.0
            v_phi = v_ln_nom * (1.0 - v_drop_factors[idx] * load_factor * 0.5)
            v_phi = max(1.0, v_phi)
            phase_voltages.append(round(v_phi, 2))

            # Phase current I_phi = (S_phi * 1000) / V_phi
            i_phi = (s_phi * 1000.0) / v_phi
            phase_currents.append(round(i_phi, 2))

        # NEMA Voltage Unbalance Rate (VUR):
        # VUR = (max(|V_phi - V_avg|) / V_avg) * 100
        v_avg = sum(phase_voltages) / 3.0
        v_max_dev = max(abs(v - v_avg) for v in phase_voltages)
        v_unbalance_pct = round((v_max_dev / v_avg) * 100.0, 2) if v_avg > 0 else 0.0

        # NEMA Current Unbalance Rate (CUR):
        # CUR = (max(|I_phi - I_avg|) / I_avg) * 100
        i_avg = sum(phase_currents) / 3.0
        if i_avg > 0.01:
            i_max_dev = max(abs(i - i_avg) for i in phase_currents)
            i_unbalance_pct = round((i_max_dev / i_avg) * 100.0, 2)
        else:
            i_unbalance_pct = 0.0

        return {
            "voltageUnbalancePct": v_unbalance_pct,
            "currentUnbalancePct": i_unbalance_pct,
            "phaseVoltagesV": phase_voltages,
            "phaseCurrentsA": phase_currents
        }

    def simulate_diurnal_solar_kw(
        self,
        rated_capacity_kwp: float,
        now: Optional[datetime] = None,
        tz_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Simulates diurnal rooftop solar generation based on solar zenith angle.
        Active generation peaks near 12:30 local civil time, with zero output between 18:30 and 06:12.
        """
        decimal_hour = self.get_local_decimal_hour(now, tz_name)

        sunrise = 6.2
        sunset = 18.5

        if decimal_hour < sunrise or decimal_hour > sunset:
            return {
                "activePowerKw": 0.0,
                "reactivePowerKvar": 0.0,
                "irradianceWm2": 0.0,
                "inverterEfficiencyPct": 0.0
            }

        solar_duration = sunset - sunrise
        progress = (decimal_hour - sunrise) / solar_duration
        sin_factor = math.sin(math.pi * progress)

        # Base clear-sky irradiance peaking at 1000 W/m^2
        cloud_factor = 0.95 + 0.05 * math.sin(decimal_hour * 3.5)
        irradiance_wm2 = max(0.0, 1000.0 * sin_factor * cloud_factor)

        # Inverter efficiency curve (peaks at 98.4%)
        efficiency_pct = 98.2 if irradiance_wm2 > 200.0 else (85.0 + 13.0 * (irradiance_wm2 / 200.0))
        active_kw = (irradiance_wm2 / 1000.0) * rated_capacity_kwp * (efficiency_pct / 100.0)

        # Smart inverters operate at near unity PF (slight inductive VAR for grid code)
        reactive_kvar = max(5.0, active_kw * 0.04)

        return {
            "activePowerKw": round(active_kw, 2),
            "reactivePowerKvar": round(reactive_kvar, 2),
            "irradianceWm2": round(irradiance_wm2, 1),
            "inverterEfficiencyPct": round(efficiency_pct, 2)
        }

    def simulate_building_load_kw(
        self,
        contract_demand_kw: float,
        category: str,
        now: Optional[datetime] = None,
        tz_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Simulates commercial building load profiles:
        Commercial retail/hospitality/office diurnal demand with HVAC and tenant usage.
        Driven by local civil time.
        """
        decimal_hour = self.get_local_decimal_hour(now, tz_name)

        if category == "COMMERCIAL_RETAIL":
            # Opens 10:00, peaks 14:00 - 20:30, closes 22:00
            if decimal_hour < 8.0:
                load_factor = 0.22  # Base lighting/security/chillers
            elif decimal_hour < 10.0:
                load_factor = 0.45  # Pre-cooling and staff prep
            elif decimal_hour < 21.0:
                load_factor = 0.65 + 0.25 * math.sin(math.pi * (decimal_hour - 10.0) / 11.0)
            else:
                load_factor = 0.35
        elif category == "COMMERCIAL_OFFICE":
            # Typical IT business park 08:30 - 18:30 with continuous data center baseload
            if decimal_hour < 7.0 or decimal_hour > 21.0:
                load_factor = 0.35  # Server rooms and emergency loads
            elif decimal_hour < 9.0:
                load_factor = 0.60
            elif decimal_hour < 18.0:
                load_factor = 0.82 + 0.08 * math.sin(math.pi * (decimal_hour - 9.0) / 9.0)
            else:
                load_factor = 0.48
        else:  # HOSPITALITY
            # Hotels: morning peak 07:00 - 10:00, evening banquet peak 18:30 - 23:00
            if decimal_hour < 6.0:
                load_factor = 0.38
            elif decimal_hour < 11.0:
                load_factor = 0.72
            elif decimal_hour < 17.0:
                load_factor = 0.58
            else:
                load_factor = 0.84

        active_kw = contract_demand_kw * load_factor
        # Commercial buildings operate at target PF 0.95 - 0.98 with capacitor banks
        pf = 0.96
        reactive_kvar = active_kw * math.tan(math.acos(pf))

        hvac_pct = 0.52
        lighting_pct = 0.23
        other_pct = 0.25

        return {
            "activePowerKw": round(active_kw, 2),
            "reactivePowerKvar": round(reactive_kvar, 2),
            "hvacLoadKw": round(active_kw * hvac_pct, 2),
            "lightingLoadKw": round(active_kw * lighting_pct, 2),
            "plugLoadKw": round(active_kw * other_pct, 2)
        }

    BESS_ROUND_TRIP_EFFICIENCY: float = 0.885
    BESS_USABLE_CAPACITY_KWH: float = 2000.0
    BESS_SOC_MIN_PCT: float = 15.0
    BESS_SOC_MAX_PCT: float = 95.0

    def simulate_bess_dynamics(
        self,
        solar_active_kw: float,
        hour: float = 12.0,
        dt_sec: float = 5.0,
        round_trip_efficiency: Optional[float] = None,
        now: Optional[datetime] = None,
        tz_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Simulates Battery Energy Storage System (BESS) charge/discharge logic:
        - Absorbs local rooftop solar when generation exceeds 400 kW and SOC < 92%.
        - Discharges to support corridor during evening peak (18:00 - 21:00) when SOC > 20%.
        - Standby floating mode otherwise with parasitic auxiliary losses.
        - Enforces physical round-trip efficiency: charge stores ac_in * sqrt(eta_rt),
          discharge removes ac_out / sqrt(eta_rt), and standby drains parasitic losses.
        """
        effective_hour = self.get_local_decimal_hour(now, tz_name) if now is not None else hour
        with self._lock:
            soc = self._bess_soc_pct

            # Mode selection
            if solar_active_kw > 400.0 and soc < 92.0:
                mode = "CHARGING"
                power_kw = -min(650.0, solar_active_kw * 0.55)
            elif 18.0 <= effective_hour <= 21.0 and soc > 22.0:
                mode = "DISCHARGING"
                power_kw = 550.0
            else:
                mode = "STANDBY"
                power_kw = -8.0  # Parasitic BMS and cooling losses

            usable_kwh = self.BESS_USABLE_CAPACITY_KWH
            eta_rt = round_trip_efficiency if round_trip_efficiency is not None else self.BESS_ROUND_TRIP_EFFICIENCY
            eta_one_way = math.sqrt(eta_rt) if eta_rt > 0 else 1.0
            dt_hours = dt_sec / 3600.0

            if mode == "CHARGING":
                ac_kwh_in = abs(power_kw) * dt_hours
                energy_delta_kwh = ac_kwh_in * eta_one_way
            elif mode == "DISCHARGING":
                ac_kwh_out = abs(power_kw) * dt_hours
                energy_delta_kwh = -(ac_kwh_out / eta_one_way)
            else:  # STANDBY
                parasitic_kwh = abs(power_kw) * dt_hours
                energy_delta_kwh = -parasitic_kwh

            new_soc = soc + (energy_delta_kwh / usable_kwh) * 100.0
            new_soc = min(self.BESS_SOC_MAX_PCT, max(self.BESS_SOC_MIN_PCT, new_soc))
            self._bess_soc_pct = round(new_soc, 2)

            reactive_kvar = 12.0

            return {
                "activePowerKw": round(power_kw, 2),
                "reactivePowerKvar": round(reactive_kvar, 2),
                "operatingMode": mode,
                "stateOfChargePct": self._bess_soc_pct,
                "usableCapacityKwh": usable_kwh,
                "roundTripEfficiency": round(eta_rt, 3)
            }

    def simulate_ev_hub_dynamics(
        self,
        hour: float = 12.0,
        total_plugs: int = 12,
        plug_capacity_kw: float = 60.0,
        now: Optional[datetime] = None,
        tz_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Simulates DC Fast-Charging Plaza dynamics with vehicle arrivals and charging pulses.
        Driven by local civil time.
        """
        effective_hour = self.get_local_decimal_hour(now, tz_name) if now is not None else hour
        with self._lock:
            # Vehicle arrivals rise in late afternoon and evening
            if 7.0 <= effective_hour <= 9.5:
                target_plugs = 5
            elif 12.0 <= effective_hour <= 14.5:
                target_plugs = 7
            elif 17.0 <= effective_hour <= 21.5:
                target_plugs = 10
            elif effective_hour > 23.0 or effective_hour < 6.0:
                target_plugs = 2
            else:
                target_plugs = 4

            # Slight random walk +/- 1 plug
            variation = random.choice([-1, 0, 0, 1])
            self._ev_active_plugs = max(1, min(total_plugs, target_plugs + variation))

            active_kw = self._ev_active_plugs * plug_capacity_kw * random.uniform(0.85, 0.98)
            # Modern DC fast chargers have active PFC with PF > 0.98
            pf = 0.985
            reactive_kvar = active_kw * math.tan(math.acos(pf))

            return {
                "activePowerKw": round(active_kw, 2),
                "reactivePowerKvar": round(reactive_kvar, 2),
                "activePlugs": self._ev_active_plugs,
                "totalPlugs": total_plugs,
                "utilizationRatePct": round((self._ev_active_plugs / total_plugs) * 100.0, 1),
                "smartThrottlingActive": False
            }

    async def get_topology_tree(self, session: Optional[AsyncSession] = None) -> Dict[str, Any]:
        """
        Returns the hierarchical single-line diagram graph:
        Substation -> Feeders -> Connected Distributed Energy Resources and Loads.
        """
        close_session = False
        if session is None:
            session = AsyncSessionLocal()
            close_session = True

        try:
            # Query all energy network nodes
            nodes_res = await session.execute(
                text("SELECT node_id, name, node_type, parent_node_id, nominal_voltage_kv, rated_capacity_kva, rated_current_amps, coordinates, properties FROM energy_network_nodes ORDER BY nominal_voltage_kv DESC, node_id ASC")
            )
            raw_nodes = nodes_res.fetchall()

            # Query latest telemetry for each node
            telem_res = await session.execute(
                text("""
                    SELECT t.asset_id, t.active_power_kw, t.reactive_power_kvar, t.apparent_power_kva,
                           t.power_factor, t.voltage_v, t.current_a, t.frequency_hz,
                           t.voltage_unbalance_pct, t.current_unbalance_pct, t.device_metrics_json,
                           t.observed_at, t.source_mode, t.quality_status
                    FROM energy_asset_telemetry t
                    INNER JOIN (
                        SELECT asset_id, MAX(id) AS max_id
                        FROM energy_asset_telemetry
                        GROUP BY asset_id
                    ) m ON t.id = m.max_id
                """)
            )
            telem_map: Dict[str, Any] = {}
            for row in telem_res.fetchall():
                metrics_raw = row[10]
                if isinstance(metrics_raw, str):
                    try:
                        metrics_dict = json.loads(metrics_raw)
                    except Exception:
                        metrics_dict = {}
                else:
                    metrics_dict = metrics_raw or {}

                obs_time = row[11].isoformat() if hasattr(row[11], "isoformat") else str(row[11])
                telem_map[row[0]] = {
                    "activePowerKw": float(row[1]),
                    "reactivePowerKvar": float(row[2]),
                    "apparentPowerKva": float(row[3]),
                    "powerFactor": float(row[4]),
                    "voltageV": float(row[5]),
                    "currentA": float(row[6]),
                    "frequencyHz": float(row[7]),
                    "voltageUnbalancePct": float(row[8]),
                    "currentUnbalancePct": float(row[9]),
                    "deviceMetrics": metrics_dict,
                    "observedAt": obs_time,
                    "sourceMode": row[12],
                    "qualityStatus": row[13]
                }

            # Assemble hierarchy
            nodes_by_id: Dict[str, Dict[str, Any]] = {}
            children_by_parent: Dict[str, List[Dict[str, Any]]] = {}

            for r in raw_nodes:
                nid = r[0]
                coords_raw = r[7]
                coords = json.loads(coords_raw) if isinstance(coords_raw, str) else (coords_raw or [])
                props_raw = r[8]
                props = json.loads(props_raw) if isinstance(props_raw, str) else (props_raw or {})

                telem = telem_map.get(nid, {
                    "activePowerKw": 0.0,
                    "reactivePowerKvar": 0.0,
                    "apparentPowerKva": 0.0,
                    "powerFactor": 1.0,
                    "voltageV": float(r[4]) * 1000.0,
                    "currentA": 0.0,
                    "frequencyHz": 50.00,
                    "voltageUnbalancePct": 0.40,
                    "currentUnbalancePct": 1.10,
                    "deviceMetrics": {},
                    "observedAt": datetime.now(timezone.utc).isoformat(),
                    "sourceMode": "SIMULATION",
                    "qualityStatus": "VALID"
                })

                rated_current = float(r[6])
                actual_current = telem.get("currentA", 0.0)
                loading_pct = round((actual_current / rated_current) * 100.0, 1) if rated_current > 0 else 0.0

                node_obj = {
                    "nodeId": nid,
                    "name": r[1],
                    "nodeType": r[2],
                    "parentNodeId": r[3],
                    "nominalVoltageKv": float(r[4]),
                    "ratedCapacityKva": float(r[5]),
                    "ratedCurrentAmps": rated_current,
                    "loadingPct": loading_pct,
                    "coordinates": coords,
                    "properties": props,
                    "telemetry": telem,
                    "children": []
                }
                nodes_by_id[nid] = node_obj

                pid = r[3]
                if pid:
                    children_by_parent.setdefault(pid, []).append(node_obj)

            # Link children into parent nodes
            root_nodes: List[Dict[str, Any]] = []
            for nid, node_obj in nodes_by_id.items():
                if nid in children_by_parent:
                    node_obj["children"] = children_by_parent[nid]
                if not node_obj.get("parentNodeId"):
                    root_nodes.append(node_obj)

            # Resolve active study area ID dynamically from spatial registry
            study_area_id = "urn:ngsi-ld:StudyArea:CORRIDOR"
            try:
                from backend.services.spatial_registry_service import spatial_service
                study_area_id = spatial_service.catalog.studyAreaId
            except Exception as e:
                logger.debug("Spatial registry study area resolution fallback: %s", e)

            return {
                "studyAreaId": study_area_id,
                "substation": root_nodes[0] if root_nodes else None,
                "totalNodes": len(raw_nodes),
                "generatedAt": datetime.now(timezone.utc).isoformat()
            }
        finally:
            if close_session:
                await session.close()

    async def get_live_telemetry(self, session: Optional[AsyncSession] = None) -> List[Dict[str, Any]]:
        """
        Returns flat latest 3-phase AC telemetry for all assets.
        """
        close_session = False
        if session is None:
            session = AsyncSessionLocal()
            close_session = True

        try:
            res = await session.execute(
                text("""
                    SELECT t.asset_id, n.name, n.node_type, n.nominal_voltage_kv,
                           n.rated_capacity_kva, n.rated_current_amps,
                           t.active_power_kw, t.reactive_power_kvar, t.apparent_power_kva,
                           t.power_factor, t.voltage_v, t.current_a, t.frequency_hz,
                           t.voltage_unbalance_pct, t.current_unbalance_pct,
                           t.device_metrics_json, t.observed_at, t.source_mode, t.quality_status
                    FROM energy_asset_telemetry t
                    JOIN energy_network_nodes n ON t.asset_id = n.node_id
                    INNER JOIN (
                        SELECT asset_id, MAX(id) AS max_id
                        FROM energy_asset_telemetry
                        GROUP BY asset_id
                    ) m ON t.id = m.max_id
                    ORDER BY t.asset_id ASC
                """)
            )
            items = []
            for r in res.fetchall():
                metrics_raw = r[15]
                metrics = json.loads(metrics_raw) if isinstance(metrics_raw, str) else (metrics_raw or {})
                obs_time = r[16].isoformat() if hasattr(r[16], "isoformat") else str(r[16])
                rated_current = float(r[5])
                actual_current = float(r[11])
                loading_pct = round((actual_current / rated_current) * 100.0, 1) if rated_current > 0 else 0.0

                items.append({
                    "assetId": r[0],
                    "name": r[1],
                    "nodeType": r[2],
                    "nominalVoltageKv": float(r[3]),
                    "ratedCapacityKva": float(r[4]),
                    "ratedCurrentAmps": rated_current,
                    "loadingPct": loading_pct,
                    "activePowerKw": float(r[6]),
                    "reactivePowerKvar": float(r[7]),
                    "apparentPowerKva": float(r[8]),
                    "powerFactor": float(r[9]),
                    "voltageV": float(r[10]),
                    "currentA": actual_current,
                    "frequencyHz": float(r[12]),
                    "voltageUnbalancePct": float(r[13]),
                    "currentUnbalancePct": float(r[14]),
                    "deviceMetrics": metrics,
                    "observedAt": obs_time,
                    "sourceMode": r[17],
                    "qualityStatus": r[18]
                })
            return items
        finally:
            if close_session:
                await session.close()

    async def get_microgrid_summary(self, session: Optional[AsyncSession] = None) -> Dict[str, Any]:
        """
        Calculates corridor-wide aggregate microgrid KPIs:
        Net Grid Import, Total Solar Generation, BESS Power & SOC, Total EV Power,
        Total Building Load, Net Corridor Power Factor, and Renewable Self-Consumption.
        """
        telemetry = await self.get_live_telemetry(session)

        solar_kw = 0.0
        bess_kw = 0.0
        ev_kw = 0.0
        building_kw = 0.0
        substation_kw = 0.0
        substation_kvar = 0.0
        bess_soc = self._bess_soc_pct

        for item in telemetry:
            nt = item["nodeType"]
            p = item["activePowerKw"]
            q = item["reactivePowerKvar"]

            if nt == "SUBSTATION":
                substation_kw += p
                substation_kvar += q
            elif nt == "SOLAR_PV":
                solar_kw += max(0.0, p)
            elif nt == "BESS":
                bess_kw += p
                bess_soc = item.get("deviceMetrics", {}).get("stateOfChargePct", self._bess_soc_pct)
            elif nt == "EV_HUB":
                ev_kw += p
            elif nt == "BUILDING_LOAD":
                building_kw += p

        # Net power factor at Substation Point of Common Coupling (PCC)
        s_net = math.sqrt(substation_kw * substation_kw + substation_kvar * substation_kvar)
        net_pf = round(abs(substation_kw / s_net), 3) if s_net > 0 else 0.98

        # Renewable self consumption
        total_generation = solar_kw + max(0.0, bess_kw)
        total_demand = building_kw + ev_kw + max(0.0, -bess_kw)
        self_consumption_pct = min(100.0, round((min(total_generation, total_demand) / max(1.0, total_generation)) * 100.0, 1)) if total_generation > 0 else 0.0

        # Carbon offset: ~0.82 kg CO2 / kWh from solar generation
        carbon_offset_kg_hr = round(solar_kw * 0.82, 1)

        return {
            "gridImportKw": round(substation_kw, 2),
            "solarGenerationKw": round(solar_kw, 2),
            "bessPowerKw": round(bess_kw, 2),
            "bessStateOfChargePct": round(bess_soc, 1),
            "evChargingLoadKw": round(ev_kw, 2),
            "buildingLoadKw": round(building_kw, 2),
            "netPowerFactor": net_pf,
            "renewableSelfConsumptionPct": self_consumption_pct,
            "carbonOffsetKgPerHour": carbon_offset_kg_hr,
            "sourceMode": "SIMULATION",
            "qualityStatus": "VALID",
            "observedAt": datetime.now(timezone.utc).isoformat()
        }

    def _compute_asset_telemetry_batch(
        self,
        *,
        db_nodes: List[Any],
        now_utc: datetime,
        grid_freq: float,
        obs_val: Any,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Builds physics readings and batch parameter dicts off the asyncio event loop."""
        decimal_hour = self.get_local_decimal_hour(now_utc)

        if db_nodes:
            endpoint_readings: Dict[str, Dict[str, Any]] = {}
            for r in db_nodes:
                nid, _name, ntype, _pid, v_kv, cap_kva, props_raw = (
                    r[0],
                    r[1],
                    r[2],
                    r[3],
                    float(r[4]),
                    float(r[5]),
                    r[6],
                )
                props = json.loads(props_raw) if isinstance(props_raw, str) else (props_raw or {})
                v_nom = v_kv * 1000.0 if v_kv > 0 else 415.0

                if ntype == "SOLAR_PV":
                    kwp = cap_kva if cap_kva > 0 else 1200.0
                    solar_data = self.simulate_diurnal_solar_kw(kwp, now_utc)
                    endpoint_readings[nid] = {
                        "id": nid,
                        "p": solar_data["activePowerKw"],
                        "q": solar_data["reactivePowerKvar"],
                        "v": v_nom,
                        "metrics": {
                            "irradianceWm2": solar_data["irradianceWm2"],
                            "inverterEfficiencyPct": solar_data["inverterEfficiencyPct"],
                        },
                    }
                elif ntype == "BUILDING_LOAD":
                    kw = cap_kva if cap_kva > 0 else 2500.0
                    cat = props.get("category", "COMMERCIAL_OFFICE")
                    bld = self.simulate_building_load_kw(kw, cat, now_utc)
                    endpoint_readings[nid] = {
                        "id": nid,
                        "p": bld["activePowerKw"],
                        "q": bld["reactivePowerKvar"],
                        "v": v_nom,
                        "metrics": {
                            "hvacLoadKw": bld["hvacLoadKw"],
                            "lightingLoadKw": bld["lightingLoadKw"],
                        },
                    }
                elif ntype == "BESS":
                    solar_p = next(
                        (ep["p"] for ep in endpoint_readings.values() if "irradianceWm2" in ep.get("metrics", {})),
                        600.0,
                    )
                    bess = self.simulate_bess_dynamics(solar_p, decimal_hour, 5.0, now=now_utc)
                    endpoint_readings[nid] = {
                        "id": nid,
                        "p": bess["activePowerKw"],
                        "q": bess["reactivePowerKvar"],
                        "v": v_nom,
                        "metrics": {
                            "operatingMode": bess["operatingMode"],
                            "stateOfChargePct": bess["stateOfChargePct"],
                        },
                    }
                elif ntype == "EV_HUB":
                    plugs = int(props.get("totalPlugs", 12))
                    plug_kw = float(props.get("plugCapacityKw", 60.0))
                    ev = self.simulate_ev_hub_dynamics(decimal_hour, plugs, plug_kw, now=now_utc)
                    endpoint_readings[nid] = {
                        "id": nid,
                        "p": ev["activePowerKw"],
                        "q": ev["reactivePowerKvar"],
                        "v": v_nom,
                        "metrics": {
                            "activePlugs": ev["activePlugs"],
                            "utilizationRatePct": ev["utilizationRatePct"],
                        },
                    }

            feeder_readings: Dict[str, Dict[str, Any]] = {}
            for r in db_nodes:
                nid, name, ntype, _pid, v_kv, cap_kva = r[0], r[1], r[2], r[3], float(r[4]), float(r[5])
                if ntype == "FEEDER":
                    v_nom = v_kv * 1000.0 if v_kv > 0 else 11000.0
                    fdr_p = 0.0
                    fdr_q = 0.0
                    for child in db_nodes:
                        if child[3] == nid and child[0] in endpoint_readings:
                            cp = float(endpoint_readings[child[0]]["p"])
                            cq = float(endpoint_readings[child[0]]["q"])
                            if child[2] in ("SOLAR_PV", "BESS"):
                                fdr_p -= cp
                            else:
                                fdr_p += cp
                            fdr_q += cq

                    cap_val = cap_kva if cap_kva > 0 else 5000.0
                    loading_pct = round(((abs(fdr_p) / cap_val) * 100.0), 1)
                    feeder_readings[nid] = {
                        "id": nid,
                        "p": fdr_p,
                        "q": fdr_q,
                        "v": v_nom,
                        "metrics": {"feederName": name, "feederLoadingPct": loading_pct},
                    }

            substation_readings: Dict[str, Dict[str, Any]] = {}
            for r in db_nodes:
                nid, _name, ntype, _pid, v_kv, _cap_kva = r[0], r[1], r[2], r[3], float(r[4]), float(r[5])
                if ntype == "SUBSTATION":
                    v_nom = v_kv * 1000.0 if v_kv > 0 else 22000.0
                    feeder_sum_p = sum(float(f["p"]) for f in feeder_readings.values())
                    sub_p = feeder_sum_p * 1.025
                    sub_q = sum(float(f["q"]) for f in feeder_readings.values()) * 1.035
                    transformer_loss_kw = round(sub_p - feeder_sum_p, 1)
                    substation_readings[nid] = {
                        "id": nid,
                        "p": sub_p,
                        "q": sub_q,
                        "v": v_nom,
                        "metrics": {
                            "powerDirection": "IMPORT" if sub_p >= 0 else "EXPORT",
                            "transformerLossKw": transformer_loss_kw,
                        },
                    }

            asset_readings = (
                list(substation_readings.values())
                + list(feeder_readings.values())
                + list(endpoint_readings.values())
            )
        else:
            solar_data = self.simulate_diurnal_solar_kw(1200.0, now_utc)
            bld_phoenix = self.simulate_building_load_kw(2500.0, "COMMERCIAL_RETAIL", now_utc)
            bess_data = self.simulate_bess_dynamics(solar_data["activePowerKw"], decimal_hour, 5.0, now=now_utc)
            bld_solitaire = self.simulate_building_load_kw(3000.0, "COMMERCIAL_OFFICE", now_utc)
            ev_data = self.simulate_ev_hub_dynamics(decimal_hour, 12, 60.0, now=now_utc)
            bld_hyatt = self.simulate_building_load_kw(1600.0, "HOSPITALITY", now_utc)

            fdr_a_p = bld_phoenix["activePowerKw"] - solar_data["activePowerKw"]
            fdr_a_q = bld_phoenix["reactivePowerKvar"] + solar_data["reactivePowerKvar"]
            fdr_b_p = bld_solitaire["activePowerKw"] - bess_data["activePowerKw"]
            fdr_b_q = bld_solitaire["reactivePowerKvar"] + bess_data["reactivePowerKvar"]
            fdr_c_p = bld_hyatt["activePowerKw"] + ev_data["activePowerKw"]
            fdr_c_q = bld_hyatt["reactivePowerKvar"] + ev_data["reactivePowerKvar"]

            feeder_sum_p = fdr_a_p + fdr_b_p + fdr_c_p
            sub_p = feeder_sum_p * 1.025
            sub_q = (fdr_a_q + fdr_b_q + fdr_c_q) * 1.035
            transformer_loss_kw = round(sub_p - feeder_sum_p, 1)

            asset_readings = [
                {"id": "SUB-NR-22KV", "p": sub_p, "q": sub_q, "v": 22000.0, "metrics": {"powerDirection": "IMPORT", "transformerLossKw": transformer_loss_kw}},
                {"id": "FDR-NR-RETAIL-11KV", "p": fdr_a_p, "q": fdr_a_q, "v": 11000.0, "metrics": {"feederName": "Feeder A - Retail", "feederLoadingPct": round(((fdr_a_p / 5000.0) * 100.0), 1)}},
                {"id": "FDR-NR-ENTERPRISE-11KV", "p": fdr_b_p, "q": fdr_b_q, "v": 11000.0, "metrics": {"feederName": "Feeder B - Enterprise", "feederLoadingPct": round(((fdr_b_p / 5000.0) * 100.0), 1)}},
                {"id": "FDR-NR-HOSPITALITY-11KV", "p": fdr_c_p, "q": fdr_c_q, "v": 11000.0, "metrics": {"feederName": "Feeder C - Hospitality", "feederLoadingPct": round(((fdr_c_p / 5000.0) * 100.0), 1)}},
                {"id": "AST-PV-PHOENIX-01", "p": solar_data["activePowerKw"], "q": solar_data["reactivePowerKvar"], "v": 415.0, "metrics": {"irradianceWm2": solar_data["irradianceWm2"], "inverterEfficiencyPct": solar_data["inverterEfficiencyPct"]}},
                {"id": "AST-BLD-PHOENIX-01", "p": bld_phoenix["activePowerKw"], "q": bld_phoenix["reactivePowerKvar"], "v": 415.0, "metrics": {"hvacLoadKw": bld_phoenix["hvacLoadKw"], "lightingLoadKw": bld_phoenix["lightingLoadKw"]}},
                {"id": "AST-BESS-SOLITAIRE-01", "p": bess_data["activePowerKw"], "q": bess_data["reactivePowerKvar"], "v": 415.0, "metrics": {"operatingMode": bess_data["operatingMode"], "stateOfChargePct": bess_data["stateOfChargePct"]}},
                {"id": "AST-BLD-SOLITAIRE-01", "p": bld_solitaire["activePowerKw"], "q": bld_solitaire["reactivePowerKvar"], "v": 415.0, "metrics": {"officeTenantsLoadKw": bld_solitaire["hvacLoadKw"]}},
                {"id": "AST-EV-HUB-01", "p": ev_data["activePowerKw"], "q": ev_data["reactivePowerKvar"], "v": 415.0, "metrics": {"activePlugs": ev_data["activePlugs"], "utilizationRatePct": ev_data["utilizationRatePct"]}},
                {"id": "AST-BLD-HYATT-01", "p": bld_hyatt["activePowerKw"], "q": bld_hyatt["reactivePowerKvar"], "v": 415.0, "metrics": {"hospitalityLoadKw": bld_hyatt["hvacLoadKw"]}},
            ]

        telemetry_rows: List[Dict[str, Any]] = []
        state_rows: List[Dict[str, Any]] = []
        generated_records: List[Dict[str, Any]] = []

        for r in asset_readings:
            p_kw = _safe_float(r.get("p"), 0.0)
            q_kvar = _safe_float(r.get("q"), 0.0)
            v_volts = _safe_float(r.get("v"), 415.0)
            ac = self.calculate_ac_physics(p_kw, q_kvar, v_volts, phase_count=3)
            unbalance = self.calculate_3phase_unbalance(p_kw, q_kvar, v_volts, phase_count=3)
            v_unbalance = unbalance["voltageUnbalancePct"]
            i_unbalance = unbalance["currentUnbalancePct"]

            raw_metrics = r.get("metrics")
            device_metrics = dict(raw_metrics) if isinstance(raw_metrics, dict) else {}
            device_metrics["phaseVoltagesV"] = unbalance["phaseVoltagesV"]
            device_metrics["phaseCurrentsA"] = unbalance["phaseCurrentsA"]
            metrics_json = json.dumps(device_metrics)

            telemetry_rows.append({
                "asset_id": r["id"],
                "observed_at": obs_val,
                "active_power_kw": ac["activePowerKw"],
                "reactive_power_kvar": ac["reactivePowerKvar"],
                "apparent_power_kva": ac["apparentPowerKva"],
                "power_factor": ac["powerFactor"],
                "voltage_v": ac["voltageV"],
                "current_a": ac["currentA"],
                "frequency_hz": grid_freq,
                "voltage_unbalance_pct": v_unbalance,
                "current_unbalance_pct": i_unbalance,
                "device_metrics_json": metrics_json,
            })

            state_payload = {
                "activePowerKw": ac["activePowerKw"],
                "reactivePowerKvar": ac["reactivePowerKvar"],
                "apparentPowerKva": ac["apparentPowerKva"],
                "powerFactor": ac["powerFactor"],
                "voltageV": ac["voltageV"],
                "currentA": ac["currentA"],
                "frequencyHz": grid_freq,
                "voltageUnbalancePct": v_unbalance,
                "currentUnbalancePct": i_unbalance,
                "deviceMetrics": device_metrics,
            }
            state_rows.append({
                "entity_id": r["id"],
                "observed_at": obs_val,
                "updated_at": obs_val,
                "metrics": json.dumps(state_payload),
            })

            generated_records.append({
                "assetId": r["id"],
                **ac,
                "frequencyHz": grid_freq,
                "voltageUnbalancePct": v_unbalance,
                "currentUnbalancePct": i_unbalance,
                "deviceMetrics": device_metrics,
                "observedAt": now_utc.isoformat(),
                "sourceMode": "SIMULATION",
                "qualityStatus": "VALID",
            })

        return telemetry_rows, state_rows, generated_records

    async def generate_telemetry_tick(
        self,
        session: Optional[AsyncSession] = None,
        commit: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Generates a fresh real-time telemetry tick across all canonical microgrid assets,
        updates entity_current_state, logs to energy_asset_telemetry, and returns records.
        """
        close_session = False
        if session is None:
            session = AsyncSessionLocal()
            close_session = True

        now_utc = datetime.now(timezone.utc)
        is_pg = get_active_backend() == "postgresql"
        grid_freq = round(50.0 + random.uniform(-0.06, 0.06), 2)
        obs_val = now_utc if is_pg else now_utc.isoformat()

        insert_stmt = text("""
            INSERT INTO energy_asset_telemetry (
                asset_id, observed_at, source_mode, active_power_kw,
                reactive_power_kvar, apparent_power_kva, power_factor,
                voltage_v, current_a, frequency_hz, voltage_unbalance_pct,
                current_unbalance_pct, device_metrics_json, quality_status
            ) VALUES (
                :asset_id, :observed_at, 'SIMULATION', :active_power_kw,
                :reactive_power_kvar, :apparent_power_kva, :power_factor,
                :voltage_v, :current_a, :frequency_hz, :voltage_unbalance_pct,
                :current_unbalance_pct, :device_metrics_json, 'VALID'
            );
        """)
        upsert_state = text("""
            INSERT INTO entity_current_state (
                entity_id, entity_type, source_mode, observed_at,
                updated_at, metrics, quality_status, freshness_seconds
            ) VALUES (
                :entity_id, 'EnergyAsset', 'SIMULATION', :observed_at,
                :updated_at, :metrics, 'VALID', 0.0
            )
            ON CONFLICT (entity_id) DO UPDATE SET
                entity_type = 'EnergyAsset',
                source_mode = 'SIMULATION',
                observed_at = EXCLUDED.observed_at,
                updated_at = EXCLUDED.updated_at,
                metrics = EXCLUDED.metrics,
                quality_status = 'VALID',
                freshness_seconds = 0.0
            WHERE (
                entity_current_state.source_mode NOT IN ('LIVE', 'REPLAY')
            );
        """)

        try:
            nodes_res = await session.execute(
                text(
                    "SELECT node_id, name, node_type, parent_node_id, nominal_voltage_kv, rated_capacity_kva, properties "
                    "FROM energy_network_nodes ORDER BY nominal_voltage_kv ASC, node_id ASC"
                )
            )
            db_nodes = list(nodes_res.fetchall())

            telemetry_rows, state_rows, generated_records = await asyncio.to_thread(
                self._compute_asset_telemetry_batch,
                db_nodes=db_nodes,
                now_utc=now_utc,
                grid_freq=grid_freq,
                obs_val=obs_val,
            )

            if telemetry_rows:
                await session.execute(insert_stmt, telemetry_rows)
            if state_rows:
                await session.execute(upsert_state, state_rows)

            if commit or close_session:
                await session.commit()
            return generated_records
        except Exception as e:
            logger.error("Energy telemetry tick generation failed: %s", e, exc_info=True)
            if commit or close_session:
                await session.rollback()
                return []
            raise
        finally:
            if close_session:
                await session.close()


energy_topology_service = EnergyTopologyService()
