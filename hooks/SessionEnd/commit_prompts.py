#!/usr/bin/env python3
"""Auto-commit changes to ~/.claude-prompts on session end."""

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROMPTS_DIR = Path.home() / ".claude-prompts"


def main() -> None:
    """Check for changes and commit if any."""
    if not PROMPTS_DIR.exists():
        sys.exit(0)

    try:
        # Check for changes
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=PROMPTS_DIR,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if not result.stdout.strip():
            sys.exit(0)  # No changes

        # Stage and commit
        subprocess.run(
            ["git", "add", "-A"],
            cwd=PROMPTS_DIR,
            check=True,
            timeout=10,
        )

        timestamp = datetime.now(timezone.utc).strftime("%B %d, %Y at %H:%M UTC")
        subprocess.run(
            ["git", "commit", "-m", f"Update prompts - {timestamp}"],
            cwd=PROMPTS_DIR,
            check=True,
            timeout=30,
        )
    except subprocess.CalledProcessError as e:
        print(f"Warning: git operation failed: {e}", file=sys.stderr)
    except subprocess.TimeoutExpired:
        print("Warning: git operation timed out", file=sys.stderr)
    except OSError as e:
        print(f"Warning: Failed to run git: {e}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
