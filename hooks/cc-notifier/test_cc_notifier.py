"""
Basic tests for cc-notifier.
"""

import tempfile
from unittest.mock import MagicMock, patch

import pytest

# Import from the cc_notifier package
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import config
import database
import notifier
import utils

Config = config.Config
SessionTracker = database.SessionTracker
MacNotifier = notifier.MacNotifier
format_duration = utils.format_duration
validate_input = utils.validate_input


class TestFormatDuration:
    """Test duration formatting."""

    def test_seconds_only(self):
        assert format_duration(53) == "53s"
        assert format_duration(0) == "0s"
        assert format_duration(59) == "59s"

    def test_minutes_and_seconds(self):
        assert format_duration(130) == "2m10s"
        assert format_duration(413) == "6m53s"

    def test_minutes_only(self):
        assert format_duration(240) == "4m"
        assert format_duration(60) == "1m"

    def test_hours(self):
        assert format_duration(3661) == "1h1m"
        assert format_duration(3600) == "1h"
        assert format_duration(7384) == "2h3m"


class TestValidateInput:
    """Test input validation."""

    def test_valid_input(self):
        data = {
            "session_id": "test-session",
            "cwd": "/Users/test/project",
            "prompt": "test prompt",
        }
        # Should not raise
        validate_input(data)

    def test_path_traversal(self):
        data = {"cwd": "/Users/test/../../../etc/passwd"}
        with pytest.raises(ValueError, match="Path traversal"):
            validate_input(data)

    def test_invalid_session_id(self):
        data = {"session_id": ""}
        with pytest.raises(ValueError, match="Invalid session_id"):
            validate_input(data)

    def test_long_session_id(self):
        data = {"session_id": "x" * 256}
        with pytest.raises(ValueError, match="Invalid session_id"):
            validate_input(data)


class TestSessionTracker:
    """Test SessionTracker database operations."""

    @pytest.fixture
    def temp_config(self):
        """Create temporary config with test database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config()
            config.db_path = Path(tmpdir) / "test.db"
            config.hook_dir = Path(tmpdir)
            yield config

    def test_track_prompt(self, temp_config):
        tracker = SessionTracker(temp_config)
        tracker.track_prompt("session-1", "test prompt", "/Users/test/project")

        # Verify insertion
        with tracker._get_connection() as conn:
            cursor = conn.execute("SELECT session_id, prompt, cwd, job_number FROM sessions")
            result = cursor.fetchone()
            assert result[0] == "session-1"
            assert result[1] == "test prompt"
            assert result[2] == "/Users/test/project"
            assert result[3] == 1  # Auto-incremented job number

    def test_job_number_increment(self, temp_config):
        tracker = SessionTracker(temp_config)
        tracker.track_prompt("session-1", "prompt 1", "/Users/test/project")
        tracker.track_prompt("session-1", "prompt 2", "/Users/test/project")

        with tracker._get_connection() as conn:
            cursor = conn.execute(
                "SELECT job_number FROM sessions WHERE session_id = 'session-1' ORDER BY id"
            )
            results = cursor.fetchall()
            assert results[0][0] == 1
            assert results[1][0] == 2

    def test_mark_stopped(self, temp_config):
        tracker = SessionTracker(temp_config)
        tracker.track_prompt("session-1", "test", "/Users/test/project")
        tracker.mark_stopped("session-1")

        with tracker._get_connection() as conn:
            cursor = conn.execute(
                "SELECT stopped_at, duration_seconds FROM sessions WHERE session_id = 'session-1'"
            )
            result = cursor.fetchone()
            assert result[0] is not None  # stopped_at should be set
            assert result[1] is not None  # duration should be calculated

    def test_get_job_info(self, temp_config):
        tracker = SessionTracker(temp_config)
        tracker.track_prompt("session-1", "test", "/Users/test/project")
        tracker.mark_stopped("session-1")

        job_number, duration = tracker.get_job_info("session-1")
        assert job_number == 1
        assert duration is not None
        assert duration >= 0

    def test_get_stats(self, temp_config):
        tracker = SessionTracker(temp_config)
        tracker.track_prompt("session-1", "test 1", "/Users/test/project")
        tracker.track_prompt("session-1", "test 2", "/Users/test/project")
        tracker.track_prompt("session-2", "test 3", "/Users/test/project")

        stats = tracker.get_stats()
        assert stats["total_prompts"] == 3
        assert stats["unique_sessions"] == 2


class TestMacNotifier:
    """Test MacNotifier notification logic."""

    @pytest.fixture
    def notifier(self):
        return MacNotifier()

    @patch("subprocess.run")
    def test_check_available_true(self, mock_run, notifier):
        mock_run.return_value = MagicMock(returncode=0)
        assert notifier.check_available() is True

    @patch("subprocess.run")
    def test_check_available_false(self, mock_run, notifier):
        mock_run.return_value = MagicMock(returncode=1)
        assert notifier.check_available() is False

    @patch("subprocess.run")
    def test_send_notification_success(self, mock_run, notifier):
        notifier._available = True
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        result = notifier.send_notification("Test", "Subtitle")
        assert result is True

        # Verify command structure
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "terminal-notifier"
        assert "-title" in call_args
        assert "Test" in call_args
        assert "-subtitle" in call_args
        assert "Subtitle" in call_args

    @patch("subprocess.run")
    def test_send_notification_unavailable(self, mock_run, notifier):
        notifier._available = False
        result = notifier.send_notification("Test", "Subtitle")
        assert result is False
        mock_run.assert_not_called()

    def test_get_project_name(self, notifier):
        assert notifier.get_project_name("/Users/test/my-project") == "my-project"
        assert notifier.get_project_name("/Users/test/project/") == "project"
        assert notifier.get_project_name("/Users/test/.claude") == ".claude"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
