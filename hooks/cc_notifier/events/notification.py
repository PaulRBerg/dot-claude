#!/usr/bin/env python3
"""
Notification hook handler.

Handles Claude's built-in notifications and tracks waiting state.
Suppresses "waiting for input" notifications since Stop handler will send job completion.
"""

import sys
from pathlib import Path

# Add ~/.claude to path for hooks.cc_notifier imports
sys.path.insert(0, str(Path.home() / ".claude"))

from loguru import logger

from hooks.cc_notifier.database import SessionTracker
from hooks.cc_notifier.utils import read_stdin_json, setup_logging, validate_input


def main() -> None:
    """Handle Notification event."""
    setup_logging()

    try:
        # Read and validate input
        data = read_stdin_json()
        validate_input(data)

        # Extract required fields
        session_id = data.get("session_id", "")
        message = data.get("message", "")

        if not session_id:
            logger.error("Missing session_id in input")
            sys.exit(1)

        # Check if this is a "waiting for input" notification
        waiting_keywords = ["waiting for input", "waiting for user", "approval needed"]
        is_waiting = any(keyword in message.lower() for keyword in waiting_keywords)

        if is_waiting:
            # Track waiting state but don't send notification
            # The Stop handler will send the job completion notification
            tracker = SessionTracker()
            tracker.mark_waiting(session_id)
            logger.debug(f"Suppressed waiting notification for session {session_id}")
        else:
            # For other notifications, just log them
            logger.info(f"Notification: {message}")

        sys.exit(0)

    except Exception as e:
        logger.error(f"Notification handler failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
