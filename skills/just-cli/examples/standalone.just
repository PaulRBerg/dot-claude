set allow-duplicate-recipes
set allow-duplicate-variables
set shell := ["bash", "-euo", "pipefail", "-c"]
set unstable

# ---------------------------------------------------------------------------- #
#                                 DEPENDENCIES                                 #
# ---------------------------------------------------------------------------- #

# Bun: https://bun.sh
bun := require("bun")

# Ni: https://github.com/antfu-collective/ni
na := require("na")
ni := require("ni")
nlx := require("nlx")

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

# Install dependencies
[no-cd]
install *args:
    ni {{ args }}
alias i := install

# Build the project
@build:
    just clean
    just tsc-build
alias b := build

# Clean build artifacts
@clean:
    bunx del-cli dist
    echo "✅ Cleaned build files"

# ---------------------------------------------------------------------------- #
#                                    CHECKS                                    #
# ---------------------------------------------------------------------------- #

# Run all code checks
[group("checks")]
[no-cd]
@full-check:
    just _run-with-status biome-check
    just _run-with-status prettier-check
    just _run-with-status tsc-check
    echo ""
    echo -e '{{ GREEN }}All code checks passed!{{ NORMAL }}'
alias fc := full-check

# Run all code fixes
[group("checks")]
[no-cd]
@full-write:
    just _run-with-status biome-write
    just _run-with-status prettier-write
    echo ""
    echo -e '{{ GREEN }}All code fixes applied!{{ NORMAL }}'
alias fw := full-write

# Check code with Biome
[group("checks")]
[no-cd]
@biome-check +globs=".":
    na biome check {{ globs }}
alias bc := biome-check

# Lint code with Biome
[group("checks")]
[no-cd]
@biome-lint +globs=".":
    na biome lint {{ globs }}
alias bl := biome-lint

# Fix code with Biome
[group("checks")]
[no-cd]
@biome-write +globs=".":
    na biome check --write {{ globs }}
    na biome lint --unsafe --write --only correctness/noUnusedImports {{ globs }}
alias bw := biome-write

# Check Prettier formatting
[group("checks")]
[no-cd]
@prettier-check +globs=GLOBS_PRETTIER:
    na prettier --check --cache --no-error-on-unmatched-pattern {{ globs }}
alias pc := prettier-check

# Format using Prettier
[group("checks")]
[no-cd]
@prettier-write +globs=GLOBS_PRETTIER:
    na prettier --write --cache --no-error-on-unmatched-pattern {{ globs }}
alias pw := prettier-write

# Type check with TypeScript
[group("checks")]
[no-cd]
@type-check compiler="tsc" project="tsconfig.json":
    na {{ compiler }} --noEmit --project {{ project }}
alias tc := type-check

# ---------------------------------------------------------------------------- #
#                                     TESTS                                    #
# ---------------------------------------------------------------------------- #

# Run all tests
[group("test")]
test *args:
    bun vitest run --hideSkippedTests {{ args }}
alias t := test

# Run tests with UI
[group("test")]
test-ui *args:
    bun vitest --hideSkippedTests --ui {{ args }}
alias tui := test-ui

# ---------------------------------------------------------------------------- #
#                                   UTILITIES                                  #
# ---------------------------------------------------------------------------- #

# Private recipe to run a check with formatted output
[no-cd]
@_run-with-status recipe *args:
    echo ""
    echo -e '{{ CYAN }}→ Running {{ recipe }}...{{ NORMAL }}'
    just {{ recipe }} {{ args }}
    echo -e '{{ GREEN }}✓ {{ recipe }} completed{{ NORMAL }}'
alias rws := _run-with-status
