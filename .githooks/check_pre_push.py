#!/usr/bin/env python3
"""
pre-push Git Hook for Digital Twin Smart City Platform.

Enforces rules defined in AGENTS.md:
1. Runs full backend test suite hermetically (pytest tests/).
2. Runs frontend production build (npm run build in frontend/).
Guarantees that broken builds or test regressions never reach GitHub.
"""

import sys
import subprocess
import os
from pathlib import Path


def find_pytest() -> str:
    venv_win = Path(".venv/Scripts/pytest.exe")
    if venv_win.exists():
        return str(venv_win)
    venv_unix = Path(".venv/bin/pytest")
    if venv_unix.exists():
        return str(venv_unix)
    return "pytest"


def run_tests() -> bool:
    pytest_bin = find_pytest()
    print(f"[GIT HOOK] Executing hermetic backend test suite ({pytest_bin} tests/ -q)...")
    try:
        res = subprocess.run([pytest_bin, "tests/", "-q"])
        if res.returncode != 0:
            print("[GIT HOOK ERROR] Backend test suite failed. Push aborted.")
            return False
        print("[GIT HOOK] All backend tests passed.")
        return True
    except Exception as e:
        print(f"[GIT HOOK ERROR] Failed to execute backend test runner: {e}")
        return False


def run_frontend_build() -> bool:
    print("[GIT HOOK] Executing frontend production build check (npm run build)...")
    try:
        res = subprocess.run("npm run build", cwd="frontend", shell=True)
        if res.returncode != 0:
            print("[GIT HOOK ERROR] Frontend production build failed. Push aborted.")
            return False
        print("[GIT HOOK] Frontend production build succeeded.")
        return True
    except Exception as e:
        print(f"[GIT HOOK ERROR] Failed to run frontend build: {e}")
        return False


def main() -> int:
    print("=" * 60)
    print("[GIT HOOK] Pre-Push Quality & Hermetic Verification Gate")
    print("=" * 60)

    if not run_tests():
        return 1

    if not run_frontend_build():
        return 1

    print("[GIT HOOK] All pre-push checks passed successfully. Pushing to remote.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
