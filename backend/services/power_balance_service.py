"""
power_balance_service.py

Electrical Bus Power Balance & Feeder Thermal Loading Engine (Energy TASK-02).
Provides live node-by-node Kirchhoff active/reactive power conservation calculations,
branch conductor technical I^2*R loss modeling, and feeder ampacity thermal loading
margin evaluations (NOMINAL, WARNING, CRITICAL_OVERLOAD_RISK).
"""

import json
import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.constants import QualityStatus
from backend.core.database import AsyncSessionLocal, get_active_backend
from backend.services.energy_topology_service import energy_topology_service

logger = logging.getLogger("digital_twin.energy.power_balance")


def _subtree_ids(root_id: str, nodes_by_id: Dict[str, Dict[str, Any]]) -> set:
    """Node ids in the selected substation, including every descendant."""
    children: Dict[Optional[str], List[str]] = {}
    for nid, node in nodes_by_id.items():
        children.setdefault(node.get("parentNodeId"), []).append(nid)
    selected: set = set()
    stack = [root_id]
    while stack:
        current = stack.pop()
        if current in selected:
            continue
        selected.add(current)
        stack.extend(children.get(current, []))
    return selected


class PowerBalanceService:
    """
    Computes live electrical bus active and reactive power conservation,
    branch thermal ampacity loading margins, and technical distribution losses.
    """

    # Typical 3-phase medium/low voltage cable resistance benchmarks:
    # 300 mm^2 XLPE copper feeder: ~0.08 Ohm/km
    DEFAULT_FEEDER_RESISTANCE_OHM = 0.065
    DEFAULT_LINE_VOLTAGE_V = 415.0

    # Feeder thermal loading ratio thresholds
    THRESHOLD_WARNING = 0.75
    THRESHOLD_CRITICAL = 0.90

    def evaluate_feeder_thermal_status(self, loading_ratio: float) -> str:
        """
        Evaluates thermal ampacity status for a distribution branch:
        - ratio < 0.75: NOMINAL (Optimal operating zone)
        - 0.75 <= ratio < 0.90: WARNING (Elevated thermal loading, headroom shrinking)
        - ratio >= 0.90: CRITICAL_OVERLOAD_RISK (High thermal risk, trigger operator advisory)
        """
        if loading_ratio >= self.THRESHOLD_CRITICAL:
            return "CRITICAL_OVERLOAD_RISK"
        elif loading_ratio >= self.THRESHOLD_WARNING:
            return "WARNING"
        return "NOMINAL"

    def calculate_branch_loss_kw(
        self,
        current_amps: float,
        resistance_ohm: float = DEFAULT_FEEDER_RESISTANCE_OHM
    ) -> float:
        """
        Calculates 3-phase technical line distribution loss:
        P_loss = 3 * I^2 * R / 1000 (in kW)
        """
        loss_watts = 3.0 * (current_amps ** 2) * resistance_ohm
        return round(loss_watts / 1000.0, 2)

    def calculate_headroom_kw(
        self,
        rated_current_amps: float,
        actual_current_amps: float,
        line_voltage_v: Optional[float] = None,
        power_factor: float = 0.95,
        nominal_voltage_kv: Optional[float] = None,
    ) -> float:
        """
        Calculates available active power capacity headroom before reaching thermal ampacity rating:
        Headroom = sqrt(3) * V_line * max(0, I_rated - I_actual) * PF / 1000 (in kW)
        When line_voltage_v is omitted or <= 0, falls back to nominal_voltage_kv * 1000.0,
        and finally to DEFAULT_LINE_VOLTAGE_V (415.0 V).
        """
        if line_voltage_v is not None and line_voltage_v > 0.0:
            v_line = line_voltage_v
        elif nominal_voltage_kv is not None and nominal_voltage_kv > 0.0:
            v_line = nominal_voltage_kv * 1000.0
        else:
            v_line = self.DEFAULT_LINE_VOLTAGE_V

        delta_i = max(0.0, rated_current_amps - actual_current_amps)
        headroom_kw = (math.sqrt(3.0) * v_line * delta_i * power_factor) / 1000.0
        return round(headroom_kw, 1)

    async def calculate_power_balance(
        self,
        substation_id: Optional[str] = None,
        session: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Evaluates live Kirchhoff active power conservation and branch thermal margins
        across the active microgrid topology:
        P_grid + P_solar + P_bess = P_loads + P_losses
        """
        close_session = False
        if session is None:
            session = AsyncSessionLocal()
            close_session = True

        try:
            # 1. Fetch latest telemetry and registered nodes
            telemetry_list = await energy_topology_service.get_live_telemetry(session=session)
            nodes_res = await session.execute(
                text("SELECT node_id, name, node_type, parent_node_id, nominal_voltage_kv, rated_capacity_kva, rated_current_amps, properties FROM energy_network_nodes ORDER BY node_id ASC")
            )
            raw_nodes = nodes_res.fetchall()

            # Build map by asset ID
            telem_by_id: Dict[str, Dict[str, Any]] = {t["assetId"]: t for t in telemetry_list}
            nodes_by_id: Dict[str, Any] = {
                r[0]: {
                    "nodeId": r[0],
                    "name": r[1],
                    "nodeType": r[2],
                    "parentNodeId": r[3],
                    "nominalVoltageKv": float(r[4]),
                    "ratedCapacityKva": float(r[5]),
                    "ratedCurrentAmps": float(r[6]),
                    "properties": json.loads(r[7]) if isinstance(r[7], str) else (r[7] or {})
                }
                for r in raw_nodes
            }

            # 2. The requested substation is the only bus that is evaluated.
            substation_ids = [
                nid for nid, node in nodes_by_id.items() if node["nodeType"] == "SUBSTATION"
            ]
            if substation_id:
                if substation_id not in substation_ids:
                    raise LookupError("No substation is registered for this identifier")
                active_substation_id = substation_id
            elif len(substation_ids) == 1:
                active_substation_id = substation_ids[0]
            elif not substation_ids:
                raise LookupError("No substation is registered for this identifier")
            else:
                raise ValueError("substation_id is required when more than one substation is registered")

            selected_ids = _subtree_ids(active_substation_id, nodes_by_id)
            grid_telem = telem_by_id.get(active_substation_id)
            grid_meter_missing = grid_telem is None
            p_grid_import = 0.0 if grid_meter_missing else float(grid_telem.get("activePowerKw", 0.0))
            p_solar = 0.0
            p_bess_net = 0.0
            p_loads_total = 0.0

            for nid in selected_ids:
                node = nodes_by_id[nid]
                telem = telem_by_id.get(nid, {})
                p_val = float(telem.get("activePowerKw", 0.0))
                ntype = node["nodeType"]
                if ntype == "SOLAR_PV":
                    p_solar += p_val
                elif ntype == "BESS":
                    # Discharging is a source. Charging is a sink.
                    p_bess_net += p_val
                elif ntype in ("BUILDING_LOAD", "EV_HUB"):
                    p_loads_total += p_val

            # 3. Evaluate feeder thermal loading and branch losses
            feeders_data: List[Dict[str, Any]] = []
            total_losses_kw = 0.0
            max_loading_ratio = 0.0
            critical_feeder_id: Optional[str] = None

            for nid, node in nodes_by_id.items():
                if nid not in selected_ids or node["nodeType"] != "FEEDER":
                    continue
                telem = telem_by_id.get(nid, {})
                actual_current = float(telem.get("currentA", 0.0))
                rated_current = max(1.0, float(node["ratedCurrentAmps"]))
                loading_ratio = round(actual_current / rated_current, 3)
                loading_pct = round(loading_ratio * 100.0, 1)

                if loading_ratio > max_loading_ratio:
                    max_loading_ratio = loading_ratio
                    critical_feeder_id = nid

                status = self.evaluate_feeder_thermal_status(loading_ratio)
                v_line = float(telem.get("voltageV") or (node["nominalVoltageKv"] * 1000.0))
                pf = max(0.1, float(telem.get("powerFactor") or 0.95))

                cable_length_m = float(node["properties"].get("cableLengthMeters", 750.0))
                resistance_ohm = round((cable_length_m / 1000.0) * self.DEFAULT_FEEDER_RESISTANCE_OHM, 4)
                branch_loss_kw = self.calculate_branch_loss_kw(actual_current, resistance_ohm)
                total_losses_kw += branch_loss_kw

                headroom_kw = self.calculate_headroom_kw(
                    rated_current,
                    actual_current,
                    line_voltage_v=v_line,
                    power_factor=pf,
                    nominal_voltage_kv=node["nominalVoltageKv"],
                )

                feeders_data.append({
                    "feederId": nid,
                    "name": node["name"],
                    "voltageKv": node["nominalVoltageKv"],
                    "currentAmps": round(actual_current, 1),
                    "ratedCurrentAmps": round(rated_current, 1),
                    "thermalLoadingRatio": loading_ratio,
                    "thermalLoadingPct": loading_pct,
                    "status": status,
                    "availableHeadroomKw": headroom_kw,
                    "activePowerKw": float(telem.get("activePowerKw", 0.0)),
                    "reactivePowerKvar": float(telem.get("reactivePowerKvar", 0.0)),
                    "apparentPowerKva": float(telem.get("apparentPowerKva", 0.0)),
                    "powerFactor": pf,
                    "cableLengthMeters": cable_length_m,
                    "conductorResistanceOhm": resistance_ohm,
                    "branchLossKw": branch_loss_kw
                })

            # Signed residual: positive means supply exceeds load.
            bess_discharge_kw = p_bess_net if p_bess_net > 0 else 0.0
            bess_charge_kw = abs(p_bess_net) if p_bess_net < 0 else 0.0
            total_sources_kw = p_grid_import + p_solar + bess_discharge_kw
            total_sinks_kw = p_loads_total + total_losses_kw + bess_charge_kw
            residual_kw = total_sources_kw - total_sinks_kw
            if abs(residual_kw) < 0.05:
                residual_kw = 0.0
            residual_kw = round(residual_kw, 2)

            throughput_kw = max(total_sources_kw, total_sinks_kw)
            residual_share = 0.0 if throughput_kw <= 0 else abs(residual_kw) / throughput_kw
            share_threshold = float(settings.POWER_BALANCE_RESIDUAL_SHARE_THRESHOLD)
            if grid_meter_missing or residual_share > share_threshold:
                quality_status = QualityStatus.DEGRADED.value
            else:
                quality_status = QualityStatus.VALID.value

            overall_thermal_status = self.evaluate_feeder_thermal_status(max_loading_ratio)

            return {
                "substationId": active_substation_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "pccGridImportKw": None if grid_meter_missing else round(p_grid_import, 2),
                "solarGenerationKw": round(p_solar, 2),
                "bessNetPowerKw": round(p_bess_net, 2),
                "facilityTotalLoadKw": round(p_loads_total, 2),
                "technicalLossesKw": round(total_losses_kw, 2),
                "powerBalanceResidualKw": residual_kw,
                "residualShare": round(residual_share, 4),
                "residualShareThreshold": share_threshold,
                "gridMeterStatus": "MISSING" if grid_meter_missing else "MEASURED",
                "maxFeederLoadingRatio": round(max_loading_ratio, 3),
                "criticalFeederId": critical_feeder_id,
                "thermalAlertStatus": overall_thermal_status,
                "feeders": feeders_data,
                "provenance": {
                    "sourceMode": "SIMULATION",
                    "solverMethod": "KIRCHHOFF_POWER_CONSERVATION",
                    "qualityStatus": quality_status
                }
            }
        finally:
            if close_session:
                await session.close()

    async def record_power_balance_snapshot(
        self,
        substation_id: Optional[str] = None,
        session: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Calculates power balance and persists an authoritative snapshot to Table 34 (energy_power_balance_history).
        """
        close_session = False
        if session is None:
            session = AsyncSessionLocal()
            close_session = True

        try:
            snapshot = await self.calculate_power_balance(substation_id=substation_id, session=session)
            now_utc = datetime.now(timezone.utc)
            is_pg = get_active_backend() == "postgresql"

            if is_pg:
                stmt = text("""
                    INSERT INTO energy_power_balance_history (
                        observed_at, substation_id, grid_import_kw, solar_generation_kw,
                        bess_net_power_kw, facility_total_load_kw, technical_losses_kw,
                        power_balance_residual_kw, feeder_metrics_json, max_feeder_loading_ratio,
                        critical_feeder_id, thermal_alert_status, source_mode, quality_status
                    ) VALUES (
                        :observed_at, :substation_id, :grid_import_kw, :solar_generation_kw,
                        :bess_net_power_kw, :facility_total_load_kw, :technical_losses_kw,
                        :power_balance_residual_kw, :feeder_metrics_json, :max_feeder_loading_ratio,
                        :critical_feeder_id, :thermal_alert_status, :source_mode, :quality_status
                    )
                """)
            else:
                stmt = text("""
                    INSERT INTO energy_power_balance_history (
                        observed_at, substation_id, grid_import_kw, solar_generation_kw,
                        bess_net_power_kw, facility_total_load_kw, technical_losses_kw,
                        power_balance_residual_kw, feeder_metrics_json, max_feeder_loading_ratio,
                        critical_feeder_id, thermal_alert_status, source_mode, quality_status
                    ) VALUES (
                        :observed_at, :substation_id, :grid_import_kw, :solar_generation_kw,
                        :bess_net_power_kw, :facility_total_load_kw, :technical_losses_kw,
                        :power_balance_residual_kw, :feeder_metrics_json, :max_feeder_loading_ratio,
                        :critical_feeder_id, :thermal_alert_status, :source_mode, :quality_status
                    )
                """)

            await session.execute(stmt, {
                "observed_at": now_utc,
                "substation_id": snapshot["substationId"],
                "grid_import_kw": snapshot["pccGridImportKw"] if snapshot["pccGridImportKw"] is not None else 0.0,
                "solar_generation_kw": snapshot["solarGenerationKw"],
                "bess_net_power_kw": snapshot["bessNetPowerKw"],
                "facility_total_load_kw": snapshot["facilityTotalLoadKw"],
                "technical_losses_kw": snapshot["technicalLossesKw"],
                "power_balance_residual_kw": snapshot["powerBalanceResidualKw"],
                "feeder_metrics_json": json.dumps(snapshot["feeders"]),
                "max_feeder_loading_ratio": snapshot["maxFeederLoadingRatio"],
                "critical_feeder_id": snapshot["criticalFeederId"],
                "thermal_alert_status": snapshot["thermalAlertStatus"],
                "source_mode": snapshot["provenance"]["sourceMode"],
                "quality_status": snapshot["provenance"]["qualityStatus"]
            })
            await session.commit()
            return snapshot
        finally:
            if close_session:
                await session.close()

    async def get_feeder_thermal_margins(
        self,
        substation_id: Optional[str] = None,
        session: Optional[AsyncSession] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves feeder branch thermal ampacity loading margins and available headroom.
        """
        balance = await self.calculate_power_balance(substation_id=substation_id, session=session)
        return balance.get("feeders", [])

    async def get_power_balance_history(
        self,
        substation_id: Optional[str] = None,
        limit: int = 50,
        session: Optional[AsyncSession] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves historical power balance snapshots from Table 34.
        """
        close_session = False
        if session is None:
            session = AsyncSessionLocal()
            close_session = True

        try:
            query = """
                SELECT id, observed_at, substation_id, grid_import_kw, solar_generation_kw,
                       bess_net_power_kw, facility_total_load_kw, technical_losses_kw,
                       power_balance_residual_kw, feeder_metrics_json, max_feeder_loading_ratio,
                       critical_feeder_id, thermal_alert_status, source_mode, quality_status
                FROM energy_power_balance_history
            """
            params: Dict[str, Any] = {"limit": limit}
            if substation_id:
                query += " WHERE substation_id = :substation_id"
                params["substation_id"] = substation_id
            query += " ORDER BY observed_at DESC LIMIT :limit"

            res = await session.execute(text(query), params)
            rows = res.fetchall()

            history: List[Dict[str, Any]] = []
            for r in rows:
                feeders_raw = r[9]
                feeders = json.loads(feeders_raw) if isinstance(feeders_raw, str) else (feeders_raw or [])
                obs_time = r[1].isoformat() if hasattr(r[1], "isoformat") else str(r[1])
                history.append({
                    "id": r[0],
                    "observedAt": obs_time,
                    "substationId": r[2],
                    "gridImportKw": float(r[3]),
                    "solarGenerationKw": float(r[4]),
                    "bessNetPowerKw": float(r[5]),
                    "facilityTotalLoadKw": float(r[6]),
                    "technicalLossesKw": float(r[7]),
                    "powerBalanceResidualKw": float(r[8]),
                    "feeders": feeders,
                    "maxFeederLoadingRatio": float(r[10]),
                    "criticalFeederId": r[11],
                    "thermalAlertStatus": r[12],
                    "sourceMode": r[13],
                    "qualityStatus": r[14]
                })
            return history
        finally:
            if close_session:
                await session.close()


# Singleton instance
power_balance_service = PowerBalanceService()
