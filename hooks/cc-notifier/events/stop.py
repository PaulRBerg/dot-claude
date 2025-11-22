#!/usr/bin/env python3
"""
Stop hook handler.

Marks session as stopped, calculates duration, and sends completion notification.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from database import SessionTracker
from notifier import MacNotifier
from utils import format_duration, read_stdin_json, setup_logging, validate_input


def main() -> None:
    """Handle Stop event."""
    logger = setup_logging()

    try:
        # Read and validate input
        data = read_stdin_json()
        validate_input(data)

        # Extract required fields
        session_id = data.get("session_id", "")
        cwd = data.get("cwd", "")

        if not session_id:
            logger.error("Missing session_id in input")
            sys.exit(1)

        # Mark session as stopped
        tracker = SessionTracker()
        tracker.mark_stopped(session_id)

        # Get job info for notification
        job_number, duration_seconds = tracker.get_job_info(session_id)

        if job_number is not None and duration_seconds is not None:
            # Send notification
            notifier = MacNotifier()
            project_name = notifier.get_project_name(cwd)
            duration_str = format_duration(duration_seconds)

            notifier.notify_job_done(project_name, job_number, duration_str)
            logger.info(f"Job #{job_number} completed in {duration_str}")
        else:
            logger.warning(f"No job info found for session {session_id}")

        sys.exit(0)

    except Exception as e:
        logger.error(f"Stop handler failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
