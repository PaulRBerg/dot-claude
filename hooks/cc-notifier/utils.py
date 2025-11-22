"""
Utility functions for cc-notifier.
"""

import json
import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import Any

from config import Config, LOG_BACKUP_COUNT, LOG_DATE_FORMAT, LOG_FORMAT, LOG_MAX_BYTES


def format_duration(seconds: int) -> str:
    """
    Format duration in seconds to human-readable string.

    Examples:
        53 -> "53s"
        130 -> "2m10s"
        413 -> "6m53s"
        240 -> "4m"
        3661 -> "1h1m"

    Args:
        seconds: Duration in seconds

    Returns:
        Human-readable duration string
    """
    if seconds < 60:
        return f"{seconds}s"

    minutes = seconds // 60
    remaining_seconds = seconds % 60

    if minutes < 60:
        if remaining_seconds == 0:
            return f"{minutes}m"
        return f"{minutes}m{remaining_seconds}s"

    hours = minutes // 60
    remaining_minutes = minutes % 60

    if remaining_minutes == 0:
        return f"{hours}h"
    return f"{hours}h{remaining_minutes}m"


def setup_logging(name: str = "cc-notifier") -> logging.Logger:
    """
    Set up logging with rotation.

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    config = Config()
    config.ensure_directories()

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # File handler with rotation
    handler = RotatingFileHandler(
        config.log_path,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
    )
    handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
    logger.addHandler(handler)

    return logger


def validate_input(data: dict[str, Any]) -> None:
    """
    Validate and sanitize input data for security.

    Raises:
        ValueError: If input validation fails

    Args:
        data: Input data dictionary to validate
    """
    # Check for path traversal in cwd
    if "cwd" in data:
        cwd = str(data["cwd"])
        if ".." in cwd:
            raise ValueError("Path traversal detected in cwd")

    # Validate session_id format if present
    if "session_id" in data:
        session_id = str(data["session_id"])
        if not session_id or len(session_id) > 255:
            raise ValueError("Invalid session_id")

    # Block sensitive file paths
    sensitive_paths = [".env", ".git/", "credentials", "secrets", "password"]
    if "cwd" in data:
        cwd_lower = str(data["cwd"]).lower()
        for sensitive in sensitive_paths:
            if sensitive in cwd_lower:
                logging.warning(f"Sensitive path detected: {data['cwd']}")


def read_stdin_json() -> dict[str, Any]:
    """
    Read and parse JSON from stdin.

    Returns:
        Parsed JSON data

    Raises:
        ValueError: If JSON parsing fails
    """
    try:
        data = json.load(sys.stdin)
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from stdin: {e}")
    except Exception as e:
        raise ValueError(f"Failed to read stdin: {e}")
