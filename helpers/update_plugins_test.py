#!/usr/bin/env python3
"""Tests for update_plugins.py"""

from __future__ import annotations

import subprocess
from datetime import timezone
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, patch


from update_plugins import (
    delete_cache,
    get_commit_sha,
    get_default_branch,
    get_iso_timestamp,
    main,
    update_installed_plugins,
    update_known_marketplaces,
    update_marketplace,
)


class TestGetIsoTimestamp:
    """Tests for get_iso_timestamp function."""

    @patch("update_plugins.datetime")
    def test_returns_utc_iso_format_with_milliseconds(self, mock_datetime):
        """Test that timestamp is in correct UTC ISO format with millisecond precision."""
        # Mock datetime to return a specific UTC time
        mock_now = Mock()
        mock_now.strftime.return_value = "2025-12-20T15:30:45."
        mock_now.microsecond = 123456  # Should convert to 123 milliseconds
        mock_datetime.now.return_value = mock_now
        mock_datetime.timezone.utc = timezone.utc

        result = get_iso_timestamp()

        assert result == "2025-12-20T15:30:45.123Z"
        mock_datetime.now.assert_called_with(timezone.utc)
        mock_now.strftime.assert_called_once_with("%Y-%m-%dT%H:%M:%S.")

    @patch("update_plugins.datetime")
    def test_handles_zero_microseconds(self, mock_datetime):
        """Test that zero microseconds converts to 000 milliseconds."""
        mock_now = Mock()
        mock_now.strftime.return_value = "2025-01-01T00:00:00."
        mock_now.microsecond = 0
        mock_datetime.now.return_value = mock_now
        mock_datetime.timezone.utc = timezone.utc

        result = get_iso_timestamp()

        assert result == "2025-01-01T00:00:00.000Z"

    @patch("update_plugins.datetime")
    def test_handles_max_microseconds(self, mock_datetime):
        """Test that maximum microseconds converts correctly."""
        mock_now = Mock()
        mock_now.strftime.return_value = "2025-12-31T23:59:59."
        mock_now.microsecond = 999999  # Should convert to 999 milliseconds
        mock_datetime.now.return_value = mock_now
        mock_datetime.timezone.utc = timezone.utc

        result = get_iso_timestamp()

        assert result == "2025-12-31T23:59:59.999Z"


class TestDeleteCache:
    """Tests for delete_cache function."""

    @patch("update_plugins.shutil.rmtree")
    def test_deletes_cache_when_exists(self, mock_rmtree):
        """Test that cache directory is removed when it exists."""
        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = True

        result = delete_cache(mock_path)

        assert result is True
        mock_path.exists.assert_called_once()
        mock_rmtree.assert_called_once_with(mock_path)

    @patch("update_plugins.shutil.rmtree")
    def test_handles_non_existent_cache(self, mock_rmtree):
        """Test that non-existent cache directory is handled gracefully."""
        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = False

        result = delete_cache(mock_path)

        assert result is True
        mock_path.exists.assert_called_once()
        mock_rmtree.assert_not_called()


class TestGetDefaultBranch:
    """Tests for get_default_branch function."""

    @patch("update_plugins.subprocess.run")
    def test_parses_symbolic_ref_successfully(self, mock_run):
        """Test successful parsing of git symbolic-ref output."""
        mock_result = Mock()
        mock_result.stdout = "refs/remotes/origin/main\n"
        mock_run.return_value = mock_result

        repo_path = Path("/fake/repo")
        result = get_default_branch(repo_path)

        assert result == "main"
        mock_run.assert_called_once_with(
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )

    @patch("update_plugins.subprocess.run")
    def test_parses_master_branch(self, mock_run):
        """Test parsing of master branch from symbolic-ref."""
        mock_result = Mock()
        mock_result.stdout = "refs/remotes/origin/master\n"
        mock_run.return_value = mock_result

        result = get_default_branch(Path("/fake/repo"))

        assert result == "master"

    @patch("update_plugins.subprocess.run")
    def test_fallback_to_main_on_symbolic_ref_error(self, mock_run):
        """Test fallback to checking main branch when symbolic-ref fails."""
        # First call raises error, second call succeeds for main branch
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, "git"),
            Mock(returncode=0),
        ]

        repo_path = Path("/fake/repo")
        result = get_default_branch(repo_path)

        assert result == "main"
        assert mock_run.call_count == 2
        assert mock_run.call_args_list[1] == call(
            ["git", "rev-parse", "--verify", "origin/main"],
            cwd=repo_path,
            capture_output=True,
            check=False,
        )

    @patch("update_plugins.subprocess.run")
    def test_fallback_to_master_when_main_not_found(self, mock_run):
        """Test fallback to master when main branch doesn't exist."""
        # First call raises error, second fails for main, third succeeds for master
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, "git"),
            Mock(returncode=1),
            Mock(returncode=0),
        ]

        result = get_default_branch(Path("/fake/repo"))

        assert result == "master"
        assert mock_run.call_count == 3

    @patch("update_plugins.subprocess.run")
    def test_returns_none_when_no_branch_found(self, mock_run):
        """Test returns None when no default branch can be determined."""
        # All attempts fail
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, "git"),
            Mock(returncode=1),
            Mock(returncode=1),
        ]

        result = get_default_branch(Path("/fake/repo"))

        assert result is None


