"""Tests for the git_guard PreToolUse hook."""

import json
from io import StringIO
from pathlib import Path

import pytest

import git_guard

DENIED = [
    # Bare stash and its implicit or explicit push forms.
    "git stash",
    "git stash -u",
    "git stash -p",
    "git stash push -m wip",
    "git stash save wip",
    "git stash clear",
    "git stash -- src/app.ts",
    # Options after other arguments, which permission patterns cannot reach.
    "git commit -m msg -a",
    "git commit -qam msg",
    "git commit --amend --all --no-edit",
    "git commit -m msg .",
    "git add -v .",
    "git add --verbose -A",
    "git add -u",
    "git add :/",
    "git checkout HEAD -- .",
    "git restore --staged .",
    "git restore --source HEAD~1 .",
    "git reset HEAD~1 --hard",
    "git clean -n",
    "git pull --rebase --autostash",
    "git rebase main --autostash",
    "git -c rebase.autoStash=true pull --rebase",
    # Global options, wrappers, compound commands, and nested shells.
    "git -C /tmp/repo stash",
    "git --no-pager -c color.ui=never stash",
    "GIT_TRACE=1 git stash",
    "env -u FOO git stash",
    "sudo -n git clean -fd",
    "timeout 10 git stash",
    "/usr/bin/git stash",
    "git status && git stash",
    "git status; git add .",
    "git fetch\ngit reset --hard origin/main",
    "echo $(git stash)",
    "echo `git stash`",
    "git stash 2>/dev/null",
    "git stash > /dev/null",
    "(cd repo && git add -A)",
    "bash -lc 'git stash'",
    "zsh -c \"git commit -m 'msg' -a\"",
    "bash --login -c 'git add .'",
]

ASKED = [
    "git push origin main --force",
    "git push origin main -f",
    "git push --force-with-lease=main:abc123 origin main",
    "git push origin +main",
    "git push upstream --force",
    "git -C repo push --force origin main",
    "git push --force-with-lease origin main",
    "git push origin --force",
    "git push -f",
]

ALLOWED = [
    "git stash list",
    "git stash show -p stash@{0}",
    "git stash pop",
    "git stash apply abc123",
    "git reflog show stash",
    "git commit -m msg",
    "git commit -m 'stage -a later' src/app.ts",
    "git commit -ma",
    "git commit -S -m msg",
    "git commit -F msg.txt src/app.ts",
    "git add src/app.ts",
    "git add -p src/app.ts",
    "git add -u src/",
    "git checkout main",
    "git checkout -- src/app.ts",
    "git restore --staged src/app.ts",
    "git reset --soft HEAD~1",
    "git pull --rebase --no-autostash",
    "git -c rebase.autoStash=false pull --rebase",
    "git push",
    "git push origin main",
    "git status --short",
    "echo 'git stash'",
    "rg -n 'git add -A' docs",
    "ai-commit commit abc -m 'Forbid git stash and git clean'",
    "bash scripts/check.sh",
    "",
]


@pytest.mark.parametrize("command", DENIED)
def test_denies_banned_git_forms(command: str) -> None:
    result = git_guard.command_decision(command)
    assert result is not None
    assert result[0] == "deny"


@pytest.mark.parametrize("command", ASKED)
def test_asks_before_any_force_push(command: str) -> None:
    result = git_guard.command_decision(command)
    assert result is not None
    assert result[0] == "ask"


@pytest.mark.parametrize("command", ALLOWED)
def test_allows_safe_git_forms(command: str) -> None:
    assert git_guard.command_decision(command) is None


def run_hook(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], payload: object
) -> str:
    monkeypatch.setattr("sys.stdin", StringIO(json.dumps(payload)))
    assert git_guard.main() == 0
    return capsys.readouterr().out


def test_emits_deny_decision(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    output = json.loads(run_hook(monkeypatch, capsys, {"tool_input": {"command": "git stash"}}))
    decision = output["hookSpecificOutput"]
    assert decision["hookEventName"] == "PreToolUse"
    assert decision["permissionDecision"] == "deny"
    assert "git stash list" in decision["permissionDecisionReason"]


def test_allows_silently(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run_hook(monkeypatch, capsys, {"tool_input": {"command": "git stash list"}}) == ""


def test_fails_open_on_malformed_input(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run_hook(monkeypatch, capsys, {"tool_input": {}}) == ""
    assert run_hook(monkeypatch, capsys, {"tool_input": {"command": "echo 'unterminated"}}) == ""


def test_hook_is_registered_for_bash() -> None:
    settings = (Path(__file__).parents[2] / "settings" / "hooks.jsonc").read_text()
    assert "~/.claude/hooks/PreToolUse/git_guard.py" in settings
