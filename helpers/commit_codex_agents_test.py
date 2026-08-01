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
    assert git(codex_repo, "show", "HEAD:AGENTS.md") == "new instructions"


def test_commits_agents_only_with_other_dirty_and_staged_paths(tmp_path: Path) -> None:
    claude_repo = tmp_path / "claude"
    codex_repo = tmp_path / ".codex"
    init_repo(claude_repo)
    init_repo(codex_repo)

    (codex_repo / "AGENTS.md").write_text("old instructions\n")
    foreign_file = codex_repo / "foreign.txt"
    foreign_file.write_text("base\n")
    commit_all(codex_repo, "Initialize Codex fixture")

    (codex_repo / "AGENTS.md").write_text("new instructions\n")
    foreign_file.write_text("staged change\n")
    git(codex_repo, "add", "foreign.txt")
    foreign_file.write_text("unstaged change\n")
    index_before = git(codex_repo, "hash-object", ".git/index")
    staged_diff_before = git(codex_repo, "diff", "--cached", "--", "foreign.txt")
    unstaged_diff_before = git(codex_repo, "diff", "--", "foreign.txt")
    environment = os.environ.copy()
    environment["HOME"] = str(tmp_path)
    result = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        cwd=claude_repo,
        env=environment,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert git(codex_repo, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD") == "AGENTS.md"
    assert git(codex_repo, "show", "HEAD:AGENTS.md") == "new instructions"
    assert git(codex_repo, "hash-object", ".git/index") == index_before
    assert foreign_file.read_text() == "unstaged change\n"
    assert git(codex_repo, "show", ":foreign.txt") == "staged change"
    assert git(codex_repo, "diff", "--cached", "--", "foreign.txt") == staged_diff_before
    assert git(codex_repo, "diff", "--", "foreign.txt") == unstaged_diff_before
