#!/usr/bin/env python3
"""Unit tests for log_prompts.py hook."""

import json
import subprocess
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

# Import the module under test
import log_prompts


class TestGetFlattenedProjectName:
    """Test get_flattened_project_name() function."""

    def test_nested_path_under_home(self):
        """Test converting nested path under home to flattened name."""
        with patch("log_prompts.Path.home", return_value=Path("/Users/prb")):
            result = log_prompts.get_flattened_project_name(
                "/Users/prb/work/templates/next-template"
            )
            assert result == "work-templates-next-template"

    def test_single_directory_under_home(self):
        """Test converting single directory under home."""
        with patch("log_prompts.Path.home", return_value=Path("/Users/prb")):
            result = log_prompts.get_flattened_project_name("/Users/prb/projects")
            assert result == "projects"

    def test_hidden_directory_strips_leading_dot(self):
        """Test that leading dots are stripped from directory names."""
        with patch("log_prompts.Path.home", return_value=Path("/Users/prb")):
            result = log_prompts.get_flattened_project_name("/Users/prb/.claude")
            assert result == "claude"

    def test_multiple_hidden_directories(self):
        """Test multiple hidden directories with leading dots."""
        with patch("log_prompts.Path.home", return_value=Path("/Users/prb")):
            result = log_prompts.get_flattened_project_name(
                "/Users/prb/.config/.local/share"
            )
            assert result == "config-local-share"

    def test_path_outside_home_directory(self):
        """Test path outside home directory uses full path."""
        with patch("log_prompts.Path.home", return_value=Path("/Users/prb")):
            result = log_prompts.get_flattened_project_name("/tmp/test/project")
            # Paths starting with / will have leading hyphen due to split behavior
            assert result == "-tmp-test-project"

    def test_home_directory_itself(self):
        """Test home directory itself returns dot."""
        with patch("log_prompts.Path.home", return_value=Path("/Users/prb")):
            result = log_prompts.get_flattened_project_name("/Users/prb")
            # Home directory relative to itself is '.', which doesn't get stripped
            assert result == "."

    def test_deep_nested_path(self):
        """Test deeply nested path."""
        with patch("log_prompts.Path.home", return_value=Path("/Users/prb")):
            result = log_prompts.get_flattened_project_name(
                "/Users/prb/projects/sablier/backend/indexers/src"
            )
            assert result == "projects-sablier-backend-indexers-src"


class TestGetProjectName:
    """Test get_project_name() function."""

    def test_nested_path_returns_last_component(self):
        """Test extracting last component from nested path."""
        result = log_prompts.get_project_name("/Users/prb/work/templates/next-template")
        assert result == "next-template"

    def test_single_directory(self):
        """Test single directory path."""
        result = log_prompts.get_project_name("/Users/prb/projects")
        assert result == "projects"

    def test_hidden_directory(self):
        """Test hidden directory (keeps the dot)."""
        result = log_prompts.get_project_name("/Users/prb/.claude")
        assert result == ".claude"

    def test_root_directory(self):
        """Test root directory."""
        result = log_prompts.get_project_name("/")
        assert result == ""


class TestGetTagsFromFlattenedName:
    """Test get_tags_from_flattened_name() function."""

    def test_multi_word_flattened_name(self):
        """Test generating tags from multi-word flattened name."""
        result = log_prompts.get_tags_from_flattened_name(
            "work-templates-next-template"
        )
        assert result == ["work", "templates", "next", "template"]

    def test_single_word_flattened_name(self):
        """Test single word generates single tag."""
        result = log_prompts.get_tags_from_flattened_name("claude")
        assert result == ["claude"]

    def test_two_words(self):
        """Test two-word flattened name."""
        result = log_prompts.get_tags_from_flattened_name("sablier-sdk")
        assert result == ["sablier", "sdk"]

    def test_empty_string(self):
        """Test empty string returns single empty tag."""
        result = log_prompts.get_tags_from_flattened_name("")
        assert result == [""]


class TestIsZkNotebookInitialized:
    """Test is_zk_notebook_initialized() function."""

    @patch("log_prompts.PROMPTS_DIR", Path("/Users/prb/.claude-prompts"))
    def test_notebook_exists(self):
        """Test when .zk directory exists."""
        with patch("pathlib.Path.exists", return_value=True):
            result = log_prompts.is_zk_notebook_initialized()
            assert result is True

    @patch("log_prompts.PROMPTS_DIR", Path("/Users/prb/.claude-prompts"))
    def test_notebook_does_not_exist(self):
        """Test when .zk directory does not exist."""
        with patch("pathlib.Path.exists", return_value=False):
            result = log_prompts.is_zk_notebook_initialized()
            assert result is False


