#!/usr/bin/env python3
"""
PermissionRequest hook handler.

Sends desktop notifications when Claude requests permissions.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from notifier import MacNotifier
from utils import read_stdin_json, setup_logging, validate_input


def main() -> None:
    """Handle PermissionRequest event."""
    logger = setup_logging()

    try:
        # Read and validate input
        data = read_stdin_json()
        validate_input(data)

        # Extract required fields
        cwd = data.get("cwd", "")
        tool_input = data.get("tool_input", {})

        # Get permission details
        if isinstance(tool_input, dict):
            # Extract tool name or command being requested
            tool_name = tool_input.get("name", "")
            command = tool_input.get("command", "")
            description = tool_input.get("description", "")

            # Build notification message
            if command:
                message = f"Command: {command}"
            elif tool_name:
                message = f"Tool: {tool_name}"
            elif description:
                message = description
            else:
                message = "Permission requested"
        else:
            message = "Permission requested"

        # Send notification
        notifier = MacNotifier()
        project_name = notifier.get_project_name(cwd)
        notifier.notify_permission_request(project_name, message)

        logger.info(f"Permission request notification sent: {message}")
        sys.exit(0)

    except Exception as e:
        logger.error(f"PermissionRequest handler failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
