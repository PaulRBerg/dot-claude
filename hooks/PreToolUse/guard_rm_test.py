"""Unit tests for guard_rm.py hook."""

import json
import re
from io import StringIO
from pathlib import Path

import guard_rm
import pytest


@pytest.fixture
def home(tmp_path, monkeypatch):
    """Fake home with work clones, dot-directories, and a plain directory, outside temp roots."""
    monkeypatch.setattr(guard_rm, "in_temp_dir", lambda _path: False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("UNSET_DIR", raising=False)
    repo = tmp_path / "work" / "repo"
    (repo / ".git").mkdir(parents=True)
    (repo / "build").mkdir()
    (repo / "lib" / "submodule").mkdir(parents=True)
    (repo / "lib" / "submodule" / ".git").write_text("gitdir: ../../.git/modules/submodule\n")
    (repo / "node_modules" / "dependency" / ".git").mkdir(parents=True)
    (tmp_path / "work" / "plain").mkdir()
    for name in ("Library", ".claude", ".coderabbit"):
        (tmp_path / name).mkdir()
    return tmp_path


def run(command: str, cwd: Path) -> list[str]:
    return guard_rm.find_denials(command, str(cwd))


class TestFindDenials:
    """Test find_denials() classification."""

    @pytest.mark.parametrize(
        "command",
        [
            "rm -rf ~",
            "rm -rf ~/work",
            "rm -fr $HOME/work/",
            'rm -r -f "${HOME}/work"',
            "rm --recursive --force ~/Library",
            "rm -Rf ~/*",
            "rm -rf ~/.*",
            "rm -rf ~/.claude",
            "/bin/rm -rf ~/work",
            "FOO=1 command rm -rf ~/work",
            "bash -c 'rm -rf ~/work'",
            "D=~/work; rm -rf $D",
            "export D=~/work && rm -rf $D",
            "for d in a b; do rm -rf ~/work; done",
            "if true; then rm -rf ~/work; fi",
            "cleanup() { rm -rf ~/work; }",
            "rm -rf ~/work/*",
        ],
    )
    def test_home(self, home, command):
        assert run(command, home / "work" / "plain")

    @pytest.mark.parametrize(
        "command",
        [
            "rm -rf repo",
            "rm -rf repo/.git",
            "rm -rf repo/*",
            "cd repo && rm -rf *",
            "echo hi; rm -rf ~/work/repo",
            "cat <<EOF\nit's a heredoc\nEOF\nrm -rf repo",
            "echo 'unterminated\nrm -rf repo",
        ],
    )
    def test_git_repositories(self, home, command):
        assert run(command, home / "work")

    @pytest.mark.parametrize("command", ["rm -rf ./*", 'rm -rf "$(pwd)"', "rm -rf $PWD/*"])
    def test_git_repository_as_working_directory(self, home, command):
        assert run(command, home / "work" / "repo")

    @pytest.mark.parametrize(
        "command",
        [
            "rm -rf /",
            "rm -rf /usr",
            "rm -rf /*",
            "rm -rf /tmp/*",
            'rm -rf "$UNSET_DIR"/*',
            "rm -rf $UNSET_DIR/",
            "rm -rf ${UNSET_DIR}/usr",
            'cd "$UNSET_DIR" && rm -rf /usr',
        ],
    )
    def test_system_directories(self, home, command):
        assert run(command, home / "work")

    def test_unset_variable_denial_names_the_guard(self, home):
        (finding,) = run('rm -rf "$UNSET_DIR"/*', home / "work")
        assert "$UNSET_DIR is empty" in finding
        assert "${VAR:?}" in finding

    @pytest.mark.parametrize(
        "command",
        [
            "rm -rf repo/build",
            "rm -rf repo/build/*",
            "rm -rf repo/*.log",
            "rm -rf repo/lib/submodule",
            "rm -rf repo/node_modules/dependency",
            "rm -f ~/work",
            "rm ~/work/file.txt",
            "rm -rf ~/.coderabbit",
            "rm -rf ~/missing",
            "rm -rf $TARGET",
            "rm -rf $UNSET_DIR/build",
            'rm -rf "${UNSET_DIR:?}"/*',
            "rm -rf plain",
            "ls -rf ~/work",
            "echo rm -rf ~/work",
            "cat <<EOF\nrm -rf ~/work\nEOF",
            "rm -rf 'unterminated",
            "S=/tmp/x",
            "f=$(fd x | tail -1); echo $f",
            "D=/tmp/x && echo $D",
            'T=$(mktemp -d) && cd "$T" && rm -rf *',
            "pushd $SOMEWHERE && rm -rf repo",
            "export OUT=plain/out && rm -rf $OUT/*",
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

    def test_denies_protected_target(self, home, monkeypatch, capsys):
        payload = {"tool_input": {"command": "rm -rf ~/work"}, "cwd": str(home)}
        monkeypatch.setattr("sys.stdin", StringIO(json.dumps(payload)))
        assert guard_rm.main() == 0
        output = json.loads(capsys.readouterr().out)["hookSpecificOutput"]
        assert output["permissionDecision"] == "deny"
        assert str(home / "work") in output["permissionDecisionReason"]

    def test_silent_for_safe_target(self, home, monkeypatch, capsys):
        payload = {"tool_input": {"command": "rm -rf work/plain"}, "cwd": str(home)}
        monkeypatch.setattr("sys.stdin", StringIO(json.dumps(payload)))
        assert guard_rm.main() == 0
        assert capsys.readouterr().out == ""

    @pytest.mark.parametrize("stdin", ["not json", "{}"])
    def test_fails_open_on_malformed_input(self, stdin, monkeypatch, capsys):
        monkeypatch.setattr("sys.stdin", StringIO(stdin))
        assert guard_rm.main() == 0
        assert capsys.readouterr().out == ""


def test_settings_keep_the_rm_prompt_waiver():
    """One deny or ask rule for Bash, Edit, or Read, or any PermissionRequest hook, makes
    Claude Code ignore CLAUDE_CODE_EVEN_MORE_DANGEROUSLY_SKIP_PERMISSIONS."""
    settings = Path(__file__).parents[2] / "settings"
    hooks = (settings / "hooks.jsonc").read_text()
    rules = "".join(
        path.read_text() for path in settings.rglob("*.jsonc") if path.name != "hooks.jsonc"
    )
    assert not re.search(r'"(Bash|Edit|Read)[("]', rules)
    assert not re.search(r'"PermissionRequest"\s*:', hooks)
    for guard in ("command_guard", "git_guard", "guard_rm", "path_guard"):
        assert f"~/.claude/hooks/PreToolUse/{guard}.py" in hooks