class TestGetCommitSha:
    """Tests for get_commit_sha function."""

    @patch("update_plugins.subprocess.run")
    def test_returns_head_sha_successfully(self, mock_run):
        """Test successful retrieval of HEAD commit SHA."""
        mock_result = Mock()
        mock_result.stdout = "abc123def456\n"
        mock_run.return_value = mock_result

        repo_path = Path("/fake/repo")
        result = get_commit_sha(repo_path)

        assert result == "abc123def456"
        mock_run.assert_called_once_with(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )

    @patch("update_plugins.subprocess.run")
    def test_handles_git_error(self, mock_run):
        """Test returns None when git command fails."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        result = get_commit_sha(Path("/fake/repo"))

        assert result is None


class TestUpdateMarketplace:
    """Tests for update_marketplace function."""

    @patch("update_plugins.get_commit_sha")
    @patch("update_plugins.get_default_branch")
    @patch("update_plugins.subprocess.run")
    def test_successful_marketplace_update(self, mock_run, mock_get_branch, mock_get_sha):
        """Test successful marketplace update returns success status."""
        # Setup mocks
        mock_path = MagicMock(spec=Path)
        mock_path.name = "test-marketplace"
        mock_path.is_dir.return_value = True
        mock_path.__truediv__.return_value.exists.return_value = True

        mock_run.return_value = Mock(returncode=0)
        mock_get_branch.return_value = "main"
        mock_get_sha.return_value = "abc123def456"

        # Execute
        success, branch, sha = update_marketplace(mock_path)

        # Verify
        assert success is True
        assert branch == "main"
        assert sha == "abc123def456"
        assert mock_run.call_count == 2  # fetch and reset

    @patch("update_plugins.subprocess.run")
    def test_fails_when_directory_not_found(self, mock_run):
        """Test returns failure when marketplace directory doesn't exist."""
        mock_path = MagicMock(spec=Path)
        mock_path.name = "missing-marketplace"
        mock_path.is_dir.return_value = False

        success, branch, sha = update_marketplace(mock_path)

        assert success is False
        assert branch is None
        assert sha is None
        mock_run.assert_not_called()

    @patch("update_plugins.subprocess.run")
    def test_fails_when_not_git_repository(self, mock_run):
        """Test returns failure when directory is not a git repository."""
        mock_path = MagicMock(spec=Path)
        mock_path.name = "not-git"
        mock_path.is_dir.return_value = True
        mock_git_path = MagicMock()
        mock_git_path.exists.return_value = False
        mock_path.__truediv__.return_value = mock_git_path

        success, branch, sha = update_marketplace(mock_path)

        assert success is False
        assert branch is None
        assert sha is None
        mock_run.assert_not_called()

    @patch("update_plugins.subprocess.run")
    def test_fails_when_fetch_errors(self, mock_run):
        """Test returns failure when git fetch fails."""
        mock_path = MagicMock(spec=Path)
        mock_path.name = "fetch-fail"
        mock_path.is_dir.return_value = True
        mock_path.__truediv__.return_value.exists.return_value = True

        mock_run.return_value = Mock(returncode=1, stderr="fetch failed")

        success, branch, sha = update_marketplace(mock_path)

        assert success is False
        assert branch is None
        assert sha is None

    @patch("update_plugins.get_default_branch")
    @patch("update_plugins.subprocess.run")
    def test_fails_when_default_branch_unknown(self, mock_run, mock_get_branch):
        """Test returns failure when default branch cannot be determined."""
        mock_path = MagicMock(spec=Path)
        mock_path.name = "unknown-branch"
        mock_path.is_dir.return_value = True
        mock_path.__truediv__.return_value.exists.return_value = True

        mock_run.return_value = Mock(returncode=0)
        mock_get_branch.return_value = None

        success, branch, sha = update_marketplace(mock_path)

        assert success is False
        assert branch is None
        assert sha is None

    @patch("update_plugins.get_default_branch")
    @patch("update_plugins.subprocess.run")
    def test_fails_when_reset_errors(self, mock_run, mock_get_branch):
        """Test returns failure when git reset fails."""
        mock_path = MagicMock(spec=Path)
        mock_path.name = "reset-fail"
        mock_path.is_dir.return_value = True
        mock_path.__truediv__.return_value.exists.return_value = True

        mock_run.side_effect = [
            Mock(returncode=0),  # fetch succeeds
            Mock(returncode=1, stderr="reset failed"),  # reset fails
        ]
        mock_get_branch.return_value = "main"

        success, branch, sha = update_marketplace(mock_path)

        assert success is False
        assert branch is None
        assert sha is None

    @patch("update_plugins.get_commit_sha")
    @patch("update_plugins.get_default_branch")
    @patch("update_plugins.subprocess.run")
    def test_fails_when_commit_sha_unavailable(self, mock_run, mock_get_branch, mock_get_sha):
        """Test returns failure when commit SHA cannot be retrieved."""
        mock_path = MagicMock(spec=Path)
        mock_path.name = "sha-fail"
        mock_path.is_dir.return_value = True
        mock_path.__truediv__.return_value.exists.return_value = True

        mock_run.return_value = Mock(returncode=0)
        mock_get_branch.return_value = "main"
        mock_get_sha.return_value = None

        success, branch, sha = update_marketplace(mock_path)

        assert success is False
        assert branch is None
        assert sha is None


