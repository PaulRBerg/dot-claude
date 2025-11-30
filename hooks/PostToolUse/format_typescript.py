#!/usr/bin/env python3
"""Auto-format TypeScript files after Edit/Write tool use.

USAGE: Add this hook to .claude/settings.local.json in each project where you
want automatic TypeScript formatting after Claude edits files.

Example settings.local.json:
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/PostToolUse/format_typescript.py"
          }
        ]
      }
    ]
  }
}
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path.home() / ".claude/hooks/PostToolUse/format_typescript.log"


def log_error(message: str, file_path: str, exit_code: int, stderr: str) -> None:
    """Append error to log file."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    entry = f"[{timestamp}] ERROR: {message} for {file_path}\n  Exit code: {exit_code}\n"
    if stderr:
        entry += f"  Stderr: {stderr}\n"

    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a") as f:
            f.write(entry)
    except OSError:
        pass  # Silent failure for logging


def run_biome(file_path: str) -> None:
    """Run biome format and lint on a TypeScript file."""
    commands = [
        ["na", "biome", "format", "--write", file_path],
        [
            "na",
            "biome",
            "lint",
            "--unsafe",
            "--write",
            "--only",
            "correctness/noUnusedImports",
            file_path,
        ],
    ]

    for cmd in commands:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                log_error(
                    f"{cmd[1]} {cmd[2]} failed",
                    file_path,
                    result.returncode,
                    result.stderr.strip(),
                )
        except subprocess.TimeoutExpired:
            log_error(f"{cmd[1]} {cmd[2]} timed out", file_path, -1, "")
        except FileNotFoundError:
            log_error(f"{cmd[0]} not found", file_path, -1, "")
        except Exception as e:
            log_error(f"{cmd[1]} {cmd[2]} exception", file_path, -1, str(e))


def main() -> None:
    """Main hook entry point."""
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # Don't break hook chain

    file_path = input_data.get("tool_input", {}).get("file_path", "")
    if not file_path:
        sys.exit(0)

    # Only format TypeScript files
    if not file_path.endswith((".ts", ".tsx")):
        sys.exit(0)

    run_biome(file_path)
    sys.exit(0)


if __name__ == "__main__":
    main()
