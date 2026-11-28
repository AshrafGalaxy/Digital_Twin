"""Verification checks for Task 1: Operations basemap controls, active buttons, and marker contrast."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAP_VIEW_PATH = ROOT / "frontend" / "src" / "components" / "MapOperationsView.tsx"
INDEX_CSS_PATH = ROOT / "frontend" / "src" / "index.css"


def test_operations_toolbar_has_only_satellite_and_streets_basemaps() -> None:
    """Basemap switcher must expose Satellite and Streets only (top theme toggle handles Dark/Light)."""
    src = MAP_VIEW_PATH.read_text(encoding="utf-8")

    assert "setBasemapMode('satellite')" in src
    assert "setBasemapMode('streets')" in src
    assert "setBasemapMode('dark')" not in src
    assert "Dark Operations Canvas" not in src


def test_operations_toolbar_and_markers_use_theme_tokens() -> None:
    """Segmented toolbar active state and map markers must adapt cleanly to Light and Dark themes."""
    css = INDEX_CSS_PATH.read_text(encoding="utf-8")
    src = MAP_VIEW_PATH.read_text(encoding="utf-8")

    assert "background: var(--color-primary-subtle);" in css
    assert "color: var(--color-primary);" in css
    assert ".energy-entity-marker" in css
    assert "[data-theme=\"light\"] .energy-entity-marker" in css
    assert "[data-theme=\"light\"] .env-station-marker" in css
    assert "energyEl.style.backgroundColor = '#161B22'" not in src
    assert "envEl.style.backgroundColor = '#161B22'" not in src
