#!/usr/bin/env bash
# check-gemini.sh - Validate Gemini CLI availability
#
# Exit codes:
#   0 - Gemini CLI is available
#   1 - Gemini CLI is not installed

set -euo pipefail

if command -v gemini &>/dev/null; then
    # Use timeout to detect hung processes (5 seconds max)
    if timeout 5 gemini --version &>/dev/null; then
        echo "gemini ready"
        exit 0
    else
        echo "ERROR: Gemini CLI is installed but not responding (timeout)" >&2
        exit 1
    fi
else
    cat >&2 <<'EOF'
ERROR: Gemini CLI is not installed or not in PATH.

Install Gemini CLI:
  npm install -g @google/gemini-cli

Or via Homebrew:
  brew install gemini-cli

Documentation: https://github.com/google-gemini/gemini-cli

After installation, ensure 'gemini' is available in your PATH.
EOF
    exit 1
fi
