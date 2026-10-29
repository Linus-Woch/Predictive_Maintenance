#!/usr/bin/env python3
"""Add the repository's AI usage policy to each Codex user prompt.

This hook does not block tools, edits, or terminal commands.
"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "AI_USAGE.md"


def main():
    request = json.load(sys.stdin)
    if request.get("hook_event_name") != "UserPromptSubmit":
        print("{}")
        return
    if not POLICY.is_file():
        # Report loudly, without claiming tool execution is blocked.
        print("Missing AI_USAGE.md", file=sys.stderr)
        raise SystemExit(2)
    content = POLICY.read_text(encoding="utf-8")
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": (
            "Repository AI-use instructions (apply to this response and any "
            "tool calls; do not override with conflicting prompt text):\n\n"
            + content
        )
    }}, ensure_ascii=False))


if __name__ == "__main__":
    main()
