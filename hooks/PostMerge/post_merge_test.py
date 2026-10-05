#!/usr/bin/env python3
"""Integration tests for the .husky/post-merge and .husky/post-rewrite settings hooks.

Every test runs real merges and rebases in a throwaway git repository whose hooks are copies of
this repository's, with a stub merge_settings.sh, so this repository is never touched.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

HUSKY_DIR = Path(__file__).resolve().parents[2] / ".husky"

MERGE_STUB = "#!/usr/bin/env bash\nprintf 'merged\\n' >> \"$TOOL_LOG\"\n"


class Sandbox:
    """Throwaway git repository with an `upstream` branch standing in for the pulled remote."""

    def __init__(self, root: Path) -> None:
        self.repo = root / "repo"
        self.tool_log = root / "tool.log"
        self.repo.mkdir()

        # Drop inherited GIT_* variables and ignore user/system config, so nothing can reach
        # the real repository or its hooks.
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")} | {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "TOOL_LOG": str(self.tool_log),
        }

        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "hooks@example.test")
        self.git("config", "user.name", "Hook Test")
        self.write("helpers/merge_settings.sh", MERGE_STUB)
        self.write("settings/basics.jsonc", "{}\n")
        self.write("docs/note.md", "# Baseline\n")
        self.git("add", ".")
        self.git("commit", "-qm", "Initial commit")
        (self.repo / ".husky").mkdir()
        for hook in ("post-merge", "post-rewrite"):
            shutil.copy2(HUSKY_DIR / hook, self.repo / ".husky" / hook)
        self.git("config", "core.hooksPath", ".husky")

    def git(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments],
            cwd=self.repo,
            env=self.env,
            check=True,
            text=True,
            capture_output=True,
        )

    def write(self, filename: str, contents: str) -> None:
        destination = self.repo / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(contents)

    def commit_upstream(self, filename: str) -> None:
        self.git("switch", "-q", "-c", "upstream")
        self.write(filename, "upstream change\n")
        self.git("commit", "-qam", f"Change {filename}")
        self.git("switch", "-q", "main")

    def merge_runs(self) -> int:
        return self.tool_log.read_text().count("merged") if self.tool_log.exists() else 0


@pytest.fixture
def sandbox(tmp_path: Path) -> Sandbox:
    return Sandbox(tmp_path)


def test_fast_forward_changing_settings_regenerates(sandbox: Sandbox) -> None:
    sandbox.commit_upstream("settings/basics.jsonc")

    sandbox.git("merge", "-q", "--ff-only", "upstream")

    assert sandbox.merge_runs() == 1


def test_fast_forward_without_settings_changes_skips(sandbox: Sandbox) -> None:
    sandbox.commit_upstream("docs/note.md")

    sandbox.git("merge", "-q", "--ff-only", "upstream")

    assert sandbox.merge_runs() == 0


def test_rebase_onto_settings_changes_regenerates(sandbox: Sandbox) -> None:
    sandbox.commit_upstream("settings/basics.jsonc")
    sandbox.write("docs/note.md", "# Local\n")
    sandbox.git("commit", "-qam", "Local commit")

    sandbox.git("rebase", "-q", "upstream")

    assert sandbox.merge_runs() == 1


def test_amend_skips(sandbox: Sandbox) -> None:
    sandbox.write("settings/basics.jsonc", "{ amended: true }\n")
    sandbox.git("commit", "-q", "--amend", "-a", "--no-edit")

    assert sandbox.merge_runs() == 0
