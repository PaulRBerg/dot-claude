#!/usr/bin/env bash
# Sync enabledPlugins from settings.json to settings/plugins.jsonc (additive)

set -euo pipefail

ROOT="$HOME/.claude/settings.json"
PLUGINS="$HOME/.claude/settings/plugins.jsonc"

[[ -f "$ROOT" && -f "$PLUGINS" ]] || exit 0

root_plugins=$(jq '.enabledPlugins // {}' "$ROOT") || {
  echo "Error: Failed to parse $ROOT" >&2
  exit 1
}

local_plugins=$(grep -v '^\s*//' "$PLUGINS" | jq '.enabledPlugins // {}') || {
  echo "Error: Failed to parse $PLUGINS" >&2
  exit 1
}

# Additive merge: root + local (local wins on conflicts, new keys from root added)
merged=$(jq -n --argjson r "$root_plugins" --argjson l "$local_plugins" \
  '$r + $l | to_entries | sort_by(.key) | from_entries') || {
  echo "Error: Failed to merge plugins" >&2
  exit 1
}

jq -n --argjson p "$merged" '{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  enabledPlugins: $p
}' > "$PLUGINS"
