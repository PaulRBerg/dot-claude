set allow-duplicate-variables
set allow-duplicate-recipes
set shell := ["bash", "-euo", "pipefail", "-c"]
set unstable

# ---------------------------------------------------------------------------- #
#                                 DEPENDENCIES                                 #
# ---------------------------------------------------------------------------- #

# Bun: https://bun.sh
bun := require("bun")

# UV: https://github.com/astral-sh/uv
uv := require("uv")

# ---------------------------------------------------------------------------- #
#                                   CONSTANTS                                  #
# ---------------------------------------------------------------------------- #

GLOBS_PRETTIER := "\"**/*.{json,jsonc,yaml,yml}\""

# ---------------------------------------------------------------------------- #
#                                   COMMANDS                                   #
# ---------------------------------------------------------------------------- #

# Show available commands
default:
    @just --list

# Install all dependencies for .claude
install:
    bun install
    uv sync --all-extras --dev
    just install-utils

# Install CLI utilities (skipped in CI)
[script]
install-utils:
    if [ "$CI" = "true" ]; then
        echo "Skipping brew install in CI environment"
    else
        brew install bat delta eza fd fzf gh gum jq just rg ruff uv yq
    fi

# ---------------------------------------------------------------------------- #
#                                   HELPERS                                    #
# ---------------------------------------------------------------------------- #

# Add Bash permission to project's local Claude settings (run from project dir)
[no-cd]
[group("helpers")]
@allow-bash:
    uv run helpers/allow_all_bash.py
alias ab := allow-bash

# Clean ~/.claude.json by removing conversation history
[group("helpers")]
@cleanup:
    uv run helpers/cleanup.py

# Manage claude-island hooks (add|remove|status)
[group("helpers")]
@manage-claude-island action="status":
    uv run helpers/manage-claude-island.py {{ action }}
alias mci := manage-claude-island

# Merge JSONC settings files into settings.json
[group("helpers")]
@merge-settings:
    gum spin --spinner dot --title "Merging JSONC settings..." -- bash -c './helpers/merge_settings.sh'
alias ms := merge-settings

# Sync a section from template across projects (default: ## Lint Rules)
[group("helpers")]
sync-section section="":
    uv run helpers/sync_context_section.py --section "{{ section }}"
alias ss := sync-section

# Update all plugin marketplaces and refresh metadata
[group("helpers")]
@update-plugins:
    uv run helpers/update_plugins.py
alias up := update-plugins

# ---------------------------------------------------------------------------- #
#                                    CHECKS                                    #
# ---------------------------------------------------------------------------- #

# Run all code checks
[group("checks")]
@full-check:
    just _run-with-status mdformat-check
    just _run-with-status prettier-check
    just _run-with-status ruff-check
    just _run-with-status pyright-check
    echo ""
    echo -e '{{ GREEN }}All code checks passed!{{ NORMAL }}'
alias fc := full-check

# Run all code fixes
[group("checks")]
@full-write:
    just _run-with-status mdformat-write
    just _run-with-status prettier-write
    just _run-with-status ruff-write
    echo ""
    echo -e '{{ GREEN }}All code fixes applied!{{ NORMAL }}'
alias fw := full-write

# Check Markdown formatting (exclusions in .mdformat.toml)
[group("checks")]
@mdformat-check +paths=".":
    uv run mdformat --check {{ paths }}
alias mc := mdformat-check

# Format Markdown files (exclusions in .mdformat.toml)
[group("checks")]
@mdformat-write +paths=".":
    uv run mdformat {{ paths }}
alias mw := mdformat-write

# Check Prettier formatting
[group("checks")]
@prettier-check +globs=GLOBS_PRETTIER:
    bun prettier --check --cache {{ globs }}
alias pc := prettier-check

# Format using Prettier
[group("checks")]
@prettier-write +globs=GLOBS_PRETTIER:
    bun prettier --write --cache --log-level warn {{ globs }}
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
@test *args:
    just test-hooks {{ args }}
alias t := test

# Run pytest tests
[group("test")]
@test-hooks *args:
    uv run pytest hooks {{ args }}
alias th := test-hooks

# ---------------------------------------------------------------------------- #
#                                   UTILITIES                                  #
# ---------------------------------------------------------------------------- #

# Private recipe to run a check with formatted output
@_run-with-status recipe:
    echo ""
    echo -e '{{ CYAN }}→ Running {{ recipe }}...{{ NORMAL }}'
    just {{ recipe }}
    echo -e '{{ GREEN }}✓ {{ recipe }} completed{{ NORMAL }}'
alias rws := _run-with-status
