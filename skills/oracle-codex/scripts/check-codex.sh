#!/usr/bin/env bash
# check-codex.sh - Validate Codex CLI availability and authentication
#
# Exit codes:
#   0 - Codex CLI is ready (installed and authenticated)
#   1 - Codex CLI is not installed
#   2 - Codex CLI is not responding (timeout)
#   3 - Codex CLI is not authenticated
#
# Options:
#   -v, --verbose   Show detailed status
#   -q, --quiet     Suppress output on success
#   --skip-auth     Skip authentication check

set -euo pipefail

VERBOSE=0
QUIET=0
SKIP_AUTH=0
TIMEOUT_SECS=5

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Validate Codex CLI availability and authentication.

Options:
  -v, --verbose   Show detailed status information
  -q, --quiet     Suppress output on success (exit code only)
  --skip-auth     Skip authentication check
  -h, --help      Show this help message

Exit codes:
  0  Codex CLI is ready
  1  Codex CLI is not installed
  2  Codex CLI is not responding
  3  Codex CLI is not authenticated
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -v|--verbose) VERBOSE=1; shift ;;
        -q|--quiet) QUIET=1; shift ;;
        --skip-auth) SKIP_AUTH=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
    esac
done

log() {
    [[ $QUIET -eq 0 ]] && echo "$@" || true
}

log_verbose() {
    [[ $VERBOSE -eq 1 ]] && echo "$@" || true
}

log_error() {
    echo "$@" >&2
}

# Check 1: Is codex installed?
if ! command -v codex &>/dev/null; then
    log_error "ERROR: Codex CLI is not installed or not in PATH."
    log_error ""
    log_error "Install Codex CLI:"
    log_error "  npm install -g @openai/codex"
    log_error ""
    log_error "Or via Homebrew:"
    log_error "  brew install openai/tap/codex"
    log_error ""
    log_error "Documentation: https://github.com/openai/codex"
    exit 1
fi

log_verbose "Found: $(command -v codex)"

# Check 2: Is codex responding?
if ! version=$(timeout "$TIMEOUT_SECS" codex --version 2>/dev/null); then
    log_error "ERROR: Codex CLI is installed but not responding (timeout after ${TIMEOUT_SECS}s)"
    log_error "Try running 'codex --version' manually to diagnose."
    exit 2
fi

log_verbose "Version: $version"

# Check 3: Is codex authenticated?
if [[ $SKIP_AUTH -eq 0 ]]; then
    if ! auth_status=$(timeout "$TIMEOUT_SECS" codex login status 2>&1); then
        log_error "ERROR: Codex CLI is not authenticated."
        log_error ""
        log_error "Run: codex login"
        log_error ""
        log_error "Or set OPENAI_API_KEY and run:"
        log_error "  printenv OPENAI_API_KEY | codex login --with-api-key"
        exit 3
    fi
    log_verbose "Auth: $auth_status"
fi

# Success
if [[ $VERBOSE -eq 1 ]]; then
    log "codex ready ($version)"
elif [[ $QUIET -eq 0 ]]; then
    log "codex ready"
fi

exit 0
