#!/usr/bin/env bash
#
# commit_codex_agents.sh
#
# Run from this repo's pre-commit lint-staged step (.lintstagedrc.js), after
# `just build` regenerates ~/.codex/AGENTS.md from the root CLAUDE.md. Commits
# AGENTS.md in the ~/.codex repo when it changed. The commit is constructed
# with an isolated index so concurrent work in that repository is untouched.
#
# Usage: commit_codex_agents.sh

set -euo pipefail

codex_repo="$HOME/.codex"

[[ -d "$codex_repo/.git" ]] || exit 0

# Hooks inherit repository-local variables from the calling Git process, and
# `git -C` does not replace values such as GIT_INDEX_FILE for a foreign repo.
git_env_vars=$(git rev-parse --local-env-vars)
while IFS= read -r git_env_var; do
  [[ -n "$git_env_var" ]] && unset "$git_env_var"
done <<<"$git_env_vars"
unset git_env_var git_env_vars

if git -C "$codex_repo" diff --quiet HEAD -- AGENTS.md; then
  exit 0
fi

temp_dir=$(mktemp -d "${TMPDIR:-/tmp}/commit-codex-agents.XXXXXX")
isolated_index="$temp_dir/index"

cleanup() {
  rm -f "$isolated_index" "$isolated_index.lock"
  rmdir "$temp_dir" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

head_commit=$(git -C "$codex_repo" rev-parse --verify 'HEAD^{commit}')
branch_ref=$(git -C "$codex_repo" symbolic-ref -q HEAD)

GIT_INDEX_FILE="$isolated_index" git -C "$codex_repo" read-tree "$head_commit"
GIT_INDEX_FILE="$isolated_index" git -C "$codex_repo" add -- AGENTS.md
tree=$(GIT_INDEX_FILE="$isolated_index" git -C "$codex_repo" write-tree)
commit=$(printf '%s\n' "Sync AGENTS.md from ~/.claude commit" |
  git -C "$codex_repo" commit-tree "$tree" -p "$head_commit")
git -C "$codex_repo" update-ref "$branch_ref" "$commit" "$head_commit"
