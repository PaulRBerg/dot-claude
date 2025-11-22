"""
Notification layer for macOS terminal-notifier integration.
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional

from config import Config


class MacNotifier:
    """Sends macOS desktop notifications using terminal-notifier."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize Mac notifier.

        Args:
            config: Configuration instance (creates default if None)
        """
        self.config = config or Config()
        self.logger = logging.getLogger("cc-notifier.notifier")
        self._available: Optional[bool] = None

    def check_available(self) -> bool:
        """
        Check if terminal-notifier is available.

        Returns:
            True if terminal-notifier is installed and executable
        """
        if self._available is not None:
            return self._available

        try:
            result = subprocess.run(
                ["which", "terminal-notifier"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            self._available = result.returncode == 0
            if not self._available:
                self.logger.warning("terminal-notifier not found, notifications disabled")
            return self._available
        except Exception as e:
            self.logger.warning(f"Failed to check terminal-notifier: {e}")
            self._available = False
            return False

    def send_notification(
        self,
        title: str,
        subtitle: str,
        message: str = "",
        sound: Optional[str] = None,
    ) -> bool:
        """
        Send a desktop notification.

        Args:
            title: Notification title (e.g., project name)
            subtitle: Notification subtitle (e.g., event details)
            message: Optional notification message body
            sound: Optional sound name (defaults to config setting)

        Returns:
            True if notification was sent successfully
        """
        if not self.check_available():
            self.logger.debug("Skipping notification (terminal-notifier not available)")
            return False

        try:
            cmd = [
                "terminal-notifier",
                "-title", title,
                "-subtitle", subtitle,
                "-sound", sound or self.config.notification_sound,
                "-activate", self.config.notification_app_bundle,
            ]

            if message:
                cmd.extend(["-message", message])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                self.logger.info(f"Sent notification: {title} - {subtitle}")
                return True
            else:
                self.logger.warning(f"Notification failed: {result.stderr}")
                return False

        except FileNotFoundError:
            self.logger.warning("terminal-notifier not found")
            self._available = False
            return False
        except subprocess.TimeoutExpired:
            self.logger.error("Notification timed out")
            return False
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")
            return False

    def notify_job_done(
        self,
        project_name: str,
        job_number: int,
        duration_str: str,
    ) -> bool:
        """
        Send job completion notification.

        Args:
            project_name: Project name (from cwd)
            job_number: Job sequence number
            duration_str: Human-readable duration (e.g., "53s", "6m53s")

        Returns:
            True if notification was sent successfully
        """
        subtitle = f"job#{job_number} done, duration: {duration_str}"
        return self.send_notification(
            title=project_name,
            subtitle=subtitle,
        )

    def notify_permission_request(
        self,
        project_name: str,
        message: str = "Permission requested",
    ) -> bool:
        """
        Send permission request notification.

        Args:
            project_name: Project name (from cwd)
            message: Permission request message

        Returns:
            True if notification was sent successfully
        """
        return self.send_notification(
            title=project_name,
            subtitle="Permission Request",
            message=message,
        )

    def notify_action_required(
        self,
        project_name: str,
        message: str,
    ) -> bool:
        """
        Send action required notification.

        Args:
            project_name: Project name (from cwd)
            message: Action required message

        Returns:
            True if notification was sent successfully
        """
        return self.send_notification(
            title=project_name,
            subtitle="Action Required",
            message=message,
        )

    @staticmethod
    def get_project_name(cwd: str) -> str:
        """
        Extract project name from current working directory.

        Args:
            cwd: Current working directory path

        Returns:
            Project name (basename of directory)
        """
        return Path(cwd).name
