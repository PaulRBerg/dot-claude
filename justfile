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

# Check Prettier formatting
[group("lint")]
prettier-check:
    nlx prettier --check "**/*.{json,jsonc,md,yaml,yml}"
alias pc := prettier-check

# Format using Prettier
[group("lint")]
prettier-write:
    nlx prettier --write "**/*.{json,jsonc,md,yaml,yml}"
alias pw := prettier-write
