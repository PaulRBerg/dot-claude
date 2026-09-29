#!/usr/bin/env python3
"""Integration tests for the shared-worktree-safe .husky/pre-commit hook.

Every test runs the hook in a throwaway git repository with stubbed `bun` and `sleep` binaries, so
this repository's index and worktree are never touched.
"""

import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

HOOK_SOURCE = Path(__file__).resolve().parents[2] / ".husky" / "pre-commit"

LINT_STAGED_LOG = "bun:run lint-staged --no-stash --no-hide-partially-staged\n"

# Records every invocation, optionally fails with "Failed to get staged files!" for the first two
# attempts (BUN_MODE=transient), and otherwise exits with BUN_EXIT after printing BUN_ERROR.
BUN_STUB = """#!/bin/sh
printf 'bun-index:%s\\n' "${GIT_INDEX_FILE-}" >> "$TOOL_LOG"
printf 'bun:%s\\n' "$*" >> "$TOOL_LOG"
if [ "${BUN_MODE-}" = transient ]; then
  attempt=0
  if [ -f "$BUN_ATTEMPTS_FILE" ]; then
    attempt=$(sed -n '1p' "$BUN_ATTEMPTS_FILE")
  fi
  attempt=$((attempt + 1))
  printf '%s\\n' "$attempt" > "$BUN_ATTEMPTS_FILE"
  if [ "$attempt" -lt 3 ]; then
    printf 'Failed to get staged files!\\n' >&2
    exit 1
  fi
fi
if [ -n "${BUN_ERROR-}" ]; then
  printf '%s\\n' "$BUN_ERROR" >&2
fi
exit "${BUN_EXIT:-0}"
"""

# The hook backs off between retries; skip the real delay.
SLEEP_STUB = "#!/bin/sh\nexit 0\n"


