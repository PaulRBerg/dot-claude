"""Unit tests for command_guard.py hook."""

import json
from io import StringIO

import command_guard
import pytest

DENIED = [
    "sudo ls",
    "/usr/bin/sudo ls",
    "env FOO=1 sudo ls",
    "doas ls",
    "su - root",
    "passwd",
    "userdel bob",
    "usermod -aG wheel bob",
    "dd if=/dev/zero of=/dev/disk2",
    "mkfs /dev/disk2",
    "mkfs.ext4 /dev/sda1",
    "timeout 5 reboot",
    "echo hi && shutdown -h now",
    "systemctl restart nginx",
    "killall node",
    "kill -9 123",
    "kill -KILL 123",
    "kill -s SIGKILL 123",
    "chmod -R 777 .",
    "chown -Rv prb .",
    "chmod --recursive 755 dir",
    "npm publish",
    "npm publish --access public",
    "bash -c 'sudo ls'",
    "if true; then sudo ls; fi",
    "for f in a b; do chmod -R 777 $f; done",
    "bash <<EOF\nsudo ls\nEOF",
    "cd repo && /bin/bash -s <<'EOF'\nsudo ls\nEOF",
]

ALLOWED = [
    "echo sudo",
    "git commit -m 'sudo make me a sandwich'",
    "cat > install.md <<EOF\nsudo apt-get install jq\nEOF",
    "mkdir -p out && cat > out/run.sh <<'EOF'\nkill -9 $PID\nEOF\nchmod +x out/run.sh",
    "kill 123",
    "kill -TERM 123",
    "chmod +x script.sh",
    "chmod -r file",
    "ls -R",
    "npm install",
    "npm run publish",
    "rg dd",
    "echo 'unterminated",
    "",
]


@pytest.mark.parametrize("command", DENIED)
def test_denies_system_commands(command: str) -> None:
    assert command_guard.command_denial(command)


@pytest.mark.parametrize("command", ALLOWED)
def test_allows_other_commands(command: str) -> None:
    assert command_guard.command_denial(command) is None


def run_hook(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], payload: object
) -> str:
    monkeypatch.setattr("sys.stdin", StringIO(json.dumps(payload)))
    assert command_guard.main() == 0
    return capsys.readouterr().out


def test_emits_deny_decision(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    output = json.loads(run_hook(monkeypatch, capsys, {"tool_input": {"command": "sudo ls"}}))
    decision = output["hookSpecificOutput"]
    assert decision["permissionDecision"] == "deny"
    assert "`sudo ls` escalates privileges" in decision["permissionDecisionReason"]


def test_allows_silently_and_fails_open(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run_hook(monkeypatch, capsys, {"tool_input": {"command": "ls"}}) == ""
    assert run_hook(monkeypatch, capsys, {"tool_input": {}}) == ""
