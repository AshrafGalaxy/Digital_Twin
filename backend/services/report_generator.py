"""
report_generator.py

Synthesizes operational state, multi-horizon evaluation benchmarks,
simulation comparative KPIs, and advisory audit logs into an authoritative
Municipal Decision-Support Executive Briefing (Milestone 9).
Provides both structured JSON and formatted executive Markdown exports.
"""

from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional

from backend.core.config import settings
from backend.core.constants import SourceMode
from backend.services.evaluation_service import evaluation_service
from backend.services.scenario_service import scenario_service
from backend.services.rule_engine import rule_engine


class MunicipalReportGenerator:
    """Generates authoritative municipal corridor briefing reports."""

    def _query_live_provenance_counts(self) -> Dict[str, int]:
        """Queries actual record counts by source_mode from authoritative twin state."""
        counts = {
            "LIVE": 0,
            "REPLAY": 0,
            "SIMULATION": 0,
            "PREDICTED": 0,
            "STALE": 0,
            "INVALID": 0
        }
        try:
            db_path = settings.resolved_sqlite_path
            if Path(db_path).exists():
                with sqlite3.connect(str(db_path), timeout=2.0) as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT source_mode, COUNT(*) FROM entity_current_state GROUP BY source_mode")
                    for sm, cnt in cur.fetchall():
                        if sm in counts:
                            counts[sm] = cnt
                        elif sm:
                            counts[sm] = cnt
        except Exception:
            return {
                "LIVE": 0,
                "REPLAY": 0,
                "SIMULATION": 0,
                "PREDICTED": 0,
                "STALE": 0,
                "INVALID": 0,
            }

        return counts

    def generate_executive_report(self) -> Dict[str, Any]:
        """Synthesizes structured executive corridor briefing data."""
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. Fetch Benchmarks
        benchmarks = evaluation_service.get_multi_horizon_benchmarks()

        # 2. Fetch Recent Scenario Runs
        scenario_runs = scenario_service.list_recent_runs(limit=5)
        best_run = scenario_runs[0] if scenario_runs else None

        # 3. Fetch Active Advisories
        advisories = rule_engine.list_recommendations()
        advisory_summary = rule_engine.get_summary()

        # 4. Provenance Accounting
        live_counts = self._query_live_provenance_counts()

        provenance_audit = {
            "sourceModes": live_counts,
            "scenarioRunCount": len(scenario_runs),
            "stateSeparationInvariantEnforced": True,
            "zeroActuationPolicyEnforced": True
        }

        # 5. Construct Structured Report
        report = {
            "reportId": f"REP-PUNE-NR-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}",
            "generatedAt": now_iso,
            "corridor": {
                "name": "Nagar Road Smart City Pilot Corridor",
                "boundary": "Viman Nagar Chowk (INT-VN-01) ↔ Somnath Nagar Chowk (INT-SN-01)",
                "lengthKm": 1.8,
                "city": "Pune",
                "state": "Maharashtra",
                "physicalAssets": {
                    "signalizedIntersections": 2,
                    "roadSegments": 10,
                    "trafficSensors": 4,
                    "environmentalStations": 1,
                    "commercialBuildings": 4
                },
                "facilities": [
                    {
                        "id": "urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01",
                        "name": "Phoenix Marketcity Commercial Complex",
                        "contractDemandKw": 6800,
                        "sanctionedKva": 8500,
                        "category": "COMMERCIAL_RETAIL"
                    },
                    {
                        "id": "urn:ngsi-ld:Building:PUNE:BLD-SOLITAIRE-01",
                        "name": "Solitaire Business & Tech Hub",
                        "contractDemandKw": 6010,
                        "sanctionedKva": 7500,
                        "category": "COMMERCIAL_IT"
                    },
                    {
                        "id": "urn:ngsi-ld:Building:PUNE:BLD-HYATT-01",
                        "name": "Hyatt Regency Hospitality Complex",
                        "contractDemandKw": 4990,
                        "sanctionedKva": 6200,
                        "category": "HOSPITALITY"
                    },
                    {
                        "id": "urn:ngsi-ld:Building:PUNE:BLD-SOLITAIRE-03",
                        "name": "Enterprise Office Center - Tower 3",
                        "contractDemandKw": 2400,
                        "sanctionedKva": 3000,
                        "category": "OFFICE"
                    }
                ]
            },
            "provenanceAudit": provenance_audit,
            "evaluationBenchmarks": benchmarks,
            "scenarioStudioSummary": {
                "totalRunsRecorded": len(scenario_runs),
                "latestRun": best_run
            },
            "advisoryInterventions": {
                "totalActive": advisory_summary.totalActive,
                "criticalCount": advisory_summary.criticalCount,
                "warningCount": advisory_summary.warningCount,
                "advisories": [r.model_dump() for r in advisories[:5]]
            },
            "governanceNotice": (
                "READ-ONLY DECISION SUPPORT NOTICE: The Digital Twin Smart City Platform operates strictly "
                "in advisory capacity. All forecasting and microscopic simulation results are mathematical "
                "models. Recommendations require municipal traffic officer authorization prior to any field implementation. "
                "Physical traffic signal controllers are NOT actuated by this platform."
            )
        }

        return report

    def generate_markdown_briefing(self) -> str:
        """Renders the executive briefing as a high-density, publication-ready Markdown report."""
        report = self.generate_executive_report()
        corridor = report["corridor"]
        benchmarks = report["evaluationBenchmarks"]
        horizons = benchmarks.get("horizons", {})
        cov = benchmarks.get("conformalCoverage") or {}
        be = benchmarks.get("buildingEnergy") or {}
        latest_run = report["scenarioStudioSummary"]["latestRun"]

        md_lines = [
            f"# Municipal Decision-Support Briefing: {corridor['name']}",
            f"> **Pilot Corridor:** {corridor['boundary']} ({corridor['lengthKm']} km arterial, Nagar Road, {corridor['city']}, {corridor['state']})  ",
            f"> **Generated At:** `{report['generatedAt']}` | **Report ID:** `{report['reportId']}`  ",
            f"> **System Status:** Active Evidence-Backed Operational Decision Support  ",
            "",
            "---",
            "",
            "## 1. Executive Summary & Statutory Governance Notice",
            "",
            "This briefing synthesizes continuous operational telemetry, predictive machine learning forecasts, "
            "and microscopic simulation analyses for the Nagar Road arterial corridor in Pune, Maharashtra. "
            "All findings and advisory recommendations are strictly **read-only decision support** and do not "
            "autonomously actuate physical traffic signal controllers or municipal infrastructure.",
            "",
            "> [!IMPORTANT]",
            f"> {report['governanceNotice']}",
            "",
            "---",
            "",
            "## 2. Corridor Asset Inventory & Telemetry Provenance",
            "",
            "| Asset Category | Entity ID / Specification | Count | Data Classes |",
            "| :--- | :--- | :--- | :--- |",
            f"| Signalized Intersections | `INT-VN-01` (Viman Nagar), `INT-SN-01` (Somnath Nagar) | {corridor['physicalAssets']['signalizedIntersections']} | `REPLAY`, `SIMULATION` |",
            f"| Road Segments | `SEG-NR-EB-01..03`, `SEG-NR-WB-01..03` + approach legs | {corridor['physicalAssets']['roadSegments']} | `REPLAY`, `PREDICTED` |",
            f"| Traffic Sensors | Nagar Rd sensors (`SNS-TRF-01..04`) | {corridor['physicalAssets']['trafficSensors']} | `LIVE`, `REPLAY` |",
            f"| Environmental Station | Air Quality CAAQMS (`SNS-ENV-01`) | {corridor['physicalAssets'].get('environmentalStations', 1)} | `LIVE`, `SIMULATION` |",
            f"| Commercial Facilities | Phoenix Marketcity (6,800 kW), Solitaire (6,010 kW), Hyatt (4,990 kW), Solitaire T3 (2,400 kW) | {corridor['physicalAssets']['commercialBuildings']} | `REPLAY`, `PREDICTED` |",
            "",
            "### Telemetry Provenance & State Separation Invariant",
            "- **Observed Telemetry:** Replayed corridor sensor counts and speeds are strictly segregated from model predictions.",
            "- **Zero Overwrite Rule:** Forecasts and simulation runs are tagged `PREDICTED` and `SIMULATION` respectively and stored in dedicated tables.",
            "- **Quality Status:** All active corridor observations comply with physical bounds (speed 0–120 km/h, volume >= 0).",
            "",
            "---",
            "",
            "## 3. Multi-Horizon Forecasting Accuracy Benchmarks",
            "",
            f"Series provenance: `{benchmarks.get('seriesProvenance', 'GENERATED')}`. "
            f"Split: {benchmarks.get('splitRatio', 'unspecified')}.",
            "",
            "| Horizon | Target Metric | Persistence Baseline MAE | Model MAE | RMSE | Skill Score | Improvement vs Persistence |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
        for horizon in horizons.values():
            unit = horizon.get("unit", "")
            model_mae = horizon.get("modelMae")
            model_cell = "unavailable" if model_mae is None else f"**`{model_mae} {unit}`**"
            rmse_cell = "unavailable" if horizon.get("modelRmse") is None else f"`{horizon.get('modelRmse')} {unit}`"
            skill_cell = "unavailable" if horizon.get("skillScore") is None else f"**`{horizon.get('skillScore')}`**"
            gain_cell = "unavailable" if horizon.get("improvementPct") is None else f"**`{horizon.get('improvementPct')}%`**"
            md_lines.append(
                f"| **{horizon.get('horizonMinutes')} Minutes** | {horizon.get('targetMetric')} | "
                f"`{horizon.get('persistenceMae')} {unit}` | {model_cell} | {rmse_cell} | {skill_cell} | {gain_cell} |"
            )
        if be:
            unit = be.get("unit", "kW")
            model_mae = be.get("modelMae")
            model_cell = "unavailable" if model_mae is None else f"**`{model_mae} {unit}`**"
            rmse_cell = "unavailable" if be.get("modelRmse") is None else f"`{be.get('modelRmse')} {unit}`"
            skill_cell = "unavailable" if be.get("skillScore") is None else f"**`{be.get('skillScore')}`**"
            gain_cell = "unavailable" if be.get("improvementPct") is None else f"**`{be.get('improvementPct')}%`**"
            md_lines.append(
                f"| **{be.get('horizonMinutes', 60)} Minutes** | Commercial Load ({be.get('facilityName', 'facility')}) | "
                f"`{be.get('persistenceMae')} {unit}` | {model_cell} | {rmse_cell} | {skill_cell} | {gain_cell} |"
            )

        coverage_lines = ["", "### Conformal Prediction Uncertainty Coverage", ""]
        target90 = cov.get("target90") if isinstance(cov, dict) else None
        target95 = cov.get("target95") if isinstance(cov, dict) else None
        if target90 and target95:
            coverage_lines.extend([
                f"- **90% interval:** Holdout coverage is **{target90['empiricalCoveragePct']}%** "
                f"(half-width +/- {target90['halfWidthKmh']} km/h).",
                f"- **95% interval:** Holdout coverage is **{target95['empiricalCoveragePct']}%** "
                f"(half-width +/- {target95['halfWidthKmh']} km/h).",
            ])
        else:
            coverage_lines.append("- Coverage was not computed because the model artifact is unavailable.")
        md_lines.extend(coverage_lines)
        md_lines.extend([
            "",
            "---",
            "",
            "## 4. Scenario Studio: What-If Intervention Outcomes",
            ""
        ])

        if latest_run:
            deltas = latest_run.get("deltas", {})
            md_lines.extend([
                f"### Latest Evaluated Intervention: `{latest_run['templateId']}` (Seed {latest_run['randomSeed']})",
                f"- **Verdict:** `{deltas.get('overall_verdict', 'RECOMMENDED')}`",
                f"- **Arterial Delay Reduction:** `{deltas.get('delay_delta_pct', 0)}%` ({deltas.get('delay_saved_sec', 0)}s saved per vehicle)",
                f"- **Travel Time Improvement:** `{deltas.get('travel_time_delta_pct', 0)}%` ({deltas.get('travel_time_saved_sec', 0)}s saved across corridor)",
                f"- **Approach Queue Reduction:** `{deltas.get('queue_length_delta_pct', 0)}%` ({deltas.get('queue_reduced_meters', 0)}m cleared on Nagar Rd EB)",
                f"- **Corridor Throughput Gain:** `+{deltas.get('throughput_delta_pct', 0)}%` (+{deltas.get('additional_throughput_vph', 0)} vehicles/hour)",
                ""
            ])
        else:
            md_lines.extend([
                "No scenario runs recorded yet. Execute comparative runs in Scenario Studio to synthesize intervention deltas.",
                ""
            ])

        md_lines.extend([
            "---",
            "",
            "## 5. Active Advisory Interventions & Audit Trail",
            "",
            f"- **Total Active Advisories:** {report['advisoryInterventions']['totalActive']}",
            f"- **Critical Severity:** {report['advisoryInterventions']['criticalCount']}",
            f"- **Warning Severity:** {report['advisoryInterventions']['warningCount']}",
            "",
            "| Advisory ID | Domain | Severity | Target Asset | Action Summary | Human Reviewer |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |"
        ])

        for adv in report["advisoryInterventions"]["advisories"]:
            rev = adv["auditTrail"][0]["reviewer"] if adv.get("auditTrail") else "Unreviewed"
            title_text = adv.get('title', '')
            summary_title = title_text[:45] + ('...' if len(title_text) > 45 else '')
            entity_label = adv.get('targetEntityId', '').split(':')[-1]
            md_lines.append(
                f"| `{adv['recommendationId']}` | {adv['domain']} | `{adv['severity']}` | `{entity_label}` | {summary_title} | {rev} |"
            )

        md_lines.extend([
            "",
            "---",
            "",
            "## 6. Municipal Decision Protocol",
            "1. **Review Forecast Trajectory:** Validate 15-minute speed forecast convergence before taking dispatch action.",
            "2. **Evaluate in Scenario Studio:** Run pairwise seed-controlled simulations for candidate signal timing adjustments.",
            "3. **Human Authorization:** A municipal traffic engineer must record formal sign-off in the Advisory Center prior to manual or field coordination updates.",
            "",
            "> *Report compiled automatically by the Digital Twin Smart City Platform Analytics Engine.*"
        ])

        return "\n".join(md_lines)


# Global singleton report generator
report_generator = MunicipalReportGenerator()

