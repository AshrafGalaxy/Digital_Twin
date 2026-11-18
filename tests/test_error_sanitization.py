"""
test_error_sanitization.py

Hermetic automated test suite verifying BUG-38:
Internal server failures must return fixed, standardized client messages
without leaking stack traces, filesystem paths, or database error strings.
"""

from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_study_area_success(client):
    """Verifies that normal GET /api/v1/study-area returns 200 and valid GeoJSON."""
    resp = client.get("/api/v1/study-area")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("type") in ("FeatureCollection", "Feature", "Polygon", "MultiPolygon")


def test_study_area_error_sanitization(client):
    """
    Verifies that when file reading raises an exception, GET /api/v1/study-area
    returns HTTP 500 with a fixed message and does not leak the path or exception string.
    """
    sensitive_path_error = "/var/secret/corridor/internal_schema.json: Permission denied"
    with patch("builtins.open", side_effect=PermissionError(sensitive_path_error)):
        resp = client.get("/api/v1/study-area")
        assert resp.status_code == 500
        detail = resp.json().get("detail", "")
        assert detail == "Failed to load study area geometry."
        assert "Permission denied" not in detail
        assert "secret" not in detail
        assert "json" not in detail.lower()


def test_traffic_forecast_error_sanitization(client):
    """
    Verifies that when traffic forecast generation raises an exception,
    GET /api/v1/forecasts/traffic/{segment_id} returns HTTP 500 with a fixed message
    and does not leak internal database or model exception strings.
    """
    db_leak_error = "FATAL: Connection to database 10.0.0.15:5432 failed with timeout in pg_catalog"
    with patch("backend.api.v1.endpoints.forecasts.forecast_service.get_traffic_forecast", side_effect=RuntimeError(db_leak_error)):
        resp = client.get("/api/v1/forecasts/traffic/urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01")
        assert resp.status_code == 500
        detail = resp.json().get("detail", "")
        assert detail == "Failed to generate traffic forecast."
        assert "FATAL" not in detail
        assert "10.0.0.15" not in detail
        assert "database" not in detail.lower()


def test_energy_forecast_error_sanitization(client):
    """
    Verifies that when energy forecast generation raises an exception,
    GET /api/v1/forecasts/energy/{building_id} returns HTTP 500 with a fixed message
    and does not leak internal model exception strings.
    """
    model_leak_error = "XGBoost internal error: division by zero in booster leaf weights"
    with patch("backend.api.v1.endpoints.forecasts.forecast_service.get_energy_forecast", side_effect=ValueError(model_leak_error)):
        resp = client.get("/api/v1/forecasts/energy/urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01")
        assert resp.status_code == 500
        detail = resp.json().get("detail", "")
        assert detail == "Failed to generate energy forecast."
        assert "XGBoost" not in detail
        assert "division by zero" not in detail
        assert "booster" not in detail.lower()


def test_dataset_manifest_error_sanitization(client):
    """
    Verifies that dataset manifest endpoints return fixed messages on unexpected internal failures.
    """
    io_leak_error = "Disk corruption in /data/manifests/catalog.json: I/O failure"
    with patch("backend.api.v1.endpoints.datasets.open", side_effect=IOError(io_leak_error)):
        resp = client.get("/api/v1/datasets/manifests")
        assert resp.status_code == 500
        detail = resp.json().get("detail", "")
        assert detail == "Failed to load dataset manifests."
        assert "Disk corruption" not in detail
        assert "catalog.json" not in detail.lower()
