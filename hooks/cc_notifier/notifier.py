"""
Notification layer using notify-py for cross-platform notifications.
"""

from pathlib import Path
from typing import Optional

from loguru import logger
from notifypy import Notify

from hooks.cc_notifier.config import Config


class MacNotifier:
    """Sends desktop notifications using notify-py (cross-platform)."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize notifier.

        Args:
            config: Configuration instance (creates default if None)
        """
        self.config = config or Config()
        self._notification = Notify()
        self._available: Optional[bool] = None

    def check_available(self) -> bool:
        """
        Check if notifications are available on this platform.

        Returns:
            True if notifications are supported
        """
        if self._available is not None:
            return self._available

        try:
            # notify-py handles platform detection automatically
            # Just check if we can create a notification object
            self._available = True
            return True
        except Exception as e:
            logger.warning(f"Notifications not available: {e}")
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
            sound: Optional sound name (unused in notify-py)

        Returns:
            True if notification was sent successfully
        """
        if not self.check_available():
            logger.debug("Skipping notification (not available on this platform)")
            return False

        try:
            # Create a new notification for each send
            notification = Notify()
            notification.title = title
            notification.message = f"{subtitle}\n{message}" if message else subtitle
            notification.application_name = self.config.notification_app_bundle

            # Send the notification
            notification.send(block=False)

            logger.info(f"Sent notification: {title} - {subtitle}")
            return True

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            self._available = False
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
