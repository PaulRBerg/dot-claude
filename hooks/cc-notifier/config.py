"""
Configuration and constants for cc-notifier.
"""

from pathlib import Path

# Paths
HOOK_DIR = Path.home() / ".claude" / "hooks" / "cc-notifier"
DB_PATH = HOOK_DIR / "cc-notifier.db"
LOG_PATH = HOOK_DIR / "cc-notifier.log"

# Notification settings
NOTIFICATION_SOUND = "default"
NOTIFICATION_APP_BUNDLE = "dev.warp.Warp-Stable"  # Focus Warp terminal on click

# Database schema
DB_SCHEMA = """--sql
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    prompt TEXT,
    cwd TEXT,
    job_number INTEGER,
    stopped_at DATETIME,
    last_wait_at DATETIME,
    duration_seconds INTEGER
);

CREATE INDEX IF NOT EXISTS idx_session_id ON sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_created_at ON sessions(created_at);

CREATE TRIGGER IF NOT EXISTS auto_job_number
AFTER INSERT ON sessions
FOR EACH ROW
WHEN NEW.job_number IS NULL
BEGIN
    UPDATE sessions
    SET job_number = (
        SELECT COALESCE(MAX(job_number), 0) + 1
        FROM sessions
        WHERE session_id = NEW.session_id
    )
    WHERE id = NEW.id;
END;
"""

# SQL queries
SQL_INSERT_PROMPT = """--sql
INSERT INTO sessions (session_id, prompt, cwd)
VALUES (?, ?, ?)
"""

SQL_UPDATE_STOPPED = """--sql
UPDATE sessions
SET stopped_at = CURRENT_TIMESTAMP,
    duration_seconds = CAST((julianday(CURRENT_TIMESTAMP) - julianday(created_at)) * 86400 AS INTEGER)
WHERE id = (
    SELECT id FROM sessions
    WHERE session_id = ?
      AND stopped_at IS NULL
    ORDER BY created_at DESC
    LIMIT 1
)
"""

SQL_UPDATE_WAITING = """--sql
UPDATE sessions
SET last_wait_at = CURRENT_TIMESTAMP
WHERE id = (
    SELECT id FROM sessions
    WHERE session_id = ?
      AND stopped_at IS NULL
    ORDER BY created_at DESC
    LIMIT 1
)
"""

SQL_GET_JOB_INFO = """--sql
SELECT job_number, duration_seconds
FROM sessions
WHERE session_id = ?
  AND stopped_at IS NOT NULL
ORDER BY created_at DESC
LIMIT 1
"""

# Logging configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5


class Config:
    """Central configuration class."""

    def __init__(self):
        self.hook_dir = HOOK_DIR
        self.db_path = DB_PATH
        self.log_path = LOG_PATH
        self.notification_sound = NOTIFICATION_SOUND
        self.notification_app_bundle = NOTIFICATION_APP_BUNDLE

    def ensure_directories(self) -> None:
        """Ensure all necessary directories exist."""
        self.hook_dir.mkdir(parents=True, exist_ok=True)
