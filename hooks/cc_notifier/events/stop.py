#!/usr/bin/env python3
"""
Stop hook handler.

Marks session as stopped, calculates duration, and sends completion notification.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add ~/.claude to path for hooks.cc_notifier imports
sys.path.insert(0, str(Path.home() / ".claude"))

from loguru import logger

from hooks.cc_notifier.config import get_runtime_config, DEFAULT_CONFIG_DIR
from hooks.cc_notifier.database import SessionTracker
from hooks.cc_notifier.notifier import MacNotifier
from hooks.cc_notifier.utils import format_duration, read_stdin_json, setup_logging, validate_input


# Timestamp file for tracking last cleanup
LAST_CLEANUP_FILE = DEFAULT_CONFIG_DIR / ".last_cleanup"


def should_run_auto_cleanup() -> bool:
    """
    Check if auto-cleanup should run (if >24 hours since last cleanup).

    Returns:
        True if cleanup should run, False otherwise
    """
    if not LAST_CLEANUP_FILE.exists():
        return True

    try:
        last_cleanup = datetime.fromtimestamp(LAST_CLEANUP_FILE.stat().st_mtime)
        return datetime.now() - last_cleanup > timedelta(hours=24)
    except OSError:
        return True


def mark_cleanup_done() -> None:
    """Mark cleanup as completed by updating timestamp file."""
    try:
        LAST_CLEANUP_FILE.parent.mkdir(parents=True, exist_ok=True)
        LAST_CLEANUP_FILE.touch()
    except OSError as e:
        logger.warning(f"Failed to mark cleanup done: {e}")


def main() -> None:
    """Handle Stop event."""
    setup_logging()

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
            # Get runtime config for notification threshold
            runtime_config = get_runtime_config()
            threshold = runtime_config.notification.threshold_seconds

            # Smart filtering: only notify if duration meets threshold
            if duration_seconds >= threshold:
                # Send notification
                notifier = MacNotifier()
                project_name = notifier.get_project_name(cwd)
                duration_str = format_duration(duration_seconds)

                notifier.notify_job_done(project_name, job_number, duration_str)
                logger.info(f"Job #{job_number} completed in {duration_str}")
            else:
                # Skip notification for short-duration jobs
                duration_str = format_duration(duration_seconds)
                logger.debug(
                    f"Skipping notification for job #{job_number} "
                    f"(duration {duration_str} < threshold {threshold}s)"
                )
        else:
            logger.warning(f"No job info found for session {session_id}")

        # Auto-cleanup if enabled and enough time has passed
        runtime_config = get_runtime_config()
        if runtime_config.cleanup.auto_cleanup_enabled and should_run_auto_cleanup():
            logger.info("Running auto-cleanup...")
            stats = tracker.cleanup_old_data(
                retention_days=runtime_config.cleanup.retention_days,
                export_before=runtime_config.cleanup.export_before_cleanup
            )
            mark_cleanup_done()
            logger.info(
                f"Auto-cleanup complete: {stats['rows_deleted']} rows deleted, "
                f"{stats['space_freed_kb']} KB freed"
            )

        sys.exit(0)

    except Exception as e:
        logger.error(f"Stop handler failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
