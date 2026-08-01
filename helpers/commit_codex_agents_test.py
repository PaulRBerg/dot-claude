import os
import subprocess
from pathlib import Path


SCRIPT = Path(__file__).with_name("commit_codex_agents.sh")


def git(repo: Path, *args: str, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )
    return result.stdout.strip()


def init_repo(repo: Path) -> None:
    repo.mkdir()
    git(repo, "init", "--quiet")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "Test User")


def commit_all(repo: Path, message: str) -> None:
    git(repo, "add", ".")
    git(repo, "commit", "--quiet", "-m", message)


def test_ignores_calling_repositories_git_environment(tmp_path: Path) -> None:
    claude_repo = tmp_path / "claude"
    codex_repo = tmp_path / ".codex"
    init_repo(claude_repo)
    init_repo(codex_repo)

    (claude_repo / "AGENTS.md").write_text("foreign index content\n")
    commit_all(claude_repo, "Initialize Claude fixture")

    agents_file = codex_repo / "AGENTS.md"
    agents_file.write_text("old instructions\n")
    commit_all(codex_repo, "Initialize Codex fixture")
    agents_file.write_text("new instructions\n")

    alternate_index = tmp_path / "claude.index"
    polluted_env = os.environ.copy()
    polluted_env["GIT_INDEX_FILE"] = str(alternate_index)
    polluted_env["HOME"] = str(tmp_path)
    git(claude_repo, "read-tree", "HEAD", env=polluted_env)

    result = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        cwd=claude_repo,
        env=polluted_env,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert git(codex_repo, "status", "--porcelain=v1") == ""
    assert git(codex_repo, "show", "HEAD:AGENTS.md") == "new instructions"
