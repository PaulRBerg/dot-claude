#!/usr/bin/env python3
"""Tests for cleanup.py"""

import json
from unittest.mock import MagicMock, patch


import cleanup


class TestCleanClaudeJson:
    """Test cases for clean_claude_json function."""

    @patch("cleanup.Path")
    @patch("cleanup.datetime")
    def test_creates_timestamped_backup_before_modification(self, mock_datetime, mock_path_class):
        """Test that a timestamped backup is created before modifying the file."""
        mock_datetime.now.return_value.strftime.return_value = "20231225_143000"

        mock_claude_json = MagicMock()
        mock_claude_json.exists.return_value = True
        mock_claude_json.stat.return_value.st_size = 100 * 1024 * 1024  # 100 MB

        mock_backup_path = MagicMock()
        mock_claude_json.with_suffix.return_value = mock_backup_path

        mock_home = MagicMock()
        mock_home.__truediv__ = MagicMock(return_value=mock_claude_json)
        mock_path_class.home.return_value = mock_home

        mock_data = {
            "projects": {"proj1": {"history": [{"msg": "test"}], "settings": {"foo": "bar"}}}
        }

        # Track file operations
        file_reads = []
        file_writes = []

        def mock_open_fn(path, mode="r"):
            m = MagicMock()
            if mode == "r":
                m.__enter__ = MagicMock(return_value=m)
                m.__exit__ = MagicMock(return_value=False)
                m.read.return_value = json.dumps(mock_data)
                file_reads.append(path)

                class MockJsonLoad:
                    pass

                m_file = MagicMock()
                m_file.__enter__ = MagicMock(return_value=m_file)
                m_file.__exit__ = MagicMock(return_value=False)
                return m_file
            else:
                m.__enter__ = MagicMock(return_value=m)
                m.__exit__ = MagicMock(return_value=False)
                file_writes.append(path)
                return m

        with patch("builtins.open", side_effect=mock_open_fn):
            with patch("json.load", return_value=mock_data):
                result = cleanup.clean_claude_json()

        assert result == 0
        mock_claude_json.with_suffix.assert_called_once_with(".json.backup.20231225_143000")

    @patch("cleanup.Path")
    @patch("cleanup.datetime")
    def test_clears_history_arrays_from_all_projects(self, mock_datetime, mock_path_class):
        """Test that history arrays are cleared from all projects."""
        mock_datetime.now.return_value.strftime.return_value = "20231225_143000"

        mock_claude_json = MagicMock()
        mock_claude_json.exists.return_value = True
        mock_claude_json.stat.return_value.st_size = 100 * 1024 * 1024

        mock_backup_path = MagicMock()
        mock_claude_json.with_suffix.return_value = mock_backup_path

        mock_home = MagicMock()
        mock_home.__truediv__ = MagicMock(return_value=mock_claude_json)
        mock_path_class.home.return_value = mock_home

        mock_data = {
            "projects": {
                "proj1": {
                    "history": [{"msg": "test1"}, {"msg": "test2"}],
                    "settings": {"foo": "bar"},
                },
                "proj2": {"history": [{"msg": "test3"}], "name": "Project 2"},
                "proj3": {"name": "No history project"},
            }
        }

        cleaned_data = None

        def capture_dump(data, f, **kwargs):
            nonlocal cleaned_data
            cleaned_data = data

        with patch("builtins.open", MagicMock()):
            with patch("json.load", return_value=mock_data.copy()):
                with patch("json.dump", side_effect=capture_dump):
                    result = cleanup.clean_claude_json()

        assert result == 0
        # Last dump call is the cleaned file
        assert cleaned_data is not None
        assert cleaned_data["projects"]["proj1"]["history"] == []
        assert cleaned_data["projects"]["proj2"]["history"] == []

    @patch("cleanup.Path")
    @patch("cleanup.datetime")
    def test_preserves_non_history_project_data(self, mock_datetime, mock_path_class):
        """Test that non-history project data is preserved."""
        mock_datetime.now.return_value.strftime.return_value = "20231225_143000"

        mock_claude_json = MagicMock()
        mock_claude_json.exists.return_value = True
        mock_claude_json.stat.return_value.st_size = 100 * 1024 * 1024

        mock_backup_path = MagicMock()
        mock_claude_json.with_suffix.return_value = mock_backup_path

        mock_home = MagicMock()
        mock_home.__truediv__ = MagicMock(return_value=mock_claude_json)
        mock_path_class.home.return_value = mock_home

        mock_data = {
            "globalSettings": {"theme": "dark"},
            "projects": {
                "proj1": {
                    "history": [{"msg": "test"}],
                    "settings": {"foo": "bar"},
                    "name": "Test Project",
                    "lastAccessed": "2023-12-25",
                }
            },
            "recentProjects": ["proj1"],
        }

        cleaned_data = None

        def capture_dump(data, f, **kwargs):
            nonlocal cleaned_data
            cleaned_data = data

        with patch("builtins.open", MagicMock()):
            with patch("json.load", return_value=mock_data.copy()):
                with patch("json.dump", side_effect=capture_dump):
                    result = cleanup.clean_claude_json()

        assert result == 0
        assert cleaned_data is not None
        assert cleaned_data["globalSettings"] == {"theme": "dark"}
        assert cleaned_data["projects"]["proj1"]["settings"] == {"foo": "bar"}
        assert cleaned_data["projects"]["proj1"]["name"] == "Test Project"
        assert cleaned_data["projects"]["proj1"]["lastAccessed"] == "2023-12-25"
        assert cleaned_data["recentProjects"] == ["proj1"]

    @patch("cleanup.Path")
    @patch("cleanup.datetime")
    def test_reports_size_reduction_correctly(self, mock_datetime, mock_path_class, capsys):
        """Test that size reduction is calculated and reported correctly."""
        mock_datetime.now.return_value.strftime.return_value = "20231225_143000"

        mock_claude_json = MagicMock()
        mock_claude_json.exists.return_value = True

        original_size = 100 * 1024 * 1024  # 100 MB
        new_size = 50 * 1024  # 50 KB

        mock_claude_json.stat.side_effect = [
            MagicMock(st_size=original_size),
            MagicMock(st_size=new_size),
        ]

        mock_backup_path = MagicMock()
        mock_claude_json.with_suffix.return_value = mock_backup_path

        mock_home = MagicMock()
        mock_home.__truediv__ = MagicMock(return_value=mock_claude_json)
        mock_path_class.home.return_value = mock_home

        mock_data = {"projects": {"proj1": {"history": [{"msg": "test"}]}}}

        with patch("builtins.open", MagicMock()):
            with patch("json.load", return_value=mock_data):
                with patch("json.dump"):
                    result = cleanup.clean_claude_json()

        captured = capsys.readouterr()
        expected_reduction = ((original_size - new_size) / original_size) * 100

        assert result == 0
        assert f"Original file size: {original_size / 1024 / 1024:.2f} MB" in captured.out
        assert f"New size: {new_size / 1024:.2f} KB" in captured.out
        assert f"Reduced by: {expected_reduction:.1f}%" in captured.out

    @patch("cleanup.Path")
    def test_handles_missing_file(self, mock_path_class, capsys):
        """Test that the function handles missing ~/.claude.json file."""
        mock_claude_json = MagicMock()
        mock_claude_json.exists.return_value = False

        mock_home = MagicMock()
        mock_home.__truediv__ = MagicMock(return_value=mock_claude_json)
        mock_path_class.home.return_value = mock_home

        result = cleanup.clean_claude_json()

        captured = capsys.readouterr()
        assert result == 1
        assert "~/.claude.json not found" in captured.out


