#!/usr/bin/env bash
# check-codex.sh - Validate Codex CLI availability
#
# Exit codes:
#   0 - Codex CLI is available
#   1 - Codex CLI is not installed

set -euo pipefail

if command -v codex &>/dev/null; then
    echo "codex $(codex --version 2>/dev/null || echo 'installed')"
    exit 0
else
    cat >&2 <<'EOF'
ERROR: Codex CLI is not installed or not in PATH.

Install Codex CLI:
  npm install -g @openai/codex

Or via Homebrew:
  brew install openai/tap/codex

Documentation: https://github.com/openai/codex

After installation, ensure 'codex' is available in your PATH.
EOF
    exit 1
fi
