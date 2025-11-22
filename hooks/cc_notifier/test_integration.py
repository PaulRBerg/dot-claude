"""
Integration tests for cc-notifier.

Tests complete workflows including event handlers, CLI commands, and auto-cleanup.
"""

import json
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import cli
import config_loader
from hooks.cc_notifier.config import Config
from hooks.cc_notifier.database import SessionTracker
from hooks.cc_notifier.events import stop, user_prompt


class TestUserPromptToStopWorkflow:
    """Test complete workflow from UserPrompt to Stop."""

    @pytest.fixture
    def temp_config(self):
        """Create temporary config with test database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = Config()
            cfg.db_path = Path(tmpdir) / "test.db"
            cfg.hook_dir = Path(tmpdir)
            yield cfg

    @pytest.fixture
    def temp_config_file(self):
        """Create temporary config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            # Create default config
            loader = config_loader.ConfigLoader(config_path)
            loader.save(config_loader.CCNotifierConfig())
            yield config_path

    def test_complete_workflow_long_job(self, temp_config, temp_config_file):
        """Test complete workflow with a job that exceeds notification threshold."""
        session_id = "test-session-1"
        prompt = "Test prompt"
        cwd = "/Users/test/project"

        # Step 1: Track prompt (simulating UserPrompt event)
        tracker = SessionTracker(temp_config)
        tracker.track_prompt(session_id, prompt, cwd)

        # Verify prompt was tracked
        with tracker._get_connection() as conn:
            cursor = conn.execute(
                "SELECT session_id, prompt, cwd FROM sessions WHERE session_id = ?",
                (session_id,)
            )
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == session_id
            assert result[1] == prompt
            assert result[2] == cwd

        # Step 2: Simulate some time passing (15 seconds)
        with tracker._get_connection() as conn:
            # Backdate the created_at timestamp to simulate 15 seconds ago
            conn.execute(
                "UPDATE sessions SET created_at = datetime('now', '-15 seconds') WHERE session_id = ?",
                (session_id,)
            )
            conn.commit()

        # Step 3: Mark as stopped (simulating Stop event)
        tracker.mark_stopped(session_id)

        # Step 4: Verify job info
        job_number, duration_seconds = tracker.get_job_info(session_id)
        assert job_number == 1
        assert duration_seconds >= 14  # Should be ~15 seconds (allow for rounding)

        # Step 5: Verify notification would be sent (duration >= 10s threshold)
        loader = config_loader.ConfigLoader(temp_config_file)
        cfg = loader.load()
        assert duration_seconds >= cfg.notification.threshold_seconds

    def test_complete_workflow_short_job(self, temp_config, temp_config_file):
        """Test workflow with a job below notification threshold (should be filtered)."""
        session_id = "test-session-2"
        prompt = "Quick test"
        cwd = "/Users/test/project"

        # Track prompt
        tracker = SessionTracker(temp_config)
        tracker.track_prompt(session_id, prompt, cwd)

        # Simulate 5 seconds passing (below 10s threshold)
        with tracker._get_connection() as conn:
            conn.execute(
                "UPDATE sessions SET created_at = datetime('now', '-5 seconds') WHERE session_id = ?",
                (session_id,)
            )
            conn.commit()

        # Mark as stopped
        tracker.mark_stopped(session_id)

        # Verify job info
        job_number, duration_seconds = tracker.get_job_info(session_id)
        assert job_number == 1
        assert duration_seconds >= 4  # Should be ~5 seconds (allow for rounding)

        # Verify notification would NOT be sent (duration < 10s threshold)
        loader = config_loader.ConfigLoader(temp_config_file)
        cfg = loader.load()
        assert duration_seconds < cfg.notification.threshold_seconds


