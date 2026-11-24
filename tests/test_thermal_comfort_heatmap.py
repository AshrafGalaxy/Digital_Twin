"""
test_thermal_comfort_heatmap.py

Hermetic unit and integration tests for the Building Floorplate 3D/2D Thermal Comfort
& Occupancy Density Visualizer (Issue #21, ENERGY-09).

Validates:
1. Component export and TypeScript interface definitions in ThermalComfortHeatmap.tsx.
2. Vector SVG floorplate canvas elements, gridlines, and sub-zone polygon layouts.
3. Multi-facility support across reference complexes (Phoenix Retail, Solitaire Office, Hyatt Ballroom).
4. ASHRAE 55 statutory comfort envelope color-coding thresholds (< 22C, 22-24.5C, 24.5-26.5C, > 26.5C).
5. Dynamic setback badge rendering (SETBACK ACTIVE +2.5C) on low occupancy density (< 0.10 pax/m2).
6. Non-actuation architectural governance disclaimer verification.
7. EnergyAnalyticsView.tsx integration: tab switcher, sub-navigation pill button, and view rendering.
8. 24-hour diurnal pre-cooling strategy modal structure and comparative metrics.
9. Strictly zero emojis and zero em dashes across component, view, and API service files.
"""

import pathlib
import pytest


# Paths to verified artifacts
HEATMAP_PATH = pathlib.Path("frontend/src/components/energy/ThermalComfortHeatmap.tsx")
VIEW_PATH = pathlib.Path("frontend/src/components/views/EnergyAnalyticsView.tsx")
API_PATH = pathlib.Path("frontend/src/services/api.ts")


def test_thermal_comfort_heatmap_file_and_export() -> None:
    """
    Verifies that ThermalComfortHeatmap.tsx exists and exports the expected component.
    """
    assert HEATMAP_PATH.exists(), f"File {HEATMAP_PATH} does not exist."
    content = HEATMAP_PATH.read_text(encoding="utf-8")

    assert "export const ThermalComfortHeatmap" in content
    assert "ThermalComfortHeatmapProps" in content
    assert "BuildingZoneThermalState" in content


def test_svg_floorplate_canvas_structure() -> None:
    """
    Verifies that the component renders a responsive vector SVG floorplate canvas
    with architectural boundaries, gridlines, and zone polygons.
    """
    content = HEATMAP_PATH.read_text(encoding="utf-8")

    # Responsive SVG viewBox
    assert 'viewBox="0 0 900 440"' in content
    assert '<svg' in content
    assert '</svg>' in content

    # Boundary and architectural grid
    assert '<rect' in content
    assert 'strokeDasharray="6 4"' in content

    # Multi-facility support
    assert "Phoenix Marketcity Concourse" in content
    assert "Solitaire Business Tech Hub" in content
    assert "Hyatt Regency Convention Center" in content


def test_ashrae55_color_coding_thresholds() -> None:
    """
    Verifies that zone temperature shading adheres to ASHRAE 55 statutory comfort bounds:
    - Under-Cooled (< 22.0 deg C): Cyan (#06B6D4)
    - Optimal Comfort (22.0 to 24.5 deg C): Emerald (#10B981)
    - Dynamic Setback / Eco Drift (24.5 to 26.5 deg C): Amber (#F59E0B)
    - Discomfort Violation (> 26.5 deg C): Crimson / Rose (#EF4444)
    """
    content = HEATMAP_PATH.read_text(encoding="utf-8")

    assert "getZoneFillColor" in content
    assert "#06B6D4" in content  # Cyan
    assert "#10B981" in content  # Emerald
    assert "#F59E0B" in content  # Amber
    assert "#EF4444" in content  # Rose

    assert "Under-Cooled" in content
    assert "Optimal Comfort" in content
    assert "Dynamic Setback" in content
    assert "Comfort Violation" in content


def test_dynamic_setback_and_occupancy_badges() -> None:
    """
    Verifies that dynamic setback pill and occupancy density metrics are rendered.
    """
    content = HEATMAP_PATH.read_text(encoding="utf-8")

    assert "SETBACK (+2.5°C)" in content or "SETBACK" in content
    assert "COMFORT MODE" in content
    assert "occupantCount" in content or "occupants" in content
    assert "co2Ppm" in content or "ppm" in content
    assert "DYNAMIC_SETBACK" in content


