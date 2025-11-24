# Settings Management

## Overview

The `settings.json` file is automatically generated from modular JSONC source files in this directory. **Do not edit
`settings.json` directly** - your changes will be overwritten.

## How It Works

### Source Files (edit these)

- `settings/basics.jsonc` - Basic configuration, environment, status line
- `settings/hooks.jsonc` - Event hooks configuration
- `settings/plugins.jsonc` - Enabled plugins
- `settings/permissions/*.jsonc` - Permission rules organized by category

### Generated File (don't edit)

- `settings.json` - Merged output (gitignored, auto-regenerated)

### Auto-regeneration

The `settings.json` file is automatically regenerated:

- **On every commit** - Pre-commit hook runs `helpers/merge_settings.sh`
- **After npm install** - `package.json` prepare script
- **Manually** - Run `just merge-settings` or `bash helpers/merge_settings.sh`

### Merge Logic

The merge script (`helpers/merge_settings.sh`):

1. Discovers all `.jsonc` and `.json` files in `settings/` (sorted alphabetically)
2. Parses JSONC to JSON (strips comments, allows trailing commas)
3. Merges with special handling:
   - **Permissions arrays**: Deduplicated across all files (`additionalDirectories`, `allow`, `deny`)
   - **Other keys**: Later files override earlier files
   - **Schema field**: Removed from output
4. Writes merged JSON to `settings.json`

## Editing Workflow

1. Edit the appropriate `.jsonc` file in `settings/` or `settings/permissions/`
2. (Optional) Run `just merge-settings` to preview changes
3. Commit your changes - `settings.json` regenerates automatically
4. Push - other developers' `settings.json` will regenerate on their machines

## Why JSONC?

JSONC (JSON with Comments) allows:

- `// comments` and `/* block comments */`
- Trailing commas
- Better documentation inline with configuration

## Local Overrides

Machine-specific settings go in `.claude/settings.local.json` (gitignored, not merged).
