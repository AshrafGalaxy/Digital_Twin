"""
test_client_telemetry_honesty.py

Automated hermetic tests enforcing Client Telemetry Honesty (Issue #39 [BUG-16]):
1. Verifies frontend/src/App.tsx contains zero Math.random telemetry mutations.
2. Verifies frontend/src/App.tsx contains zero artificial interval timers mutating liveStates or liveEnergyKw.
3. Verifies frontend/src/components/MapOperationsView.tsx contains zero Math.random telemetry mutations.
4. Verifies frontend/src/components/Header.tsx contains staleness thresholding logic (180s SLA threshold,
   distinguishing Synced, Stale, and Awaiting states).
"""

from pathlib import Path
import re
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend" / "src"
APP_TSX = FRONTEND_DIR / "App.tsx"
HEADER_TSX = FRONTEND_DIR / "components" / "Header.tsx"
MAP_VIEW_TSX = FRONTEND_DIR / "components" / "MapOperationsView.tsx"


def test_app_tsx_contains_zero_math_random_telemetry_mutations():
    """
    Verifies frontend/src/App.tsx does not use Math.random to invent or jitter
    telemetry metrics (speed, congestion, energy demand).
    """
    assert APP_TSX.is_file(), f"App.tsx not found at {APP_TSX}"
    content = APP_TSX.read_text(encoding="utf-8")

    # Check for any Math.random calls
    math_random_matches = [
        line.strip()
        for line in content.splitlines()
        if "Math.random" in line and not line.strip().startswith("//") and not line.strip().startswith("/*")
    ]
    assert len(math_random_matches) == 0, (
        f"Detected unauthorized Math.random calls in App.tsx: {math_random_matches}"
    )


def test_app_tsx_contains_zero_artificial_interval_timers_mutating_telemetry():
    """
    Verifies frontend/src/App.tsx does not contain artificial interval timers
    (e.g. setInterval) that mutate liveStates or liveEnergyKw when the socket is quiet.
    """
    assert APP_TSX.is_file(), f"App.tsx not found at {APP_TSX}"
    content = APP_TSX.read_text(encoding="utf-8")

    # Search for setInterval blocks that invoke state setters for telemetry
    set_interval_blocks = re.findall(
        r"setInterval\s*\(\s*\(\)\s*=>\s*\{([\s\S]*?)\}\s*,\s*(\d+)\s*\)",
        content
    )

    for body, delay_str in set_interval_blocks:
        assert "setLiveStates" not in body, (
            f"Found artificial interval timer ({delay_str}ms) mutating liveStates in App.tsx"
        )
        assert "setLiveEnergyKw" not in body, (
            f"Found artificial interval timer ({delay_str}ms) mutating liveEnergyKw in App.tsx"
        )
        assert "speedJitter" not in body, (
            f"Found speed jitter calculation in interval timer in App.tsx"
        )


def test_map_operations_view_contains_zero_math_random_telemetry_mutations():
    """
    Verifies frontend/src/components/MapOperationsView.tsx contains zero Math.random
    telemetry mutations or synthetic state generation.
    """
    assert MAP_VIEW_TSX.is_file(), f"MapOperationsView.tsx not found at {MAP_VIEW_TSX}"
    content = MAP_VIEW_TSX.read_text(encoding="utf-8")

    math_random_matches = [
        line.strip()
        for line in content.splitlines()
        if "Math.random" in line and not line.strip().startswith("//") and not line.strip().startswith("/*")
    ]
    assert len(math_random_matches) == 0, (
        f"Detected unauthorized Math.random calls in MapOperationsView.tsx: {math_random_matches}"
    )


def test_header_tsx_contains_staleness_thresholding_logic():
    """
    Verifies frontend/src/components/Header.tsx implements the 180s (180000ms)
    telemetry staleness SLA check and displays Stale vs Synced vs Awaiting.
    """
    assert HEADER_TSX.is_file(), f"Header.tsx not found at {HEADER_TSX}"
    content = HEADER_TSX.read_text(encoding="utf-8")

    # Must contain 180000 ms SLA threshold check
    assert "180000" in content or "180 * 1000" in content, (
        "Header.tsx must define or check the 180000ms (180s) staleness threshold"
    )

    # Must contain logic rendering Stale badge text
    assert "Stale" in content, (
        "Header.tsx must include 'Stale' state badge text for expired telemetry"
    )

    # Must contain logic rendering Synced badge text
    assert "Synced" in content, (
        "Header.tsx must include 'Synced' state badge text for fresh telemetry"
    )

    # Must contain logic rendering Awaiting badge text
    assert "Awaiting" in content, (
        "Header.tsx must include 'Awaiting' state badge text when lastUpdated is null"
    )

    # Must reference CSS variable for status warning ink
    assert "--status-warning-ink" in content, (
        "Header.tsx must use var(--status-warning-ink) for stale/awaiting telemetry status"
    )

    # Must reference CSS variable for badge synced ink
    assert "--badge-synced-ink" in content, (
        "Header.tsx must use var(--badge-synced-ink) for synced telemetry status"
    )


def test_staleness_threshold_logic_simulation():
    """
    Unit simulation testing the staleness boundary conditions adhering to AGENTS.md Section 3:
    - Observations > 180s are STALE.
    - Observations <= 180s are fresh (SYNCED).
    - Null/empty timestamp is AWAITING.
    """
    staleness_threshold_ms = 180000

    def evaluate_status(last_updated_epoch_ms: float | None, current_time_epoch_ms: float) -> str:
        if last_updated_epoch_ms is None:
            return "Awaiting"
        elapsed = current_time_epoch_ms - last_updated_epoch_ms
        if elapsed > staleness_threshold_ms:
            return "Stale"
        return "Synced"

    now = 1700000000000.0

    # Null timestamp -> Awaiting
    assert evaluate_status(None, now) == "Awaiting"

    # Exact same moment -> Synced
    assert evaluate_status(now, now) == "Synced"

    # 30 seconds ago -> Synced
    assert evaluate_status(now - 30000, now) == "Synced"

    # 179.9 seconds ago -> Synced
    assert evaluate_status(now - 179900, now) == "Synced"

    # Exactly 180 seconds ago -> Synced (boundary condition elapsed <= 180000)
    assert evaluate_status(now - 180000, now) == "Synced"

    # 180.001 seconds ago -> Stale
    assert evaluate_status(now - 180001, now) == "Stale"

    # 5 minutes ago -> Stale
    assert evaluate_status(now - 300000, now) == "Stale"
