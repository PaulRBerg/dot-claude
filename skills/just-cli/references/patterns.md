# Justfile Patterns & Conventions

Established patterns and conventions for organizing justfiles, based on real-world usage across multiple projects.

## Section Headers

Use centered ASCII art headers to organize justfiles:

```just
# ---------------------------------------------------------------------------- #
#                                 DEPENDENCIES                                 #
# ---------------------------------------------------------------------------- #
```

### Standard Sections (in order)

1. **DEPENDENCIES** - Required tools with documentation URLs
2. **ENVIRONMENT VARS** - Exported environment variables
3. **CONSTANTS** - Glob patterns, paths, configuration values
4. **COMMANDS / RECIPES** - Main public recipes
5. **CHECKS** - Code quality and validation recipes
6. **TESTS** - Testing recipes
7. **UTILITIES / INTERNAL HELPERS** - Private helper recipes

## Dependencies Section

Document required tools with URLs:

```just
# ---------------------------------------------------------------------------- #
#                                 DEPENDENCIES                                 #
# ---------------------------------------------------------------------------- #

# Bun: https://bun.sh
bun := require("bun")

# UV: https://github.com/astral-sh/uv
uv := require("uv")

# Ni: https://github.com/antfu-collective/ni
na := require("na")
ni := require("ni")
nlx := require("nlx")

# Pnpm: https://github.com/pnpm/pnpm
pnpm := require("pnpm")
```

**Common tool sets:**

| Ecosystem | Tools                            |
| --------- | -------------------------------- |
| Node.js   | `ni`, `na`, `nlx`, `pnpm`, `bun` |
| Python    | `uv`, `ruff`, `pyright`          |
| Utilities | `jq`, `yq`, `fd`, `rg`           |

## Constants Section

### Glob Patterns

Quote glob patterns for shell expansion:

```just
# ---------------------------------------------------------------------------- #
#                                   CONSTANTS                                  #
# ---------------------------------------------------------------------------- #

GLOBS_PRETTIER := "\"**/*.{json,jsonc,yaml,yml}\""
GLOBS_SOLIDITY := "{scripts,src,tests}/**/*.sol"
GLOBS_CLEAN := "**/{.logs,bindings,build,generated}"
GLOBS_CLEAN_IGNORE := "!graph/common/bindings"
```

### Environment Variables

```just
export LOG_LEVEL := env("LOG_LEVEL", "info")
export NODE_ENV := env("NODE_ENV", "development")
```

### Path References

```just
JUST_DIR := justfile_dir()
CONFIG_DIR := join(justfile_dir(), "config")
```

## Recipe Groups

Use `[group()]` attribute for organized `just --list` output:

```just
[group("checks")]     # Linting, formatting, type checking
[group("codegen")]    # Code generation
[group("test")]       # Testing
[group("cli")]        # CLI command helpers
[group("dev")]        # Development utilities
[group("deploy")]     # Deployment recipes
[group("print")]      # Debug/print utilities
```

**Multiple groups per recipe:**

```just
[group("codegen")]
[group("envio")]
codegen-envio:
    ./codegen.sh
```

## Alias Conventions

Define aliases immediately after recipe names for discoverability:

```just
# Run all code checks
[group("checks")]
@full-check:
    just _run-with-status biome-check
alias fc := full-check
```

### Standard Aliases

| Recipe             | Alias | Purpose          |
| ------------------ | ----- | ---------------- |
| `full-check`       | `fc`  | Run all checks   |
| `full-write`       | `fw`  | Apply all fixes  |
| `biome-check`      | `bc`  | Biome check      |
| `biome-write`      | `bw`  | Biome fix        |
| `biome-lint`       | `bl`  | Biome lint only  |
| `prettier-check`   | `pc`  | Prettier check   |
| `prettier-write`   | `pw`  | Prettier fix     |
| `mdformat-check`   | `mc`  | Markdown check   |
| `mdformat-write`   | `mw`  | Markdown fix     |
| `ruff-check`       | `rc`  | Ruff check       |
| `ruff-write`       | `rw`  | Ruff fix         |
| `tsc-check`        | `tc`  | TypeScript check |
| `tsc-build`        | `tb`  | TypeScript build |
| `pyright-check`    | `pyc` | Pyright check    |
| `knip-check`       | `kc`  | Knip check       |
| `knip-write`       | `kw`  | Knip fix         |
| `test`             | `t`   | Run tests        |
| `test-unit`        | `tu`  | Unit tests       |
| `test-ui`          | `tui` | UI tests         |
| `build`            | `b`   | Build project    |
| `clean`            | `c`   | Clean artifacts  |
| `install`          | `i`   | Install deps     |
| `deploy`           | `d`   | Deploy           |
| `_run-with-status` | `rws` | Status helper    |

