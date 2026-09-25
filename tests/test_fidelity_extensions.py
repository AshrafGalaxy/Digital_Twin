"""
test_fidelity_extensions.py

Comprehensive test suite verifying analytical and fidelity extensions:
1. Conformal Prediction uncertainty calibration bounds.
2. TreeSHAP local feature attribution explainability.
3. Environmental Anomaly Detection on sensor telemetry.
4. FIWARE Orion-LD / NGSI-LD 1.3 interoperability exports.
5. FastAPI forecast and interop API endpoints.
6. Open-Meteo weather client and diurnal fallback.
7. Population Stability Index (PSI) feature drift detection and analytics API.
"""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.ingestion.weather_client import OpenMeteoWeatherClient
from backend.services.anomaly_detector import EnvironmentalAnomalyDetector
from backend.services.fiware_adapter import FIWAREOrionLDAdapter
from backend.services.rule_engine import rule_engine
from backend.schemas.recommendations import RecommendationDomain, RecommendationSeverity
from ml.conformal_calibrator import ConformalPredictionCalibrator
from ml.drift_detector import FeatureDriftDetector
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


@pytest.mark.asyncio
async def test_weather_client_live_and_fallback():
    """Verifies that OpenMeteoWeatherClient fetches or falls back gracefully."""
    weather_client = OpenMeteoWeatherClient(timeout_seconds=3.0)
    weather = await weather_client.get_current_weather()

    assert "temperature_c" in weather
    assert "humidity_pct" in weather
    assert weather["source_mode"] in ["LIVE", "SIMULATION"]
    assert 10.0 <= weather["temperature_c"] <= 50.0
    assert 0.0 <= weather["humidity_pct"] <= 100.0

    # Test diurnal fallback explicitly
    fallback = weather_client._compute_diurnal_fallback(datetime(2026, 9, 20, 14, 0, tzinfo=timezone.utc))
    assert fallback["source_mode"] == "SIMULATION"
    assert fallback["source_id"] == "diurnal-atmospheric-model:pune-corridor"
    assert 20.0 <= fallback["temperature_c"] <= 40.0


def test_feature_drift_detector():
    """Verifies that FeatureDriftDetector calculates PSI and classifies drift correctly."""
    detector = FeatureDriftDetector()
    assert len(detector.reference_df) > 0

    # Inlier sample from reference distribution -> STABLE
    sample_ref = detector.reference_df.sample(200, random_state=42)
    stable_eval = detector.evaluate_drift(sample_ref)
    assert stable_eval["overallStatus"] == "STABLE"
    assert stable_eval["qualityFlag"] == "valid"
    assert stable_eval["maxPsi"] < 0.15

    # Artificially shifted sample -> DRIFT_DETECTED
    shifted_sample = sample_ref.copy()
    shifted_sample["speed_lag_5m"] = shifted_sample["speed_lag_5m"] + 30.0
    drift_eval = detector.evaluate_drift(shifted_sample)
    assert drift_eval["overallStatus"] == "DRIFT_DETECTED"
    assert drift_eval["qualityFlag"] == "suspect"
    assert drift_eval["maxPsi"] >= 0.25
    assert "speed_lag_5m" in drift_eval["driftedFeatures"]


def test_analytics_drift_api_endpoint():
    """Tests the GET /api/v1/analytics/drift endpoint."""
    resp = client.get("/api/v1/analytics/drift?hours_ago=6")
    assert resp.status_code == 200
    data = resp.json()
    assert "overallStatus" in data
    assert "maxPsi" in data
    assert "qualityFlag" in data
    assert "perFeatureMetrics" in data
    assert data["overallStatus"] in ["STABLE", "EARLY_WARNING", "DRIFT_DETECTED"]