class TestMain:
    """Test cases for main function."""

    @patch("cleanup.clean_claude_json")
    @patch("cleanup.Path")
    def test_skips_small_files_less_than_1mb(self, mock_path_class, mock_clean, capsys):
        """Test that files smaller than 1MB prompt for confirmation."""
        mock_claude_json = MagicMock()
        mock_claude_json.exists.return_value = True
        mock_claude_json.stat.return_value.st_size = 500 * 1024  # 0.5 MB

        mock_home = MagicMock()
        mock_home.__truediv__ = MagicMock(return_value=mock_claude_json)
        mock_path_class.home.return_value = mock_home

        with patch("builtins.input", return_value="n") as mock_input:
            result = cleanup.main()

        captured = capsys.readouterr()
        assert result == 0
        assert "File is already small" in captured.out
        # input() is called with the prompt, check it was called with "Clean anyway?"
        mock_input.assert_called_once()
        assert "Clean anyway?" in mock_input.call_args[0][0]
        mock_clean.assert_not_called()

    @patch("cleanup.clean_claude_json")
    @patch("cleanup.Path")
    def test_handles_y_confirmation(self, mock_path_class, mock_clean):
        """Test that 'y' confirmation proceeds with cleaning."""
        mock_claude_json = MagicMock()
        mock_claude_json.exists.return_value = True
        mock_claude_json.stat.return_value.st_size = 500 * 1024  # 0.5 MB

        mock_home = MagicMock()
        mock_home.__truediv__ = MagicMock(return_value=mock_claude_json)
        mock_path_class.home.return_value = mock_home
        mock_clean.return_value = 0

        with patch("builtins.input", return_value="y"):
            result = cleanup.main()

        mock_clean.assert_called_once()
        assert result == 0

    @patch("cleanup.clean_claude_json")
    @patch("cleanup.Path")
    def test_handles_n_confirmation(self, mock_path_class, mock_clean):
        """Test that 'n' confirmation skips cleaning."""
        mock_claude_json = MagicMock()
        mock_claude_json.exists.return_value = True
        mock_claude_json.stat.return_value.st_size = 500 * 1024  # 0.5 MB

        mock_home = MagicMock()
        mock_home.__truediv__ = MagicMock(return_value=mock_claude_json)
        mock_path_class.home.return_value = mock_home

        with patch("builtins.input", return_value="n"):
            result = cleanup.main()

        mock_clean.assert_not_called()
        assert result == 0

    @patch("cleanup.clean_claude_json")
    @patch("cleanup.Path")
    def test_handles_missing_claude_json(self, mock_path_class, mock_clean):
        """Test that missing ~/.claude.json is handled gracefully."""
        mock_claude_json = MagicMock()
        mock_claude_json.exists.return_value = False

        mock_home = MagicMock()
        mock_home.__truediv__ = MagicMock(return_value=mock_claude_json)
        mock_path_class.home.return_value = mock_home
        mock_clean.return_value = 1

        result = cleanup.main()

        mock_clean.assert_called_once()
        assert result == 1

    @patch("cleanup.clean_claude_json")
    @patch("cleanup.Path")
    def test_proceeds_for_large_files(self, mock_path_class, mock_clean):
        """Test that large files (>1MB) proceed without confirmation."""
        mock_claude_json = MagicMock()
        mock_claude_json.exists.return_value = True
        mock_claude_json.stat.return_value.st_size = 10 * 1024 * 1024  # 10 MB

        mock_home = MagicMock()
        mock_home.__truediv__ = MagicMock(return_value=mock_claude_json)
        mock_path_class.home.return_value = mock_home
        mock_clean.return_value = 0

        result = cleanup.main()

        mock_clean.assert_called_once()
        assert result == 0
