#!/usr/bin/env python3
"""Unit tests for add_plan_frontmatter.py hook."""

import json
import subprocess
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import add_plan_frontmatter


class TestGetGitBranch:
    """Test get_git_branch() function."""

    @patch("subprocess.run")
    def test_returns_branch_name(self, mock_run):
        """Test returning branch name from git."""
        mock_run.return_value = MagicMock(returncode=0, stdout="main\n")
        result = add_plan_frontmatter.get_git_branch("/some/path")
        assert result == "main"

    @patch("subprocess.run")
    def test_returns_empty_on_failure(self, mock_run):
        """Test returning empty string when git fails."""
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = add_plan_frontmatter.get_git_branch("/some/path")
        assert result == ""

    @patch("subprocess.run")
    def test_returns_empty_on_timeout(self, mock_run):
        """Test returning empty string on timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("git", 5)
        result = add_plan_frontmatter.get_git_branch("/some/path")
        assert result == ""

    def test_returns_empty_for_empty_cwd(self):
        """Test returning empty string for empty cwd."""
        result = add_plan_frontmatter.get_git_branch("")
        assert result == ""


class TestBuildFrontmatter:
    """Test build_frontmatter() function."""

    @patch("pathlib.Path.home")
    @patch("add_plan_frontmatter.get_git_branch")
    @patch("add_plan_frontmatter.datetime")
    def test_builds_complete_frontmatter(self, mock_datetime, mock_git, mock_home):
        """Test building frontmatter with all fields."""
        mock_home.return_value = Path("/Users/prb")
        mock_datetime.now.return_value = datetime(2025, 12, 2, 14, 30, 0, tzinfo=timezone.utc)
        mock_datetime.timezone = timezone
        mock_git.return_value = "feature-branch"

        data = {"session_id": "abc123", "cwd": "/Users/prb/projects/test"}
        plan_path = "/Users/prb/.claude/plans/test-plan.md"

        result = add_plan_frontmatter.build_frontmatter(data, plan_path)

        assert "---" in result
        # Fields ordered alphabetically
        assert 'created: "2025-12-02T14:30:00Z"' in result
        assert 'git_branch: "feature-branch"' in result
        assert 'plan_path: "~/.claude/plans/test-plan.md"' in result
        assert 'project_directory: "~/projects/test"' in result
        assert 'session_id: "abc123"' in result

    @patch("add_plan_frontmatter.get_git_branch")
    @patch("add_plan_frontmatter.datetime")
    def test_skips_empty_git_branch(self, mock_datetime, mock_git):
        """Test that empty git branch is omitted."""
        mock_datetime.now.return_value = datetime(2025, 12, 2, 14, 30, 0, tzinfo=timezone.utc)
        mock_datetime.timezone = timezone
        mock_git.return_value = ""

        data = {"session_id": "abc123", "cwd": "/tmp/no-repo"}
        plan_path = "/tmp/test-plans/plan.md"

        result = add_plan_frontmatter.build_frontmatter(data, plan_path)

        assert "git_branch" not in result

    @patch("pathlib.Path.home")
    @patch("add_plan_frontmatter.get_git_branch")
    @patch("add_plan_frontmatter.datetime")
    def test_handles_path_with_spaces(self, mock_datetime, mock_git, mock_home):
        """Test that paths with spaces are properly quoted."""
        mock_home.return_value = Path("/Users/prb")
        mock_datetime.now.return_value = datetime(2025, 12, 2, 14, 30, 0, tzinfo=timezone.utc)
        mock_datetime.timezone = timezone
        mock_git.return_value = "main"

        data = {"session_id": "abc", "cwd": "/Users/prb/My Documents/project"}
        plan_path = "/tmp/test-plans/plan.md"

        result = add_plan_frontmatter.build_frontmatter(data, plan_path)

        assert 'project_directory: "~/My Documents/project"' in result

    @patch("add_plan_frontmatter.get_git_branch")
    @patch("add_plan_frontmatter.datetime")
    def test_escapes_yaml_special_characters(self, mock_datetime, mock_git):
        """Test that quotes and backslashes are escaped for YAML safety."""
        mock_datetime.now.return_value = datetime(2025, 12, 2, 14, 30, 0, tzinfo=timezone.utc)
        mock_datetime.timezone = timezone
        mock_git.return_value = "feature/test"

        data = {"session_id": "abc123", "cwd": 'C:\\Users\\name\\"quoted"'}
        plan_path = "/tmp/test-plans/plan.md"

        result = add_plan_frontmatter.build_frontmatter(data, plan_path)

        # Backslashes and quotes should be escaped
        assert 'project_directory: "C:\\\\Users\\\\name\\\\\\"quoted\\""' in result

    def test_to_tilde_path_converts_home_directory(self):
        """Test that home directory paths are converted to ~ notation."""
        home = str(Path.home())
        result = add_plan_frontmatter.to_tilde_path(f"{home}/.claude/plans/test.md")
        assert result == "~/.claude/plans/test.md"

    def test_to_tilde_path_preserves_non_home_paths(self):
        """Test that non-home paths are preserved."""
        result = add_plan_frontmatter.to_tilde_path("/tmp/test-plans/plan.md")
        assert result == "/tmp/test-plans/plan.md"


class TestMain:
    """Test main() entry point."""

    @patch("sys.stdin", new_callable=StringIO)
    def test_exits_on_invalid_json(self, mock_stdin):
        """Test graceful exit on invalid JSON."""
        mock_stdin.write("not valid json{")
        mock_stdin.seek(0)

        with pytest.raises(SystemExit) as exc_info:
            add_plan_frontmatter.main()

        assert exc_info.value.code == 0

    @patch("sys.stdin", new_callable=StringIO)
    def test_exits_on_non_write_tool(self, mock_stdin):
        """Test exit when tool_name is not Write."""
        data = {"tool_name": "Read", "tool_input": {"file_path": "/some/file"}}
        mock_stdin.write(json.dumps(data))
        mock_stdin.seek(0)

        with pytest.raises(SystemExit) as exc_info:
            add_plan_frontmatter.main()

        assert exc_info.value.code == 0

    @patch("add_plan_frontmatter.PLANS_DIR", Path("/tmp/test-plans"))
    @patch("sys.stdin", new_callable=StringIO)
    def test_exits_on_file_outside_plans_dir(self, mock_stdin):
        """Test exit when file is outside plans directory."""
        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": "/some/other/file.md"},
        }
        mock_stdin.write(json.dumps(data))
        mock_stdin.seek(0)

        with pytest.raises(SystemExit) as exc_info:
            add_plan_frontmatter.main()

        assert exc_info.value.code == 0

    @patch("add_plan_frontmatter.PLANS_DIR", Path("/tmp/test-plans"))
    @patch("sys.stdin", new_callable=StringIO)
    def test_exits_on_non_markdown_file(self, mock_stdin):
        """Test exit when file is not a markdown file."""
        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/test-plans/file.txt"},
        }
        mock_stdin.write(json.dumps(data))
        mock_stdin.seek(0)

        with pytest.raises(SystemExit) as exc_info:
            add_plan_frontmatter.main()

        assert exc_info.value.code == 0

    @patch("add_plan_frontmatter.PLANS_DIR", Path("/tmp/test-plans"))
    @patch("pathlib.Path.read_text")
    @patch("sys.stdin", new_callable=StringIO)
    def test_skips_file_with_existing_frontmatter(self, mock_stdin, mock_read):
        """Test idempotency - skip if frontmatter exists."""
        mock_read.return_value = "---\ncreated: 2025-01-01\n---\n# Plan"

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/test-plans/existing.md"},
        }
        mock_stdin.write(json.dumps(data))
        mock_stdin.seek(0)

        with pytest.raises(SystemExit) as exc_info:
            add_plan_frontmatter.main()

        assert exc_info.value.code == 0

    @patch("add_plan_frontmatter.PLANS_DIR", Path("/tmp/test-plans"))
    @patch("add_plan_frontmatter.build_frontmatter")
    @patch("pathlib.Path.write_text")
    @patch("pathlib.Path.read_text")
    @patch("sys.stdin", new_callable=StringIO)
    def test_adds_frontmatter_to_new_plan(self, mock_stdin, mock_read, mock_write, mock_build):
        """Test adding frontmatter to new plan file."""
        mock_read.return_value = "# My Plan\n\nSome content"
        mock_build.return_value = '---\ncreated: "2025-12-02T14:30:00Z"\n---'

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/test-plans/new-plan.md"},
            "session_id": "abc123",
            "cwd": "/Users/prb/project",
        }
        mock_stdin.write(json.dumps(data))
        mock_stdin.seek(0)

        with pytest.raises(SystemExit) as exc_info:
            add_plan_frontmatter.main()

        assert exc_info.value.code == 0
        mock_write.assert_called_once()
        written = mock_write.call_args[0][0]
        assert written.startswith('---\ncreated: "2025-12-02T14:30:00Z"\n---')
        assert "# My Plan" in written

    @patch("add_plan_frontmatter.PLANS_DIR", Path("/tmp/test-plans"))
    @patch("pathlib.Path.read_text")
    @patch("sys.stdin", new_callable=StringIO)
    def test_handles_read_error_gracefully(self, mock_stdin, mock_read):
        """Test graceful handling of file read errors."""
        mock_read.side_effect = IOError("Permission denied")

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/test-plans/unreadable.md"},
        }
        mock_stdin.write(json.dumps(data))
        mock_stdin.seek(0)

        with pytest.raises(SystemExit) as exc_info:
            add_plan_frontmatter.main()

        assert exc_info.value.code == 0

    @patch("add_plan_frontmatter.PLANS_DIR", Path("/tmp/test-plans"))
    @patch("add_plan_frontmatter.build_frontmatter")
    @patch("pathlib.Path.write_text")
    @patch("pathlib.Path.read_text")
    @patch("sys.stdin", new_callable=StringIO)
    def test_handles_write_error_gracefully(self, mock_stdin, mock_read, mock_write, mock_build):
        """Test graceful handling of file write errors."""
        mock_read.return_value = "# Plan"
        mock_build.return_value = "---\n---"
        mock_write.side_effect = IOError("Disk full")

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": "/tmp/test-plans/plan.md"},
        }
        mock_stdin.write(json.dumps(data))
        mock_stdin.seek(0)

        with pytest.raises(SystemExit) as exc_info:
            add_plan_frontmatter.main()

        assert exc_info.value.code == 0  # Should not crash
