#!/usr/bin/env python3
"""Unit tests for agent_presence.py hook."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import agent_presence


class TestRepoRoot:
    """Test _repo_root() function."""

    @patch("subprocess.run")
    def test_returns_git_toplevel(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="/repo/root\n")
        assert agent_presence._repo_root("/repo/root/sub") == "/repo/root"

    @patch("subprocess.run")
    def test_falls_back_to_cwd_on_git_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=128, stdout="")
        assert agent_presence._repo_root("/not/a/repo") == "/not/a/repo"

    @patch("subprocess.run")
    def test_falls_back_to_cwd_on_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired("git", 2)
        assert agent_presence._repo_root("/some/path") == "/some/path"


class TestPathWithin:
    """Test _path_within() function."""

    def test_nested_path(self, tmp_path):
        assert agent_presence._path_within(tmp_path / "sub", tmp_path)

    def test_root_itself(self, tmp_path):
        assert agent_presence._path_within(tmp_path, tmp_path)

    def test_outside_path(self, tmp_path):
        assert not agent_presence._path_within(Path("/elsewhere"), tmp_path)


class TestSanitizeLabel:
    """Test _sanitize_label() function."""

    def test_passes_through_plain_text(self):
        assert agent_presence._sanitize_label("fix auth bug") == "fix auth bug"

    def test_collapses_newlines_and_tabs(self):
        assert agent_presence._sanitize_label("a\nb\t c  d") == "a b c d"

    def test_strips_escape_characters(self):
        assert agent_presence._sanitize_label("red\x1b[31mtext") == "red [31mtext"

    def test_truncates_long_text(self):
        result = agent_presence._sanitize_label("x" * 100)
        assert len(result) == agent_presence.MAX_LABEL_CHARS
        assert result.endswith("…")

    def test_whitespace_only_becomes_empty(self):
        assert agent_presence._sanitize_label("  \n\t ") == ""


class TestSessionLabel:
    """Test _session_label() function."""

    def test_prefers_label(self):
        session = {"label": "my task", "name": "ignored", "client": "claude"}
        assert agent_presence._session_label(session) == "my task"

    def test_falls_back_to_name(self):
        session = {"label": None, "name": "session-name", "client": "claude"}
        assert agent_presence._session_label(session) == "session-name"

    def test_sanitizes_label(self):
        session = {"label": "evil\nsecond line"}
        assert agent_presence._session_label(session) == "evil second line"

    def test_falls_back_to_client_and_short_id(self):
        session = {"client": "codex", "session_id": "abcdef1234567890"}
        assert agent_presence._session_label(session) == "codex/abcdef12"

    def test_blank_label_falls_through(self):
        session = {"label": "  ", "client": "claude", "session_id": "12345678abc"}
        assert agent_presence._session_label(session) == "claude/12345678"


class TestBuildPresenceLine:
    """Test build_presence_line() function."""

    def test_empty_document(self):
        assert agent_presence.build_presence_line({}, "/repo", "own-id") == ""

    def test_solo_session_no_notes(self, tmp_path):
        document = {"sessions": [{"session_id": "own-id", "cwd": str(tmp_path)}]}
        assert agent_presence.build_presence_line(document, str(tmp_path), "own-id") == ""

    def test_counts_other_session_in_repo(self, tmp_path):
        document = {
            "sessions": [
                {"session_id": "own-id", "cwd": str(tmp_path)},
                {"session_id": "peer", "cwd": str(tmp_path), "label": "refactor"},
            ]
        }
        line = agent_presence.build_presence_line(document, str(tmp_path), "own-id")
        assert line == "agents: 1 other session in this repo (refactor)"

    def test_excludes_session_outside_repo(self, tmp_path):
        document = {"sessions": [{"session_id": "peer", "cwd": "/elsewhere"}]}
        assert agent_presence.build_presence_line(document, str(tmp_path), "own-id") == ""

    def test_counts_notes_for_repo(self, tmp_path):
        document = {"sessions": [], "notes": {str(tmp_path): [{"id": "a"}, {"id": "b"}]}}
        line = agent_presence.build_presence_line(document, str(tmp_path), "own-id")
        assert line == "agents: 2 notes pending — run agents-status"

    def test_combines_sessions_and_notes(self, tmp_path):
        document = {
            "sessions": [
                {"session_id": "p1", "cwd": str(tmp_path)},
                {"session_id": "p2", "cwd": str(tmp_path / "sub")},
            ],
            "notes": {str(tmp_path): [{"id": "a"}]},
        }
        line = agent_presence.build_presence_line(document, str(tmp_path), "own-id")
        assert line.startswith("agents: 2 other sessions in this repo (")
        assert line.endswith("; 1 note pending — run agents-status")

    def test_skips_malformed_session_entries(self, tmp_path):
        document = {"sessions": [None, "junk", {"session_id": "peer", "cwd": 42}]}
        assert agent_presence.build_presence_line(document, str(tmp_path), "own-id") == ""
