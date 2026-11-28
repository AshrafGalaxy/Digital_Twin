"""Verification tests for WebGL context loss recovery ([ENH-05] / Issue #61)."""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
WEBGL_HELPER_PATH = ROOT / "frontend" / "src" / "utils" / "webglRecovery.ts"
WEBGL_OVERLAY_PATH = ROOT / "frontend" / "src" / "components" / "common" / "WebGLRecoveryOverlay.tsx"
ERROR_BOUNDARY_PATH = ROOT / "frontend" / "src" / "components" / "common" / "ErrorBoundary.tsx"
MAP_VIEW_PATH = ROOT / "frontend" / "src" / "components" / "MapOperationsView.tsx"
CESIUM_VIEW_PATH = ROOT / "frontend" / "src" / "components" / "CesiumCorridorViewer.tsx"

EMOJI_PATTERN = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F]")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_webgl_recovery_utility_contracts() -> None:
    """Shared canvas helper must preventDefault on loss and cleanly detach listeners."""
    src = _read(WEBGL_HELPER_PATH)

    assert "export function attachWebGLContextListeners(" in src
    assert "'webglcontextlost'" in src
    assert "'webglcontextrestored'" in src
    assert "event.preventDefault();" in src
    assert "handlers.onLost(event);" in src
    assert "handlers.onRestored(event);" in src
    assert "removeEventListener('webglcontextlost', handleLost, false)" in src
    assert "removeEventListener('webglcontextrestored', handleRestored, false)" in src


def test_webgl_recovery_overlay_accessibility_and_hygiene() -> None:
    """Operator recovery overlay must expose accessible alert status and rebuild action."""
    src = _read(WEBGL_OVERLAY_PATH)

    assert 'role="alert"' in src
    assert 'aria-live="assertive"' in src
    assert "AlertTriangle" in src
    assert "RotateCcw" in src
    assert "onRebuild" in src
    assert "Rebuild {viewLabel}" in src
    assert "--bg-card" in src
    assert "--text-primary" in src


def test_map_operations_view_webgl_recovery_wiring() -> None:
    """2D Mapbox view must recover cleanly from WebGL context loss without page reload."""
    src = _read(MAP_VIEW_PATH)

    assert "attachWebGLContextListeners" in src
    assert "WebGLRecoveryOverlay" in src
    assert "webglContextLost" in src
    assert "mapRebuildNonce" in src
    assert "savedCameraRef" in src
    assert "newMap.getCanvas()" in src
    assert "detachWebGLListeners()" in src
    assert "}, [mapRebuildNonce]);" in src
    assert "}, [basemapMode, mapLoaded]);" in src
    assert "handleManualMapRebuild" in src
    assert "<WebGLRecoveryOverlay" in src
    assert "window.location.reload" not in src


def test_cesium_corridor_viewer_webgl_recovery_wiring() -> None:
    """3D Cesium viewer must detect context/render failure and rebuild viewer + layers."""
    src = _read(CESIUM_VIEW_PATH)

    assert "attachWebGLContextListeners" in src
    assert "WebGLRecoveryOverlay" in src
    assert "webglContextLost" in src
    assert "viewerRebuildNonce" in src
    assert "savedCameraRef" in src
    assert "scene.renderError.addEventListener" in src
    assert "detachWebGLListeners()" in src
    assert "removeRenderErrorListener()" in src
    assert "vehiclesCollectionRef.current = null;" in src
    assert "signalsCollectionRef.current = null;" in src
    assert "[viewerRebuildNonce]" in src
    assert "[currentTheme, viewerRebuildNonce]" in src
    assert "[effectiveBasemap, viewerRebuildNonce]" in src
    assert "[corridorGeoJson, currentTheme, viewerRebuildNonce]" in src
    assert "[liveStates, roadSegments, viewerRebuildNonce]" in src
    assert "handleManualViewerRebuild" in src
    assert "<WebGLRecoveryOverlay" in src
    assert "window.location.reload" not in src


def test_error_boundary_preserves_render_exception_isolation() -> None:
    """ErrorBoundary must remain wired for normal React render exceptions with clean remount."""
    src = _read(ERROR_BOUNDARY_PATH)

    assert "getDerivedStateFromError" in src
    assert "componentDidCatch" in src
    assert "resetCount" in src
    assert "<Fragment key={this.state.resetCount}>" in src
    assert "Recover Component" in src
    assert "--bg-card" in src
    assert "zIndex: 100" in src


def test_modified_webgl_recovery_files_zero_forbidden_characters() -> None:
    """All WebGL recovery source and test files must avoid emojis and em/en dashes."""
    for path in (
        WEBGL_HELPER_PATH,
        WEBGL_OVERLAY_PATH,
        ERROR_BOUNDARY_PATH,
        MAP_VIEW_PATH,
        CESIUM_VIEW_PATH,
        Path(__file__),
    ):
        text = _read(path)
        assert "\u2014" not in text, f"Found em dash in {path}"
        assert "\u2013" not in text, f"Found en dash in {path}"
        assert not EMOJI_PATTERN.search(text), f"Found emoji in {path}"
