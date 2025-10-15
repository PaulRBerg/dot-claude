set allow-duplicate-variables := true
set allow-duplicate-recipes := true
set shell := ["bash", "-euo", "pipefail", "-c"]

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

# ---------------------------------------------------------------------------- #
#                                    SCRIPTS                                   #
# ---------------------------------------------------------------------------- #

# Show available commands
default:
    @just --list

# ---------------------------------------------------------------------------- #
#                                   PRETTIER                                   #
# ---------------------------------------------------------------------------- #

# Check Prettier formatting
[group("checks")]
prettier-check:
    nlx prettier --check "**/*.{json,jsonc,md,yaml,yml}"
alias pc := prettier-check

# Format using Prettier
[group("checks")]
prettier-write:
    nlx prettier --write "**/*.{json,jsonc,md,yaml,yml}"
alias pw := prettier-write

# ---------------------------------------------------------------------------- #
#                                    PYTHON                                    #
# ---------------------------------------------------------------------------- #

# Sync the Most Important Thing section across projects
[group("checks")]
sync-mit:
    python -u helpers/sync-most-important-thing.py

# Check Python files
[group("checks")]
ruff-check:
    ruff check .
alias rc := ruff-check

# Format Python files
[group("checks")]
ruff-write:
    ruff check --fix . && ruff format .
alias rw := ruff-write
