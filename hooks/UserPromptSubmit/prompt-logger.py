#!/usr/bin/env python3
"""Log user prompts to nb notebook for later inspection.

Captures all user-submitted prompts before Claude processes them and stores
them in a dedicated nb notebook with metadata for easy searching and review.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def log_prompt_to_nb(prompt: str, session_id: str, cwd: str) -> None:
    """Save prompt to nb notebook with metadata.

    Args:
        prompt: The user's prompt text
        session_id: Unique session identifier
        cwd: Current working directory when prompt was submitted
    """
    timestamp = datetime.now()

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
        # Add to claude-prompts notebook using nb add
        subprocess.run(
            ["nb", "claude-prompts:add", filename, "--content", entry],
            capture_output=True,
            text=True,
            check=True,
            timeout=5
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

    session_id = input_data.get("session_id", "unknown")
    cwd = input_data.get("cwd", "unknown")

    # Log to nb (errors are handled gracefully inside)
    log_prompt_to_nb(prompt, session_id, cwd)

    # Exit cleanly without output (silent operation)
    sys.exit(0)


if __name__ == "__main__":
    main()
