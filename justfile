set allow-duplicate-variables
set allow-duplicate-recipes
set shell := ["bash", "-euo", "pipefail", "-c"]
set unstable

# ---------------------------------------------------------------------------- #
#                                 DEPENDENCIES                                 #
# ---------------------------------------------------------------------------- #

# Claude Code
claude := require("claude")

# Ni: https://github.com/antfu-collective/ni
ni := require("ni")
na := require("na")
nlx := require("nlx")

# Ruff: https://github.com/astral-sh/ruff
ruff := require("ruff")

# UV: https://github.com/astral-sh/uv
uv := require("uv")
uvx := require("uvx")

# Pytest: https://github.com/pytest-dev/pytest
pytest := require("pytest")

# Modern CLI Tools
bat := require("bat")
delta := require("delta")
eza := require("eza")
fd := require("fd")
fzf := require("fzf")
gh := require("gh")
jq := require("jq")
rg := require("rg")
yq := require("yq")

# ---------------------------------------------------------------------------- #
#                                   CONSTANTS                                  #
# ---------------------------------------------------------------------------- #

CLAUDE_DIR := "$HOME/.claude"
GLOBS_PRETTIER := "\"**/*.{json,jsonc,md,yaml,yml}\""
SETTINGS_FILES := ```
    arr=(
        "settings/basics.jsonc"
        "settings/permissions.jsonc"
        "settings/hooks.jsonc"
    )
    echo "${arr[*]}"
```


# ---------------------------------------------------------------------------- #
#                                   COMMANDS                                   #
# ---------------------------------------------------------------------------- #

# Show available commands
default:
    @just --list

# Merge JSONC settings files into settings.json
[group("settings")]
[script]
merge-settings:
    cd {{ CLAUDE_DIR }}
    # Parse JSONC files and merge with jq
    for file in {{ SETTINGS_FILES }}; do
        npx -y json5@latest "$file" # Outputs clean JSON to STDOUT
    done | jq -s 'reduce .[] as $item ({}; . * $item)' > settings.json
    echo "✓ Merged settings.json from JSONC files"
alias ms := merge-settings

# Sync the Most Important Thing section across projects
sync-mit:
    python -u helpers/sync-most-important-thing.py

# ---------------------------------------------------------------------------- #
#                                    CHECKS                                    #
# ---------------------------------------------------------------------------- #

# Run all code checks
[group("checks")]
@full-check:
    just prettier-check
    just ruff-check
alias fc := full-check

# Run all code fixes
[group("checks")]
@full-write:
    just prettier-write
    just ruff-write
alias fw := full-write

# Check Prettier formatting
[group("checks")]
@prettier-check +globs=GLOBS_PRETTIER:
    na prettier --check --cache {{ globs }}
alias pc := prettier-check

# Format using Prettier
[group("checks")]
@prettier-write +globs=GLOBS_PRETTIER:
    na prettier --write --cache {{ globs }}
alias pw := prettier-write

# Check Python files
[group("checks")]
@ruff-check:
    ruff check .
alias rc := ruff-check

# Format Python files
[group("checks")]
@ruff-write:
    ruff check --fix .
    ruff format .
alias rw := ruff-write

# ---------------------------------------------------------------------------- #
#                                     TESTS                                    #
# ---------------------------------------------------------------------------- #

# Run all tests
[group("test")]
@test:
    just test-hooks
alias t := test

# Run pytest tests
[group("test")]
@test-hooks:
    pytest hooks/ -v
alias th := test-hooks
