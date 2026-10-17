#!/usr/bin/env python3
"""
Install Git Hooks for Digital Twin Smart City Platform.

Configures git core.hooksPath to point to .githooks directory.
"""

import subprocess
import sys


def main() -> int:
    try:
        subprocess.run(["git", "config", "core.hooksPath", ".githooks"], check=True)
        print("[GIT HOOKS] Successfully configured git core.hooksPath to '.githooks'.")
        print("[GIT HOOKS] Active hooks:")
        print("  - pre-commit: forbids currentproblems.md, checks em dashes, checks emojis, runs tsc --noEmit")
        print("  - commit-msg: enforces <60 chars, no 'phase' words, conventional commit format")
        print("  - pre-push: runs pytest tests/ and frontend npm run build")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"[GIT HOOKS ERROR] Failed to configure git hooks: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
