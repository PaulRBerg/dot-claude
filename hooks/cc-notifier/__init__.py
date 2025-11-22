"""
cc-notifier: Desktop notification system for Claude Code.

Tracks Claude Code session activity and sends macOS notifications for key events.
"""

__version__ = "2.0.0"
__author__ = "Claude Code User"

from config import Config
from database import SessionTracker
from notifier import MacNotifier
from utils import format_duration, setup_logging, validate_input, read_stdin_json

__all__ = [
    "Config",
    "SessionTracker",
    "MacNotifier",
    "format_duration",
    "setup_logging",
    "validate_input",
    "read_stdin_json",
]
