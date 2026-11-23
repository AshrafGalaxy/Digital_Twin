"""
test_microgrid_sld_canvas.py

Hermetic verification tests for Issue #20 (ENERGY-08):
Interactive Microgrid Single-Line Diagram (SLD) & Power Flow Canvas.
Verifies frontend component architecture, SVG structure, directional power flow
particle animation rules, thermal loading thresholds, zero emojis, and zero em dashes.
"""

import re
from pathlib import Path
import pytest


def test_microgrid_sld_canvas_component_exists():
    """Verify that MicrogridSLDCanvas.tsx exists and exports the component."""
    canvas_path = Path("frontend/src/components/energy/MicrogridSLDCanvas.tsx")
    assert canvas_path.exists(), "MicrogridSLDCanvas.tsx must exist"
    
    content = canvas_path.read_text(encoding="utf-8")
    assert "export const MicrogridSLDCanvas" in content
    assert "MicrogridSLDCanvasProps" in content


def test_microgrid_sld_canvas_zero_emojis():
    """Verify strictly zero emojis in MicrogridSLDCanvas.tsx."""
    canvas_path = Path("frontend/src/components/energy/MicrogridSLDCanvas.tsx")
    content = canvas_path.read_text(encoding="utf-8")
    
    # Common emoji Unicode blocks
    emoji_pattern = re.compile(
        r"[\U0001F600-\U0001F64F"  # Emoticons
        r"\U0001F300-\U0001F5FF"  # Misc Symbols & Pictographs
        r"\U0001F680-\U0001F6FF"  # Transport & Map
        r"\U0001F1E0-\U0001F1FF"  # Flags
        r"\U00002702-\U000027B0"  # Dingbats
        r"\U0001F900-\U0001F9FF"  # Supplemental Symbols & Pictographs
        r"]+",
        flags=re.UNICODE,
    )
    matches = emoji_pattern.findall(content)
    assert len(matches) == 0, f"Found emojis in MicrogridSLDCanvas.tsx: {matches}"


def test_microgrid_sld_canvas_zero_em_dashes():
    """Verify strictly zero em dashes or en dashes in MicrogridSLDCanvas.tsx."""
    canvas_path = Path("frontend/src/components/energy/MicrogridSLDCanvas.tsx")
    content = canvas_path.read_text(encoding="utf-8")
    
    assert "\u2014" not in content, "Found em dash in MicrogridSLDCanvas.tsx"
    assert "\u2013" not in content, "Found en dash in MicrogridSLDCanvas.tsx"


def test_microgrid_sld_canvas_schematic_nodes():
    """Verify required electrical schematic nodes are present in the SVG layout."""
    canvas_path = Path("frontend/src/components/energy/MicrogridSLDCanvas.tsx")
    content = canvas_path.read_text(encoding="utf-8")

    # PCC Substation Node
    assert "Primary Substation (PCC)" in content
    assert "CB-01 CLOSED" in content
    assert "Dyn11 Step-Down Trafo" in content

    # 415V Busbar
    assert "415V AC THREE-PHASE LOW-VOLTAGE BUSBAR" in content

    # Distributed Energy Resources (DERs)
    assert "Rooftop Solar PV" in content
    assert "Substation Support BESS" in content

    # Feeder Branches & Commercial Loads
    assert "Feeder 1 (Retail)" in content
    assert "Feeder 2 (Enterprise)" in content
    assert "Feeder 3 (Transit)" in content
    assert "Commercial Retail Zone" in content
    assert "Commercial Enterprise" in content
    assert "EV DC Fast Plaza" in content
    assert "Hospitality Zone" in content


def test_microgrid_sld_canvas_power_flow_particles():
    """Verify SVG keyframe animations for dynamic directional power flow."""
    canvas_path = Path("frontend/src/components/energy/MicrogridSLDCanvas.tsx")
    content = canvas_path.read_text(encoding="utf-8")

    # Keyframes
    assert "@keyframes sldFlowDown" in content
    assert "@keyframes sldFlowUp" in content
    assert "stroke-dasharray" in content or "strokeDasharray" in content

    # Flow classes
    assert "sld-flow-grid" in content
    assert "sld-flow-solar" in content
    assert "sld-flow-bess" in content
    assert "sld-flow-load" in content
    assert "sld-flow-ev" in content


def test_microgrid_sld_canvas_feeder_thermal_loading():
    """Verify feeder thermal loading ratio thresholds (0.70 and 0.85)."""
    canvas_path = Path("frontend/src/components/energy/MicrogridSLDCanvas.tsx")
    content = canvas_path.read_text(encoding="utf-8")

    assert "0.85" in content, "Must evaluate >= 0.85 critical overload ratio"
    assert "0.70" in content, "Must evaluate >= 0.70 warning ratio"
    assert "#F43F5E" in content, "Must include rose color for critical overload"
    assert "#F59E0B" in content, "Must include amber color for warning"
    assert "#10B981" in content, "Must include emerald color for nominal"


def test_microgrid_sld_canvas_non_actuation_notice():
    """Verify non-actuation safety disclaimer on the canvas."""
    canvas_path = Path("frontend/src/components/energy/MicrogridSLDCanvas.tsx")
    content = canvas_path.read_text(encoding="utf-8")

    assert "Advisory Only (Non-Actuating)" in content
    assert "Breaker actuation requires field personnel authorization" in content


def test_energy_analytics_view_integrates_sld_canvas():
    """Verify that EnergyAnalyticsView.tsx integrates MicrogridSLDCanvas with view switcher."""
    view_path = Path("frontend/src/components/views/EnergyAnalyticsView.tsx")
    content = view_path.read_text(encoding="utf-8")

    assert "import { MicrogridSLDCanvas } from '../energy/MicrogridSLDCanvas';" in content
    assert "topologyViewMode" in content
    assert "SLD Schematic Canvas" in content
    assert "Hierarchical Tree" in content
    assert "<MicrogridSLDCanvas" in content
    assert "\u2014" not in content, "Found em dash in EnergyAnalyticsView.tsx"
    assert "\u2013" not in content, "Found en dash in EnergyAnalyticsView.tsx"