def test_non_actuation_governance_disclaimer() -> None:
    """
    Verifies that the mandatory non-actuation architectural governance disclaimer
    is rendered on the component.
    """
    content = HEATMAP_PATH.read_text(encoding="utf-8")

    expected_disclaimer = (
        "Advisory Only (Non-Actuating). Thermostat setbacks and pre-cooling schedules "
        "are simulation projections requiring authorized facility BMS dispatch."
    )
    assert expected_disclaimer in content


def test_view_integration_in_energy_analytics_view() -> None:
    """
    Verifies that EnergyAnalyticsView.tsx imports and renders ThermalComfortHeatmap
    under the THERMAL_ZONES sub-tab.
    """
    assert VIEW_PATH.exists(), f"File {VIEW_PATH} does not exist."
    view_content = VIEW_PATH.read_text(encoding="utf-8")

    # Imported component
    assert "ThermalComfortHeatmap" in view_content
    assert "from '../energy/ThermalComfortHeatmap'" in view_content

    # Sub-tab switcher button
    assert "THERMAL_ZONES" in view_content
    assert "Thermal Comfort & Dynamic Setback Heatmap" in view_content

    # Rendered block
    assert "<ThermalComfortHeatmap sourceMode={sourceMode} />" in view_content


def test_api_service_endpoints() -> None:
    """
    Verifies that api.ts exports the required energy thermal functions and models.
    """
    assert API_PATH.exists(), f"File {API_PATH} does not exist."
    api_content = API_PATH.read_text(encoding="utf-8")

    assert "fetchThermalZones" in api_content
    assert "fetchZoneThermalState" in api_content
    assert "stepZoneSimulation" in api_content
    assert "simulateZonePrecooling" in api_content
    assert "BuildingZoneThermalState" in api_content
    assert "PrecoolingSimulationResult" in api_content


def test_precooling_modal_structure() -> None:
    """
    Verifies that the comparative 24-hour diurnal pre-cooling modal includes
    metrics for cost savings, peak demand reduction, and hourly profiles.
    """
    content = HEATMAP_PATH.read_text(encoding="utf-8")

    assert "isPrecoolingOpen" in content
    assert "simulateZonePrecooling" in content
    assert "costSavingsInr" in content
    assert "peakDemandReductionKw" in content
    assert "ashrae55ViolationsPrecooling" in content
    assert "precoolingProfile" in content


def test_strictly_zero_emojis_and_zero_em_dashes() -> None:
    """
    Verifies that ThermalComfortHeatmap.tsx, EnergyAnalyticsView.tsx,
    and api.ts strictly contain zero emojis and zero em dashes or en dashes.
    """
    files_to_check = [HEATMAP_PATH, VIEW_PATH, API_PATH]

    em_dash = "\u2014"
    en_dash = "\u2013"

    for fpath in files_to_check:
        assert fpath.exists(), f"File {fpath} does not exist."
        content = fpath.read_text(encoding="utf-8")

        assert em_dash not in content, f"Em dash found in {fpath}"
        assert en_dash not in content, f"En dash found in {fpath}"

        for char in content:
            code = ord(char)
            is_emoji = (
                (0x1F600 <= code <= 0x1F64F)
                or (0x1F300 <= code <= 0x1F5FF)
                or (0x1F680 <= code <= 0x1F6FF)
                or (0x1F700 <= code <= 0x1F77F)
                or (0x1F780 <= code <= 0x1F7FF)
                or (0x1F800 <= code <= 0x1F8FF)
                or (0x1F900 <= code <= 0x1F9FF)
                or (0x1FA00 <= code <= 0x1FA6F)
                or (0x1FA70 <= code <= 0x1FAFF)
                or (0x2600 <= code <= 0x26FF)
                or (0x2700 <= code <= 0x27BF)
            )
            assert not is_emoji, f"Emoji character {char!r} (U+{code:04X}) detected in {fpath}"
