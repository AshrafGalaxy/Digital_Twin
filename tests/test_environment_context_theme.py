"""Verification checks for Task 4: Environment Context light-theme warnings, readings, and notices."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENV_VIEW_PATH = ROOT / "frontend" / "src" / "components" / "views" / "EnvironmentContextView.tsx"
INDEX_CSS_PATH = ROOT / "frontend" / "src" / "index.css"


def test_environment_context_readings_and_verdict_use_theme_tokens() -> None:
    """Weather readings and Anomaly Engine verdict banner must use theme tokens."""
    src = ENV_VIEW_PATH.read_text(encoding="utf-8")

    assert "#F0F6FC" not in src
    assert "rgba(22, 27, 34, 0.95)" not in src
    assert "color: 'var(--text-primary)'" in src
    assert "background: 'var(--bg-surface-elevated)'" in src


def test_caveat_evidence_and_notice_banners_support_light_theme() -> None:
    """Integrity caveat banner, evidence box, and notice box must adapt cleanly to Light mode."""
    css = INDEX_CSS_PATH.read_text(encoding="utf-8")

    assert "[data-theme=\"light\"] .integrity-caveat-banner" in css
    assert ".advisory-evidence-box {\n  background: var(--bg-surface-elevated);" in css
    assert ".analytics-notice-box {\n  display: flex;\n  align-items: flex-start;\n  gap: var(--space-2);\n  padding: var(--space-2) var(--space-3);\n  background: var(--bg-surface-elevated);" in css
