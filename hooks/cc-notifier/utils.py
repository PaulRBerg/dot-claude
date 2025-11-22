"""
Utility functions for cc-notifier.
"""

import json
import sys
from typing import Any, Optional

from loguru import logger
from pydantic import BaseModel, Field, field_validator

from config import Config


class BaseEventData(BaseModel):
    """Base model for event input data with common validation."""

    session_id: str = Field(..., min_length=1, max_length=255)
    cwd: str = Field(...)

    @field_validator("cwd")
    @classmethod
    def validate_cwd(cls, v: str) -> str:
        """Validate cwd for path traversal and sensitive paths."""
        if ".." in v:
            raise ValueError("Path traversal detected in cwd")

        # Warn about sensitive paths
        sensitive_paths = [".env", ".git/", "credentials", "secrets", "password"]
        cwd_lower = v.lower()
        for sensitive in sensitive_paths:
            if sensitive in cwd_lower:
                logger.warning(f"Sensitive path detected: {v}")

        return v


class UserPromptData(BaseEventData):
    """Input data for UserPromptSubmit event."""

    prompt: Optional[str] = None


class StopEventData(BaseEventData):
    """Input data for Stop event."""

    pass


class PermissionRequestData(BaseEventData):
    """Input data for PermissionRequest event."""

    tool_input: Optional[dict[str, Any]] = None


class NotificationData(BaseEventData):
    """Input data for Notification event."""

    message: Optional[str] = None


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


def setup_logging() -> None:
    """
    Set up logging with rotation using loguru.

    Configures loguru to write to the configured log file with rotation.
    """
    config = Config()
    config.ensure_directories()

    # Remove default handler and add file handler with rotation
    logger.remove()  # Remove default handler
    logger.add(
        config.log_path,
        rotation="10 MB",
        retention=5,
        format="{time:YYYY-MM-DD HH:mm:ss} - {name} - {level} - {message}",
        level="INFO",
    )


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
                logger.warning(f"Sensitive path detected: {data['cwd']}")


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


def parse_event_data(data: dict[str, Any], model_class: type[BaseModel]) -> BaseModel:
    """
    Parse and validate event data using a Pydantic model.

    Args:
        data: Raw input data dictionary
        model_class: Pydantic model class to validate against

    Returns:
        Validated Pydantic model instance

    Raises:
        ValueError: If validation fails
    """
    try:
        return model_class.model_validate(data)
    except Exception as e:
        raise ValueError(f"Input validation failed: {e}")
