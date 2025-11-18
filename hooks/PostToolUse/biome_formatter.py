#!/usr/bin/env python3
"""
Biome Auto-Formatter Hook for Claude Code

Runs after Edit/Write/Serena MCP tools to auto-format TypeScript files.

Supported tools:
  - Edit, Write (native Claude tools)
  - mcp__serena__replace_symbol_body
  - mcp__serena__insert_after_symbol
  - mcp__serena__insert_before_symbol

Exit code: Always 0 (never blocks Claude)
Output: Silent (no context pollution)

Configuration:
Add this to your .claude/settings.json or .claude/settings.local.json:

{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|mcp__serena__(replace_symbol_body|insert_.*_symbol)",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/PostToolUse/biome-formatter.py"
          }
        ]
      }
    ]
  }
}
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path


def extract_file_path() -> str | None:
    """
    Extract file path from various tool inputs.

    Returns:
        File path as string, or None if not found
    """
    # Method 1: Direct file path (Edit/Write tools)
    if file_path := os.environ.get("TOOL_INPUT_FILE_PATH"):
        return file_path

    # Method 2: Relative path from Serena tools
    if relative_path := os.environ.get("TOOL_INPUT_RELATIVE_PATH"):
        if project_dir := os.environ.get("CLAUDE_PROJECT_DIR"):
            return str(Path(project_dir) / relative_path)
        return relative_path

    # Method 3: Parse from TOOL_CALL JSON (fallback)
    if tool_call := os.environ.get("TOOL_CALL"):
        try:
            data = json.loads(tool_call)
            if relative_path := data.get("relative_path"):
                if project_dir := os.environ.get("CLAUDE_PROJECT_DIR"):
                    return str(Path(project_dir) / relative_path)
                return relative_path
        except (json.JSONDecodeError, ValueError):
            pass

    return None


def is_typescript_file(file_path: str) -> bool:
    """Check if file is a TypeScript file (.ts or .tsx)."""
    return bool(re.search(r"\.(ts|tsx)$", file_path))


def run_biome(file_path: str) -> None:
    """
    Run Biome formatter on the file.

    Suppresses all output and never raises exceptions.
    """
    try:
        subprocess.run(
            ["biome", "check", "--apply", file_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,  # Don't raise on non-zero exit
            timeout=10,   # Timeout after 10 seconds
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        # Silently ignore all errors
        pass


def main() -> int:
    """Main entry point. Always returns 0."""
    try:
        # Extract file path
        file_path = extract_file_path()
        if not file_path:
            return 0

        # Filter: only TypeScript files
        if not is_typescript_file(file_path):
            return 0

        # Check file exists
        if not Path(file_path).is_file():
            return 0

        # Run formatter
        run_biome(file_path)

        return 0
    except Exception:
        # Silently catch any unexpected errors
        # Never block Claude
        return 0


if __name__ == "__main__":
    sys.exit(main())
