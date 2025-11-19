#!/usr/bin/env bash
#
# merge-settings.sh
#
# Merges multiple JSONC settings files from the settings/ directory into a single
# settings.json file. This script handles:
# - Parsing JSONC files (JSON with comments) using json5
# - Collecting and deduplicating permission arrays across all files
# - Merging non-permission top-level keys from all files
#
# Usage: merge-settings.sh

set -euo pipefail

# ---------------------------------------------------------------------------- #
#                                 CONFIGURATION                                #
# ---------------------------------------------------------------------------- #

# Navigate to the Claude directory
cd "$HOME/.claude"

# ---------------------------------------------------------------------------- #
#                              1. DISCOVER FILES                               #
# ---------------------------------------------------------------------------- #

# Find all .json and .jsonc files in settings/ directory (excluding settings.json)
# Files are sorted alphabetically to ensure consistent merge order
settings_files=$(fd --type f -e jsonc -e json . settings/ --exclude settings.json | sort)

if [ -z "$settings_files" ]; then
    echo "No settings files found in settings/ directory"
    exit 0
fi

# ---------------------------------------------------------------------------- #
#                             2. PARSE JSONC FILES                             #
# ---------------------------------------------------------------------------- #

# Parse all JSONC files to valid JSON using json5 in a single Node.js process
# The json5 tool allows comments and trailing commas in JSON files
# Using a single Node.js process is much faster than calling npx per file
# If a file fails to parse, fall back to empty object
parsed_json=$(npx -y -p json5 node -e "
const fs = require('fs');
const JSON5 = require('json5');
process.argv.slice(1).forEach(file => {
  try {
    console.log(JSON.stringify(JSON5.parse(fs.readFileSync(file, 'utf8'))));
  } catch {
    console.log('{}');
  }
});
" $settings_files)

# ---------------------------------------------------------------------------- #
#                               3. MERGE WITH JQ                               #
# ---------------------------------------------------------------------------- #

# Merge all parsed JSON files using jq
# The merge strategy is:
#   1. Collect all permission arrays from all files and deduplicate
#   2. Merge all other top-level keys (later values override earlier ones)
merged_json=$(echo "$parsed_json" | jq -s '
    # First, build the permissions object by collecting arrays from all files
    {
        permissions: {
            # Collect additionalDirectories from all files, flatten, and deduplicate
            additionalDirectories: ([.[].permissions.additionalDirectories // [] | .[] ] | unique),

            # Collect allow patterns from all files, flatten, and deduplicate
            allow: ([.[].permissions.allow // [] | .[] ] | unique),

            # Collect deny patterns from all files, flatten, and deduplicate
            deny: ([.[].permissions.deny // [] | .[] ] | unique)
        }
    } *
    # Then merge all non-permissions top-level keys from all files
    # Later files override earlier files for conflicting keys
    (reduce .[] as $item ({}; . * ($item | del(.permissions))))
')

# ---------------------------------------------------------------------------- #
#                              4. WRITE OUTPUT                                 #
# ---------------------------------------------------------------------------- #

# Write the merged JSON to settings.json
echo "$merged_json" > settings.json

echo "✓ Merged settings.json from JSONC files"