class TestUpdateKnownMarketplaces:
    """Tests for update_known_marketplaces function."""

    @patch("update_plugins.get_iso_timestamp")
    def test_updates_timestamps_in_json(self, mock_timestamp):
        """Test updates timestamps for marketplaces in JSON."""
        mock_timestamp.return_value = "2025-12-20T15:30:45.123Z"

        existing_data = {
            "marketplace-1": {"name": "Marketplace 1", "lastUpdated": "old-time"},
            "marketplace-2": {"name": "Marketplace 2", "lastUpdated": "old-time"},
        }

        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True

        written_data = None

        def capture_dump(data, f, **kwargs):
            nonlocal written_data
            written_data = data

        with patch("builtins.open", MagicMock()):
            with patch("json.load", return_value=existing_data.copy()):
                with patch("json.dump", side_effect=capture_dump):
                    updates = {"marketplace-1": "sha1", "marketplace-2": "sha2"}
                    result = update_known_marketplaces(mock_path, updates)

        assert result is True
        assert written_data is not None
        assert written_data["marketplace-1"]["lastUpdated"] == "2025-12-20T15:30:45.123Z"
        assert written_data["marketplace-2"]["lastUpdated"] == "2025-12-20T15:30:45.123Z"

    def test_skips_when_file_not_found(self):
        """Test returns False when JSON file doesn't exist."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = False

        result = update_known_marketplaces(mock_path, {})

        assert result is False

    @patch("update_plugins.get_iso_timestamp")
    def test_only_updates_specified_marketplaces(self, mock_timestamp):
        """Test only updates marketplaces that are in the updates dict."""
        mock_timestamp.return_value = "2025-12-20T15:30:45.123Z"

        existing_data = {
            "marketplace-1": {"lastUpdated": "old-time"},
            "marketplace-2": {"lastUpdated": "old-time"},
            "marketplace-3": {"lastUpdated": "old-time"},
        }

        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True

        written_data = None

        def capture_dump(data, f, **kwargs):
            nonlocal written_data
            written_data = data

        with patch("builtins.open", MagicMock()):
            with patch("json.load", return_value=existing_data.copy()):
                with patch("json.dump", side_effect=capture_dump):
                    updates = {"marketplace-1": "sha1"}
                    result = update_known_marketplaces(mock_path, updates)

        assert result is True
        assert written_data is not None
        assert written_data["marketplace-1"]["lastUpdated"] == "2025-12-20T15:30:45.123Z"
        assert written_data["marketplace-2"]["lastUpdated"] == "old-time"
        assert written_data["marketplace-3"]["lastUpdated"] == "old-time"


class TestUpdateInstalledPlugins:
    """Tests for update_installed_plugins function."""

    @patch("update_plugins.get_iso_timestamp")
    def test_updates_shas_and_timestamps_in_json(self, mock_timestamp):
        """Test updates commit SHAs and timestamps for installed plugins."""
        mock_timestamp.return_value = "2025-12-20T15:30:45.123Z"

        existing_data = {
            "plugins": {
                "plugin-1@marketplace-1": [{"lastUpdated": "old-time", "gitCommitSha": "old-sha"}],
                "plugin-2@marketplace-2": [{"lastUpdated": "old-time", "gitCommitSha": "old-sha"}],
            }
        }

        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True

        written_data = None

        def capture_dump(data, f, **kwargs):
            nonlocal written_data
            written_data = data

        with patch("builtins.open", MagicMock()):
            with patch("json.load", return_value=existing_data.copy()):
                with patch("json.dump", side_effect=capture_dump):
                    marketplace_updates = {
                        "marketplace-1": "new-sha-1",
                        "marketplace-2": "new-sha-2",
                    }
                    result = update_installed_plugins(mock_path, marketplace_updates)

        assert result is True
        assert written_data is not None
        assert written_data["plugins"]["plugin-1@marketplace-1"][0]["gitCommitSha"] == "new-sha-1"
        assert written_data["plugins"]["plugin-2@marketplace-2"][0]["gitCommitSha"] == "new-sha-2"

    def test_skips_when_file_not_found(self):
        """Test returns False when JSON file doesn't exist."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = False

        result = update_installed_plugins(mock_path, {})

        assert result is False

    @patch("update_plugins.get_iso_timestamp")
    def test_skips_plugins_without_at_symbol(self, mock_timestamp):
        """Test skips plugin keys that don't contain @ symbol."""
        mock_timestamp.return_value = "2025-12-20T15:30:45.123Z"

        existing_data = {
            "plugins": {
                "invalid-plugin-key": [{"lastUpdated": "old-time", "gitCommitSha": "old-sha"}],
                "valid@marketplace": [{"lastUpdated": "old-time", "gitCommitSha": "old-sha"}],
            }
        }

        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True

        written_data = None

        def capture_dump(data, f, **kwargs):
            nonlocal written_data
            written_data = data

        with patch("builtins.open", MagicMock()):
            with patch("json.load", return_value=existing_data.copy()):
                with patch("json.dump", side_effect=capture_dump):
                    marketplace_updates = {"marketplace": "new-sha"}
                    result = update_installed_plugins(mock_path, marketplace_updates)

        assert result is True
        assert written_data is not None
        # The invalid plugin key should be untouched
        assert written_data["plugins"]["invalid-plugin-key"][0]["gitCommitSha"] == "old-sha"
        # The valid plugin should be updated
        assert written_data["plugins"]["valid@marketplace"][0]["gitCommitSha"] == "new-sha"


