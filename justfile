set allow-duplicate-variables
set allow-duplicate-recipes
set shell := ["bash", "-euo", "pipefail", "-c"]
set unstable

# ---------------------------------------------------------------------------- #
#                             PROJECT DEPENDENCIES                             #
# ---------------------------------------------------------------------------- #

# Bun: https://bun.sh
bun := require("bun")

# UV: https://github.com/astral-sh/uv
uv := require("uv")

# ---------------------------------------------------------------------------- #
#                                   CONSTANTS                                  #
# ---------------------------------------------------------------------------- #

GLOBS_PRETTIER := "\"**/*.{json,jsonc,md,yaml,yml}\""

# ANSI color codes for formatted output
CYAN := '\033[0;36m'
GREEN := '\033[0;32m'
NORMAL := '\033[0m'


# ---------------------------------------------------------------------------- #
#                                   COMMANDS                                   #
# ---------------------------------------------------------------------------- #

# Show available commands
default:
    @just --list

# Merge JSONC settings files into settings.json
[group("settings")]
@merge-settings:
    gum spin --spinner dot --title "Merging JSONC settings..." -- bash -c './helpers/merge_settings.sh'
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
    just _run-with-status prettier-check
    just _run-with-status ruff-check
    just _run-with-status pyright-check
    echo ""
    echo -e '{{ GREEN }}All code checks passed!{{ NORMAL }}'
alias fc := full-check

# Run all code fixes
[group("checks")]
@full-write:
    just _run-with-status prettier-write
    just _run-with-status ruff-write
    echo ""
    echo -e '{{ GREEN }}All code fixes applied!{{ NORMAL }}'
alias fw := full-write

# Check Prettier formatting
[group("checks")]
@prettier-check +globs=GLOBS_PRETTIER:
    bun prettier --check --cache {{ globs }}
alias pc := prettier-check

# Format using Prettier
[group("checks")]
@prettier-write +globs=GLOBS_PRETTIER:
    bun prettier --write --cache {{ globs }}
alias pw := prettier-write

# Check Python type hints
[group("checks")]
@pyright-check:
    uv run pyright
alias pyc := pyright-check

# Check Python files
[group("checks")]
@ruff-check:
    uv run ruff check .
alias rc := ruff-check

# Format Python files
[group("checks")]
@ruff-write:
    uv run ruff check --fix .
    uv run ruff format .
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
    uv run pytest hooks/ -v
alias th := test-hooks

# ---------------------------------------------------------------------------- #
#                                   UTILITIES                                  #
# ---------------------------------------------------------------------------- #

# Private recipe to run a check with formatted output
[no-cd]
@_run-with-status recipe:
    echo ""
    echo -e '{{ CYAN }}→ Running {{ recipe }}...{{ NORMAL }}'
    just {{ recipe }}
    echo -e '{{ GREEN }}✓ {{ recipe }} completed{{ NORMAL }}'
alias rws := _run-with-status
