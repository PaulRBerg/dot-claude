#!/usr/bin/env python3
"""Log user prompts to nb notebook for later inspection.

Captures all user-submitted prompts before Claude processes them and stores
them in a dedicated nb notebook per project with metadata for easy searching
and review.
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def cwd_to_notebook_name(cwd: str, segments: int = 2) -> str:
    """Convert cwd path to safe nb notebook name.

    Args:
        cwd: Current working directory path
        segments: Number of path segments to include (default: 2)

    Returns:
        Sanitized notebook name with 'claude-' prefix
    """
    path = Path(cwd)
    # Extract last N segments
    parts = path.parts[-segments:] if len(path.parts) >= segments else path.parts

    # Join and sanitize: lowercase, replace special chars with hyphens
    name = "-".join(parts)
    name = re.sub(r"[^a-zA-Z0-9-]", "-", name.lower())
    # Remove consecutive hyphens and trim
    name = re.sub(r"-+", "-", name).strip("-")

    return f"claude-{name}"


def ensure_notebook_exists(notebook_name: str) -> bool:
    """Ensure nb notebook exists, create if missing.

    Args:
        notebook_name: Name of the notebook to check/create

    Returns:
        True if notebook exists or was created successfully
    """
    try:
        # Check if notebook exists
        result = subprocess.run(
            ["nb", "notebooks", "--names"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        existing_notebooks = result.stdout.strip().split("\n")

        if notebook_name in existing_notebooks:
            return True

        # Create the notebook
        subprocess.run(
            ["nb", "notebooks", "add", notebook_name],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        return True

    except subprocess.TimeoutExpired:
        print(f"Warning: nb notebooks check/create timed out", file=sys.stderr)
        return False
    except subprocess.CalledProcessError as e:
        print(
            f"Warning: Failed to check/create notebook {notebook_name}: {e.stderr}",
            file=sys.stderr,
        )
        return False
    except FileNotFoundError:
        print("Warning: nb command not found", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Warning: Unexpected error with notebook: {e}", file=sys.stderr)
        return False


def log_prompt_to_nb(prompt: str, session_id: str, cwd: str) -> None:
    """Save prompt to project-specific nb notebook with metadata.

    Args:
        prompt: The user's prompt text
        session_id: Unique session identifier
        cwd: Current working directory when prompt was submitted
    """
    timestamp = datetime.now()

    # Generate notebook name from project path
    notebook_name = cwd_to_notebook_name(cwd)

    # Ensure notebook exists
    if not ensure_notebook_exists(notebook_name):
        print(
            f"Warning: Could not ensure notebook {notebook_name} exists",
            file=sys.stderr,
        )
        return

    # Format entry with YAML frontmatter
    entry = f"""---
session_id: {session_id}
timestamp: {timestamp.isoformat()}
cwd: {cwd}
tags: claude-code prompt
---

# Prompt: {timestamp.strftime("%Y-%m-%d %H:%M:%S")}

{prompt}
"""

    # Use timestamp-based filename for chronological sorting
    filename = timestamp.strftime("%Y%m%d_%H%M%S") + ".md"

    try:
        # Add to project-specific notebook using nb add
        subprocess.run(
            ["nb", f"{notebook_name}:add", filename, "--content", entry],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        print("Warning: nb add timed out", file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to log prompt to nb: {e.stderr}", file=sys.stderr)
    except FileNotFoundError:
        print("Warning: nb command not found", file=sys.stderr)
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

    # Log to nb (errors are handled gracefully inside)
    log_prompt_to_nb(prompt, session_id, cwd)

    # Exit cleanly without output (silent operation)
    sys.exit(0)


if __name__ == "__main__":
    main()
