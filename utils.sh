#!/usr/bin/env zsh

###############################################################################
# ALIASES                                                                     #
###############################################################################

alias cd_claude="cd ~/.claude"
alias cd_codex="cd ~/.codex"
alias cd_gemini="cd ~/.gemini"
alias codex="codex --dangerously-bypass-approvals-and-sandbox"
alias gemini="gemini --yolo"
alias edit_claude="code ~/.claude"
alias edit_codex="code ~/.codex"
alias edit_gemini="code ~/.gemini"

###############################################################################
# FUNCTIONS                                                                   #
###############################################################################

# Claude Code commit
function ccc() {
  # Check if we're in a git repository
  if ! git rev-parse --git-dir &>/dev/null; then
    echo "❌ Error: Not in a git repository"
    return 1
  fi

  # Check for changes (staged, unstaged, and untracked)
  if [[ -z "$(git status --porcelain)" ]]; then
    echo "⚠️  Warning: No changes to commit (working tree clean)"
    return 0
  fi

  # If no args provided, default to --all
  if [[ $# -eq 0 ]]; then
    set -- --all
  fi

  # Proceed with commit
  local output
  if command -v gum &>/dev/null; then
    output=$(gum spin --spinner dot --title "Claude is git committing..." -- claude --model "haiku" --print "/commit $*" --output-format json)
  else
    output=$(claude --model "haiku" --print "/commit $*" --output-format json)
  fi

  # Clean up the conversation history
  _claude_cleanup_session "$output"

  # Display the result text
  jq -r '.result' <<<"$output"
}

# Claude Code commit and push
# Best suited for feature branches with upstream configured
function cccp() {
  ccc --all --push
}

# Claude Code bump release
function ccbump() {
  # Proceed with release bump
  if command -v gum &>/dev/null; then
    gum spin --spinner dot --title "Claude is bumping release..." -- claude --print "/bump-release $*"
  else
    claude --print "/bump-release $*"
  fi
}

# Wrapper for claude CLI that auto-loads .mcp.json if present
# See https://github.com/anthropics/claude-code/issues/3321#issuecomment-3401742599
function claude() {
  local has_p_flag=false

  # Check if -p flag is present
  for arg in "$@"; do
    if [[ "$arg" == "-p" ]]; then
      has_p_flag=true
      break
    fi
  done

  # Determine the base command
  local base_cmd
  if [[ -f .mcp.json ]]; then
    base_cmd=(command claude --mcp-config .mcp.json --dangerously-skip-permissions "$@")
  else
    base_cmd=(command claude --dangerously-skip-permissions "$@")
  fi

  # Execute with or without gum spinner
  if [[ "$has_p_flag" == true ]] && command -v gum &>/dev/null; then
    gum spin --spinner dot --title "Claude is thinking..." -- "${base_cmd[@]}"
  else
    "${base_cmd[@]}"
  fi
}

# Helper function to delete Claude conversation history from a JSON response
function _claude_cleanup_session() {
  local json_output="$1"

  # Extract session_id from JSON
  local session_id
  session_id=$(jq -r '.session_id' <<<"$json_output" 2>/dev/null)

  # Delete the .jsonl file if session_id exists
  if [[ -n "$session_id" && "$session_id" != "null" ]]; then
    local jsonl_file
    jsonl_file=$(find ~/.claude/projects -name "${session_id}.jsonl" 2>/dev/null | head -1)
    [[ -n "$jsonl_file" ]] && rm -f "$jsonl_file"
  fi
}
