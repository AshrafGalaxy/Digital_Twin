"""
test_frontend_code_splitting.py

Automated hermetic tests verifying frontend bundle code splitting and lazy loading
for Issue #62 (ENH-06):
1. Unconditional static/source invariants across App.tsx, MapOperationsView.tsx,
   vite.config.ts, and ViewLoadingFallback.tsx (runs on CI without dist/).
2. Zero emojis and zero em/en dashes across all Issue #62 files.
3. Conditional Vite dist artifact verification when frontend/dist/assets exists
   locally, confirming isolated vendor chunks, lazy view chunks, Cesium
   isolation, and entry index-*.js chunk under 500 kB.
"""

from pathlib import Path
import re

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
SRC_DIR = FRONTEND_DIR / "src"
APP_TSX = SRC_DIR / "App.tsx"
MAP_VIEW_TSX = SRC_DIR / "components" / "MapOperationsView.tsx"
VITE_CONFIG_TS = FRONTEND_DIR / "vite.config.ts"
FALLBACK_TSX = SRC_DIR / "components" / "common" / "ViewLoadingFallback.tsx"
DIST_DIR = FRONTEND_DIR / "dist"
DIST_ASSETS_DIR = DIST_DIR / "assets"
DIST_CESIUM_DIR = DIST_DIR / "cesium"

LAZY_VIEW_NAMES = (
    "AuthPageView",
    "ProvisioningView",
    "MapOperationsView",
    "TrafficAnalyticsView",
    "EnergyAnalyticsView",
    "EnvironmentContextView",
    "ScenarioStudioView",
    "RecommendationsView",
    "SystemHealthView",
    "PilotEvaluationView",
)

LAZY_OVERLAY_NAMES = (
    "ScenarioStudio",
    "AdvisoryCenterModal",
    "AdminProvisioningModal",
    "EntityDetailDrawer",
)

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FAFF"
    "\u2600-\u26FF"
    "\u2700-\u27BF"
    "]"
)


def _strip_comments_minimal(text: str) -> str:
    """Remove single-line // comments for import inspection."""
    return "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith("//")
    )


def test_app_tsx_lazy_loads_views_with_suspense() -> None:
    """Verify App.tsx uses React.lazy + Suspense and avoids static view imports."""
    assert APP_TSX.is_file(), f"App.tsx not found at {APP_TSX}"
    content = APP_TSX.read_text(encoding="utf-8")
    code_only = _strip_comments_minimal(content)

    assert "React.lazy" in code_only, "App.tsx must use React.lazy for route/view splitting"
    assert "Suspense" in code_only, "App.tsx must wrap lazy views in React Suspense"
    assert "ViewLoadingFallback" in code_only, "App.tsx must render ViewLoadingFallback"
    assert re.search(
        r"import\s*\{[^}]*\bLandingPageView\b[^}]*\}\s*from\s*['\"][^'\"]+['\"]",
        code_only,
    ), "LandingPageView should remain an eager import for fast initial paint"

    static_import_block = "\n".join(
        re.findall(r"^import\s+[\s\S]*?from\s+['\"][^'\"]+['\"];?", code_only, flags=re.MULTILINE)
    )

    for component_name in (*LAZY_VIEW_NAMES, *LAZY_OVERLAY_NAMES):
        assert not re.search(
            rf"\b{re.escape(component_name)}\b",
            static_import_block,
        ), f"{component_name} must not be statically imported in App.tsx"

        assert re.search(
            rf"const\s+{re.escape(component_name)}\s*=\s*lazyNamed\(",
            code_only,
        ), f"{component_name} must be declared with lazyNamed() in App.tsx"

        assert f"<{component_name}" in code_only, (
            f"{component_name} must be rendered inside App.tsx"
        )

    assert "<Suspense fallback={<ViewLoadingFallback" in code_only, (
        "App.tsx must pass ViewLoadingFallback to Suspense fallback for lazy views"
    )


