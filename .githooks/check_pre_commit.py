#!/usr/bin/env python3
"""
pre-commit Git Hook for Digital Twin Smart City Platform.

Enforces rules defined in AGENTS.md:
1. Rejects staging of forbidden files (currentproblems.md, .env, *.db, scratch/).
2. Rejects em dashes (\u2014) or en dashes (\u2013) in staged text lines.
3. Rejects raw emojis in frontend component and styling files (.tsx, .ts, .css).
4. Runs fast TypeScript type checking (tsc --noEmit) if frontend files are modified.
"""

import sys
import subprocess
import re
from pathlib import Path

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001F900-\U0001F9FF"
    "\U0001FA70-\U0001FAFF"
    "\U00002600-\U000026FF"
    "]+",
    flags=re.UNICODE
)

FORBIDDEN_FILES = [
    re.compile(r"^currentproblems\.md$"),
    re.compile(r"^\.env(\..+)?$"),
    re.compile(r"^scratch/"),
    re.compile(r"\.(sqlite3|db|db-wal|db-shm)$")
]

TEXT_EXTENSIONS = {
    ".ts", ".tsx", ".py", ".css", ".json", ".md", ".html", ".sql", ".yaml", ".yml"
}


def check_forbidden_files(staged_files: list[str]) -> bool:
    has_error = False
    for f in staged_files:
        norm = f.replace("\\", "/")
        if norm == ".env.example":
            continue
        for pat in FORBIDDEN_FILES:
            if pat.search(norm):
                print(f"[GIT HOOK ERROR] Forbidden file staged for commit: '{f}'")
                print("  This file is strictly prohibited from being committed to source control.")
                has_error = True
                break
    return not has_error


def check_staged_content() -> bool:
    has_error = False
    try:
        res = subprocess.run(
            ["git", "diff", "--cached", "-U0"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True
        )
    except Exception as e:
        print(f"[GIT HOOK ERROR] Failed to inspect git diff: {e}")
        return False

    current_file = ""
    for line in res.stdout.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:].strip().replace("\\", "/")
            continue

        if line.startswith("+") and not line.startswith("+++"):
            added_text = line[1:]
            ext = Path(current_file).suffix.lower()

            # Rule: Zero em dashes or en dashes
            if ext in TEXT_EXTENSIONS and ("\u2014" in added_text or "\u2013" in added_text):
                print(f"[GIT HOOK ERROR] Em dash or en dash found in staged changes in '{current_file}':")
                print(f"  Line: '{added_text.strip()}'")
                print("Per AGENTS.md Section 2.7, em and en dashes are strictly prohibited.")
                has_error = True

            # Rule: Zero raw emojis in frontend components / styles
            if ext in {".tsx", ".ts", ".css"} and EMOJI_PATTERN.search(added_text):
                print(f"[GIT HOOK ERROR] Raw emoji detected in staged frontend file '{current_file}':")
                print(f"  Line: '{added_text.strip()}'")
                print("Per AGENTS.md Section 2.6, emojis are strictly prohibited in UI components.")
                has_error = True

    return not has_error


def check_frontend_types(staged_files: list[str]) -> bool:
    frontend_touched = any(
        f.replace("\\", "/").startswith("frontend/src/") or
        f.replace("\\", "/") in {"frontend/package.json", "frontend/tsconfig.json"}
        for f in staged_files
    )

    if not frontend_touched:
        return True

    print("[GIT HOOK] Verifying frontend TypeScript types (tsc --noEmit)...")
    try:
        # Use npx on Windows / shell
        res = subprocess.run(
            "npx tsc --noEmit",
            cwd="frontend",
            shell=True,
            capture_output=True,
            text=True
        )
        if res.returncode != 0:
            print("[GIT HOOK ERROR] TypeScript typecheck failed:")
            print(res.stdout or res.stderr)
            return False
        print("[GIT HOOK] TypeScript typecheck passed.")
        return True
    except Exception as e:
        print(f"[GIT HOOK WARNING] Could not run tsc --noEmit: {e}")
        return True


def main() -> int:
    try:
        res = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True
        )
        staged_files = [f.strip() for f in res.stdout.splitlines() if f.strip()]
    except Exception as e:
        print(f"[GIT HOOK ERROR] Failed to list staged files: {e}")
        return 1

    if not staged_files:
        return 0

    ok_files = check_forbidden_files(staged_files)
    ok_content = check_staged_content()
    ok_types = check_frontend_types(staged_files)

    if not (ok_files and ok_content and ok_types):
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
