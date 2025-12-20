#!/usr/bin/env python3
"""Tests for allow_all_bash.py"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch


from allow_all_bash import main


class TestMain:
    """Test cases for the main() function."""

    @patch("allow_all_bash.Path")
    def test_creates_directory_when_missing(self, mock_path_cls):
        """Creates .claude/ directory and file when missing."""
        mock_cwd = MagicMock(spec=Path)
        mock_path_cls.cwd.return_value = mock_cwd

        mock_settings_path = MagicMock(spec=Path)
        mock_settings_path.exists.return_value = False
        mock_parent = MagicMock()
        mock_settings_path.parent = mock_parent

        mock_cwd.__truediv__.return_value = mock_settings_path

        result = main()

        assert result == 0
        mock_parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_settings_path.write_text.assert_called_once()

        written_content = mock_settings_path.write_text.call_args[0][0]
        expected = json.dumps({"permissions": {"allow": ["Bash"]}}, indent=2) + "\n"
        assert written_content == expected

    @patch("allow_all_bash.Path")
    def test_creates_new_file_with_bash_permission(self, mock_path_cls):
        """Creates new settings.local.json with Bash permission."""
        mock_cwd = MagicMock(spec=Path)
        mock_path_cls.cwd.return_value = mock_cwd

        mock_settings_path = MagicMock(spec=Path)
        mock_settings_path.exists.return_value = False
        mock_settings_path.parent = MagicMock()

        mock_cwd.__truediv__.return_value = mock_settings_path

        result = main()

        assert result == 0
        written_content = mock_settings_path.write_text.call_args[0][0]
        data = json.loads(written_content.strip())

        assert "permissions" in data
        assert "allow" in data["permissions"]
        assert "Bash" in data["permissions"]["allow"]

    @patch("allow_all_bash.Path")
    def test_appends_bash_to_existing_permissions(self, mock_path_cls):
        """Appends Bash to existing permissions array."""
        mock_cwd = MagicMock(spec=Path)
        mock_path_cls.cwd.return_value = mock_cwd

        existing_data = {"permissions": {"allow": ["Read", "Write"]}}

        mock_settings_path = MagicMock(spec=Path)
        mock_settings_path.exists.return_value = True
        mock_settings_path.read_text.return_value = json.dumps(existing_data)

        mock_cwd.__truediv__.return_value = mock_settings_path

        result = main()

        assert result == 0
        written_content = mock_settings_path.write_text.call_args[0][0]
        data = json.loads(written_content.strip())

        assert data["permissions"]["allow"] == ["Read", "Write", "Bash"]

    @patch("allow_all_bash.Path")
    def test_skips_if_bash_already_present(self, mock_path_cls):
        """Skips if Bash already present (idempotent)."""
        mock_cwd = MagicMock(spec=Path)
        mock_path_cls.cwd.return_value = mock_cwd

        existing_data = {"permissions": {"allow": ["Bash", "Read"]}}

        mock_settings_path = MagicMock(spec=Path)
        mock_settings_path.exists.return_value = True
        mock_settings_path.read_text.return_value = json.dumps(existing_data)

        mock_cwd.__truediv__.return_value = mock_settings_path

        result = main()

        assert result == 0
        mock_settings_path.write_text.assert_not_called()

    @patch("allow_all_bash.Path")
    def test_handles_malformed_json(self, mock_path_cls):
        """Handles malformed JSON gracefully (returns 1)."""
        mock_cwd = MagicMock(spec=Path)
        mock_path_cls.cwd.return_value = mock_cwd

        mock_settings_path = MagicMock(spec=Path)
        mock_settings_path.exists.return_value = True
        mock_settings_path.read_text.return_value = "{ invalid json "

        mock_cwd.__truediv__.return_value = mock_settings_path

        result = main()

        assert result == 1
        mock_settings_path.write_text.assert_not_called()

    @patch("allow_all_bash.Path")
    def test_handles_empty_permissions_object(self, mock_path_cls):
        """Handles empty permissions object."""
        mock_cwd = MagicMock(spec=Path)
        mock_path_cls.cwd.return_value = mock_cwd

        existing_data = {"permissions": {}}

        mock_settings_path = MagicMock(spec=Path)
        mock_settings_path.exists.return_value = True
        mock_settings_path.read_text.return_value = json.dumps(existing_data)

        mock_cwd.__truediv__.return_value = mock_settings_path

        result = main()

        assert result == 0
        written_content = mock_settings_path.write_text.call_args[0][0]
        data = json.loads(written_content.strip())

        assert data["permissions"]["allow"] == ["Bash"]

    @patch("allow_all_bash.Path")
    def test_handles_empty_allow_array(self, mock_path_cls):
        """Handles empty allow array."""
        mock_cwd = MagicMock(spec=Path)
        mock_path_cls.cwd.return_value = mock_cwd

        existing_data = {"permissions": {"allow": []}}

        mock_settings_path = MagicMock(spec=Path)
        mock_settings_path.exists.return_value = True
        mock_settings_path.read_text.return_value = json.dumps(existing_data)

        mock_cwd.__truediv__.return_value = mock_settings_path

        result = main()

        assert result == 0
        written_content = mock_settings_path.write_text.call_args[0][0]
        data = json.loads(written_content.strip())

        assert data["permissions"]["allow"] == ["Bash"]

    @patch("allow_all_bash.Path")
    def test_handles_missing_permissions_key(self, mock_path_cls):
        """Handles missing permissions key in existing file."""
        mock_cwd = MagicMock(spec=Path)
        mock_path_cls.cwd.return_value = mock_cwd

        existing_data = {"someOtherKey": "value"}

        mock_settings_path = MagicMock(spec=Path)
        mock_settings_path.exists.return_value = True
        mock_settings_path.read_text.return_value = json.dumps(existing_data)

        mock_cwd.__truediv__.return_value = mock_settings_path

        result = main()

        assert result == 0
        written_content = mock_settings_path.write_text.call_args[0][0]
        data = json.loads(written_content.strip())

        assert "permissions" in data
        assert data["permissions"]["allow"] == ["Bash"]
        assert data["someOtherKey"] == "value"
