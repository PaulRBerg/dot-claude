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
from datetime import datetime, timezone
from pathlib import Path

# Notebook name for storing prompts
NB_ROOT_DIR = "home"


def get_notebook_folder_path(cwd: str) -> str:
    """Convert cwd to folder path within the claude notebook.

    Args:
        cwd: Current working directory path

    Returns:
        Folder path like 'Sablier/sdk' that mirrors the directory
        structure relative to home directory
    """
    path = Path(cwd)
    home = Path.home()

    # Strip home directory prefix if present
    try:
        relative_path = path.relative_to(home)
    except ValueError:
        # If path is not under home, use the full path as folder name
        relative_path = path

    # Convert to string with forward slashes (nb uses / as separator)
    path_str = str(relative_path).replace("\\", "/")
    # Strip leading dots from each component to avoid hidden folders in nb
    components = [part.lstrip(".") or part for part in path_str.split("/")]
    return "/".join(components)


def ensure_notebook_exists(notebook_name: str = NB_ROOT_DIR) -> bool:
    """Ensure nb notebook exists, create if missing.

    Args:
        notebook_name: Name of the notebook to check/create (default: NB_ROOT_DIR)

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
        print("Warning: nb notebooks check/create timed out", file=sys.stderr)
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
    timestamp = datetime.now(timezone.utc)

    # Ensure claude notebook exists
    if not ensure_notebook_exists():
        print(
            "Warning: Could not ensure claude notebook exists",
            file=sys.stderr,
        )
        return

    # Get folder path within claude notebook
    folder_path = get_notebook_folder_path(cwd)

    # Format entry as a timestamped section for appending to daily note
    time_header = timestamp.strftime("%H:%M:%S")
    entry = f"""
## {time_header}

{prompt}

---
"""

    # Use daily filename for grouping all prompts by date
    filename = timestamp.strftime("%Y-%m-%d") + ".md"

    # Construct full path: home:Sablier/sdk/2025-11-17.md
    note_path = f"{folder_path}/{filename}"

    try:
        # Append to daily note (creates if doesn't exist)
        subprocess.run(
            ["nb", "edit", f"{NB_ROOT_DIR}:{note_path}", "--content", entry],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        print("Warning: nb edit timed out", file=sys.stderr)
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
