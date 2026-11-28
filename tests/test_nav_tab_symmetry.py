"""Regression checks for symmetric vertical spacing on navigation tab buttons."""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
INDEX_CSS_PATH = ROOT / "frontend" / "src" / "index.css"
HEADER_TSX_PATH = ROOT / "frontend" / "src" / "components" / "Header.tsx"


def _extract_css_block(css_text: str, selector: str) -> str:
    pattern = re.compile(rf"{re.escape(selector)}\s*\{{([^}}]*)\}}", re.MULTILINE)
    match = pattern.search(css_text)
    assert match is not None, f"Missing CSS block for {selector}"
    return match.group(1)


def test_nav_tab_btn_has_symmetric_vertical_padding_and_borders() -> None:
    """All header navigation buttons must have symmetric top/bottom padding and borders."""
    css = INDEX_CSS_PATH.read_text(encoding="utf-8")

    nav_container_block = _extract_css_block(css, ".header-nav-tabs")
    assert "align-items: stretch;" in nav_container_block
    assert "height: 38px;" in nav_container_block

    nav_btn_block = _extract_css_block(css, ".nav-tab-btn")
    assert "padding: 6px 12px;" in nav_btn_block
    assert "border-top: 2px solid transparent;" in nav_btn_block
    assert "border-bottom: 2px solid transparent;" in nav_btn_block
    assert "line-height: 1.15;" in nav_btn_block
    assert "justify-content: center;" in nav_btn_block

    nav_label_block = _extract_css_block(css, ".nav-tab-label")
    assert "display: inline-flex;" in nav_label_block
    assert "align-items: center;" in nav_label_block
    assert "line-height: 1.15;" in nav_label_block


def test_header_renders_nav_tab_label_for_all_menu_tabs() -> None:
    """Header must render every primary view tab with nav-tab-btn and nav-tab-label."""
    tsx = HEADER_TSX_PATH.read_text(encoding="utf-8")
    assert 'className={`nav-tab-btn ${activeTab === tab.id ? \'active\' : \'\'}`}' in tsx
    assert '<span className="nav-tab-label">{tab.label}</span>' in tsx
