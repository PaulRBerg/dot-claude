#!/usr/bin/env python3
"""Add YAML frontmatter to plan files created in ~/.claude/plans/.

This PostToolUse hook intercepts Write tool executions and adds metadata
frontmatter to plan files, enabling better organization and searchability.

See https://github.com/anthropics/claude-code/issues/12378
"""

# ruff: noqa: D103

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Target directory for plan files
PLANS_DIR = Path.home() / ".claude" / "plans"


def get_git_branch(cwd: str) -> str:
    """Get current git branch, or empty string if not in repo.

    Args:
        cwd: Directory to check for git repository

    Returns:
        Branch name or empty string if not in a git repo
    """
    if not cwd:
        return ""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
        return ""


def to_tilde_path(path: str) -> str:
    """Convert absolute path to ~-prefixed path if under home directory."""
    home = str(Path.home())
    if path.startswith(home):
        return "~" + path[len(home) :]
    return path


def build_frontmatter(data: dict, plan_path: str) -> str:
    """Build YAML frontmatter string with metadata.

    Args:
        data: Hook input data containing session_id and cwd
        plan_path: Absolute path to the plan file

    Returns:
        YAML frontmatter block as string
    """
    cwd = data.get("cwd", "")

    # All values are quoted for YAML safety (paths with spaces, special chars)
    # Fields ordered alphabetically
    fields = [
        ("created", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")),
        ("git_branch", get_git_branch(cwd)),
        ("plan_path", to_tilde_path(plan_path)),
        ("project_directory", to_tilde_path(cwd)),
        ("session_id", data.get("session_id", "unknown")),
    ]

    lines = ["---"]
    for key, value in fields:
        if value:  # Skip empty values
            # Escape backslashes and quotes for YAML safety
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'{key}: "{escaped}"')
    lines.append("---")

    return "\n".join(lines)


def main() -> None:
    """Main hook entry point."""
    # Parse stdin JSON
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # Invalid input, don't break hook chain

    # Only process Write tool
    if data.get("tool_name") != "Write":
        sys.exit(0)

    # Get file path from tool input
    file_path_str = data.get("tool_input", {}).get("file_path", "")
    if not file_path_str:
        sys.exit(0)

    # Check if file is in plans directory
    try:
        file_path = Path(file_path_str).resolve()
        plans_dir_resolved = PLANS_DIR.resolve()

        if not file_path.is_relative_to(plans_dir_resolved):
            sys.exit(0)  # Not in plans directory

        if file_path.suffix != ".md":
            sys.exit(0)  # Not a markdown file
    except (ValueError, TypeError, OSError):
        sys.exit(0)

    # Read file content
    try:
        content = file_path.read_text()
    except (OSError, IOError):
        sys.exit(0)  # Can't read file

    # Skip if frontmatter already exists (idempotent)
    if content.startswith("---"):
        sys.exit(0)

    # Build and prepend frontmatter
    frontmatter = build_frontmatter(data, file_path_str)

    try:
        file_path.write_text(f"{frontmatter}\n{content}")
    except (OSError, IOError) as e:
        print(f"Warning: Failed to add frontmatter: {e}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
