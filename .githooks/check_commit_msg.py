#!/usr/bin/env python3
"""
commit-msg Git Hook for Digital Twin Smart City Platform.

Enforces rules defined in AGENTS.md:
1. Commit message subject length must be strictly < 60 characters.
2. Strictly NEVER include the word 'phase' or phase tags (e.g. 'Phase 8', 'P4B').
3. Conventional commit prefix (feat, fix, refactor, test, chore, docs, perf, style, ci, build).
4. Strictly NO raw emojis in the commit message.
5. Strictly NO em dashes (\u2014) or en dashes (\u2013).
"""

import sys
import re

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

CONVENTIONAL_PATTERN = re.compile(
    r"^(feat|fix|refactor|test|chore|docs|perf|style|ci|build)(\([a-zA-Z0-9_\-\./]+\))?!?: .+"
)

PHASE_PATTERN = re.compile(r"(?i)\bphase\b|\bP\d+[A-Za-z0-9]*\b")


def main() -> int:
    if len(sys.argv) < 2:
        print("[GIT HOOK ERROR] Path to commit message file missing.")
        return 1

    msg_file = sys.argv[1]
    try:
        with open(msg_file, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if not line.strip().startswith("#")]
    except Exception as e:
        print(f"[GIT HOOK ERROR] Could not read commit message file: {e}")
        return 1

    # Filter out empty lines to find the subject
    non_empty = [l for l in lines if l]
    if not non_empty:
        print("[GIT HOOK ERROR] Commit message cannot be empty.")
        return 1

    subject = non_empty[0]

    # Rule 1: Subject length < 60 characters
    if len(subject) >= 60:
        print(f"[GIT HOOK ERROR] Commit message subject exceeds 60 characters ({len(subject)} chars):")
        print(f"  '{subject}'")
        print("Per AGENTS.md Section 7, commit messages must strictly be <60 characters.")
        return 1

    # Rule 2: Strictly NO word 'phase' or phase tags
    match_phase = PHASE_PATTERN.search(subject)
    if match_phase:
        print(f"[GIT HOOK ERROR] Commit message contains forbidden word or tag '{match_phase.group(0)}':")
        print(f"  '{subject}'")
        print("Per AGENTS.md Section 7, strictly NEVER include the word 'phase' or phase tags.")
        return 1

    # Rule 3: Strictly NO emojis
    if EMOJI_PATTERN.search(subject):
        print("[GIT HOOK ERROR] Commit message contains raw emojis:")
        print(f"  '{subject}'")
        print("Per AGENTS.md Section 2.6, emojis are strictly prohibited.")
        return 1

    # Rule 4: Strictly NO em dashes or en dashes
    if "\u2014" in subject or "\u2013" in subject:
        print("[GIT HOOK ERROR] Commit message contains em dash or en dash:")
        print(f"  '{subject}'")
        print("Per AGENTS.md Section 2.7, use hyphens (-), colons (:), commas, or periods instead.")
        return 1

    # Rule 5: Conventional Commit Syntax
    if not CONVENTIONAL_PATTERN.match(subject):
        print("[GIT HOOK ERROR] Commit message does not follow Conventional Commits syntax:")
        print(f"  '{subject}'")
        print("Allowed prefixes: feat, fix, refactor, test, chore, docs, perf, style, ci, build.")
        print("Example: refactor(core): update telemetry schema validation")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
