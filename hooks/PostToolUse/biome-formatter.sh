#!/usr/bin/env bash
#
# Biome Auto-Formatter Hook
# Runs after Edit/Write/Serena MCP tools to auto-format TypeScript files
#
# Supported tools:
#   - Edit, Write (native Claude tools)
#   - mcp__serena__replace_symbol_body
#   - mcp__serena__insert_after_symbol
#   - mcp__serena__insert_before_symbol
#
# Exit code: Always 0 (never blocks Claude)
# Output: Silent (no context pollution)

set -euo pipefail

# Extract file path from various tool inputs
FILE_PATH=""

# Method 1: Direct file path (Edit/Write tools)
if [[ -n "${TOOL_INPUT_FILE_PATH:-}" ]]; then
    FILE_PATH="$TOOL_INPUT_FILE_PATH"
# Method 2: Relative path from Serena tools
elif [[ -n "${TOOL_INPUT_RELATIVE_PATH:-}" ]]; then
    if [[ -n "${CLAUDE_PROJECT_DIR:-}" ]]; then
        FILE_PATH="$CLAUDE_PROJECT_DIR/$TOOL_INPUT_RELATIVE_PATH"
    else
        FILE_PATH="$TOOL_INPUT_RELATIVE_PATH"
    fi
# Method 3: Parse from TOOL_CALL JSON (fallback)
elif [[ -n "${TOOL_CALL:-}" ]]; then
    # Try to extract relative_path from JSON
    RELATIVE_PATH=$(echo "$TOOL_CALL" | jq -r '.relative_path // empty' 2>/dev/null || true)
    if [[ -n "$RELATIVE_PATH" && "$RELATIVE_PATH" != "null" ]]; then
        if [[ -n "${CLAUDE_PROJECT_DIR:-}" ]]; then
            FILE_PATH="$CLAUDE_PROJECT_DIR/$RELATIVE_PATH"
        else
            FILE_PATH="$RELATIVE_PATH"
        fi
    fi
fi

# Exit early if no file path found
if [[ -z "$FILE_PATH" ]]; then
    exit 0
fi

# Exit early if not a TypeScript file
if [[ ! "$FILE_PATH" =~ \.(ts|tsx)$ ]]; then
    exit 0
fi

# Exit early if file doesn't exist (edge case)
if [[ ! -f "$FILE_PATH" ]]; then
    exit 0
fi

# Run Biome formatter silently
# - Suppress all output (2>/dev/null)
# - Always exit 0 (|| true) to never block Claude
biome check --apply "$FILE_PATH" 2>/dev/null || true

exit 0
