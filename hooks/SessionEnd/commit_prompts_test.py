#!/usr/bin/env python3
"""Unit tests for commit_prompts.py hook."""

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import commit_prompts


class TestMain:
    """Test main() function."""

    @patch.object(commit_prompts, "PROMPTS_DIR")
    def test_exits_early_when_directory_missing(self, mock_dir):
        """Test early exit when ~/.claude-prompts doesn't exist."""
        mock_dir.exists.return_value = False

        with pytest.raises(SystemExit) as exc_info:
            commit_prompts.main()

        assert exc_info.value.code == 0

    @patch("subprocess.run")
    @patch.object(commit_prompts, "PROMPTS_DIR")
    def test_exits_early_when_no_changes(self, mock_dir, mock_run):
        """Test early exit when git status shows no changes."""
        mock_dir.exists.return_value = True
        mock_run.return_value = MagicMock(stdout="", returncode=0)

        with pytest.raises(SystemExit) as exc_info:
            commit_prompts.main()

        assert exc_info.value.code == 0
        mock_run.assert_called_once()
        assert mock_run.call_args[0][0] == ["git", "status", "--porcelain"]

    @patch("subprocess.run")
    @patch.object(commit_prompts, "PROMPTS_DIR")
    def test_commits_when_changes_exist(self, mock_dir, mock_run):
        """Test staging and committing when changes exist."""
        mock_dir.exists.return_value = True
        # First call: git status returns changes
        # Second call: git add
        # Third call: git commit
        mock_run.side_effect = [
            MagicMock(stdout="M file.md\n", returncode=0),
            MagicMock(returncode=0),
            MagicMock(returncode=0),
        ]

        with pytest.raises(SystemExit) as exc_info:
            commit_prompts.main()

        assert exc_info.value.code == 0
        assert mock_run.call_count == 3

        # Verify git add was called
        add_call = mock_run.call_args_list[1]
        assert add_call[0][0] == ["git", "add", "-A"]

        # Verify git commit was called with timestamp
        commit_call = mock_run.call_args_list[2]
        assert commit_call[0][0][0:2] == ["git", "commit"]
        assert "-m" in commit_call[0][0]

    @patch("subprocess.run")
    @patch.object(commit_prompts, "PROMPTS_DIR")
    def test_commit_message_format(self, mock_dir, mock_run):
        """Test commit message includes correct timestamp format."""
        mock_dir.exists.return_value = True
        mock_run.side_effect = [
            MagicMock(stdout="M file.md\n", returncode=0),
            MagicMock(returncode=0),
            MagicMock(returncode=0),
        ]

        with patch("commit_prompts.datetime") as mock_datetime:
            mock_now = datetime(2025, 12, 2, 17, 8, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            with pytest.raises(SystemExit):
                commit_prompts.main()

        commit_call = mock_run.call_args_list[2]
        commit_msg = commit_call[0][0][3]  # The -m argument value
        assert "Update prompts - December 02, 2025 at 17:08 UTC" == commit_msg

    @patch("subprocess.run")
    @patch.object(commit_prompts, "PROMPTS_DIR")
    def test_uses_correct_working_directory(self, mock_dir, mock_run):
        """Test all git commands use PROMPTS_DIR as cwd."""
        mock_dir.exists.return_value = True
        mock_run.side_effect = [
            MagicMock(stdout="M file.md\n", returncode=0),
            MagicMock(returncode=0),
            MagicMock(returncode=0),
        ]

        with pytest.raises(SystemExit):
            commit_prompts.main()

        for call_args in mock_run.call_args_list:
            assert call_args[1]["cwd"] == mock_dir

    @patch("subprocess.run")
    @patch.object(commit_prompts, "PROMPTS_DIR")
    def test_handles_whitespace_only_status(self, mock_dir, mock_run):
        """Test treating whitespace-only status as no changes."""
        mock_dir.exists.return_value = True
        mock_run.return_value = MagicMock(stdout="   \n\t\n", returncode=0)

        with pytest.raises(SystemExit) as exc_info:
            commit_prompts.main()

        assert exc_info.value.code == 0
        mock_run.assert_called_once()  # Only git status, no add/commit

    @patch("subprocess.run")
    @patch.object(commit_prompts, "PROMPTS_DIR")
    def test_propagates_git_add_failure(self, mock_dir, mock_run):
        """Test that git add failure raises CalledProcessError."""
        mock_dir.exists.return_value = True
        mock_run.side_effect = [
            MagicMock(stdout="M file.md\n", returncode=0),
            subprocess.CalledProcessError(1, "git add"),
        ]

        with pytest.raises(subprocess.CalledProcessError):
            commit_prompts.main()

    @patch("subprocess.run")
    @patch.object(commit_prompts, "PROMPTS_DIR")
    def test_propagates_git_commit_failure(self, mock_dir, mock_run):
        """Test that git commit failure raises CalledProcessError."""
        mock_dir.exists.return_value = True
        mock_run.side_effect = [
            MagicMock(stdout="M file.md\n", returncode=0),
            MagicMock(returncode=0),
            subprocess.CalledProcessError(1, "git commit"),
        ]

        with pytest.raises(subprocess.CalledProcessError):
            commit_prompts.main()


class TestPromptsDir:
    """Test PROMPTS_DIR constant."""

    def test_points_to_home_claude_prompts(self):
        """Test PROMPTS_DIR is ~/.claude-prompts."""
        expected = Path.home() / ".claude-prompts"
        assert commit_prompts.PROMPTS_DIR == expected
