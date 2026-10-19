#!/usr/bin/env python3
"""Unit tests for enable_computer_use.py hook."""

import json
import sys
from io import StringIO
from pathlib import Path

import pytest

import enable_computer_use


@pytest.fixture
def home(tmp_path, monkeypatch):
    """Fake home with a git repo and a ~/.claude.json listing it."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    (tmp_path / "repo" / ".git").mkdir(parents=True)
    (tmp_path / "repo" / "src").mkdir()
    return tmp_path


def write_config(home: Path, projects: dict) -> Path:
    path = home / ".claude.json"
    path.write_text(json.dumps({"projects": projects}))
    path.chmod(0o600)
    return path


def run(monkeypatch, cwd: Path | None = None, *args: str) -> None:
    monkeypatch.setattr(sys, "argv", ["enable_computer_use.py", *args])
    monkeypatch.setattr(sys, "stdin", StringIO(json.dumps({"cwd": str(cwd)})))
    assert enable_computer_use.main() == 0


def test_enables_project_from_git_root(home, monkeypatch):
    repo = str((home / "repo").resolve())
    path = write_config(home, {repo: {"enabledMcpServers": ["other"]}})
    run(monkeypatch, home / "repo" / "src")
    config = json.loads(path.read_text())
    assert config["projects"][repo]["enabledMcpServers"] == ["other", "computer-use"]
    assert path.stat().st_mode & 0o777 == 0o600


def test_skips_missing_project_entry(home, monkeypatch):
    path = write_config(home, {})
    before = path.read_text()
    run(monkeypatch, home / "repo")
    assert path.read_text() == before


def test_leaves_enabled_project_untouched(home, monkeypatch):
    repo = str((home / "repo").resolve())
    path = write_config(home, {repo: {"enabledMcpServers": ["computer-use"]}})
    mtime = path.stat().st_mtime_ns
    run(monkeypatch, home / "repo")
    assert path.stat().st_mtime_ns == mtime


def test_all_backfills_every_project(home, monkeypatch):
    path = write_config(home, {"/a": {}, "/b": {"enabledMcpServers": ["computer-use"]}})
    run(monkeypatch, None, "--all")
    projects = json.loads(path.read_text())["projects"]
    assert all(p["enabledMcpServers"] == ["computer-use"] for p in projects.values())