def _make_sortable_mock(name, is_dir=True):
    """Create a mock path that can be sorted by name."""
    mock = MagicMock()
    mock.name = name
    mock.is_dir.return_value = is_dir
    mock.__lt__ = lambda self, other: self.name < other.name  # type: ignore[method-assign]
    mock.__gt__ = lambda self, other: self.name > other.name  # type: ignore[method-assign]
    mock.__eq__ = lambda self, other: self.name == other.name  # type: ignore[method-assign]
    return mock


def _create_path_mock(mock_path_class, mock_marketplaces_dir):
    """Helper to create the proper Path mock chain for Path.home() / '.claude' / 'plugins' / ..."""
    mock_plugins_dir = MagicMock()
    mock_plugins_dir.__truediv__ = MagicMock(
        side_effect=lambda x: {
            "marketplaces": mock_marketplaces_dir,
            "cache": MagicMock(),
            "known_marketplaces.json": MagicMock(),
            "installed_plugins.json": MagicMock(),
        }.get(x, MagicMock())
    )

    mock_claude_dir = MagicMock()
    mock_claude_dir.__truediv__ = MagicMock(return_value=mock_plugins_dir)

    mock_home = MagicMock()
    mock_home.__truediv__ = MagicMock(return_value=mock_claude_dir)
    mock_path_class.home.return_value = mock_home


