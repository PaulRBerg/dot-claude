#!/usr/bin/env bash
#
# commit_codex_agents.sh
#
# Run from this repo's pre-commit lint-staged step (.lintstagedrc.js), after
# `just build` regenerates ~/.codex/AGENTS.md from the root CLAUDE.md. Commits
# AGENTS.md in the ~/.codex repo, but only if it's the sole dirty path there —
# skips if AGENTS.md is unchanged or if anything else in ~/.codex is dirty.
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

status_output=$(git -C "$codex_repo" status --porcelain=v1)
[[ -n "$status_output" ]] || exit 0

agents_changed=false
other_dirty=false
while IFS= read -r line; do
  path="${line:3}"
  if [[ "$path" == "AGENTS.md" ]]; then
    agents_changed=true
  else
    other_dirty=true
  fi
done <<<"$status_output"

[[ "$agents_changed" == true && "$other_dirty" == false ]] || exit 0

git -C "$codex_repo" add AGENTS.md
git -C "$codex_repo" commit -m "Sync AGENTS.md from ~/.claude commit"