class Sandbox:
    """Throwaway git repository holding a copy of the hook, isolated from real git state."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.repo = root / "repo"
        self.tool_log = root / "tool.log"
        self.repo.mkdir()
        tools = root / "tools"
        tools.mkdir()
        for name, contents in (("bun", BUN_STUB), ("sleep", SLEEP_STUB)):
            tool = tools / name
            tool.write_text(contents)
            tool.chmod(tool.stat().st_mode | stat.S_IXUSR)

        # Drop inherited GIT_* variables (a hook run by `git commit` exports GIT_INDEX_FILE) and
        # ignore user/system config, so nothing can reach the real repository or its hooks.
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")} | {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "PATH": f"{tools}{os.pathsep}{os.environ['PATH']}",
            "TOOL_LOG": str(self.tool_log),
            "BUN_ATTEMPTS_FILE": str(root / "bun-attempts"),
        }

        self.git("init", "-q")
        self.git("config", "user.email", "hooks@example.test")
        self.git("config", "user.name", "Hook Test")
        self.write("docs/note.md", "# Baseline\n")
        self.git("add", "docs")
        self.git("commit", "-qm", "Initial commit")
        (self.repo / ".husky").mkdir()
        shutil.copy2(HOOK_SOURCE, self.repo / ".husky" / "pre-commit")

    def git(
        self, *arguments: str, env: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments],
            cwd=self.repo,
            env=self.env | (env or {}),
            check=True,
            text=True,
            capture_output=True,
        )

    def write(self, filename: str, contents: str) -> None:
        destination = self.repo / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(contents)

    def alternate_index(self) -> dict[str, str]:
        """Return env selecting a separate index seeded from HEAD, like `git commit <paths>`."""
        env = {"GIT_INDEX_FILE": str(self.root / "alternate.index")}
        self.git("read-tree", "HEAD", env=env)
        return env

    def default_index(self) -> bytes:
        return (self.repo / ".git" / "index").read_bytes()

    def run_hook(self, **env: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["sh", ".husky/pre-commit"],
            cwd=self.repo,
            env=self.env | env,
            check=False,
            text=True,
            capture_output=True,
        )

    def tool_calls(self) -> str:
        return self.tool_log.read_text() if self.tool_log.exists() else ""


@pytest.fixture
def sandbox(tmp_path: Path) -> Sandbox:
    return Sandbox(tmp_path)


def test_empty_index_exits_without_running_lint_staged(sandbox: Sandbox) -> None:
    result = sandbox.run_hook()

    assert result.returncode == 0, result.stderr
    assert not sandbox.tool_log.exists()


def test_default_index_partial_stage_is_rejected(sandbox: Sandbox) -> None:
    sandbox.write("docs/note.md", "# Intended\n")
    sandbox.git("add", "docs/note.md")
    sandbox.write("docs/note.md", "# Intended\nUnrelated worktree bytes.\n")

    result = sandbox.run_hook()

    assert result.returncode == 1
    assert "error: partially staged files are unsafe in the shared worktree:" in result.stderr
    assert "docs/note.md" in result.stderr
    assert not sandbox.tool_log.exists()


def test_alternate_index_partial_stage_is_rejected_without_changing_default_index(
    sandbox: Sandbox,
) -> None:
    sandbox.write("shared-stage.txt", "Unrelated shared staging.\n")
    sandbox.git("add", "shared-stage.txt")
    default_index_before = sandbox.default_index()
    alternate = sandbox.alternate_index()
    sandbox.write("docs/note.md", "# Intended\n")
    sandbox.git("add", "docs/note.md", env=alternate)
    sandbox.write("docs/note.md", "# Intended\nUnrelated worktree bytes.\n")

    result = sandbox.run_hook(**alternate)

    assert result.returncode == 1
    assert "docs/note.md" in result.stderr
    assert "shared-stage.txt" not in result.stderr
    assert sandbox.default_index() == default_index_before
    assert not sandbox.tool_log.exists()


def test_fully_staged_file_runs_lint_staged(sandbox: Sandbox) -> None:
    sandbox.write("docs/note.md", "# Fully staged\n")
    sandbox.git("add", "docs/note.md")

    result = sandbox.run_hook()

    assert result.returncode == 0, result.stderr
    assert sandbox.tool_calls() == f"bun-index:\n{LINT_STAGED_LOG}"


def test_fully_staged_alternate_index_leaves_default_index_untouched(sandbox: Sandbox) -> None:
    sandbox.write("shared-stage.txt", "Unrelated shared staging.\n")
    sandbox.git("add", "shared-stage.txt")
    default_index_before = sandbox.default_index()
    alternate = sandbox.alternate_index()
    sandbox.write("docs/note.md", "# Alternate index\n")
    sandbox.git("add", "docs/note.md", env=alternate)

    result = sandbox.run_hook(**alternate)

    assert result.returncode == 0, result.stderr
    assert sandbox.default_index() == default_index_before
    assert sandbox.tool_calls() == f"bun-index:{alternate['GIT_INDEX_FILE']}\n{LINT_STAGED_LOG}"


def test_deletion_only_commit_runs_lint_staged(sandbox: Sandbox) -> None:
    (sandbox.repo / "docs" / "note.md").unlink()
    sandbox.git("add", "docs/note.md")

    result = sandbox.run_hook()

    assert result.returncode == 0, result.stderr
    assert LINT_STAGED_LOG in sandbox.tool_calls()


def test_non_transient_lint_staged_failure_is_not_retried(sandbox: Sandbox) -> None:
    sandbox.write("docs/note.md", "# Fully staged\n")
    sandbox.git("add", "docs/note.md")

    result = sandbox.run_hook(BUN_EXIT="7", BUN_ERROR="lint failure")

    assert result.returncode == 7
    assert "lint failure" in result.stdout
    assert sandbox.tool_calls().count(LINT_STAGED_LOG) == 1


def test_transient_lint_staged_failure_is_retried(sandbox: Sandbox) -> None:
    sandbox.write("docs/note.md", "# Fully staged\n")
    sandbox.git("add", "docs/note.md")

    result = sandbox.run_hook(BUN_MODE="transient")

    assert result.returncode == 0, result.stderr
    assert sandbox.tool_calls().count(LINT_STAGED_LOG) == 3
