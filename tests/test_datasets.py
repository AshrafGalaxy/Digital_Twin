"""
test_datasets.py

Comprehensive tests for dataset manifests and data governance endpoints.
Validates AGENTS.md §7 (Data Provenance, Locality Honesty, and Admission Invariants)
and DATA_AND_ML_PLAN.md §3 catalog requirements.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_get_dataset_manifests_catalog():
    """Verifies that the dataset catalog returns all registered manifests with governance metadata."""
    response = client.get("/api/v1/datasets/manifests")
    assert response.status_code == 200
    data = response.json()

    assert "catalogVersion" in data
    assert "studyArea" in data
    assert "datasets" in data
    assert data["totalDatasets"] >= 4

    # Ensure all primary datasets exist in catalog
    dataset_ids = [d["id"] for d in data["datasets"]]
    assert "D-01" in dataset_ids
    assert "D-03" in dataset_ids
    assert "D-04" in dataset_ids
    assert "D-06" in dataset_ids

    # Verify provenance and locality metadata are attached
    for entry in data["datasets"]:
        assert "sourceMode" in entry
        assert "localityClassification" in entry
        assert "license" in entry
        assert "intendedUse" in entry


def test_get_osm_network_manifest():
    """Verifies OpenStreetMap & OSMnx pilot corridor network manifest."""
    response = client.get("/api/v1/datasets/manifests/D-01")
    assert response.status_code == 200
    manifest = response.json()

    assert manifest["datasetId"] == "D-01-OSM"
    assert manifest["localityClassification"] == "PILOT_LOCAL"
    assert manifest["sourceMode"] == "DERIVED"
    assert "Open Database License" in manifest["license"]
    assert "geographicBoundary" in manifest
    assert "fields" in manifest
    assert len(manifest["fields"]) >= 4
    assert "prohibitedClaims" in manifest


def test_get_pune_traffic_manifest_invariants():
    """
    Verifies that the Pune traffic dataset strictly enforces AGENTS.md §7.2:
    - Locality must be PUNE_NON_LOCAL
    - Prohibited claims must explicitly forbid claiming it as Viman Nagar Chowk observations
    """
    response = client.get("/api/v1/datasets/manifests/D-03")
    assert response.status_code == 200
    manifest = response.json()

    assert manifest["datasetId"] == "D-03-PUNE-TRAFFIC"
    assert manifest["localityClassification"] == "PUNE_NON_LOCAL"
    assert manifest["sourceMode"] == "REPLAY"
    assert "CC BY 4.0" in manifest["license"]

    # Mandatory data honesty invariant
    prohibited = manifest["prohibitedClaims"]
    assert "Viman Nagar" in prohibited
    assert "Must NEVER be claimed as Viman Nagar Chowk direct field observations" in prohibited


def test_get_phoenix_energy_manifest_invariants():
    """
    Verifies Phoenix Marketcity commercial load manifest:
    - Locality must be BENCHMARK_SYNTHETIC
    - Must forbid claiming as private utility smart-meter telemetry
    """
    response = client.get("/api/v1/datasets/manifests/D-06")
    assert response.status_code == 200
    manifest = response.json()

    assert manifest["datasetId"] == "D-06-PHOENIX-ENERGY"
    assert manifest["localityClassification"] == "BENCHMARK_SYNTHETIC"
    assert manifest["sourceMode"] == "SIMULATION"

    # Mandatory data honesty invariant
    prohibited = manifest["prohibitedClaims"]
    assert "smart-meter" in prohibited.lower() or "proprietary" in prohibited.lower()


def test_get_air_quality_manifest():
    """Verifies Pune ambient air quality manifest."""
    response = client.get("/api/v1/datasets/manifests/D-04")
    assert response.status_code == 200
    manifest = response.json()

    assert manifest["datasetId"] == "D-04-PUNE-AQI"
    assert manifest["localityClassification"] == "REGIONAL_CONTEXT"
    assert manifest["sourceMode"] == "REPLAY"
    assert "prohibitedClaims" in manifest


def test_get_manifest_by_manifest_id_slug():
    """Verifies that lookup works by manifestId as well as ID."""
    response = client.get("/api/v1/datasets/manifests/D-01-OSM")
    assert response.status_code == 200
    assert response.json()["datasetId"] == "D-01-OSM"


def test_get_nonexistent_manifest_returns_404():
    """Verifies that querying an unregistered dataset returns HTTP 404."""
    response = client.get("/api/v1/datasets/manifests/NON_EXISTENT_DATASET_XYZ")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
