"""
evaluation.py

API router endpoints for multi-horizon forecast evaluation benchmarks,
executive municipal decision-support reporting, and reproducible corridor bundles (Milestone 9).
"""

from typing import Any, Dict
from fastapi import APIRouter, Response, status

try:
    from services.evaluation_service import evaluation_service
    from services.report_generator import report_generator
    from services.scenario_service import scenario_service
    from services.spatial_registry_service import spatial_service
except ImportError:
    from backend.services.evaluation_service import evaluation_service
    from backend.services.report_generator import report_generator
    from backend.services.scenario_service import scenario_service
    from backend.services.spatial_registry_service import spatial_service

router = APIRouter(tags=["Evaluation, Reports & Exports"])


@router.get("/analytics/evaluation/benchmarks")
def get_evaluation_benchmarks(recompute: bool = False):
    """
    Returns multi-horizon forecasting benchmarks (15m, 30m, 60m)
    evaluated on the chronological holdout test set vs. persistence baselines.
    """
    return evaluation_service.get_multi_horizon_benchmarks(force_recompute=recompute)


@router.get("/reports/executive-summary")
def get_executive_report_json():
    """
    Synthesizes the complete municipal executive decision-support briefing
    including asset inventory, telemetry provenance audit, accuracy benchmarks,
    and scenario evaluation deltas in structured JSON.
    """
    return report_generator.generate_executive_report()


@router.get("/reports/executive-summary/markdown")
def get_executive_report_markdown():
    """
    Returns the publication-ready executive municipal decision-support briefing
    in GitHub-flavored Markdown.
    """
    md_text = report_generator.generate_markdown_briefing()
    return Response(
        content=md_text,
        media_type="text/markdown",
        headers={"Content-Disposition": 'attachment; filename="nagar_road_pilot_briefing.md"'}
    )


@router.get("/export/corridor-bundle")
def export_corridor_bundle():
    """
    Packages a reproducible bundle for academic or municipal peer review:
    canonical 3D GeoJSON assets, multi-horizon benchmarks, recent scenario runs, and audit logs.
    """
    catalog = spatial_service.get_catalog_dict()
    spatial_summary = catalog.get("studyArea", {})
    benchmarks = evaluation_service.get_multi_horizon_benchmarks()
    recent_runs = scenario_service.list_recent_runs(limit=10)
    report = report_generator.generate_executive_report()

    return {
        "corridorBundleVersion": "1.0.0",
        "exportedAt": report["generatedAt"],
        "corridorMetadata": spatial_summary,
        "evaluationBenchmarks": benchmarks,
        "scenarioRuns": recent_runs,
        "provenanceAudit": report["provenanceAudit"],
        "governanceNotice": report["governanceNotice"]
    }
