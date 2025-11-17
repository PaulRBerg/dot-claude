#!/usr/bin/env python3
"""Log user prompts to zk notebook for later inspection.

Captures all user-submitted prompts before Claude processes them and stores
them in a unified zk notebook at ~/.claude-prompts/ with metadata for easy
searching and review.

See https://github.com/zk-org/zk
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Root directory for all prompt logs
PROMPTS_DIR = Path.home() / ".claude-prompts"


def get_flattened_project_name(cwd: str) -> str:
    """Convert cwd to flattened directory name.

    Args:
        cwd: Current working directory path

    Returns:
        Flattened directory name like 'work-templates-next-template'

    Examples:
        ~/work/templates/next-template → work-templates-next-template
        ~/.claude → claude
        ~/projects/sablier/sdk → projects-sablier-sdk
    """
    path = Path(cwd)
    home = Path.home()

    # Strip home directory prefix if present
    try:
        relative_path = path.relative_to(home)
    except ValueError:
        # If path is not under home, use the full path
        relative_path = path

    # Convert to string and replace path separators with hyphens
    path_str = str(relative_path)
    # Strip leading dots from each component to avoid hidden folders
    components = [part.lstrip(".") or part for part in path_str.split("/")]
    # Join with hyphens for flat structure
    return "-".join(components)


def get_project_name(cwd: str) -> str:
    """Extract the project name (last component) from cwd.

    Args:
        cwd: Current working directory path

    Returns:
        Last component of the path (project name)

    Examples:
        ~/work/templates/next-template → next-template
        ~/.claude → claude
        ~/projects/sablier/sdk → sdk
    """
    return Path(cwd).name


def get_tags_from_flattened_name(flattened_name: str) -> list[str]:
    """Generate tags from flattened directory name.

    Args:
        flattened_name: Flattened project name like 'work-templates-next-template'

    Returns:
        List of tags, one per word in the flattened name

    Examples:
        work-templates-next-template → ['work', 'templates', 'next', 'template']
        claude → ['claude']
    """
    return flattened_name.split("-")


def ensure_zk_notebook_initialized() -> bool:
    """Ensure unified zk notebook exists at ~/.claude-prompts/.

    Returns:
        True if notebook exists or was created successfully
    """
    zk_dir = PROMPTS_DIR / ".zk"

    if zk_dir.exists():
        return True

    try:
        # Initialize the notebook
        subprocess.run(
            ["zk", "init", str(PROMPTS_DIR), "--no-input"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        return True

    except subprocess.TimeoutExpired:
        print("Warning: zk init timed out", file=sys.stderr)
        return False
    except subprocess.CalledProcessError as e:
        print(
            f"Warning: Failed to initialize zk notebook: {e.stderr}",
            file=sys.stderr,
        )
        return False
    except FileNotFoundError:
        print("Warning: zk command not found", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Warning: Unexpected error initializing notebook: {e}", file=sys.stderr)
        return False


def log_prompt_to_zk(prompt: str, session_id: str, cwd: str) -> None:
    """Save prompt to zk notebook with metadata.

    Args:
        prompt: The user's prompt text
        session_id: Unique session identifier
        cwd: Current working directory when prompt was submitted
    """
    timestamp = datetime.now(timezone.utc)

    # Ensure zk notebook exists
    if not ensure_zk_notebook_initialized():
        print(
            "Warning: Could not ensure zk notebook exists",
            file=sys.stderr,
        )
        return

    # Get flattened project directory name
    flattened_name = get_flattened_project_name(cwd)
    project_name = get_project_name(cwd)
    tags = get_tags_from_flattened_name(flattened_name)

    # Create project subdirectory if needed
    project_dir = PROMPTS_DIR / flattened_name
    project_dir.mkdir(parents=True, exist_ok=True)

    # Daily note path
    date_str = timestamp.strftime("%Y-%m-%d")
    note_path = project_dir / f"{date_str}.md"

    # Format entry
    time_header = timestamp.strftime("%H:%M:%S")

    if not note_path.exists():
        # Create new daily file with YAML frontmatter
        tags_str = ", ".join(tags)
        content = f"""---
title: Prompts submitted on {date_str} in project {project_name}
date: {timestamp.isoformat()}
project: {project_name}
session: {session_id}
tags: [{tags_str}]
---

## {time_header}

_Session ID: {session_id}_

{prompt}

---
"""
    else:
        # Append to existing daily file
        content = f"""
## {time_header}

_Session ID: {session_id}_

{prompt}

---
"""

    try:
        # Write to file (append mode)
        with open(note_path, "a") as f:
            f.write(content)

        # Trigger zk re-indexing
        subprocess.run(
            ["zk", "index", "--notebook-dir", str(PROMPTS_DIR)],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except IOError as e:
        print(f"Warning: Failed to write prompt to file: {e}", file=sys.stderr)
    except subprocess.TimeoutExpired:
        print("Warning: zk index timed out", file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to index note: {e.stderr}", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Unexpected error logging prompt: {e}", file=sys.stderr)


def main() -> None:
    """Main hook entry point."""
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(0)  # Don't break the hook chain

    prompt = input_data.get("prompt", "")
    if not prompt:
        sys.exit(0)  # No prompt to log

    # Filter out short prompts (< 25 characters)
    if len(prompt) < 25:
        sys.exit(0)

    # Filter out simple slash command invocations
    stripped = prompt.strip()
    if stripped.startswith("/") and " " not in stripped:
        sys.exit(0)  # Simple command without arguments

    session_id = input_data.get("session_id", "unknown")
    cwd = input_data.get("cwd", "unknown")

    # Log to zk (errors are handled gracefully inside)
    log_prompt_to_zk(prompt, session_id, cwd)

    # Exit cleanly without output (silent operation)
    sys.exit(0)


if __name__ == "__main__":
    main()
