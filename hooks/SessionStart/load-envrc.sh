#!/bin/bash
# Load .envrc environment variables via direnv into Claude Code sessions.
# Uses CLAUDE_ENV_FILE to inject exports into all subsequent Bash calls.

if [ -z "$CLAUDE_ENV_FILE" ]; then
  exit 0
fi

if ! command -v direnv &> /dev/null || [ ! -f .envrc ]; then
  exit 0
fi

direnv allow .envrc 2>/dev/null || true
direnv export bash 2>/dev/null | grep '^export ' >> "$CLAUDE_ENV_FILE" || true

exit 0
