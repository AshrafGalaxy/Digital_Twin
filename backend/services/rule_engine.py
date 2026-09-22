"""
rule_engine.py

Deterministic rule engine generating traceable, human-governed advisory recommendations (D-10).
Converts forecasts, current observations, and simulation outputs into operational advisories
without autonomous external actuation.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
import threading

from backend.core.constants import SourceMode
from backend.schemas.recommendations import (
    AdvisoryRecommendation,
    AdvisorySummary,
    AuditLogEntry,
    RecommendationDomain,
    RecommendationEvidence,
    RecommendationSeverity,
    RecommendationStatus
)
from backend.services.forecast_service import forecast_service
from backend.services.anomaly_detector import EnvironmentalAnomalyDetector


class AdvisoryRuleEngine:
    """
    Evaluates corridor conditions and ML forecasts against deterministic governance rules.
    Maintains recommendation lifecycle state and audit logging.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._recommendations: Dict[str, AdvisoryRecommendation] = {}
        self.anomaly_detector = EnvironmentalAnomalyDetector()
        self._seed_initial_advisories()

    def _seed_initial_advisories(self):
        """Seeds realistic initial corridor advisories reflecting current forecasts and observations."""
        now = datetime.now(timezone.utc)

        # 1. Traffic Congestion Advisory
        rec_trf = AdvisoryRecommendation(
            recommendationId="REC-TRF-20260920-001",
            domain=RecommendationDomain.TRAFFIC,
            severity=RecommendationSeverity.WARNING,
            status=RecommendationStatus.ACTIVE,
            targetEntityId="urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01",
            title="Arterial Congestion Surge Predicted on Nagar Road Eastbound",
            description="15-minute XGBoost speed forecast predicts arterial deceleration to 17.8 km/h due to evening commute convergence approaching Viman Nagar Chowk.",
            triggerRule="RULE-TRF-CONGESTION-PREDICTED",
            evidence=RecommendationEvidence(
                sourceMode=SourceMode.PREDICTED,
                metricName="averageSpeedKmh",
                observedOrPredictedValue=17.8,
                threshold=20.0,
                unit="km/h",
                horizonMinutes=15,
                modelVersion="traffic-xgb-v1",
                scenarioId="SCEN-INT-01",
                confidenceScore=0.88,
                timestamp=now
            ),
            suggestedAction="Evaluate approved signal plan SCEN-INT-01 (+15s Nagar Rd EB green extension) in Scenario Studio. Compare delay deltas before municipal dispatch.",
            humanApprovalRequired=True,
            governanceNotice="Advisory only. Requires human verification and municipal authorization before any physical intervention.",
            auditTrail=[
                AuditLogEntry(
                    timestamp=now,
                    previousStatus=RecommendationStatus.ACTIVE,
                    newStatus=RecommendationStatus.ACTIVE,
                    reviewer="System Rule Engine",
                    notes="Automated trigger: predicted speed 17.8 km/h below 20.0 km/h threshold."
                )
            ],
            createdAt=now,
            updatedAt=now
        )
        self._recommendations[rec_trf.recommendationId] = rec_trf

        # 2. Building Energy Peak Advisory
        rec_nrg = AdvisoryRecommendation(
            recommendationId="REC-NRG-20260920-002",
            domain=RecommendationDomain.ENERGY,
            severity=RecommendationSeverity.WARNING,
            status=RecommendationStatus.ACTIVE,
            targetEntityId="urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01",
            title="Commercial Peak Demand Threshold Approaching at Phoenix Marketcity",
            description="60-minute energy demand forecast projects electrical load of 4,940 kW, crossing the contracted demand threshold (4,800 kW).",
            triggerRule="RULE-NRG-PEAK-SURGE",
            evidence=RecommendationEvidence(
                sourceMode=SourceMode.PREDICTED,
                metricName="electricalDemandKw",
                observedOrPredictedValue=4940.0,
                threshold=4800.0,
                unit="kW",
                horizonMinutes=60,
                modelVersion="energy-xgb-v1",
                confidenceScore=0.92,
                timestamp=now
            ),
            suggestedAction="Advise building management to stage commercial chiller compressors and adjust HVAC setpoint by +0.5°C between 14:00-17:00 IST to avert tariff surcharges.",
            humanApprovalRequired=True,
            governanceNotice="Advisory only. Requires human verification and municipal authorization before any physical intervention.",
            auditTrail=[
                AuditLogEntry(
                    timestamp=now,
                    previousStatus=RecommendationStatus.ACTIVE,
                    newStatus=RecommendationStatus.ACTIVE,
                    reviewer="System Rule Engine",
                    notes="Automated trigger: 60-min load forecast 4,940 kW exceeded 4,800 kW limit."
                )
            ],
            createdAt=now,
            updatedAt=now
        )
        self._recommendations[rec_nrg.recommendationId] = rec_nrg

        # 3. Telemetry Gateway Stale Check
        rec_env = AdvisoryRecommendation(
            recommendationId="REC-ENV-20260920-003",
            domain=RecommendationDomain.ENVIRONMENT,
            severity=RecommendationSeverity.INFO,
            status=RecommendationStatus.ACTIVE,
            targetEntityId="urn:ngsi-ld:TrafficSensor:PUNE:DS-VN-EB-01",
            title="Sensor Telemetry Staleness Notice",
            description="Optical traffic sensor telemetry latency is nearing the 60-second threshold. Signal quality remains acceptable but requires monitoring.",
            triggerRule="RULE-ENV-STALE-TELEMETRY",
            evidence=RecommendationEvidence(
                sourceMode=SourceMode.REPLAY,
                metricName="telemetryLatencySeconds",
                observedOrPredictedValue=52.0,
                threshold=60.0,
                unit="s",
                confidenceScore=0.95,
                timestamp=now
            ),
            suggestedAction="Monitor telemetry buffer. If latency exceeds 60s, dispatch automated communication ping to optical detector gateway.",
            humanApprovalRequired=True,
            governanceNotice="Advisory only. Requires human verification and municipal authorization before any physical intervention.",
            auditTrail=[
                AuditLogEntry(
                    timestamp=now,
                    previousStatus=RecommendationStatus.ACTIVE,
                    newStatus=RecommendationStatus.ACTIVE,
                    reviewer="System Rule Engine",
                    notes="Informational notice: latency 52s approaching staleness boundary."
                )
            ],
            createdAt=now,
            updatedAt=now
        )
        self._recommendations[rec_env.recommendationId] = rec_env

    def list_recommendations(
        self,
        domain: Optional[RecommendationDomain] = None,
        status: Optional[RecommendationStatus] = None
    ) -> List[AdvisoryRecommendation]:
        """Lists all registered recommendations with optional filtering."""
        with self._lock:
            results = list(self._recommendations.values())
            if domain:
                results = [r for r in results if r.domain == domain]
            if status:
                results = [r for r in results if r.status == status]
            # Order by createdAt descending
            return sorted(results, key=lambda r: r.createdAt, reverse=True)

    def get_recommendation(self, rec_id: str) -> Optional[AdvisoryRecommendation]:
        """Retrieves a single recommendation by ID."""
        with self._lock:
            return self._recommendations.get(rec_id)

    def review_recommendation(
        self,
        rec_id: str,
        new_status: RecommendationStatus,
        reviewer: str,
        notes: Optional[str] = None
    ) -> Optional[AdvisoryRecommendation]:
        """
        Executes a human review lifecycle transition (UNDER_REVIEW, ACKNOWLEDGED, DISMISSED)
        and preserves complete chronological audit history.
        """
        with self._lock:
            rec = self._recommendations.get(rec_id)
            if not rec:
                return None

            now = datetime.now(timezone.utc)
            audit_entry = AuditLogEntry(
                timestamp=now,
                previousStatus=rec.status,
                newStatus=new_status,
                reviewer=reviewer,
                notes=notes or f"Status transitioned from {rec.status} to {new_status}."
            )

            rec.status = new_status
            rec.updatedAt = now
            rec.auditTrail.append(audit_entry)
            return rec

    def evaluate_rules(self) -> List[AdvisoryRecommendation]:
        """
        Evaluates active corridor state and current XGBoost forecasts to refresh recommendations.
        """
        with self._lock:
            now = datetime.now(timezone.utc)

            # Evaluate traffic forecast on SEG-NR-EB-01
            traffic_fc = forecast_service.get_traffic_forecast("urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01")
            predicted_speed = float(traffic_fc.get("predictedValue", 22.0))
            traffic_model_ver = str(traffic_fc.get("modelVersion", "traffic-xgb-v1"))

            if predicted_speed < 20.0:
                rec_id = "REC-TRF-20260920-001"
                severity = RecommendationSeverity.CRITICAL if predicted_speed < 15.0 else RecommendationSeverity.WARNING
                if rec_id in self._recommendations:
                    rec = self._recommendations[rec_id]
                    rec.evidence.observedOrPredictedValue = predicted_speed
                    rec.evidence.timestamp = now
                    rec.severity = severity
                    rec.updatedAt = now
                else:
                    new_rec = AdvisoryRecommendation(
                        recommendationId=rec_id,
                        domain=RecommendationDomain.TRAFFIC,
                        severity=severity,
                        status=RecommendationStatus.ACTIVE,
                        targetEntityId="urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01",
                        title="Arterial Congestion Surge Predicted on Nagar Road Eastbound",
                        description=f"15-minute speed forecast projects arterial speed of {predicted_speed:.1f} km/h below the 20.0 km/h congestion threshold.",
                        triggerRule="RULE-TRF-CONGESTION-PREDICTED",
                        evidence=RecommendationEvidence(
                            sourceMode=SourceMode.PREDICTED,
                            metricName="averageSpeedKmh",
                            observedOrPredictedValue=predicted_speed,
                            threshold=20.0,
                            unit="km/h",
                            horizonMinutes=15,
                            modelVersion=traffic_model_ver,
                            scenarioId="SCEN-INT-01",
                            confidenceScore=0.90,
                            timestamp=now
                        ),
                        suggestedAction="Evaluate SCEN-INT-01 in Scenario Studio to test green extension mitigation.",
                        humanApprovalRequired=True,
                        createdAt=now,
                        updatedAt=now
                    )
                    self._recommendations[rec_id] = new_rec

            # Evaluate energy forecast on BLD-PHOENIX-01
            energy_fc = forecast_service.get_energy_forecast("urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01")
            predicted_load = float(energy_fc.get("predictedValue", 4200.0))

            if predicted_load > 4800.0:
                rec_id = "REC-NRG-20260920-002"
                if rec_id in self._recommendations:
                    rec = self._recommendations[rec_id]
                    rec.evidence.observedOrPredictedValue = predicted_load
                    rec.evidence.timestamp = now
                    rec.updatedAt = now

            return list(self._recommendations.values())

    def evaluate_environmental_reading(
        self,
        sensor_id: str,
        pm25: float,
        pm10: Optional[float] = None,
        aqi: Optional[float] = None,
        ambient_temp_c: Optional[float] = None
    ) -> Optional[AdvisoryRecommendation]:
        """
        Evaluates an environmental sensor reading using Isolation Forest and Z-scores.
        If an anomaly is detected, creates or updates an environmental advisory recommendation.
        """
        eval_result = self.anomaly_detector.evaluate_reading(
            sensor_id=sensor_id,
            pm25=pm25,
            pm10=pm10,
            aqi=aqi,
            ambient_temp_c=ambient_temp_c
        )

        if not eval_result["isAnomaly"]:
            return None

        now = datetime.now(timezone.utc)
        rec_id = f"REC-ENV-ANOMALY-{sensor_id.split(':')[-1]}"
        sev = (
            RecommendationSeverity.CRITICAL
            if eval_result["severity"] == "CRITICAL"
            else RecommendationSeverity.WARNING
        )

        rec = AdvisoryRecommendation(
            recommendationId=rec_id,
            domain=RecommendationDomain.ENVIRONMENT,
            severity=sev,
            status=RecommendationStatus.ACTIVE,
            targetEntityId=sensor_id,
            title=f"Air Quality Anomaly Detected at {sensor_id.split(':')[-1]}",
            description="; ".join(eval_result["reasons"]),
            triggerRule="RULE-ENV-ISOLATION-ANOMALY",
            evidence=RecommendationEvidence(
                sourceMode=SourceMode.SIMULATION,
                metricName="pm25UgM3",
                observedOrPredictedValue=pm25,
                threshold=60.0,
                unit="ug/m3",
                confidenceScore=0.94,
                timestamp=now
            ),
            suggestedAction="Advise municipal ward officer to investigate localized particulate source and alert commercial buildings to engage indoor HEPA filtration stages.",
            humanApprovalRequired=True,
            governanceNotice="Advisory only. Requires human verification before issuing public health advisories.",
            auditTrail=[
                AuditLogEntry(
                    timestamp=now,
                    previousStatus=RecommendationStatus.ACTIVE,
                    newStatus=RecommendationStatus.ACTIVE,
                    reviewer="System Anomaly Engine",
                    notes=f"Anomaly detected: {eval_result['severity']} (Z-score: {eval_result['zScore']})"
                )
            ],
            createdAt=now,
            updatedAt=now
        )

        with self._lock:
            self._recommendations[rec_id] = rec

        return rec

    def add_custom_recommendation(self, rec: AdvisoryRecommendation) -> AdvisoryRecommendation:
        """Inserts or updates a custom advisory recommendation thread-safely."""
        with self._lock:
            self._recommendations[rec.recommendationId] = rec
            return rec

    def get_summary(self) -> AdvisorySummary:
        """Returns aggregated counters of recommendations across severity and domain."""
        with self._lock:
            active = [r for r in self._recommendations.values() if r.status == RecommendationStatus.ACTIVE]
            crit = sum(1 for r in active if r.severity == RecommendationSeverity.CRITICAL)
            warn = sum(1 for r in active if r.severity == RecommendationSeverity.WARNING)
            info = sum(1 for r in active if r.severity == RecommendationSeverity.INFO)

            by_domain = {
                RecommendationDomain.TRAFFIC.value: sum(1 for r in active if r.domain == RecommendationDomain.TRAFFIC),
                RecommendationDomain.ENERGY.value: sum(1 for r in active if r.domain == RecommendationDomain.ENERGY),
                RecommendationDomain.ENVIRONMENT.value: sum(1 for r in active if r.domain == RecommendationDomain.ENVIRONMENT),
            }

            return AdvisorySummary(
                totalActive=len(active),
                criticalCount=crit,
                warningCount=warn,
                infoCount=info,
                byDomain=by_domain
            )


# Global singleton rule engine instance
rule_engine = AdvisoryRuleEngine()
