#!/usr/bin/env bash
#
# settings_drift.sh
#
# Detects drift between settings.json and its settings/**/*.jsonc sources.
# Regenerates the merged settings in a temporary HOME with helpers/merge_settings.sh
# (the same merge the install flow uses), then diffs the result against the live file,
# grouped by top-level key. Lines marked "-" exist only in the live file. Lines marked
# "+" exist only in the sources.
#
# Usage: settings_drift.sh [--self-test] [live-settings-file]
# Exit:  0 clean, 1 drift, 2 error
#
# Env:   SETTINGS_DRIFT_ROOT  directory holding settings/ and helpers/ (default: ~/.claude)

set -euo pipefail

root="${SETTINGS_DRIFT_ROOT:-$HOME/.claude}"
script_path="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"

run_drift() {
    local live="$1" tmp rc=0 key
    tmp=$(mktemp -d)
    trap 'rm -rf "$tmp"' RETURN

    [ -f "$live" ] || { echo "error: live file not found: $live" >&2; return 2; }

    # Regenerate in an isolated HOME so the real settings.json stays untouched.
    mkdir -p "$tmp/home/.claude"
    cp -R "$root/settings" "$tmp/home/.claude/settings"
    if ! HOME="$tmp/home" BUN_INSTALL_CACHE_DIR="${BUN_INSTALL_CACHE_DIR:-$HOME/.bun/install/cache}" \
        bash "$root/helpers/merge_settings.sh" >"$tmp/merge.log" 2>&1; then
        cat "$tmp/merge.log" >&2
        return 2
    fi
    local merged="$tmp/home/.claude/settings.json"

    jq -S . "$live" >"$tmp/live.json"
    jq -S . "$merged" >"$tmp/merged.json"

    while IFS= read -r key; do
        jq --arg k "$key" '.[$k] // "<absent>"' "$tmp/live.json" >"$tmp/a"
        jq --arg k "$key" '.[$k] // "<absent>"' "$tmp/merged.json" >"$tmp/b"
        if ! cmp -s "$tmp/a" "$tmp/b"; then
            rc=1
            echo "== $key"
            diff -U2 --label "live: $live" --label "sources: settings/" "$tmp/a" "$tmp/b" | tail -n +3 || true
        fi
    done < <(jq -rn --slurpfile a "$tmp/live.json" --slurpfile b "$tmp/merged.json" \
        '($a[0] + $b[0]) | keys[]')

    if [ "$rc" -eq 0 ]; then
        echo "No drift: $live matches settings/ sources."
    else
        echo
        echo "Drift found. Port each change made outside the sources into the owning settings/*.jsonc file, then rerun."
    fi
    return "$rc"
}

self_test() {
    local fx rc fail=0
    fx=$(mktemp -d)
    trap 'rm -rf "$fx"' RETURN
    mkdir -p "$fx/settings" "$fx/helpers"
    cp "$root/helpers/merge_settings.sh" "$fx/helpers/"
    printf '{"model":"opus",\n// comment\n"permissions":{"allow":["A"],"defaultMode":"plan"}}\n' >"$fx/settings/a.jsonc"
    printf '{"permissions":{"allow":["B"]}}\n' >"$fx/settings/b.jsonc"
    export SETTINGS_DRIFT_ROOT="$fx"

    # Clean case: live file equals the merge output.
    printf '{"model":"opus","permissions":{"allow":["A","B"],"defaultMode":"plan"}}\n' >"$fx/live.json"
    rc=0; "$script_path" "$fx/live.json" >/dev/null || rc=$?
    [ "$rc" -eq 0 ] || { echo "FAIL: clean case exited $rc"; fail=1; }

    # Drift case: extra key and changed permission list.
    printf '{"model":"opus","extra":1,"permissions":{"allow":["A"],"defaultMode":"plan"}}\n' >"$fx/live.json"
    rc=0; "$script_path" "$fx/live.json" >"$fx/out" || rc=$?
    [ "$rc" -eq 1 ] || { echo "FAIL: drift case exited $rc"; fail=1; }
    grep -q '^== extra' "$fx/out" && grep -q '^== permissions' "$fx/out" \
        || { echo "FAIL: drift output lacks expected key groups"; fail=1; }

    [ "$fail" -eq 0 ] && echo "self-test passed"
    return "$fail"
}

case "${1:-}" in
    --self-test) self_test ;;
    *) run_drift "${1:-$root/settings.json}" ;;
esac
