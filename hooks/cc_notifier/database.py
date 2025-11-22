"""
Database layer for session tracking.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Generator, Optional

from loguru import logger

from hooks.cc_notifier.config import (
    DB_SCHEMA,
    EXPORT_DIR,
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
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database schema if it doesn't exist."""
        try:
            with self._get_connection() as conn:
                conn.executescript(DB_SCHEMA)
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}")
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
                logger.info(f"Tracked prompt for session {session_id}")
        except sqlite3.Error as e:
            logger.error(f"Failed to track prompt: {e}")

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
                    logger.info(f"Marked session {session_id} as stopped")
                else:
                    logger.warning(f"No active session found for {session_id}")
        except sqlite3.Error as e:
            logger.error(f"Failed to mark stopped: {e}")

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
                logger.debug(f"Marked session {session_id} as waiting")
        except sqlite3.Error as e:
            logger.error(f"Failed to mark waiting: {e}")

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
            logger.error(f"Failed to get job info: {e}")
            return None, None

    def export_to_json(self, output_path: Path, days: Optional[int] = None) -> int:
        """
        Export sessions to JSON file.

        Args:
            output_path: Path to output JSON file
            days: Optional number of days to limit export (None = all data)

        Returns:
            Number of sessions exported
        """
        try:
            with self._get_connection() as conn:
                # Build query based on days filter
                if days is not None:
                    cutoff_timestamp = int((datetime.now() - timedelta(days=days)).timestamp())
                    query = """
                        SELECT id, session_id, created_at, prompt, cwd,
                               job_number, stopped_at, last_wait_at, duration_seconds
                        FROM sessions
                        WHERE created_at >= ?
                        ORDER BY created_at DESC
                    """
                    cursor = conn.execute(query, (cutoff_timestamp,))
                else:
                    query = """
                        SELECT id, session_id, created_at, prompt, cwd,
                               job_number, stopped_at, last_wait_at, duration_seconds
                        FROM sessions
                        ORDER BY created_at DESC
                    """
                    cursor = conn.execute(query)

                # Fetch all rows and convert to dict
                columns = [desc[0] for desc in cursor.description]
                sessions = []
                for row in cursor.fetchall():
                    session_dict = dict(zip(columns, row))
                    sessions.append(session_dict)

                # Ensure export directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Write to JSON file
                with open(output_path, 'w') as f:
                    json.dump(sessions, f, indent=2, default=str)

                logger.info(f"Exported {len(sessions)} sessions to {output_path}")
                return len(sessions)

        except (sqlite3.Error, IOError) as e:
            logger.error(f"Failed to export to JSON: {e}")
            return 0

    def cleanup_old_data(
        self,
        retention_days: int,
        export_before: bool = True
    ) -> dict[str, int]:
        """
        Clean up sessions older than retention period.

        Args:
            retention_days: Number of days to retain
            export_before: Whether to export data before deletion

        Returns:
            Dictionary with cleanup statistics (rows_deleted, space_freed_kb, rows_exported)
        """
        stats = {"rows_deleted": 0, "space_freed_kb": 0, "rows_exported": 0}

        try:
            # Calculate cutoff timestamp
            cutoff_timestamp = int((datetime.now() - timedelta(days=retention_days)).timestamp())

            # Export before cleanup if requested
            if export_before:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_path = EXPORT_DIR / f"sessions_before_cleanup_{timestamp}.json"
                stats["rows_exported"] = self.export_to_json(export_path)

            # Get database size before cleanup
            db_size_before = self.config.db_path.stat().st_size if self.config.db_path.exists() else 0

            # Delete old sessions
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "DELETE FROM sessions WHERE created_at < ?",
                    (cutoff_timestamp,)
                )
                stats["rows_deleted"] = cursor.rowcount
                conn.commit()

                # VACUUM to reclaim space
                conn.execute("VACUUM")

            # Get database size after cleanup
            db_size_after = self.config.db_path.stat().st_size if self.config.db_path.exists() else 0
            stats["space_freed_kb"] = max(0, (db_size_before - db_size_after) // 1024)

            logger.info(
                f"Cleanup complete: deleted {stats['rows_deleted']} sessions, "
                f"freed {stats['space_freed_kb']} KB"
            )

            return stats

        except (sqlite3.Error, OSError) as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return stats

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
            logger.error(f"Failed to get stats: {e}")
            return {"total_prompts": 0, "unique_sessions": 0}
