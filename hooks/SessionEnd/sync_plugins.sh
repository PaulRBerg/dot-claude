#!/usr/bin/env bash
# Sync enabledPlugins from settings.json to settings/plugins.jsonc (additive)

ROOT="$HOME/.claude/settings.json"
PLUGINS="$HOME/.claude/settings/plugins.jsonc"

[[ -f "$ROOT" && -f "$PLUGINS" ]] || exit 0

root_plugins=$(jq '.enabledPlugins // {}' "$ROOT")
local_plugins=$(grep -v '^\s*//' "$PLUGINS" | jq '.enabledPlugins // {}')

# Additive merge: root + local (local wins on conflicts, new keys from root added)
merged=$(jq -n --argjson r "$root_plugins" --argjson l "$local_plugins" \
  '$r + $l | to_entries | sort_by(.key) | from_entries')

jq -n --argjson p "$merged" '{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  enabledPlugins: $p
}' > "$PLUGINS"
