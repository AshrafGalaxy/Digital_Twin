"""
test_markdown_math_integrity.py

Automated hermetic tests enforcing AGENTS.md Rule 11:
1. Unit tests for Markdown formatting, LaTeX syntax, and shell-escape validation.
2. Full repository scan verifying zero broken math blocks or corrupted escapes across all documentation.
"""

from pathlib import Path
import pytest
from scripts.verify_markdown_math import check_file_integrity, collect_markdown_files

ROOT_DIR = Path(__file__).resolve().parent.parent


def test_validator_detects_corrupted_shell_escape(tmp_path):
    """Verifies that mangled shell escape identifiers like \\BUG-54\\ are rejected."""
    sample_file = tmp_path / "corrupted_id.md"
    sample_file.write_text("# Title\n\n- **Defect:** \\BUG-54\\\n", encoding="utf-8")

    errors = check_file_integrity(sample_file)
    assert len(errors) == 1
    assert "corrupted shell escape identifier" in errors[0][1]


def test_validator_detects_ascii_control_characters(tmp_path):
    """Verifies that ASCII BEL (\\x07) and Form Feed (\\x0c) are rejected."""
    sample_file = tmp_path / "control_chars.md"
    sample_file.write_text("# Title\n\nSome text with \x07 and \x0c.\n", encoding="utf-8")

    errors = check_file_integrity(sample_file)
    assert len(errors) == 1
    assert "illegal ASCII control characters" in errors[0][1]


def test_validator_detects_unbalanced_display_math(tmp_path):
    """Verifies that an odd number of $$ delimiters is rejected."""
    sample_file = tmp_path / "unbalanced_display.md"
    sample_file.write_text("# Title\n\n$$ C_0 = \\frac{1.5 L + 5}{1 - Y} \n\nNo closing delimiter.", encoding="utf-8")

    errors = check_file_integrity(sample_file)
    assert any("Unbalanced display math" in msg for _, msg in errors)


def test_validator_detects_unbalanced_braces_in_math_block(tmp_path):
    """Verifies that unbalanced braces within LaTeX math blocks are rejected."""
    sample_file = tmp_path / "unbalanced_braces.md"
    sample_file.write_text("# Title\n\n$$\n\\frac{a}{b\n$$\n", encoding="utf-8")

    errors = check_file_integrity(sample_file)
    assert any("Unbalanced open brace" in msg for _, msg in errors)


def test_validator_accepts_clean_math_and_plain_text(tmp_path):
    """Verifies that valid LaTeX math and plain text pass cleanly."""
    sample_file = tmp_path / "valid_doc.md"
    sample_file.write_text(
        "# Title\n\n"
        "Here is plain text: `C_0 = (1.5 * L + 5) / (1 - Y)`.\n\n"
        "$$\n"
        "C_0 = \\frac{1.5 L + 5}{1 - Y}\n"
        "$$\n\n"
        "```math\n"
        "P_{\\text{grid}}(t) = P_{\\text{load}}(t) - \\hat{P}_{\\text{pv}}(t)\n"
        "```\n",
        encoding="utf-8"
    )

    errors = check_file_integrity(sample_file)
    assert len(errors) == 0


def test_repository_all_markdown_files_pass_integrity():
    """Scans all markdown files in the repository and verifies 100% clean integrity."""
    files = collect_markdown_files()
    assert len(files) > 0, "Expected to find repository markdown files"

    all_failures = []
    for f in files:
        rel = f.relative_to(ROOT_DIR)
        errors = check_file_integrity(f)
        for line_no, msg in errors:
            all_failures.append(f"{rel}:{line_no}: {msg}")

    assert len(all_failures) == 0, f"Found {len(all_failures)} markdown integrity issues:\n" + "\n".join(all_failures)
