#!/usr/bin/env python3
"""Unit tests for guard_rm.py hook."""

import json
from io import StringIO
from pathlib import Path

import pytest

import guard_rm


@pytest.fixture
def home(tmp_path, monkeypatch):
    """Fake home with a work dir, a git repo, and a plain directory, outside temp roots."""
    monkeypatch.setattr(guard_rm, "in_temp_dir", lambda _path: False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / "work" / "repo" / ".git").mkdir(parents=True)
    (tmp_path / "work" / "repo" / "build").mkdir()
    (tmp_path / "work" / "plain").mkdir()
    return tmp_path


def run(command: str, cwd: Path) -> list[str]:
    return guard_rm.find_protected(command, str(cwd))


class TestFindProtected:
    """Test find_protected() classification."""

    @pytest.mark.parametrize(
        "command",
        [
            "rm -rf ~/work",
            "rm -fr $HOME/work/",
            'rm -r -f "${HOME}/work"',
            "rm --recursive --force ~/Library",
            "rm -Rf ~/*",
            "/bin/rm -rf ~/work",
            "FOO=1 command rm -rf ~/work",
        ],
    )
    def test_home_children(self, home, command):
        assert run(command, home / "work" / "plain")

    @pytest.mark.parametrize(
        "command",
        [
            "rm -rf repo",
            "rm -rf repo/.git",
            "rm -rf repo/*",
            "rm -rf ./*",
            "cd repo && rm -rf *",
            "echo hi; rm -rf ~/work/repo",
            "rm -rf ~/work/*",
        ],
    )
    def test_git_repositories(self, home, command):
        cwd = home / "work" / "repo" if command == "rm -rf ./*" else home / "work"
        assert run(command, cwd)

    @pytest.mark.parametrize(
        "command",
        [
            "rm -rf repo/build",
            "rm -rf repo/build/*",
            "rm -f ~/work",
            "rm ~/work/file.txt",
            "rm -rf $TARGET",
            "rm -rf plain",
            "ls -rf ~/work",
            "echo rm -rf ~/work",
            "rm -rf 'unterminated",
        ],
    )
    def test_allowed(self, home, command):
        assert run(command, home / "work") == []

    def test_temp_dirs_exempt_from_git_rule(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
        (tmp_path / "clone" / ".git").mkdir(parents=True)
        monkeypatch.setattr(
            guard_rm, "in_temp_dir", lambda path: path.startswith(str(tmp_path / "clone"))
        )
        assert run("rm -rf clone", tmp_path) == []


class TestInTempDir:
    """Test in_temp_dir() roots."""

    @pytest.mark.parametrize("path", ["/tmp/x", "/private/tmp", "/private/var/folders/ab/T/x"])
    def test_temp(self, path):
        assert guard_rm.in_temp_dir(path)

    def test_not_temp(self):
        assert not guard_rm.in_temp_dir("/tmpfoo/x")


class TestMain:
    """Test hook I/O."""

    def test_asks_for_protected_target(self, home, monkeypatch, capsys):
        payload = {"tool_input": {"command": "rm -rf ~/work"}, "cwd": str(home)}
        monkeypatch.setattr("sys.stdin", StringIO(json.dumps(payload)))
        assert guard_rm.main() == 0
        output = json.loads(capsys.readouterr().out)["hookSpecificOutput"]
        assert output["permissionDecision"] == "ask"
        assert str(home / "work") in output["permissionDecisionReason"]

    def test_silent_for_safe_target(self, home, monkeypatch, capsys):
        payload = {"tool_input": {"command": "rm -rf work/plain"}, "cwd": str(home)}
        monkeypatch.setattr("sys.stdin", StringIO(json.dumps(payload)))
        assert guard_rm.main() == 0
        assert capsys.readouterr().out == ""

    def test_invalid_json(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.stdin", StringIO("not json"))
        assert guard_rm.main() == 0
        assert capsys.readouterr().out == ""
