"""Verification tests for Operations view LCP and render-blocking optimizations."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML_PATH = ROOT / "frontend" / "index.html"
VITE_CONFIG_PATH = ROOT / "frontend" / "vite.config.ts"
MAP_VIEW_PATH = ROOT / "frontend" / "src" / "components" / "MapOperationsView.tsx"
DIST_INDEX_PATH = ROOT / "frontend" / "dist" / "index.html"


def test_index_html_has_no_render_blocking_external_stylesheets() -> None:
    """index.html must not block initial paint on unused maplibre CDN or Google Fonts CSS."""
    html = INDEX_HTML_PATH.read_text(encoding="utf-8")

    assert "unpkg.com/maplibre-gl" not in html
    assert "fonts.googleapis.com" in html
    assert 'media="print"' in html
    assert "onload=\"this.media='all'\"" in html


def test_vite_config_defers_cesium_head_assets() -> None:
    """vite.config.ts must convert injected Cesium head tags to non-blocking/deferred."""
    cfg = VITE_CONFIG_PATH.read_text(encoding="utf-8")

    assert "nonBlockingCesiumAssets" in cfg
    assert "transformIndexHtml" in cfg
    assert "widgets" in cfg
    assert "Cesium" in cfg
    assert "<script defer src=" in cfg


def test_map_operations_view_defers_mapbox_import_with_placeholder() -> None:
    """MapOperationsView must dynamically import mapbox-gl after first paint and render placeholder."""
    src = MAP_VIEW_PATH.read_text(encoding="utf-8")

    assert "from 'mapbox-gl';" in src
    assert "type MapboxModule = typeof import('mapbox-gl')['default'];" in src
    assert "import mapboxgl from 'mapbox-gl';" not in src
    assert "import 'mapbox-gl/dist/mapbox-gl.css';" not in src
    assert "import('mapbox-gl')" in src
    assert "import('mapbox-gl/dist/mapbox-gl.css')" in src
    assert "requestAnimationFrame" in src
    assert "map-canvas-placeholder" in src


def test_built_dist_index_html_defers_cesium_assets_when_present() -> None:
    """Built dist/index.html (when generated) must not contain blocking Cesium head tags."""
    if not DIST_INDEX_PATH.exists():
        return
    dist_html = DIST_INDEX_PATH.read_text(encoding="utf-8")
    if "/cesium/Widgets/widgets.css" in dist_html:
        assert 'media="print"' in dist_html
    if "/cesium/Cesium.js" in dist_html:
        assert '<script defer src="/cesium/Cesium.js">' in dist_html


def test_operations_error_boundary_prevents_overlay_collision() -> None:
    """ErrorBoundary must isolate floating metrics/legend overlays and use zIndex 100."""
    app_src = (ROOT / "frontend" / "src" / "App.tsx").read_text(encoding="utf-8")
    eb_src = (ROOT / "frontend" / "src" / "components" / "common" / "ErrorBoundary.tsx").read_text(encoding="utf-8")
    css_src = (ROOT / "frontend" / "src" / "index.css").read_text(encoding="utf-8")

    assert "hasOperationsError" in app_src
    assert "!isOperationsTableView && !hasOperationsError" in app_src
    assert "zIndex: 100" in eb_src
    assert "inset: 0" in eb_src
    assert "translateY(-150%)" in css_src
    assert "width: min(368px, calc(100% - 24px));" in css_src
    assert "@media (max-width: 860px)" in css_src
    assert "max-width: calc(100% - 24px);" in css_src
