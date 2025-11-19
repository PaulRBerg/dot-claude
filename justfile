set allow-duplicate-variables
set allow-duplicate-recipes
set shell := ["bash", "-euo", "pipefail", "-c"]
set unstable

# ---------------------------------------------------------------------------- #
#                             PROJECT DEPENDENCIES                             #
# ---------------------------------------------------------------------------- #

# Bun: https://bun.sh
bun := require("bun")

# Claude Code
claude := require("claude")

# Gum: https://github.com/charmbracelet/gum
gum := require("gum")

# JQ: https://github.com/jqlang/jq
jq := require("jq")

# Ni: https://github.com/antfu-collective/ni
ni := require("ni")
na := require("na")
nlx := require("nlx")

# Node: https://nodejs.org
node := require("node")
npm := require("npm")
npx := require("npx")

# Ruff: https://github.com/astral-sh/ruff
ruff := require("ruff")

# UV: https://github.com/astral-sh/uv
uv := require("uv")
uvx := require("uvx")

# ---------------------------------------------------------------------------- #
#                                  MODERN CLI                                  #
# ---------------------------------------------------------------------------- #

bat := require("bat")
delta := require("delta")
eza := require("eza")
fd := require("fd")
fzf := require("fzf")
gh := require("gh")
rg := require("rg")
yq := require("yq")

# ---------------------------------------------------------------------------- #
#                                   CONSTANTS                                  #
# ---------------------------------------------------------------------------- #

CLAUDE_DIR := "$HOME/.claude"
GLOBS_PRETTIER := "\"**/*.{json,jsonc,md,yaml,yml}\""


# ---------------------------------------------------------------------------- #
#                                   COMMANDS                                   #
# ---------------------------------------------------------------------------- #

# Show available commands
default:
    @just --list

# Merge JSONC settings files into settings.json
[group("settings")]
@merge-settings:
    gum spin --spinner dot --title "Merging JSONC settings..." -- bash -c './helpers/merge-settings.sh'
alias ms := merge-settings

# Sync a section from template across projects (default: ## Lint Rules)
sync-section section="":
    uv run -u helpers/sync_context_section.py --section "{{ section }}"
alias ss := sync-section

# ---------------------------------------------------------------------------- #
#                                    CHECKS                                    #
# ---------------------------------------------------------------------------- #

# Run all code checks
[group("checks")]
@full-check:
    just prettier-check
    just ruff-check
    just pyright-check
alias fc := full-check

# Run all code fixes
[group("checks")]
@full-write:
    just prettier-write
    just ruff-write
    just pyright-fix
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

# Check Python type hints
[group("checks")]
@pyright-check:
    uv run pyright
alias pyc := pyright-check

# Type check Python files (pyright has no fix mode)
[group("checks")]
@pyright-fix:
    uv run pyright
alias pyf := pyright-fix

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
