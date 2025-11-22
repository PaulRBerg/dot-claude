"""
Database layer for session tracking.
"""

import logging
import sqlite3
from contextlib import contextmanager
from typing import Generator, Optional

from config import (
    DB_SCHEMA,
    SQL_GET_JOB_INFO,
    SQL_INSERT_PROMPT,
    SQL_UPDATE_STOPPED,
    SQL_UPDATE_WAITING,
    Config,
)


class SessionTracker:
    """Tracks Claude Code sessions in SQLite database."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize session tracker.

        Args:
            config: Configuration instance (creates default if None)
        """
        self.config = config or Config()
        self.config.ensure_directories()
        self.logger = logging.getLogger("cc-notifier.database")
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database schema if it doesn't exist."""
        try:
            with self._get_connection() as conn:
                conn.executescript(DB_SCHEMA)
                conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Get database connection as context manager.

        Yields:
            SQLite connection
        """
        conn = sqlite3.connect(str(self.config.db_path))
        try:
            yield conn
        finally:
            conn.close()

    def track_prompt(self, session_id: str, prompt: str, cwd: str) -> None:
        """
        Track a new prompt submission.

        Args:
            session_id: Session identifier
            prompt: User prompt text
            cwd: Current working directory
        """
        try:
            with self._get_connection() as conn:
                conn.execute(SQL_INSERT_PROMPT, (session_id, prompt, cwd))
                conn.commit()
                self.logger.info(f"Tracked prompt for session {session_id}")
        except sqlite3.Error as e:
            self.logger.error(f"Failed to track prompt: {e}")

    def mark_stopped(self, session_id: str) -> None:
        """
        Mark session as stopped and calculate duration.

        Args:
            session_id: Session identifier
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(SQL_UPDATE_STOPPED, (session_id,))
                conn.commit()
                if cursor.rowcount > 0:
                    self.logger.info(f"Marked session {session_id} as stopped")
                else:
                    self.logger.warning(f"No active session found for {session_id}")
        except sqlite3.Error as e:
            self.logger.error(f"Failed to mark stopped: {e}")

    def mark_waiting(self, session_id: str) -> None:
        """
        Mark session as waiting for user input.

        Args:
            session_id: Session identifier
        """
        try:
            with self._get_connection() as conn:
                conn.execute(SQL_UPDATE_WAITING, (session_id,))
                conn.commit()
                self.logger.debug(f"Marked session {session_id} as waiting")
        except sqlite3.Error as e:
            self.logger.error(f"Failed to mark waiting: {e}")

    def get_job_info(self, session_id: str) -> tuple[Optional[int], Optional[int]]:
        """
        Get job number and duration for most recent completed job.

        Args:
            session_id: Session identifier

        Returns:
            Tuple of (job_number, duration_seconds) or (None, None) if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(SQL_GET_JOB_INFO, (session_id,))
                result = cursor.fetchone()
                if result:
                    return result[0], result[1]
                return None, None
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get job info: {e}")
            return None, None

    def get_stats(self) -> dict[str, int]:
        """
        Get database statistics.

        Returns:
            Dictionary with total_prompts and unique_sessions counts
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*), COUNT(DISTINCT session_id) FROM sessions")
                result = cursor.fetchone()
                return {
                    "total_prompts": result[0] if result else 0,
                    "unique_sessions": result[1] if result else 0,
                }
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get stats: {e}")
            return {"total_prompts": 0, "unique_sessions": 0}
