"""
test_fidelity_extensions.py

Comprehensive test suite verifying analytical and fidelity extensions:
1. Conformal Prediction uncertainty calibration bounds.
2. TreeSHAP local feature attribution explainability.
3. Environmental Anomaly Detection on sensor telemetry.
4. FIWARE Orion-LD / NGSI-LD 1.3 interoperability exports.
5. FastAPI forecast and interop API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.anomaly_detector import EnvironmentalAnomalyDetector
from backend.services.fiware_adapter import FIWAREOrionLDAdapter
from backend.services.rule_engine import rule_engine
from backend.schemas.recommendations import RecommendationDomain, RecommendationSeverity
from ml.conformal_calibrator import ConformalPredictionCalibrator
from ml.explainer import LocalModelExplainer
from ml.inference.forecaster import CorridorForecaster

client = TestClient(app)


def test_conformal_prediction_intervals():
    """Verify conformal calibration provides valid 90% and 95% uncertainty intervals."""
    intervals = ConformalPredictionCalibrator.get_traffic_intervals(25.0)
    
    assert "interval90" in intervals
    assert "interval95" in intervals
    
    i90 = intervals["interval90"]
    assert i90["lower"] < 25.0 < i90["upper"]
    assert i90["margin"] == 4.80
    assert i90["coverageTarget"] == 0.90
    assert i90["empiricalTestCoverage"] >= 0.88

    i95 = intervals["interval95"]
    assert i95["margin"] == 5.66
    assert i95["upper"] > i90["upper"]
    assert i95["lower"] < i90["lower"]

    energy_intervals = ConformalPredictionCalibrator.get_energy_intervals(4200.0)
    e90 = energy_intervals["interval90"]
    assert e90["lower"] < 4200.0 < e90["upper"]
    assert e90["margin"] == 125.4


def test_local_model_explainability():
    """Verify TreeSHAP local feature attributions extract top contributing features."""
    forecaster = CorridorForecaster()
    res = forecaster.predict_traffic_speed("urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01", 20.0)

    assert "explanation" in res
    exp = res["explanation"]
    assert "baseValue" in exp
    assert "topContributors" in exp
    assert len(exp["topContributors"]) > 0

    top_feat = exp["topContributors"][0]
    assert "feature" in top_feat
    assert "displayName" in top_feat
    assert "contribution" in top_feat
    assert top_feat["impact"] in ["INCREASES", "DECREASES"]


def test_environmental_anomaly_detector():
    """Verify Isolation Forest and Z-score anomaly detector flags acute pollution spikes."""
    detector = EnvironmentalAnomalyDetector()

    # Normal ambient reading
    normal_res = detector.evaluate_reading(
        sensor_id="urn:ngsi-ld:EnvironmentSensor:PUNE:ENV-VN-AIR-01",
        pm25=42.0,
        pm10=80.0,
        aqi=95.0
    )
    assert not normal_res["isAnomaly"]
    assert normal_res["severity"] == "NORMAL"

    # Acute spike (PM2.5 = 185 ug/m3)
    spike_res = detector.evaluate_reading(
        sensor_id="urn:ngsi-ld:EnvironmentSensor:PUNE:ENV-VN-AIR-01",
        pm25=185.0,
        pm10=320.0,
        aqi=340.0
    )
    assert spike_res["isAnomaly"]
    assert spike_res["severity"] == "CRITICAL"
    assert spike_res["zScore"] > 3.0
    assert len(spike_res["reasons"]) > 0


def test_rule_engine_environmental_anomaly_advisory():
    """Verify environmental anomaly reading generates actionable advisory recommendation."""
    rec = rule_engine.evaluate_environmental_reading(
        sensor_id="urn:ngsi-ld:EnvironmentSensor:PUNE:ENV-VN-AIR-01",
        pm25=190.0,
        pm10=350.0,
        aqi=360.0
    )
    assert rec is not None
    assert rec.domain == RecommendationDomain.ENVIRONMENT
    assert rec.severity == RecommendationSeverity.CRITICAL
    assert rec.humanApprovalRequired is True
    assert "Air Quality Anomaly Detected" in rec.title


def test_fiware_ngsi_ld_export():
    """Verify FIWARE adapter produces valid ETSI GS CIM 009 / NGSI-LD entities."""
    context = FIWAREOrionLDAdapter.get_core_context()
    assert "@context" in context

    entities = FIWAREOrionLDAdapter.export_all_entities()
    assert len(entities) > 0

    # Validate intersection entity structure
    intersections = [e for e in entities if e["type"] == "RoadIntersection"]
    assert len(intersections) >= 2
    for ix in intersections:
        assert "@context" in ix
        assert "name" in ix and ix["name"]["type"] == "Property"
        assert "location" in ix and ix["location"]["type"] == "GeoProperty"
        assert "connectedSegments" in ix and ix["connectedSegments"]["type"] == "Relationship"

    # Validate road segment entity structure
    segments = [e for e in entities if e["type"] == "RoadSegment"]
    assert len(segments) >= 8
    for seg in segments:
        assert seg["lengthMeters"]["type"] == "Property"
        assert seg["freeFlowSpeed"]["unitCode"] == "KMH"


def test_api_forecast_conformal_and_explainability():
    """Verify API endpoints return conformal intervals and local feature explanations."""
    resp = client.get("/api/v1/forecasts/traffic/urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01?current_speed=22.0")
    assert resp.status_code == 200
    data = resp.json()

    assert "conformalIntervals" in data
    assert data["conformalIntervals"]["interval90"]["margin"] == 4.80
    assert "explanation" in data
    assert len(data["explanation"]["topContributors"]) > 0

    energy_resp = client.get("/api/v1/forecasts/energy/urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01?current_kw=4500.0")
    assert energy_resp.status_code == 200
    e_data = energy_resp.json()
    assert "conformalIntervals" in e_data
    assert "explanation" in e_data


def test_api_interop_endpoints():
    """Verify FastAPI interop routes export NGSI-LD context and entities."""
    ctx_resp = client.get("/api/v1/interop/ngsi-ld/context")
    assert ctx_resp.status_code == 200
    assert "@context" in ctx_resp.json()

    ent_resp = client.get("/api/v1/interop/ngsi-ld/entities?type=RoadSegment")
    assert ent_resp.status_code == 200
    ents = ent_resp.json()
    assert len(ents) >= 8
    assert all(e["type"] == "RoadSegment" for e in ents)
