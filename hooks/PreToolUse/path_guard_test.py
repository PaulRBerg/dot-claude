"""Unit tests for path_guard.py hook."""

import json
from io import StringIO
from pathlib import Path

import path_guard
import pytest


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Fake home with both secret directories and a project that links into one."""
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".ssh").mkdir()
    (tmp_path / "Drive" / "Secrets").mkdir(parents=True)
    (tmp_path / "project").mkdir()
    (tmp_path / "project" / "vault").symlink_to(tmp_path / "Drive" / "Secrets")
    return tmp_path


DENIED = [
    {"file_path": "~/.ssh/id_ed25519"},
    {"file_path": "TODO.md"},
    {"file_path": "docs/PROMPT.md"},
    {"file_path": "vault/api-keys.txt"},
    {"notebook_path": "~/Drive/Secrets/analysis.ipynb"},
    {"path": "~/Drive/Secrets", "pattern": "token"},
    {"path": "~/.ssh", "pattern": "*"},
    {"command": "cat ~/.ssh/config"},
    {"command": "head -5 TODO.md"},
    {"command": "sed -n 1,5p docs/PROMPT.md | wc -l"},
    {"command": "echo done > PROMPT.md"},
    {"command": 'wc -l < "$HOME/.ssh/id_ed25519"'},
    {"command": "cp vault/api-keys.txt /tmp/keys"},
    {"command": "bash -c 'cat TODO.md'"},
]

ALLOWED = [
    {"file_path": "README.md"},
    {"file_path": "docs/TODO.md.bak"},
    {"path": ".", "pattern": "TODO"},
    {"pattern": "**/*.md"},
    {"command": "cat README.md"},
    {"command": "ls ~/.ssh"},
    {"command": "ssh -i ~/.ssh/id_ed25519 host uptime"},
    {"command": "rg -n TODO.md"},
    {"command": "git status 2>&1"},
    {"command": "cat > notes.md <<EOF\nsee TODO.md > PROMPT.md\nEOF"},
    {"command": "echo 'unterminated"},
]


@pytest.mark.parametrize("tool_input", DENIED)
def test_denies_protected_paths(home: Path, tool_input: dict[str, object]) -> None:
    assert path_guard.tool_denial(tool_input, str(home / "project"))


@pytest.mark.parametrize("tool_input", ALLOWED)
def test_allows_other_paths(home: Path, tool_input: dict[str, object]) -> None:
    assert path_guard.tool_denial(tool_input, str(home / "project")) is None


def run_hook(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], payload: object
) -> str:
    monkeypatch.setattr("sys.stdin", StringIO(json.dumps(payload)))
    assert path_guard.main() == 0
    return capsys.readouterr().out


def test_emits_deny_decision(
    home: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    payload = {"tool_input": {"file_path": "~/.ssh/id_ed25519"}, "cwd": str(home)}
    decision = json.loads(run_hook(monkeypatch, capsys, payload))["hookSpecificOutput"]
    assert decision["permissionDecision"] == "deny"
    assert "inside ~/.ssh" in decision["permissionDecisionReason"]


def test_allows_silently_and_fails_open(
    home: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    payload = {"tool_input": {"file_path": "README.md"}, "cwd": str(home)}
    assert run_hook(monkeypatch, capsys, payload) == ""
    assert run_hook(monkeypatch, capsys, {"tool_input": "not a mapping"}) == ""
    assert run_hook(monkeypatch, capsys, {}) == ""
