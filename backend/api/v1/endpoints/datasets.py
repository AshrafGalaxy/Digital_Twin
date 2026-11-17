"""
datasets.py

Endpoints for querying the authoritative dataset manifests and data governance catalog
in compliance with AGENTS.md §7 (Data Provenance & Locality Honesty) and DATA_AND_ML_PLAN.md §3.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/datasets", tags=["Data Governance & Manifests"])

# Path resolution supporting both local development and root execution
MANIFESTS_DIR = Path("data/manifests")
FALLBACK_MANIFESTS_DIR = Path("../data/manifests")


def _get_manifests_dir() -> Path:
    if MANIFESTS_DIR.exists() and MANIFESTS_DIR.is_dir():
        return MANIFESTS_DIR
    if FALLBACK_MANIFESTS_DIR.exists() and FALLBACK_MANIFESTS_DIR.is_dir():
        return FALLBACK_MANIFESTS_DIR
    return MANIFESTS_DIR


@router.get("/manifests", response_model=Dict[str, Any])
async def get_dataset_manifests():
    """
    Returns the complete catalog of registered dataset manifests,
    including provenance mode, license, locality classification, and mandatory prohibited claims.
    """
    manifests_dir = _get_manifests_dir()
    catalog_path = manifests_dir / "catalog.json"

    if not catalog_path.exists():
        raise HTTPException(status_code=404, detail="Dataset catalog metadata not found on server")

    try:
        with open(catalog_path, "r", encoding="utf-8") as f:
            catalog_data = json.load(f)

        # Enrich each catalog item with full manifest details if JSON manifest exists
        enriched_manifests: List[Dict[str, Any]] = []
        for item in catalog_data.get("datasets", []):
            json_filename = item.get("manifestJson")
            full_manifest = None
            if json_filename:
                mf_path = manifests_dir / json_filename
                if mf_path.exists():
                    try:
                        with open(mf_path, "r", encoding="utf-8") as mf:
                            full_manifest = json.load(mf)
                    except Exception:
                        pass

            entry = {
                "id": item.get("id"),
                "manifestId": item.get("manifestId", item.get("id")),
                "name": item.get("name"),
                "localityClassification": item.get("localityClassification"),
                "sourceMode": item.get("sourceMode"),
                "license": item.get("license"),
                "intendedUse": item.get("intendedUse"),
                "prohibitedClaim": item.get("prohibitedClaim") or (full_manifest.get("prohibitedClaims") if full_manifest else None),
                "manifestJson": item.get("manifestJson"),
                "manifestMarkdown": item.get("manifestMarkdown"),
                "temporalCoverage": full_manifest.get("temporalCoverage") if full_manifest else None,
                "geographicBoundary": full_manifest.get("geographicBoundary") if full_manifest else None,
                "fieldsCount": len(full_manifest.get("fields", [])) if full_manifest else 0
            }
            enriched_manifests.append(entry)

        return {
            "catalogVersion": catalog_data.get("catalogVersion", "1.1.0"),
            "updatedAt": catalog_data.get("updatedAt"),
            "studyArea": catalog_data.get("studyArea"),
            "totalDatasets": len(enriched_manifests),
            "datasets": enriched_manifests
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed loading dataset manifests: {str(exc)}")


@router.get("/manifests/{dataset_id}", response_model=Dict[str, Any])
async def get_dataset_manifest_by_id(dataset_id: str):
    """
    Returns the comprehensive, machine-readable manifest for a specific dataset ID or filename key.
    Enforces AGENTS.md §7.3 schema invariants and strict directory containment.
    """
    clean_id = dataset_id.strip()

    # Reject directory traversal attempts and path separators immediately
    if (
        ".." in clean_id
        or "/" in clean_id
        or "\\" in clean_id
        or "%2f" in clean_id.lower()
        or "%5c" in clean_id.lower()
        or "%2e" in clean_id.lower()
    ):
        raise HTTPException(
            status_code=404,
            detail=f"Dataset manifest for '{dataset_id}' not found in catalog."
        )

    manifests_dir = _get_manifests_dir()
    catalog_path = manifests_dir / "catalog.json"

    target_json_filename: Optional[str] = None
    clean_id_lower = clean_id.lower()

    # Check catalog.json for strictly registered datasets
    if catalog_path.exists():
        try:
            with open(catalog_path, "r", encoding="utf-8") as f:
                catalog = json.load(f)
                for item in catalog.get("datasets", []):
                    item_id = str(item.get("id", "")).strip().lower()
                    manifest_id = str(item.get("manifestId", "")).strip().lower()
                    manifest_json = str(item.get("manifestJson", "")).strip().lower()
                    if (
                        item_id == clean_id_lower
                        or manifest_id == clean_id_lower
                        or manifest_json == clean_id_lower
                        or manifest_json == f"{clean_id_lower}.json"
                    ):
                        target_json_filename = item.get("manifestJson")
                        break
        except Exception:
            pass

    if not target_json_filename:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset manifest for '{dataset_id}' not found in catalog."
        )

    canonical_manifests_dir = manifests_dir.resolve()
    file_path = (manifests_dir / target_json_filename).resolve()

    try:
        file_path.relative_to(canonical_manifests_dir)
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset manifest for '{dataset_id}' not found in catalog."
        )

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"Manifest file '{target_json_filename}' could not be located."
        )

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading manifest '{target_json_filename}': {str(exc)}"
        )