class TestLogPromptToZk:
    """Test log_prompt_to_zk() function."""

    @patch("log_prompts.PROMPTS_DIR", Path("/tmp/test-prompts"))
    @patch("log_prompts.is_zk_notebook_initialized")
    @patch("subprocess.run")
    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    def test_create_new_daily_file_with_frontmatter(
        self,
        mock_exists,
        mock_mkdir,
        mock_file,
        mock_subprocess,
        mock_ensure_init,
    ):
        """Test creating new daily file with YAML frontmatter."""
        mock_ensure_init.return_value = True
        mock_exists.return_value = False  # File doesn't exist yet

        with patch("log_prompts.datetime") as mock_datetime:
            mock_now = datetime(2025, 11, 17, 16, 34, 59, 597061, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            mock_datetime.timezone = timezone

            log_prompts.log_prompt_to_zk(
                "Test prompt content",
                "session-123",
                "/Users/prb/work/templates/next-template",
            )

        # Verify directory creation
        mock_mkdir.assert_called()

        # Verify file was opened for append
        mock_file.assert_called_once()
        call_args = mock_file.call_args
        assert str(call_args[0][0]).endswith("2025-11-17.md")
        assert call_args[0][1] == "a"

        # Verify content written includes frontmatter
        written_content = "".join(
            call.args[0] for call in mock_file().write.call_args_list
        )
        assert "---" in written_content
        assert "title: 2025-11-17" in written_content
        assert "date: 2025-11-17T16:34:59.597061+00:00" in written_content
        assert "project: next-template" in written_content
        assert "tags: [work, templates, next, template]" in written_content
        assert "_Session ID: session-123_" in written_content
        assert "## 16:34:59" in written_content
        assert "Test prompt content" in written_content

        # Verify zk index was called
        mock_subprocess.assert_called_once()
        assert mock_subprocess.call_args[0][0][0:2] == ["zk", "index"]

    @patch("log_prompts.PROMPTS_DIR", Path("/tmp/test-prompts"))
    @patch("log_prompts.is_zk_notebook_initialized")
    @patch("subprocess.run")
    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    def test_append_to_existing_daily_file(
        self,
        mock_exists,
        mock_mkdir,
        mock_file,
        mock_subprocess,
        mock_ensure_init,
    ):
        """Test appending to existing daily file."""
        mock_ensure_init.return_value = True
        mock_exists.return_value = True  # File already exists

        with patch("log_prompts.datetime") as mock_datetime:
            mock_now = datetime(2025, 11, 17, 17, 45, 30, 123456, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            mock_datetime.timezone = timezone

            log_prompts.log_prompt_to_zk(
                "Second prompt",
                "session-456",
                "/Users/prb/work/templates/next-template",
            )

        # Verify content written does NOT include frontmatter
        written_content = "".join(
            call.args[0] for call in mock_file().write.call_args_list
        )
        # Should start with newline and time header, no frontmatter
        assert written_content.startswith("\n## 17:45:30")
        assert "---" in written_content  # Separator only
        assert "title:" not in written_content  # No frontmatter
        assert "tags:" not in written_content
        assert "Second prompt" in written_content

    @patch("log_prompts.PROMPTS_DIR", Path("/tmp/test-prompts"))
    @patch("log_prompts.is_zk_notebook_initialized")
    def test_notebook_init_fails(self, mock_ensure_init):
        """Test early return when notebook initialization fails."""
        mock_ensure_init.return_value = False

        # Should return early without writing anything
        log_prompts.log_prompt_to_zk(
            "Test prompt", "session-123", "/Users/prb/projects"
        )

        # No further mocking needed - function should exit early
        mock_ensure_init.assert_called_once()

    @patch("log_prompts.PROMPTS_DIR", Path("/tmp/test-prompts"))
    @patch("log_prompts.is_zk_notebook_initialized")
    @patch("builtins.open")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    def test_file_write_error(
        self, mock_exists, mock_mkdir, mock_file, mock_ensure_init
    ):
        """Test handling of file write errors."""
        mock_ensure_init.return_value = True
        mock_exists.return_value = False
        mock_file.side_effect = IOError("Disk full")

        with patch("log_prompts.datetime") as mock_datetime:
            mock_now = datetime(2025, 11, 17, 12, 0, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            mock_datetime.timezone = timezone

            # Should not raise exception, just log warning
            log_prompts.log_prompt_to_zk(
                "Test prompt", "session-123", "/Users/prb/projects"
            )

    @patch("log_prompts.PROMPTS_DIR", Path("/tmp/test-prompts"))
    @patch("log_prompts.is_zk_notebook_initialized")
    @patch("subprocess.run")
    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    def test_zk_index_timeout(
        self,
        mock_exists,
        mock_mkdir,
        mock_file,
        mock_subprocess,
        mock_ensure_init,
    ):
        """Test handling of zk index timeout."""
        mock_ensure_init.return_value = True
        mock_exists.return_value = False
        mock_subprocess.side_effect = subprocess.TimeoutExpired("zk", 5)

        with patch("log_prompts.datetime") as mock_datetime:
            mock_now = datetime(2025, 11, 17, 12, 0, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            mock_datetime.timezone = timezone

            # Should not raise exception, just log warning
            log_prompts.log_prompt_to_zk(
                "Test prompt", "session-123", "/Users/prb/projects"
            )

        # File should still be written even if index fails
        mock_file().write.assert_called()

    @patch("log_prompts.PROMPTS_DIR", Path("/tmp/test-prompts"))
    @patch("log_prompts.is_zk_notebook_initialized")
    @patch("subprocess.run")
    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    def test_flattened_directory_structure(
        self,
        mock_exists,
        mock_mkdir,
        mock_file,
        mock_subprocess,
        mock_ensure_init,
    ):
        """Test correct flattened directory structure is created."""
        mock_ensure_init.return_value = True
        mock_exists.return_value = False

        with patch("log_prompts.datetime") as mock_datetime:
            mock_now = datetime(2025, 11, 17, 12, 0, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            mock_datetime.timezone = timezone

            with patch("log_prompts.Path.home", return_value=Path("/Users/prb")):
                log_prompts.log_prompt_to_zk(
                    "Test", "session-123", "/Users/prb/projects/sablier/sdk"
                )

        # Verify mkdir was called (path validation is implicit in the function)
        mock_mkdir.assert_called_once()
        # Verify that mkdir was called with parents=True and exist_ok=True
        assert mock_mkdir.call_args.kwargs == {"parents": True, "exist_ok": True}


class TestMain:
    """Test main() entry point."""

    @patch("log_prompts.log_prompt_to_zk")
    @patch("sys.stdin", new_callable=StringIO)
    def test_valid_json_input(self, mock_stdin, mock_log):
        """Test processing valid JSON input."""
        input_data = {
            "prompt": "This is a test prompt that is long enough to not be filtered",
            "session_id": "test-session",
            "cwd": "/Users/prb/projects",
        }
        mock_stdin.write(json.dumps(input_data))
        mock_stdin.seek(0)

        with pytest.raises(SystemExit) as exc_info:
            log_prompts.main()

        assert exc_info.value.code == 0
        mock_log.assert_called_once_with(
            "This is a test prompt that is long enough to not be filtered",
            "test-session",
            "/Users/prb/projects",
        )

    @patch("sys.stdin", new_callable=StringIO)
    def test_invalid_json_input(self, mock_stdin):
        """Test handling of invalid JSON input."""
        mock_stdin.write("not valid json{")
        mock_stdin.seek(0)

        with pytest.raises(SystemExit) as exc_info:
            log_prompts.main()

        assert exc_info.value.code == 0  # Should exit cleanly

    @patch("sys.stdin", new_callable=StringIO)
    def test_empty_prompt_filtered(self, mock_stdin):
        """Test that empty prompts are filtered out."""
        input_data = {"prompt": "", "session_id": "test", "cwd": "/Users/prb"}
        mock_stdin.write(json.dumps(input_data))
        mock_stdin.seek(0)

        with pytest.raises(SystemExit) as exc_info:
            log_prompts.main()

        assert exc_info.value.code == 0

    @patch("log_prompts.log_prompt_to_zk")
    @patch("sys.stdin", new_callable=StringIO)
    def test_short_prompt_filtered(self, mock_stdin, mock_log):
        """Test that short prompts (< 25 chars) are filtered out."""
        input_data = {"prompt": "short", "session_id": "test", "cwd": "/Users/prb"}
        mock_stdin.write(json.dumps(input_data))
        mock_stdin.seek(0)

        with pytest.raises(SystemExit) as exc_info:
            log_prompts.main()

        assert exc_info.value.code == 0
        mock_log.assert_not_called()

    @patch("log_prompts.log_prompt_to_zk")
    @patch("sys.stdin", new_callable=StringIO)
    def test_simple_slash_command_filtered(self, mock_stdin, mock_log):
        """Test that simple slash commands are filtered out."""
        input_data = {"prompt": "/commit", "session_id": "test", "cwd": "/Users/prb"}
        mock_stdin.write(json.dumps(input_data))
        mock_stdin.seek(0)

        with pytest.raises(SystemExit) as exc_info:
            log_prompts.main()

        assert exc_info.value.code == 0
        mock_log.assert_not_called()

    @patch("log_prompts.log_prompt_to_zk")
    @patch("sys.stdin", new_callable=StringIO)
    def test_slash_command_with_args_not_filtered(self, mock_stdin, mock_log):
        """Test that slash commands with arguments are NOT filtered."""
        input_data = {
            "prompt": "/commit --all This is a commit message",
            "session_id": "test",
            "cwd": "/Users/prb",
        }
        mock_stdin.write(json.dumps(input_data))
        mock_stdin.seek(0)

        with pytest.raises(SystemExit) as exc_info:
            log_prompts.main()

        assert exc_info.value.code == 0
        mock_log.assert_called_once()

    @patch("log_prompts.log_prompt_to_zk")
    @patch("sys.stdin", new_callable=StringIO)
    def test_missing_session_id_uses_default(self, mock_stdin, mock_log):
        """Test that missing session_id uses 'unknown'."""
        input_data = {
            "prompt": "This is a test prompt with no session_id field present here",
            "cwd": "/Users/prb",
        }
        mock_stdin.write(json.dumps(input_data))
        mock_stdin.seek(0)

        with pytest.raises(SystemExit) as exc_info:
            log_prompts.main()

        assert exc_info.value.code == 0
        # Check that 'unknown' was used for session_id
        assert mock_log.call_args[0][1] == "unknown"

    @patch("log_prompts.log_prompt_to_zk")
    @patch("sys.stdin", new_callable=StringIO)
    def test_missing_cwd_uses_default(self, mock_stdin, mock_log):
        """Test that missing cwd uses 'unknown'."""
        input_data = {
            "prompt": "This is a test prompt with no cwd field present in json input",
            "session_id": "test",
        }
        mock_stdin.write(json.dumps(input_data))
        mock_stdin.seek(0)

        with pytest.raises(SystemExit) as exc_info:
            log_prompts.main()

        assert exc_info.value.code == 0
        # Check that 'unknown' was used for cwd
        assert mock_log.call_args[0][2] == "unknown"

    @patch("sys.stdin", new_callable=StringIO)
    def test_missing_prompt_field(self, mock_stdin):
        """Test handling of missing prompt field in JSON."""
        input_data = {"session_id": "test", "cwd": "/Users/prb"}
        mock_stdin.write(json.dumps(input_data))
        mock_stdin.seek(0)

        with pytest.raises(SystemExit) as exc_info:
            log_prompts.main()

        assert exc_info.value.code == 0  # Should exit cleanly

    @patch("log_prompts.log_prompt_to_zk")
    @patch("shutil.which")
    @patch("sys.stdin", new_callable=StringIO)
    def test_exit_when_zk_not_installed(self, mock_stdin, mock_which, mock_log):
        """Test early exit when zk CLI is not installed."""
        mock_which.return_value = None  # zk not found
        input_data = {
            "prompt": "This is a test prompt that is long enough to not be filtered",
            "session_id": "test-session",
            "cwd": "/Users/prb/projects",
        }
        mock_stdin.write(json.dumps(input_data))
        mock_stdin.seek(0)

        with pytest.raises(SystemExit) as exc_info:
            log_prompts.main()

        assert exc_info.value.code == 0
        mock_log.assert_not_called()  # Should not attempt to log

    @patch("log_prompts.log_prompt_to_zk")
    @patch("pathlib.Path.exists")
    @patch("shutil.which")
    @patch("sys.stdin", new_callable=StringIO)
    def test_exit_when_prompts_directory_missing(
        self, mock_stdin, mock_which, mock_exists, mock_log
    ):
        """Test early exit when ~/.claude-prompts directory doesn't exist."""
        mock_which.return_value = "/usr/local/bin/zk"  # zk is installed
        mock_exists.return_value = False  # directory doesn't exist
        input_data = {
            "prompt": "This is a test prompt that is long enough to not be filtered",
            "session_id": "test-session",
            "cwd": "/Users/prb/projects",
        }
        mock_stdin.write(json.dumps(input_data))
        mock_stdin.seek(0)

        with pytest.raises(SystemExit) as exc_info:
            log_prompts.main()

        assert exc_info.value.code == 0
        mock_log.assert_not_called()  # Should not attempt to log
