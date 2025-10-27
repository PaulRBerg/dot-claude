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
GLOBS_PRETTIER := "\"**/*.{json,jsonc,md,yaml,yml}\""

# ---------------------------------------------------------------------------- #
#                                    SCRIPTS                                   #
# ---------------------------------------------------------------------------- #

# Show available commands
default:
    @just --list

# Run all code checks
[group("checks")]
full-check:
    just prettier-check
    just ruff-check
alias fc := full-check

# Run all code fixes
[group("checks")]
full-write:
    just prettier-write
    just ruff-write
alias fw := full-write


# Check Prettier formatting
[group("checks")]
prettier-check +globs=GLOBS_PRETTIER:
    na prettier --check --cache {{ globs }}
alias pc := prettier-check

# Format using Prettier
[group("checks")]
prettier-write +globs=GLOBS_PRETTIER:
    na prettier --write --cache {{ globs }}
alias pw := prettier-write

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

# Sync the Most Important Thing section across projects
[group("checks")]
sync-mit:
    python -u helpers/sync-most-important-thing.py
