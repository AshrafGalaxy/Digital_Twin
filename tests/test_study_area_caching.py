"""
test_study_area_caching.py

Hermetic automated tests for Issue #60 ([ENH-04]):
1. In-memory caching avoids re-opening/re-parsing study_area.geojson on repeat requests.
2. Response carries strong quoted ETag and Cache-Control headers.
3. Matching If-None-Match (exact, weak, multi-tag, wildcard) returns HTTP 304.
4. Mismatched If-None-Match returns HTTP 200 with full GeoJSON payload.
5. Cache invalidates cleanly when the backing GeoJSON file metadata/content updates.
6. Missing files return HTTP 404, and modified modules contain zero forbidden characters.
"""

import builtins
import json
import os
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest

import backend.api.v1.endpoints.study_area as study_area_mod
from backend.api.v1.endpoints.study_area import clear_study_area_cache
from backend.main import app

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def reset_study_area_cache():
    clear_study_area_cache()
    yield
    clear_study_area_cache()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_study_area_parses_file_once_across_repeat_requests(client):
    """Two identical GET /api/v1/study-area requests must parse the GeoJSON file only once."""
    orig_json_load = json.load
    orig_open = builtins.open
    json_load_calls = 0
    study_area_open_calls = 0

    def spy_json_load(fp, *args, **kwargs):
        nonlocal json_load_calls
        if "study_area.geojson" in str(getattr(fp, "name", "")):
            json_load_calls += 1
        return orig_json_load(fp, *args, **kwargs)

    def spy_open(file, *args, **kwargs):
        nonlocal study_area_open_calls
        if "study_area.geojson" in str(file):
            study_area_open_calls += 1
        return orig_open(file, *args, **kwargs)

    with patch("backend.api.v1.endpoints.study_area.json.load", side_effect=spy_json_load), patch(
        "builtins.open", side_effect=spy_open
    ):
        resp1 = client.get("/api/v1/study-area")
        resp2 = client.get("/api/v1/study-area")

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json() == resp2.json()
    assert json_load_calls == 1
    assert study_area_open_calls == 1


def test_study_area_returns_etag_and_cache_control(client):
    """Response carries a strong quoted ETag header and Cache-Control directives."""
    resp = client.get("/api/v1/study-area")
    assert resp.status_code == 200
    etag = resp.headers.get("etag")
    cache_control = resp.headers.get("cache-control", "")

    assert etag is not None
    assert etag.startswith('"') and etag.endswith('"')
    assert len(etag) >= 10
    assert "max-age=300" in cache_control
    assert "must-revalidate" in cache_control


def test_study_area_if_none_match_returns_304(client):
    """Matching If-None-Match variants (exact, weak, multi-tag, wildcard) return HTTP 304."""
    first = client.get("/api/v1/study-area")
    assert first.status_code == 200
    etag = first.headers["etag"]

    for header_val in (etag, f"W/{etag}", f'"stale-etag-1", {etag}', "*"):
        cond = client.get("/api/v1/study-area", headers={"If-None-Match": header_val})
        assert cond.status_code == 304
        assert cond.content == b""
        assert cond.headers.get("etag") == etag
        assert "must-revalidate" in cond.headers.get("cache-control", "")


def test_study_area_mismatched_if_none_match_returns_200(client):
    """Mismatched If-None-Match returns HTTP 200 with full GeoJSON body and current ETag."""
    first = client.get("/api/v1/study-area")
    assert first.status_code == 200
    etag = first.headers["etag"]

    second = client.get("/api/v1/study-area", headers={"If-None-Match": '"outdated-tag"'})
    assert second.status_code == 200
    assert second.headers.get("etag") == etag
    assert second.json() == first.json()


def test_study_area_invalidates_cache_when_file_updates(client, tmp_path, monkeypatch):
    """Updating the underlying GeoJSON file produces updated JSON and a distinct ETag."""
    custom_file = tmp_path / "study_area.geojson"
    payload_v1 = {"type": "FeatureCollection", "name": "v1", "features": []}
    payload_v2 = {"type": "FeatureCollection", "name": "v2_updated", "features": [{"type": "Feature"}]}
    custom_file.write_text(json.dumps(payload_v1), encoding="utf-8")

    monkeypatch.setattr(study_area_mod, "STUDY_AREA_PATH", custom_file)
    monkeypatch.setattr(study_area_mod, "FALLBACK_PATH", custom_file)

    r1 = client.get("/api/v1/study-area")
    assert r1.status_code == 200
    assert r1.json() == payload_v1
    etag1 = r1.headers["etag"]

    # Update file bytes and advance mtime cleanly beyond filesystem timestamp granularity
    custom_file.write_text(json.dumps(payload_v2), encoding="utf-8")
    stat_now = custom_file.stat()
    os.utime(custom_file, ns=(stat_now.st_atime_ns, stat_now.st_mtime_ns + 5_000_000_000))

    r2 = client.get("/api/v1/study-area", headers={"If-None-Match": etag1})
    assert r2.status_code == 200
    assert r2.json() == payload_v2
    etag2 = r2.headers["etag"]
    assert etag2 != etag1

    r3 = client.get("/api/v1/study-area", headers={"If-None-Match": etag2})
    assert r3.status_code == 304


def test_study_area_missing_file_returns_404(client, tmp_path, monkeypatch):
    """Returns HTTP 404 when neither STUDY_AREA_PATH nor FALLBACK_PATH exists."""
    missing = tmp_path / "missing_study_area.geojson"
    monkeypatch.setattr(study_area_mod, "STUDY_AREA_PATH", missing)
    monkeypatch.setattr(study_area_mod, "FALLBACK_PATH", missing)

    resp = client.get("/api/v1/study-area")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_no_forbidden_characters_in_study_area_modules():
    """Verify modified files remain free of em dashes and en dashes."""
    for rel_path in (
        REPO_ROOT / "backend" / "api" / "v1" / "endpoints" / "study_area.py",
        REPO_ROOT / "tests" / "test_study_area_caching.py",
    ):
        text = rel_path.read_text(encoding="utf-8")
        assert "\u2014" not in text, f"Em dash found in {rel_path}"
        assert "\u2013" not in text, f"En dash found in {rel_path}"