class TestDataCleanup:
    """Test data cleanup functionality."""

    @pytest.fixture
    def temp_config(self):
        """Create temporary config with test database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = Config()
            cfg.db_path = Path(tmpdir) / "test.db"
            cfg.hook_dir = Path(tmpdir)
            yield cfg

    def test_cleanup_old_data_with_export(self, temp_config):
        """Test cleanup with export functionality."""
        tracker = SessionTracker(temp_config)

        # Insert old sessions (31 days ago)
        with tracker._get_connection() as conn:
            old_timestamp = int((datetime.now() - timedelta(days=31)).timestamp())
            for i in range(5):
                conn.execute(
                    "INSERT INTO sessions (session_id, prompt, cwd, created_at) VALUES (?, ?, ?, ?)",
                    (f"old-session-{i}", f"old prompt {i}", "/test", old_timestamp)
                )

            # Insert recent sessions (5 days ago)
            recent_timestamp = int((datetime.now() - timedelta(days=5)).timestamp())
            for i in range(3):
                conn.execute(
                    "INSERT INTO sessions (session_id, prompt, cwd, created_at) VALUES (?, ?, ?, ?)",
                    (f"recent-session-{i}", f"recent prompt {i}", "/test", recent_timestamp)
                )
            conn.commit()

        # Run cleanup with 30 day retention
        with tempfile.TemporaryDirectory() as export_dir:
            config_loader.EXPORT_DIR = Path(export_dir)
            stats = tracker.cleanup_old_data(retention_days=30, export_before=True)

        # Verify stats
        assert stats['rows_deleted'] == 5  # Should delete 5 old sessions
        assert stats['rows_exported'] > 0  # Should export before cleanup

        # Verify recent sessions remain
        with tracker._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM sessions")
            count = cursor.fetchone()[0]
            assert count == 3  # Only recent sessions remain

    def test_cleanup_without_export(self, temp_config):
        """Test cleanup without export."""
        tracker = SessionTracker(temp_config)

        # Insert old sessions
        with tracker._get_connection() as conn:
            old_timestamp = int((datetime.now() - timedelta(days=60)).timestamp())
            for i in range(10):
                conn.execute(
                    "INSERT INTO sessions (session_id, prompt, cwd, created_at) VALUES (?, ?, ?, ?)",
                    (f"old-session-{i}", f"old prompt {i}", "/test", old_timestamp)
                )
            conn.commit()

        # Run cleanup without export
        stats = tracker.cleanup_old_data(retention_days=30, export_before=False)

        # Verify stats
        assert stats['rows_deleted'] == 10
        assert stats['rows_exported'] == 0  # No export

    def test_export_to_json(self, temp_config):
        """Test JSON export functionality."""
        tracker = SessionTracker(temp_config)

        # Insert test data
        tracker.track_prompt("session-1", "prompt 1", "/test1")
        tracker.track_prompt("session-2", "prompt 2", "/test2")

        # Export to JSON
        with tempfile.TemporaryDirectory() as tmpdir:
            export_path = Path(tmpdir) / "export.json"
            count = tracker.export_to_json(export_path)

            assert count == 2
            assert export_path.exists()

            # Verify JSON content
            with open(export_path, 'r') as f:
                data = json.load(f)
                assert len(data) == 2
                assert any(s['session_id'] == 'session-1' for s in data)
                assert any(s['session_id'] == 'session-2' for s in data)


class TestCLICommands:
    """Test CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def temp_config_file(self):
        """Create temporary config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            loader = config_loader.ConfigLoader(config_path)
            loader.save(config_loader.CCNotifierConfig())
            yield config_path

    def test_config_show(self, runner, temp_config_file):
        """Test config show command."""
        result = runner.invoke(cli.cli, ['config', 'show', '--path', str(temp_config_file)])
        assert result.exit_code == 0
        assert 'Current Configuration' in result.output
        assert 'Notification Threshold' in result.output
        assert '10s' in result.output

    def test_config_reset(self, runner, temp_config_file):
        """Test config reset command."""
        # Modify config first
        loader = config_loader.ConfigLoader(temp_config_file)
        cfg = loader.load()
        cfg.notification.threshold_seconds = 20
        loader.save(cfg)

        # Reset config
        result = runner.invoke(
            cli.cli,
            ['config', 'reset', '--path', str(temp_config_file)],
            input='y\n'
        )
        assert result.exit_code == 0
        assert 'reset to defaults' in result.output

        # Verify reset - create new loader to avoid cache
        new_loader = config_loader.ConfigLoader(temp_config_file)
        cfg = new_loader.load()
        assert cfg.notification.threshold_seconds == 10  # Back to default

    def test_test_command(self, runner):
        """Test the test notification command."""
        with patch('cli.MacNotifier') as mock_notifier:
            mock_instance = MagicMock()
            mock_notifier.return_value = mock_instance

            result = runner.invoke(cli.cli, ['test'])

            # Should call notify_job_done
            assert mock_instance.notify_job_done.called
            assert result.exit_code == 0
            assert 'Test notification sent' in result.output

    def test_cleanup_dry_run(self, runner):
        """Test cleanup with dry-run flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create temp database with test data
            cfg = Config()
            cfg.db_path = Path(tmpdir) / "test.db"
            cfg.hook_dir = Path(tmpdir)

            tracker = SessionTracker(cfg)
            tracker.track_prompt("test-1", "prompt", "/test")

            with patch('cli.SessionTracker') as mock_tracker:
                mock_tracker.return_value = tracker

                result = runner.invoke(cli.cli, ['cleanup', '--dry-run'])

                assert result.exit_code == 0
                assert 'DRY RUN MODE' in result.output
                assert 'No data will be deleted' in result.output


