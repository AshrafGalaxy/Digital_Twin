"""
energy_topology_service.py

Canonical Electrical Network Topology & Multi-Asset Telemetry Engine (Energy TASK-01).
Provides electrical distribution graph modeling, 3-phase AC power physics calculations,
diurnal solar generation modeling, BESS dispatch dynamics, EV charging simulation,
and corridor-wide microgrid power flow analytics.
"""

import json
import logging
import math
import random
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import AsyncSessionLocal, get_active_backend

logger = logging.getLogger("digital_twin.energy")


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

    def simulate_diurnal_solar_kw(
        self,
        rated_capacity_kwp: float,
        now: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Simulates diurnal rooftop solar generation based on solar zenith angle.
        Active generation peaks near 12:30, with zero output between 19:00 and 06:00.
        """
        t = now or datetime.now(timezone.utc)
        decimal_hour = t.hour + t.minute / 60.0 + t.second / 3600.0

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
        now: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Simulates commercial building load profiles:
        Commercial retail/hospitality/office diurnal demand with HVAC and tenant usage.
        """
        t = now or datetime.now(timezone.utc)
        decimal_hour = t.hour + t.minute / 60.0 + t.second / 3600.0

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

    def simulate_bess_dynamics(
        self,
        solar_active_kw: float,
        hour: float,
        dt_sec: float = 5.0
    ) -> Dict[str, Any]:
        """
        Simulates Battery Energy Storage System (BESS) charge/discharge logic:
        - Absorbs local rooftop solar when generation exceeds 400 kW and SOC < 92%.
        - Discharges to support corridor during evening peak (18:00 - 21:00) when SOC > 20%.
        - Standby floating mode otherwise.
        """
        with self._lock:
            soc = self._bess_soc_pct

            # Mode selection
            if solar_active_kw > 400.0 and soc < 92.0:
                mode = "CHARGING"
                power_kw = -min(650.0, solar_active_kw * 0.55)
            elif 18.0 <= hour <= 21.0 and soc > 22.0:
                mode = "DISCHARGING"
                power_kw = 550.0
            else:
                mode = "STANDBY"
                power_kw = -8.0  # Parasitic BMS and cooling losses

            # Update SOC: 2000 kWh capacity
            usable_kwh = 2000.0
            energy_delta_kwh = (-power_kw * (dt_sec / 3600.0)) * 0.885  # Round trip efficiency
            new_soc = soc + (energy_delta_kwh / usable_kwh) * 100.0
            new_soc = min(95.0, max(15.0, new_soc))
            self._bess_soc_pct = round(new_soc, 2)

            reactive_kvar = 12.0

            return {
                "activePowerKw": round(power_kw, 2),
                "reactivePowerKvar": round(reactive_kvar, 2),
                "operatingMode": mode,
                "stateOfChargePct": self._bess_soc_pct,
                "usableCapacityKwh": usable_kwh
            }

    def simulate_ev_hub_dynamics(
        self,
        hour: float,
        total_plugs: int = 12,
        plug_capacity_kw: float = 60.0
    ) -> Dict[str, Any]:
        """
        Simulates DC Fast-Charging Plaza dynamics with vehicle arrivals and charging pulses.
        """
        with self._lock:
            # Vehicle arrivals rise in late afternoon and evening
            if 7.0 <= hour <= 9.5:
                target_plugs = 5
            elif 12.0 <= hour <= 14.5:
                target_plugs = 7
            elif 17.0 <= hour <= 21.5:
                target_plugs = 10
            elif hour > 23.0 or hour < 6.0:
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
                from backend.services.spatial_registry_service import spatial_registry_service
                study_area_id = spatial_registry_service.catalog.studyAreaId
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

    async def generate_telemetry_tick(self, session: Optional[AsyncSession] = None) -> List[Dict[str, Any]]:
        """
        Generates a fresh real-time telemetry tick across all canonical microgrid assets,
        updates entity_current_state, logs to energy_asset_telemetry, and returns records.
        """
        close_session = False
        if session is None:
            session = AsyncSessionLocal()
            close_session = True

        now_utc = datetime.now(timezone.utc)
        decimal_hour = now_utc.hour + now_utc.minute / 60.0 + now_utc.second / 3600.0
        is_pg = get_active_backend() == "postgresql"

        # Stochastic frequency drift around nominal 50.0 Hz (+/- 0.08 Hz)
        grid_freq = round(50.0 + random.uniform(-0.06, 0.06), 2)

        try:
            # 1. Simulate asset endpoints
            solar_data = self.simulate_diurnal_solar_kw(1200.0, now_utc)
            bld_phoenix = self.simulate_building_load_kw(2500.0, "COMMERCIAL_RETAIL", now_utc)
            bess_data = self.simulate_bess_dynamics(solar_data["activePowerKw"], decimal_hour, 5.0)
            bld_solitaire = self.simulate_building_load_kw(3000.0, "COMMERCIAL_OFFICE", now_utc)
            ev_data = self.simulate_ev_hub_dynamics(decimal_hour, 12, 60.0)
            bld_hyatt = self.simulate_building_load_kw(1600.0, "HOSPITALITY", now_utc)

            # 2. Feeder Aggregations
            # Feeder A (Retail & Solar)
            fdr_a_p = bld_phoenix["activePowerKw"] - solar_data["activePowerKw"]
            fdr_a_q = bld_phoenix["reactivePowerKvar"] + solar_data["reactivePowerKvar"]

            # Feeder B (Enterprise & BESS)
            # When BESS is discharging (power > 0), it offsets load
            fdr_b_p = bld_solitaire["activePowerKw"] - bess_data["activePowerKw"]
            fdr_b_q = bld_solitaire["reactivePowerKvar"] + bess_data["reactivePowerKvar"]

            # Feeder C (Hospitality & EV Hub)
            fdr_c_p = bld_hyatt["activePowerKw"] + ev_data["activePowerKw"]
            fdr_c_q = bld_hyatt["reactivePowerKvar"] + ev_data["reactivePowerKvar"]

            # Primary Substation (22kV)
            # Includes 2.5% transformer and line losses
            sub_p = (fdr_a_p + fdr_b_p + fdr_c_p) * 1.025
            sub_q = (fdr_a_q + fdr_b_q + fdr_c_q) * 1.035

            asset_readings = [
                {"id": "SUB-NR-22KV", "p": sub_p, "q": sub_q, "v": 22000.0, "metrics": {"powerDirection": "IMPORT", "transformerLossKw": round(sub_p * 0.025, 1)}},
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

            obs_val = now_utc if is_pg else now_utc.isoformat()
            generated_records = []

            for r in asset_readings:
                ac = self.calculate_ac_physics(r["p"], r["q"], r["v"], phase_count=3)
                v_unbalance = round(random.uniform(0.35, 0.65), 2)
                i_unbalance = round(random.uniform(0.95, 1.45), 2)
                metrics_json = json.dumps(r.get("metrics", {}))

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
                await session.execute(insert_stmt, {
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
                    "device_metrics_json": metrics_json
                })

                # Update entity_current_state for this asset
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
                        freshness_seconds = 0.0;
                """)
                state_payload = {
                    "activePowerKw": ac["activePowerKw"],
                    "reactivePowerKvar": ac["reactivePowerKvar"],
                    "apparentPowerKva": ac["apparentPowerKva"],
                    "powerFactor": ac["powerFactor"],
                    "voltageV": ac["voltageV"],
                    "currentA": ac["currentA"],
                    "frequencyHz": grid_freq,
                    "deviceMetrics": r.get("metrics", {})
                }
                await session.execute(upsert_state, {
                    "entity_id": r["id"],
                    "observed_at": obs_val,
                    "updated_at": obs_val,
                    "metrics": json.dumps(state_payload)
                })

                generated_records.append({
                    "assetId": r["id"],
                    **ac,
                    "frequencyHz": grid_freq,
                    "voltageUnbalancePct": v_unbalance,
                    "currentUnbalancePct": i_unbalance,
                    "deviceMetrics": r.get("metrics", {}),
                    "observedAt": now_utc.isoformat(),
                    "sourceMode": "SIMULATION",
                    "qualityStatus": "VALID"
                })

            await session.commit()
            return generated_records
        except Exception as e:
            logger.error("Energy telemetry tick generation failed: %s", e, exc_info=True)
            await session.rollback()
            return []
        finally:
            if close_session:
                await session.close()


energy_topology_service = EnergyTopologyService()
