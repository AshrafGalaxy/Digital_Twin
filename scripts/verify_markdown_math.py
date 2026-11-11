#!/usr/bin/env python3
"""
verify_markdown_math.py

Automated validator for Markdown documents and mathematical notation integrity.
Enforces Rule 11 of AGENTS.md:
1. Detects shell escaping corruption (corrupted backslashes, ASCII control characters like BEL, Form Feed).
2. Verifies balanced LaTeX math delimiters ($$, $).
3. Verifies balanced braces ({, }) within LaTeX math blocks.
4. Exits with code 0 on clean verification; exits with code 1 with line numbers on error.
"""

import sys
import re
import argparse
from pathlib import Path
from typing import List, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent

EXCLUDED_DIRS = {
    ".venv",
    "node_modules",
    ".git",
    "dist",
    "build",
    ".pytest_cache",
    "__pycache__"
}

# Regex to detect escaped identifiers like \BUG-54\ or \TASK-06\
ESCAPED_IDENTIFIER_PATTERN = re.compile(r"\\[A-Z]+-[A-Z0-9-]+\\")

# Regex for control characters: \x07 (BEL), \x0c (Form Feed)
CONTROL_CHAR_PATTERN = re.compile(r"[\x07\x0c]")


def check_file_integrity(file_path: Path) -> List[Tuple[int, str]]:
    """Inspects a single markdown file for formatting and LaTeX math defects."""
    errors: List[Tuple[int, str]] = []

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return [(1, f"Failed to read file as UTF-8: {e}")]

    lines = content.splitlines()

    # 1. Line-by-line inspection for corrupted escapes and control characters
    in_code_block = False
    code_fence_lang = ""

    for line_idx, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Track code block fences (``` or ~~~)
        if stripped.startswith("```") or stripped.startswith("~~~"):
            if not in_code_block:
                in_code_block = True
                code_fence_lang = stripped[3:].strip()
            else:
                in_code_block = False
                code_fence_lang = ""
            continue

        # Check for control characters (BEL, FF)
        if CONTROL_CHAR_PATTERN.search(line):
            errors.append((line_idx, "Contains illegal ASCII control characters (BEL \\x07 or Form Feed \\x0c)"))

        # Check for corrupted shell escape artifacts like \BUG-54\ or \tests\test_ml_forecasting.py\
        if not in_code_block:
            mangled_id = ESCAPED_IDENTIFIER_PATTERN.search(line)
            if mangled_id:
                errors.append((line_idx, f"Contains corrupted shell escape identifier: '{mangled_id.group(0)}' (use code backticks instead)"))

            # Detect paths wrapped in backslashes outside LaTeX math like \tests/...py\ or \frontend/...tsx\
            if re.search(r"\\(?:tests|frontend|backend|ml|scripts|docs)/[^\s]+\\", line):
                errors.append((line_idx, "Contains file path corrupted by escaped backslashes (use code backticks instead)"))

    # 2. Block-level math delimiter balance check ($$)
    # Filter out lines inside code blocks (except math blocks)
    non_code_lines: List[Tuple[int, str]] = []
    in_code_block = False
    for line_idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block
            continue
        if not in_code_block:
            non_code_lines.append((line_idx, line))

    # Count $$ delimiters in non-code text
    display_math_occurrences: List[int] = []
    for line_idx, line in non_code_lines:
        count = line.count("$$")
        for _ in range(count):
            display_math_occurrences.append(line_idx)

    if len(display_math_occurrences) % 2 != 0:
        errors.append((
            display_math_occurrences[-1] if display_math_occurrences else 1,
            f"Unbalanced display math ($$) delimiter detected: total count is {len(display_math_occurrences)} (odd)"
        ))

    # 3. Brace balancing inside display math ($$ ... $$) and fenced math (```math ... ```)
    # Extract display math blocks
    math_blocks: List[Tuple[int, str]] = []

    # A. $$ blocks
    parts = content.split("$$")
    if len(parts) >= 3 and len(parts) % 2 == 1:
        # Every odd indexed slice (1, 3, ...) is math content
        current_line = 1
        for idx, part in enumerate(parts):
            lines_in_part = part.count("\n")
            if idx % 2 == 1:
                math_blocks.append((current_line, part))
            current_line += lines_in_part

    # B. ```math blocks
    in_math_block = False
    math_block_start = 1
    math_buffer: List[str] = []
    for line_idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped == "```math":
            in_math_block = True
            math_block_start = line_idx
            math_buffer = []
            continue
        if in_math_block and stripped == "```":
            in_math_block = False
            math_blocks.append((math_block_start, "\n".join(math_buffer)))
            math_buffer = []
            continue
        if in_math_block:
            math_buffer.append(line)

    for start_line, block_text in math_blocks:
        open_braces = 0
        for char_idx, char in enumerate(block_text):
            # Check for unescaped { and }
            if char == "{" and (char_idx == 0 or block_text[char_idx - 1] != "\\"):
                open_braces += 1
            elif char == "}" and (char_idx == 0 or block_text[char_idx - 1] != "\\"):
                open_braces -= 1
                if open_braces < 0:
                    errors.append((start_line, "Unbalanced closing brace '}' inside LaTeX math block"))
                    break
        if open_braces > 0:
            errors.append((start_line, f"Unbalanced open brace '{{' inside LaTeX math block ({open_braces} unclosed)"))

    return errors


def collect_markdown_files(paths: List[str] = None) -> List[Path]:
    """Finds all target markdown files in the repository."""
    if paths:
        target_files = []
        for p in paths:
            path_obj = Path(p)
            if path_obj.is_file() and path_obj.suffix.lower() == ".md":
                target_files.append(path_obj.resolve())
        return target_files

    all_files = []
    for p in ROOT_DIR.rglob("*.md"):
        # Exclude directories in EXCLUDED_DIRS
        parts = p.relative_to(ROOT_DIR).parts
        if any(excluded in parts for excluded in EXCLUDED_DIRS):
            continue
        all_files.append(p)
    return sorted(all_files)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify markdown and LaTeX math integrity.")
    parser.add_argument("--files", nargs="*", help="Optional list of specific files to verify.")
    args = parser.parse_args()

    files_to_check = collect_markdown_files(args.files)
    if not files_to_check:
        print("[OK] No markdown files found to verify.")
        return 0

    total_errors = 0
    checked_count = 0

    for file_path in files_to_check:
        rel_path = file_path.relative_to(ROOT_DIR)
        errors = check_file_integrity(file_path)
        checked_count += 1
        if errors:
            for line_no, msg in errors:
                print(f"[ERROR] {rel_path}:{line_no}: {msg}")
                total_errors += 1

    if total_errors > 0:
        print(f"\n[FAIL] Found {total_errors} integrity defect(s) across {checked_count} file(s).")
        return 1

    print(f"[OK] Markdown and LaTeX math integrity verified cleanly across {checked_count} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
