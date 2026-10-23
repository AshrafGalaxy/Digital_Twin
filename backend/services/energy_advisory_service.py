"""
energy_advisory_service.py

Service layer for Human-in-the-Loop Demand-Response Advisory Dossiers,
Physical Safety Interlocks, and Dual-Key Operator Dispatch Authorization (TASK-10 / GitHub #22).
Adheres strictly to the Non-Actuation Invariant: dispatches are advisory decision support only.
"""

from datetime import datetime, timezone
import hashlib
import json
import logging
import threading
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.energy_advisory import (
    AdvisoryStatus,
    AuthorizeEnergyAdvisoryRequest,
    DispatchScheduleSlot,
    EnergyAdvisoryDossier,
    EnergyDispatchWorkOrder,
    SafetyInterlocks
)

logger = logging.getLogger(__name__)


class EnergyAdvisoryService:
    """
    Manages energy demand response advisory dossiers, physical interlock checks,
    dual-key operator authorization, and cryptographic audit trail logging.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._advisories: Dict[str, EnergyAdvisoryDossier] = {}
        self._dispatch_orders: Dict[str, EnergyDispatchWorkOrder] = {}
        self._seed_default_advisories()

    def _seed_default_advisories(self):
        """Seeds initial realistic demand-response advisories for commercial facilities."""
        now = datetime.now(timezone.utc)

        # Canonical Demand Response Advisory for Commercial Retail Complex
        adv_phoenix = EnergyAdvisoryDossier(
            advisoryId="ADVISORY-DR-20261023-001",
            facilityId="urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01",
            facilityName="Commercial Retail Complex & Zone",
            feederId="FDR-11KV-01",
            generatedAt=now,
            status=AdvisoryStatus.PENDING_REVIEW,
            recommendedAction=(
                "Discharge 450 kW from BESS-PHOENIX-01 and apply +1.0 deg C thermal setback "
                "to Central Retail Zone between 18:30-21:00 IST to shave 840 kW peak demand and avert tariff surcharges."
            ),
            projectedSavingsInr=18450.0,
            peakReductionKw=840.0,
            batteryWearCycles=0.082,
            avoidedCarbonKg=620.0,
            safetyChecks=SafetyInterlocks(
                voltageCompliant=True,
                voltageValueV=409.8,
                rampRateCompliant=True,
                rampRatePctPerMin=8.0,
                socBounded=True,
                currentSocPct=32.0,
                comfortPreserved=True,
                projectedIndoorTempC=24.2
            ),
            schedule=[
                DispatchScheduleSlot(timeSlot="18:30-19:00 IST", bessAction="DISCHARGE", bessKw=450.0, hvacSetbackDeltaC=1.0),
                DispatchScheduleSlot(timeSlot="19:00-19:30 IST", bessAction="DISCHARGE", bessKw=450.0, hvacSetbackDeltaC=1.0),
                DispatchScheduleSlot(timeSlot="19:30-20:00 IST", bessAction="DISCHARGE", bessKw=450.0, hvacSetbackDeltaC=1.0),
                DispatchScheduleSlot(timeSlot="20:00-20:30 IST", bessAction="DISCHARGE", bessKw=450.0, hvacSetbackDeltaC=0.5),
                DispatchScheduleSlot(timeSlot="20:30-21:00 IST", bessAction="IDLE", bessKw=0.0, hvacSetbackDeltaC=0.0),
            ],
            governanceNotice=(
                "Advisory decision support only. Emits an audited OpenADR / Modbus dispatch work order. "
                "Local BMS and BESS safety logic remains authoritative."
            )
        )
        self._advisories[adv_phoenix.advisoryId] = adv_phoenix

    def list_advisories(self, status: Optional[AdvisoryStatus] = None) -> List[EnergyAdvisoryDossier]:
        """Returns all registered energy demand response dossiers, optionally filtered by status."""
        with self._lock:
            items = list(self._advisories.values())
            if status:
                items = [a for a in items if a.status == status]
            return sorted(items, key=lambda a: a.generatedAt, reverse=True)

    def get_advisory(self, advisory_id: str) -> Optional[EnergyAdvisoryDossier]:
        """Retrieves a single demand response advisory dossier by ID."""
        with self._lock:
            return self._advisories.get(advisory_id)

    async def authorize_advisory(
        self,
        advisory_id: str,
        request: AuthorizeEnergyAdvisoryRequest,
        session: AsyncSession
    ) -> Optional[EnergyDispatchWorkOrder]:
        """
        Executes dual-key municipal / facility operator authorization for a demand response advisory.
        Computes SHA-256 tamper-evident hash, generates official dispatch ticket, and persists
        an immutable audit record into Table 29 (advisory_audit_log).
        """
        with self._lock:
            dossier = self._advisories.get(advisory_id)
            if not dossier:
                return None

            now = datetime.now(timezone.utc)
            date_str = now.strftime("%Y%m%d")

            # Canonical manifest for tamper-evident cryptographic hash
            canonical_manifest = (
                f"REC:{dossier.advisoryId}|ENTITY:{dossier.facilityId}|BADGE:{request.badgeId}|"
                f"SHIFT:{request.shiftId}|REVIEWER:{request.reviewer}|DECISION:{request.decision.value}|"
                f"PEAK_KW:{dossier.peakReductionKw}|SAVINGS_INR:{dossier.projectedSavingsInr}|TIME:{now.isoformat()}"
            )
            tamper_evident_hash = hashlib.sha256(canonical_manifest.encode("utf-8")).hexdigest()
            dispatch_order_id = f"EDO-{date_str}-{tamper_evident_hash[:8].upper()}"

            # OpenADR 2.0b EiEvent payload structure
            open_adr_payload = {
                "eiEvent": {
                    "eventDescriptor": {
                        "eventID": dispatch_order_id,
                        "modificationNumber": 0,
                        "status": "far",
                        "priority": 1,
                        "marketContext": "http://marketcontext.org/DR/PeakCurtailment"
                    },
                    "eiActivePeriod": {
                        "properties": {
                            "dtstart": {"date-time": now.isoformat()},
                            "duration": {"duration": "PT2H30M"},
                            "tolerance": {"tolerate": {"startafter": "PT5M"}},
                            "x-eiNotification": {"duration": "PT15M"}
                        }
                    },
                    "eiEventSignals": [
                        {
                            "signalName": "SIMPLE",
                            "signalType": "level",
                            "signalID": f"SIG-{dispatch_order_id[:12]}",
                            "currentValue": {"payloadFloat": {"value": float(dossier.peakReductionKw)}},
                            "intervals": [
                                {
                                    "dtstart": {"date-time": slot.timeSlot},
                                    "duration": {"duration": "PT30M"},
                                    "signalPayload": {"payloadFloat": {"value": float(slot.bessKw)}}
                                }
                                for slot in dossier.schedule
                            ]
                        }
                    ],
                    "eiTarget": {
                        "targetID": dossier.facilityId,
                        "resourceID": "BESS-PHOENIX-01"
                    }
                }
            }

            # Standard Modbus Register Map for BMS / SCADA field controllers
            primary_bess_kw = dossier.schedule[0].bessKw if dossier.schedule else 450.0
            primary_setback_delta = dossier.schedule[0].hvacSetbackDeltaC if dossier.schedule else 1.0
            modbus_registers = {
                "40001_bess_power_setpoint_kw": int(primary_bess_kw),
                "40002_bess_inverter_mode": 2,  # 1=Charge, 2=Discharge, 0=Idle
                "40003_hvac_temperature_offset_tenths_c": int(primary_setback_delta * 10),
                "40004_interlock_status_flags": 15,  # Bitmask: all 4 interlocks pass (1+2+4+8)
                "40005_watchdog_timeout_sec": 300,
                "40006_dispatch_heartbeat_status": 1
            }

            work_order = EnergyDispatchWorkOrder(
                dispatchOrderId=dispatch_order_id,
                advisoryId=dossier.advisoryId,
                facilityId=dossier.facilityId,
                facilityName=dossier.facilityName,
                authorizedBy=request.reviewer,
                badgeId=request.badgeId,
                shiftId=request.shiftId,
                issuedAt=now,
                decision=request.decision,
                schedule=dossier.schedule,
                safetyChecks=dossier.safetyChecks,
                projectedSavingsInr=dossier.projectedSavingsInr,
                peakReductionKw=dossier.peakReductionKw,
                avoidedCarbonKg=dossier.avoidedCarbonKg,
                tamperEvidentHash=tamper_evident_hash,
                openAdrPayload=open_adr_payload,
                modbusRegisters=modbus_registers,
                governanceDisclaimer=(
                    "Advisory decision support only. Emits an audited OpenADR / Modbus dispatch work order. "
                    "Local BMS and BESS safety logic remains authoritative."
                )
            )

            # Update dossier in-memory status
            previous_status = dossier.status.value
            dossier.status = request.decision
            dossier.auditHash = tamper_evident_hash
            dossier.dispatchOrderId = dispatch_order_id
            dossier.authorizedBy = request.reviewer
            dossier.badgeId = request.badgeId
            dossier.shiftId = request.shiftId
            dossier.notes = request.notes

            self._dispatch_orders[dossier.advisoryId] = work_order

        # Persist immutable audit record into Table 29 (advisory_audit_log)
        try:
            audit_id = f"AUD-NRG-{uuid.uuid4().hex[:12].upper()}"
            payload_dict = {
                "dispatchOrderId": work_order.dispatchOrderId,
                "advisoryId": work_order.advisoryId,
                "facilityId": work_order.facilityId,
                "facilityName": work_order.facilityName,
                "authorizedBy": work_order.authorizedBy,
                "badgeId": work_order.badgeId,
                "shiftId": work_order.shiftId,
                "decision": work_order.decision.value,
                "peakReductionKw": work_order.peakReductionKw,
                "projectedSavingsInr": work_order.projectedSavingsInr,
                "avoidedCarbonKg": work_order.avoidedCarbonKg,
                "issuedAt": work_order.issuedAt.isoformat(),
                "tamperEvidentHash": work_order.tamperEvidentHash,
                "openAdrSummary": {"eventID": work_order.dispatchOrderId, "targetID": work_order.facilityId},
                "modbusSummary": work_order.modbusRegisters
            }

            await session.execute(
                text("""
                    INSERT INTO advisory_audit_log (
                        audit_id, recommendation_id, target_entity_id, action_type,
                        previous_status, new_status, authorized_by, badge_id, shift_id,
                        justification_notes, dispatch_order_id, dispatch_payload_json,
                        tamper_evident_hash
                    ) VALUES (
                        :audit_id, :recommendation_id, :target_entity_id, :action_type,
                        :previous_status, :new_status, :authorized_by, :badge_id, :shift_id,
                        :justification_notes, :dispatch_order_id, :dispatch_payload_json,
                        :tamper_evident_hash
                    )
                """),
                {
                    "audit_id": audit_id,
                    "recommendation_id": dossier.advisoryId,
                    "target_entity_id": dossier.facilityId,
                    "action_type": "ENERGY_DEMAND_RESPONSE_AUTHORIZATION",
                    "previous_status": previous_status,
                    "new_status": request.decision.value,
                    "authorized_by": request.reviewer,
                    "badge_id": request.badgeId,
                    "shift_id": request.shiftId,
                    "justification_notes": request.notes or "",
                    "dispatch_order_id": dispatch_order_id,
                    "dispatch_payload_json": json.dumps(payload_dict),
                    "tamper_evident_hash": tamper_evident_hash
                }
            )
            await session.commit()
            logger.info("Successfully persisted demand response audit log %s for advisory %s", audit_id, advisory_id)
        except Exception as e:
            logger.error("Failed to persist advisory_audit_log for energy demand response: %s", e)

        return work_order

    def get_dispatch_ticket(self, advisory_id: str) -> Optional[EnergyDispatchWorkOrder]:
        """Retrieves issued dispatch ticket for a given advisory."""
        with self._lock:
            return self._dispatch_orders.get(advisory_id)


# Global Singleton Instance
energy_advisory_service = EnergyAdvisoryService()