class TestMain:
    """Tests for main orchestration function."""

    @patch("update_plugins.update_installed_plugins")
    @patch("update_plugins.update_known_marketplaces")
    @patch("update_plugins.update_marketplace")
    @patch("update_plugins.delete_cache")
    @patch("update_plugins.Path")
    def test_orchestrates_full_update_flow_successfully(
        self,
        mock_path_class,
        mock_delete_cache,
        mock_update_marketplace,
        mock_update_known,
        mock_update_installed,
    ):
        """Test main orchestrates full update flow and returns 0 on success."""
        mock_marketplaces_dir = MagicMock()
        mock_marketplaces_dir.exists.return_value = True

        mock_marketplace_1 = _make_sortable_mock("marketplace-1")
        mock_marketplace_2 = _make_sortable_mock("marketplace-2")

        mock_marketplaces_dir.iterdir.return_value = [mock_marketplace_1, mock_marketplace_2]

        _create_path_mock(mock_path_class, mock_marketplaces_dir)

        mock_delete_cache.return_value = True
        mock_update_marketplace.return_value = (True, "main", "abc123")
        mock_update_known.return_value = True
        mock_update_installed.return_value = True

        result = main()

        assert result == 0
        mock_delete_cache.assert_called_once()
        assert mock_update_marketplace.call_count == 2
        mock_update_known.assert_called_once()
        mock_update_installed.assert_called_once()

    @patch("update_plugins.delete_cache")
    @patch("update_plugins.Path")
    def test_returns_error_when_marketplaces_dir_missing(self, mock_path_class, mock_delete_cache):
        """Test main returns 1 when marketplaces directory doesn't exist."""
        mock_marketplaces_dir = MagicMock()
        mock_marketplaces_dir.exists.return_value = False

        _create_path_mock(mock_path_class, mock_marketplaces_dir)

        result = main()

        assert result == 1
        mock_delete_cache.assert_not_called()

    @patch("update_plugins.update_installed_plugins")
    @patch("update_plugins.update_known_marketplaces")
    @patch("update_plugins.update_marketplace")
    @patch("update_plugins.delete_cache")
    @patch("update_plugins.Path")
    def test_returns_error_when_some_updates_fail(
        self,
        mock_path_class,
        mock_delete_cache,
        mock_update_marketplace,
        mock_update_known,
        mock_update_installed,
    ):
        """Test main returns 1 when some marketplace updates fail."""
        mock_marketplaces_dir = MagicMock()
        mock_marketplaces_dir.exists.return_value = True

        mock_marketplace_1 = _make_sortable_mock("marketplace-1")
        mock_marketplace_2 = _make_sortable_mock("marketplace-2")

        mock_marketplaces_dir.iterdir.return_value = [mock_marketplace_1, mock_marketplace_2]

        _create_path_mock(mock_path_class, mock_marketplaces_dir)

        mock_update_marketplace.side_effect = [
            (True, "main", "abc123"),
            (False, None, None),
        ]

        result = main()

        assert result == 1

    @patch("update_plugins.update_installed_plugins")
    @patch("update_plugins.update_known_marketplaces")
    @patch("update_plugins.update_marketplace")
    @patch("update_plugins.delete_cache")
    @patch("update_plugins.Path")
    def test_skips_hidden_directories(
        self,
        mock_path_class,
        mock_delete_cache,
        mock_update_marketplace,
        mock_update_known,
        mock_update_installed,
    ):
        """Test main skips directories starting with dot."""
        mock_marketplaces_dir = MagicMock()
        mock_marketplaces_dir.exists.return_value = True

        mock_hidden = _make_sortable_mock(".hidden")
        mock_regular = _make_sortable_mock("marketplace-1")

        mock_marketplaces_dir.iterdir.return_value = [mock_hidden, mock_regular]

        _create_path_mock(mock_path_class, mock_marketplaces_dir)

        mock_update_marketplace.return_value = (True, "main", "abc123")

        result = main()

        assert mock_update_marketplace.call_count == 1
        assert result == 0

    @patch("update_plugins.update_installed_plugins")
    @patch("update_plugins.update_known_marketplaces")
    @patch("update_plugins.update_marketplace")
    @patch("update_plugins.delete_cache")
    @patch("update_plugins.Path")
    def test_skips_non_directory_items(
        self,
        mock_path_class,
        mock_delete_cache,
        mock_update_marketplace,
        mock_update_known,
        mock_update_installed,
    ):
        """Test main skips non-directory items in marketplaces folder."""
        mock_marketplaces_dir = MagicMock()
        mock_marketplaces_dir.exists.return_value = True

        mock_file = _make_sortable_mock("some-file.txt", is_dir=False)
        mock_dir = _make_sortable_mock("marketplace-1")

        mock_marketplaces_dir.iterdir.return_value = [mock_file, mock_dir]

        _create_path_mock(mock_path_class, mock_marketplaces_dir)

        mock_update_marketplace.return_value = (True, "main", "abc123")

        result = main()

        assert mock_update_marketplace.call_count == 1
        assert result == 0
