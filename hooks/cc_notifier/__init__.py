"""
cc-notifier: Desktop notification system for Claude Code.

Tracks Claude Code session activity and sends macOS notifications for key events.
"""

__version__ = "2.0.0"
__author__ = "Claude Code User"

from hooks.cc_notifier.config import Config
from hooks.cc_notifier.database import SessionTracker
from hooks.cc_notifier.notifier import MacNotifier
from hooks.cc_notifier.utils import format_duration, setup_logging, validate_input, read_stdin_json

__all__ = [
    "Config",
    "SessionTracker",
    "MacNotifier",
    "format_duration",
    "setup_logging",
    "validate_input",
    "read_stdin_json",
]
