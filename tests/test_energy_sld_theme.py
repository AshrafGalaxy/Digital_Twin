"""Verification checks for Task 3: Energy Microgrid SLD & Power Flow Light/Dark theme support."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SLD_PATH = ROOT / "frontend" / "src" / "components" / "energy" / "MicrogridSLDCanvas.tsx"
ENERGY_VIEW_PATH = ROOT / "frontend" / "src" / "components" / "views" / "EnergyAnalyticsView.tsx"


def test_microgrid_sld_adapts_to_light_and_dark_themes() -> None:
    """MicrogridSLDCanvas must observe data-theme and avoid hardcoded dark-only canvas colors."""
    src = SLD_PATH.read_text(encoding="utf-8")

    assert "data-theme" in src
    assert "MutationObserver" in src
    assert "sldPalette" in src
    assert "background: sldPalette.surfaceCanvas" in src
    assert "backgroundColor: sldPalette.surfaceCanvas" in src
    assert "fill={sldPalette.textPrimary}" in src


def test_energy_analytics_summary_uses_theme_tokens() -> None:
    """EnergyAnalyticsView power-flow summary cards must use CSS theme tokens."""
    src = ENERGY_VIEW_PATH.read_text(encoding="utf-8")
    assert "var(--color-success)" in src
    assert "var(--color-accent-violet)" in src
