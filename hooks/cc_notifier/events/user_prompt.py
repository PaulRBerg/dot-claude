#!/usr/bin/env python3
"""
UserPromptSubmit hook handler.

Tracks new prompt submissions in the database.
"""

import sys
from pathlib import Path

# Add ~/.claude to path for hooks.cc_notifier imports
sys.path.insert(0, str(Path.home() / ".claude"))

from loguru import logger

from hooks.cc_notifier.database import SessionTracker
from hooks.cc_notifier.utils import read_stdin_json, setup_logging, validate_input


def main() -> None:
    """Handle UserPromptSubmit event."""
    setup_logging()

    try:
        # Read and validate input
        data = read_stdin_json()
        validate_input(data)

        # Extract required fields
        session_id = data.get("session_id", "")
        prompt = data.get("prompt", "")
        cwd = data.get("cwd", "")

        if not session_id:
            logger.error("Missing session_id in input")
            sys.exit(1)

        # Track prompt in database
        tracker = SessionTracker()
        tracker.track_prompt(session_id, prompt, cwd)

        logger.info(f"Tracked prompt for session {session_id}")
        sys.exit(0)

    except Exception as e:
        logger.error(f"UserPromptSubmit handler failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
