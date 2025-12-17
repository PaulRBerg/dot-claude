#!/usr/bin/env bash
# run-taze.sh - Run taze in non-interactive mode
#
# Usage: run-taze.sh [-r] [path]
#   -r    Enable recursive/monorepo mode
#
# Exit codes:
#   0 - Success (updates displayed)
#   1 - taze not installed
#   2 - No package.json found

set -euo pipefail

recursive=""
while getopts "r" opt; do
    case $opt in
        r) recursive="-r" ;;
        *) ;;
    esac
done
shift $((OPTIND - 1))

# Check taze availability
if ! command -v taze &>/dev/null; then
    cat >&2 <<'EOF'
ERROR: taze CLI is not installed.

Install taze globally:
  npm install -g taze

Or run via npx:
  npx taze

Documentation: https://github.com/antfu-collective/taze
EOF
    exit 1
fi

# Check for package.json
target_dir="${1:-.}"
if [[ ! -f "$target_dir/package.json" ]]; then
    echo "ERROR: No package.json found in $target_dir" >&2
    exit 2
fi

# Run taze major to show ALL available updates (including breaking)
# -l/--include-locked shows fixed versions (no ^ or ~)
cd "$target_dir"
# shellcheck disable=SC2086
taze major $recursive --include-locked 2>&1