class TestConfigLoader:
    """Test configuration loader."""

    def test_load_default_config(self):
        """Test loading default configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nonexistent.yaml"
            loader = config_loader.ConfigLoader(config_path)
            cfg = loader.load()

            # Should load defaults
            assert cfg.notification.threshold_seconds == 10
            assert cfg.cleanup.retention_days == 30
            assert cfg.cleanup.auto_cleanup_enabled is True

    def test_load_custom_config(self):
        """Test loading custom configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "custom.yaml"

            # Create custom config
            custom_cfg = config_loader.CCNotifierConfig()
            custom_cfg.notification.threshold_seconds = 15
            custom_cfg.cleanup.retention_days = 60

            loader = config_loader.ConfigLoader(config_path)
            loader.save(custom_cfg)

            # Load and verify
            loaded_cfg = loader.load()
            assert loaded_cfg.notification.threshold_seconds == 15
            assert loaded_cfg.cleanup.retention_days == 60

    def test_config_validation(self):
        """Test configuration validation."""
        # Invalid log level should raise error
        with pytest.raises(Exception):
            cfg = config_loader.LoggingConfig(level="INVALID")


class TestAutoCleanup:
    """Test auto-cleanup functionality."""

    @pytest.fixture
    def temp_config(self):
        """Create temporary config with test database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = Config()
            cfg.db_path = Path(tmpdir) / "test.db"
            cfg.hook_dir = Path(tmpdir)
            yield cfg

    def test_should_run_auto_cleanup_first_time(self):
        """Test auto-cleanup runs on first execution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            last_cleanup_file = Path(tmpdir) / ".last_cleanup"

            # Mock the LAST_CLEANUP_FILE
            with patch('hooks.cc_notifier.events.stop.LAST_CLEANUP_FILE', last_cleanup_file):
                result = stop.should_run_auto_cleanup()
                assert result is True  # Should run since file doesn't exist

    def test_should_run_auto_cleanup_after_24_hours(self):
        """Test auto-cleanup runs after 24 hours."""
        with tempfile.TemporaryDirectory() as tmpdir:
            last_cleanup_file = Path(tmpdir) / ".last_cleanup"
            last_cleanup_file.touch()

            # Set file mtime to 25 hours ago
            old_time = (datetime.now() - timedelta(hours=25)).timestamp()
            import os
            os.utime(last_cleanup_file, (old_time, old_time))

            with patch('hooks.cc_notifier.events.stop.LAST_CLEANUP_FILE', last_cleanup_file):
                result = stop.should_run_auto_cleanup()
                assert result is True  # Should run since >24 hours

    def test_should_not_run_auto_cleanup_recent(self):
        """Test auto-cleanup doesn't run if recent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            last_cleanup_file = Path(tmpdir) / ".last_cleanup"
            last_cleanup_file.touch()  # Just created

            with patch('hooks.cc_notifier.events.stop.LAST_CLEANUP_FILE', last_cleanup_file):
                result = stop.should_run_auto_cleanup()
                assert result is False  # Should not run since <24 hours


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