def test_map_operations_view_lazy_loads_cesium_viewer() -> None:
    """Verify MapOperationsView.tsx lazy-loads CesiumCorridorViewer inside Suspense."""
    assert MAP_VIEW_TSX.is_file(), f"MapOperationsView.tsx not found at {MAP_VIEW_TSX}"
    content = MAP_VIEW_TSX.read_text(encoding="utf-8")
    code_only = _strip_comments_minimal(content)

    static_import_block = "\n".join(
        re.findall(r"^import\s+[\s\S]*?from\s+['\"][^'\"]+['\"];?", code_only, flags=re.MULTILINE)
    )
    assert "CesiumCorridorViewer" not in static_import_block, (
        "CesiumCorridorViewer must not be statically imported in MapOperationsView.tsx"
    )
    assert "Suspense" in static_import_block, (
        "MapOperationsView.tsx must import Suspense from react"
    )
    assert "ViewLoadingFallback" in static_import_block, (
        "MapOperationsView.tsx must import ViewLoadingFallback"
    )

    assert re.search(
        r"const\s+CesiumCorridorViewer\s*=\s*React\.lazy\(",
        code_only,
    ), "CesiumCorridorViewer must be declared via React.lazy in MapOperationsView.tsx"
    assert "import('./CesiumCorridorViewer')" in code_only, (
        "CesiumCorridorViewer lazy loader must dynamically import ./CesiumCorridorViewer"
    )
    assert re.search(
        r"\{is3DMode\s*&&\s*\(\s*<Suspense\s+fallback=\{<ViewLoadingFallback[^>]*>\}>\s*<CesiumCorridorViewer",
        code_only,
        flags=re.DOTALL,
    ), "CesiumCorridorViewer must be wrapped in Suspense with ViewLoadingFallback inside is3DMode guard"


def test_vite_config_manual_chunks_configuration() -> None:
    """Verify vite.config.ts defines manualChunks with slash normalization for vendor splitting."""
    assert VITE_CONFIG_TS.is_file(), f"vite.config.ts not found at {VITE_CONFIG_TS}"
    content = VITE_CONFIG_TS.read_text(encoding="utf-8")

    assert "plugins:" in content and "react()" in content and "cesium()" in content, (
        "vite.config.ts must preserve react() and cesium() plugins"
    )
    assert "manualChunks" in content, "vite.config.ts must configure rollupOptions.output.manualChunks"
    assert "replace(/\\\\/g, '/')" in content, (
        "vite.config.ts manualChunks must normalize Windows backslashes to forward slashes"
    )
    assert "'vendor-cesium'" in content, "vite.config.ts must map Cesium modules to vendor-cesium"
    assert "'vendor-mapbox'" in content, "vite.config.ts must map Mapbox/MapLibre modules to vendor-mapbox"
    assert "'vendor-motion'" in content, "vite.config.ts must map framer-motion to vendor-motion"
    assert "'vendor-icons'" in content, "vite.config.ts must map lucide-react to vendor-icons"
    assert "'vendor-react'" in content, "vite.config.ts must map react/react-dom/scheduler to vendor-react"


def test_view_loading_fallback_component_accessibility() -> None:
    """Verify ViewLoadingFallback.tsx exists and implements accessible status semantics."""
    assert FALLBACK_TSX.is_file(), f"ViewLoadingFallback.tsx not found at {FALLBACK_TSX}"
    content = FALLBACK_TSX.read_text(encoding="utf-8")

    assert "export const ViewLoadingFallback" in content
    assert 'role="status"' in content, "ViewLoadingFallback must include role=\"status\""
    assert 'aria-live="polite"' in content, "ViewLoadingFallback must include aria-live=\"polite\""
    assert "Loader2" in content, "ViewLoadingFallback must use Lucide Loader2 vector icon"
    assert "--color-surface" in content and "--color-text" in content, (
        "ViewLoadingFallback must use semantic theme tokens"
    )


