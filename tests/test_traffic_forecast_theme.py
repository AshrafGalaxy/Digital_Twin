"""Verification checks for Task 2: Traffic Analytics & ForecastPanel light-theme styling."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRAFFIC_VIEW_PATH = ROOT / "frontend" / "src" / "components" / "views" / "TrafficAnalyticsView.tsx"
INDEX_CSS_PATH = ROOT / "frontend" / "src" / "index.css"


def test_corridor_aggregate_condition_uses_theme_surface() -> None:
    """Corridor Aggregate Condition banner must use theme card token instead of dark slate."""
    src = TRAFFIC_VIEW_PATH.read_text(encoding="utf-8")
    assert "corridor-aggregate-banner" in src
    assert "rgba(15, 23, 42, 0.6)" not in src
    assert "background: 'var(--bg-card)'" in src


def test_forecast_panel_boxes_use_theme_tokens() -> None:
    """15-Min Speed Forecast, Conformal Calibration, and TreeSHAP boxes must adapt to Light theme."""
    css = INDEX_CSS_PATH.read_text(encoding="utf-8")
    assert ".forecast-hero-card {\n  background: var(--bg-card);" in css
    assert ".forecast-explanation-box {\n  background: var(--bg-card);" in css
    assert "[data-theme=\"light\"] .forecast-conformal-box" in css
    assert "[data-theme=\"light\"] .conformal-badge" in css