## Helper Patterns

### Run-With-Status Pattern

Display formatted status during multi-step workflows:

```just
# Private recipe to run a check with formatted output
@_run-with-status recipe *args:
    echo ""
    echo -e '{{ CYAN }}→ Running {{ recipe }}...{{ NORMAL }}'
    just {{ recipe }} {{ args }}
    echo -e '{{ GREEN }}✓ {{ recipe }} completed{{ NORMAL }}'
alias rws := _run-with-status
```

**Usage in aggregate recipes:**

```just
[group("checks")]
@full-check:
    just _run-with-status biome-check
    just _run-with-status prettier-check
    just _run-with-status tsc-check
    echo ""
    echo -e '{{ GREEN }}All code checks passed!{{ NORMAL }}'
alias fc := full-check
```

### For-Each Pattern

Iterate over a set of items:

```just
[private]
[script("bash")]
protocol-for-each recipe protocol:
    if [ "{{ protocol }}" = "all" ]; then
        just concurrent-protocols \
            "just {{ recipe }} airdrops" \
            "just {{ recipe }} flow" \
            "just {{ recipe }} lockup"
    else
        just {{ recipe }} {{ protocol }}
    fi
```

### Concurrent Execution Pattern

Run multiple commands in parallel:

```just
[private]
@concurrent-protocols cmd1 cmd2 cmd3:
    pnpm concurrently --group \
        -n "airdrops,flow,lockup" \
        -c "blue,green,yellow" \
        "{{ cmd1 }}" \
        "{{ cmd2 }}" \
        "{{ cmd3 }}"
```

### CLI Helper Pattern

Centralize CLI tool invocation:

```just
[private]
@cli *args:
    pnpm tsx cli/index.ts {{ args }}

[group("cli")]
@export-schema:
    just cli export-schema
```

## Check/Write Patterns

### Biome (TypeScript/JavaScript)

```just
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
```

### Prettier (JSON/YAML/Markdown)

```just
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
```

### mdformat (Markdown)

```just
# Check Markdown formatting
[group("checks")]
@mdformat-check +paths=".":
    mdformat --check {{ paths }}
alias mc := mdformat-check

# Format Markdown files
[group("checks")]
@mdformat-write +paths=".":
    mdformat {{ paths }}
alias mw := mdformat-write
```

### Ruff (Python)

```just
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

# Check Python type hints
[group("checks")]
@pyright-check:
    uv run pyright
alias pyc := pyright-check
```

### TypeScript Checks

```just
# Type check with TypeScript
[group("checks")]
[no-cd]
@type-check project="tsconfig.json":
    na tsgo --noEmit --project {{ project }}
alias tc := tsc-check
```

## Full Check/Write Pattern

Aggregate all checks with status reporting:

```just
# Run all code checks
[group("checks")]
[no-cd]
@full-check:
    just _run-with-status biome-check
    just _run-with-status prettier-check
    just _run-with-status tsc-check
    echo ""
    echo '{{ GREEN }}All code checks passed!{{ NORMAL }}'
alias fc := full-check

# Run all code fixes
[group("checks")]
[no-cd]
@full-write:
    just _run-with-status biome-write
    just _run-with-status prettier-write
    echo ""
    echo '{{ GREEN }}All code fixes applied!{{ NORMAL }}'
alias fw := full-write
```

## Default Recipe

Always define a default recipe that shows available commands:

```just
# Show available commands
default:
    @just --list
```

Alternative: Run primary action by default:

```just
# Run all checks by default
default: full-check
```

## Test Recipes