def test_issue_62_files_contain_zero_emojis_and_zero_dashes() -> None:
    """Enforce AGENTS.md invariants: zero emojis and zero em/en dashes in Issue #62 files."""
    files_to_check = [
        VITE_CONFIG_TS,
        APP_TSX,
        MAP_VIEW_TSX,
        FALLBACK_TSX,
        Path(__file__).resolve(),
    ]
    for file_path in files_to_check:
        assert file_path.is_file(), f"Expected file not found: {file_path}"
        content = file_path.read_text(encoding="utf-8")
        assert "\u2014" not in content, f"Em dash found in {file_path}"
        assert "\u2013" not in content, f"En dash found in {file_path}"
        emoji_match = EMOJI_PATTERN.search(content)
        assert emoji_match is None, f"Emoji character {emoji_match.group(0)!r} found in {file_path}"


def test_dist_code_splitting_artifacts_when_built() -> None:
    """
    Conditionally verify built Vite chunks when frontend/dist/assets exists locally.
    On clean CI Python runners where npm run build has not run, this check returns cleanly
    while the static source invariant tests above always execute unconditionally.
    """
    if not DIST_ASSETS_DIR.is_dir():
        return

    asset_files = {p.name: p for p in DIST_ASSETS_DIR.iterdir() if p.is_file()}
    js_files = [name for name in asset_files if name.endswith(".js")]

    # 1. Entry index-*.js chunk must exist and stay well below 500 kB (500 * 1024 bytes)
    index_chunks = [name for name in js_files if name.startswith("index-") and name.endswith(".js")]
    assert len(index_chunks) == 1, f"Expected single entry index-*.js chunk, got {index_chunks}"
    entry_chunk = asset_files[index_chunks[0]]
    entry_size_bytes = entry_chunk.stat().st_size
    assert entry_size_bytes < 500 * 1024, (
        f"Entry chunk {entry_chunk.name} is {entry_size_bytes} bytes (>= 500 kB limit)"
    )

    # 2. Dedicated vendor-mapbox chunk
    mapbox_chunks = [name for name in js_files if name.startswith("vendor-mapbox-")]
    assert len(mapbox_chunks) >= 1, f"Expected vendor-mapbox-*.js chunk in {js_files}"

    # 3. Dedicated vendor-motion, vendor-icons, and vendor-react chunks
    assert any(name.startswith("vendor-motion-") for name in js_files), "Missing vendor-motion-*.js chunk"
    assert any(name.startswith("vendor-icons-") for name in js_files), "Missing vendor-icons-*.js chunk"
    assert any(name.startswith("vendor-react-") for name in js_files), "Missing vendor-react-*.js chunk"

    # 4. Cesium isolation: either vendor-cesium-*.js chunk OR externalized dist/cesium/Cesium.js + lazy CesiumCorridorViewer-*.js
    has_vendor_cesium_js = any(name.startswith("vendor-cesium-") for name in js_files)
    has_external_cesium = (DIST_CESIUM_DIR / "Cesium.js").is_file()
    has_lazy_cesium_viewer = any(name.startswith("CesiumCorridorViewer-") for name in js_files)
    assert has_vendor_cesium_js or (has_external_cesium and has_lazy_cesium_viewer), (
        "Cesium runtime must be isolated in vendor-cesium-*.js or externalized dist/cesium/Cesium.js "
        "with a lazy CesiumCorridorViewer-*.js chunk"
    )
    assert has_lazy_cesium_viewer, "Expected lazy CesiumCorridorViewer-*.js chunk"

    # 5. Multiple lazy operator view chunks exist
    expected_view_prefixes = (
        "EnergyAnalyticsView-",
        "TrafficAnalyticsView-",
        "MapOperationsView-",
        "EnvironmentContextView-",
        "ScenarioStudioView-",
        "RecommendationsView-",
        "SystemHealthView-",
        "PilotEvaluationView-",
        "AuthPageView-",
        "ProvisioningView-",
    )
    for prefix in expected_view_prefixes:
        assert any(name.startswith(prefix) for name in js_files), (
            f"Expected lazy view chunk starting with {prefix} in dist/assets"
        )