```just
# Run all tests
[group("test")]
@test *args:
    just test-unit {{ args }}
alias t := test

# Run unit tests
[group("test")]
test-unit *args:
    bun vitest run --hideSkippedTests {{ args }}
alias tu := test-unit

# Run tests with UI
[group("test")]
test-ui *args:
    bun vitest --hideSkippedTests --ui {{ args }}
alias tui := test-ui
```

## Build & Clean Recipes

```just
# Build the project
@build:
    just clean
    just tsc-build
alias b := build

# Clean build artifacts
@clean globs=GLOBS_CLEAN:
    bunx del-cli "{{ globs }}"
    echo "✅ Cleaned build files"

# Clear node_modules
[confirm("Delete all node_modules? Y/n")]
[no-cd]
clean-modules +globs="node_modules **/node_modules":
    nlx del-cli {{ globs }}
```

## Install Recipes

```just
# Install dependencies
[no-cd]
install *args:
    ni {{ args }}

# Install with conditional CI behavior
[script]
install-utils:
    if [[ "$CI" == "true" ]]; then
        echo "Skipping brew install in CI"
    else
        brew install bat delta eza fd fzf jq just rg
    fi
```

## Monorepo Patterns

### Module Per Package

```just
mod client "apps/client"
mod server "apps/server"
mod shared "packages/shared"
```

### No-CD for Cross-Package Commands

```just
[no-cd]
build-all:
    just client::build
    just server::build
```

### Shared Recipes via Import

```just
# apps/client/justfile
import "../../just/shared.just"

build: shared-setup
    npm run build
```

## Script Block Patterns

### Multi-line Bash

```just
[script("bash")]
deploy chain_slug:
    set -e
    case {{ chain_slug }} in
        mainnet)
            DEPLOY_URL="https://prod.example.com"
            ;;
        testnet)
            DEPLOY_URL="https://test.example.com"
            ;;
        *)
            echo "Unknown chain: {{ chain_slug }}"
            exit 1
            ;;
    esac
    curl -X POST "$DEPLOY_URL/deploy"
```

### Conditional TUI Mode

```just
[script("bash")]
envio command tui_mode="tui_on" *args:
    set -a
    if [ "{{ tui_mode }}" = "tui_off" ]; then
        TUI_OFF=true
    fi
    pnpm envio {{ command }} {{ args }}
```

## Import Organization

### Settings First

```just
import "./just/settings.just"
import "./just/base.just"
import "./just/npm.just"
```

### Devkit Pattern

```just
# See https://github.com/sablier-labs/devkit/blob/main/just/base.just
import "./node_modules/@sablier/devkit/just/base.just"
import "./node_modules/@sablier/devkit/just/npm.just"
```

### Local Overrides Last

```just
import "./just/base.just"
import? "./just/local.just"  # Optional local overrides
```

## Attribute Combinations

### Private Group Recipe

```just
[group("internal")]
[private]
_helper:
    echo "helper"
```

### Confirmed No-CD Script

```just
[no-cd]
[script("bash")]
[confirm("Deploy to production?")]
deploy-prod:
    set -e
    npm run build
    aws s3 sync dist/ s3://prod-bucket/
```

### Documented Group Recipe

```just
[doc("Generate TypeScript types from GraphQL schema")]
[group("codegen")]
codegen-types:
    graphql-codegen
```

## Environment Variable Patterns

### Export with Default

```just
export LOG_LEVEL := env("LOG_LEVEL", "info")
export NODE_ENV := env("NODE_ENV", "development")
```

### Load from .env

```just
set dotenv-load

# Or specify path
set dotenv-path := ".env.local"
```

### Per-Recipe Environment

```just
test-integration:
    DATABASE_URL="postgres://localhost/test" npm run test:integration
```

## Error Handling

### Ignore Specific Errors

```just
cleanup:
    -rm -rf dist/
    -rm -rf coverage/
    echo "Cleanup complete"
```

### Assert Preconditions

```just
deploy:
    {{ assert(path_exists("dist/"), "Run 'just build' first") }}
    aws s3 sync dist/ s3://bucket/
```

### Graceful Fallbacks

```just
@version:
    git describe --tags 2>/dev/null || echo "v0.0.0-dev"
```
