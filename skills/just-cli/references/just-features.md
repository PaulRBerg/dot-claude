# Just Features Reference

Comprehensive reference for Just command runner features, settings, modules, attributes, constants, and functions.

## Settings

Settings configure global behavior and must appear at the top of the justfile.

### Boolean Settings

Enable with `set NAME` or `set NAME := true`:

| Setting                     | Description                                          |
| --------------------------- | ---------------------------------------------------- |
| `allow-duplicate-recipes`   | Allow later recipes to override earlier ones         |
| `allow-duplicate-variables` | Allow later variables to override earlier ones       |
| `dotenv-load`               | Load `.env` file automatically                       |
| `dotenv-required`           | Error if `.env` file is missing                      |
| `export`                    | Export all variables as environment variables        |
| `fallback`                  | Search parent directories for justfile               |
| `ignore-comments`           | Don't print comments in recipe listings              |
| `positional-arguments`      | Pass recipe arguments as $1, $2, etc.                |
| `quiet`                     | Don't echo recipe lines                              |
| `unstable`                  | Enable unstable features (modules, script attribute) |
| `windows-powershell`        | Use PowerShell on Windows                            |
| `windows-shell`             | Use cmd.exe on Windows                               |

### Value Settings

| Setting             | Example                              | Description                     |
| ------------------- | ------------------------------------ | ------------------------------- |
| `shell`             | `["bash", "-euo", "pipefail", "-c"]` | Shell and arguments for recipes |
| `dotenv-filename`   | `".env.local"`                       | Custom dotenv filename          |
| `dotenv-path`       | `"config/.env"`                      | Custom dotenv path              |
| `tempdir`           | `"/tmp/just"`                        | Temporary file directory        |
| `working-directory` | `"src"`                              | Default working directory       |

### Recommended Settings

```just
set allow-duplicate-recipes
set allow-duplicate-variables
set shell := ["bash", "-euo", "pipefail", "-c"]
set unstable
```

**Shell flags explained:**

- `-e`: Exit immediately on error
- `-u`: Treat unset variables as errors
- `-o pipefail`: Pipeline fails if any command fails
- `-c`: Execute following string as command

## Modules & Imports

### Imports

Include another justfile's contents directly:

```just
# Required import (error if missing)
import "path/to/file.just"
import "./just/settings.just"

# Optional import (no error if missing)
import? "local-overrides.just"
```

**Import behavior:**

- Imported recipes and variables merge into current namespace
- Later definitions override earlier ones (with `allow-duplicate-*`)
- Relative paths resolve from importing file's directory
- Duplicate imports are deduplicated automatically

### Modules

Load justfile as a submodule (requires `set unstable`):

```just
# Load from foo.just or foo/justfile
mod foo

# Load from custom path
mod bar "path/to/bar.just"
mod baz "other/directory"  # Looks for justfile inside

# Optional module (no error if missing)
mod? local

# Module with attributes
[private]
mod internal

[doc("Development tools")]
mod dev
```

**Calling module recipes:**

```just
# Subcommand syntax
just foo build

# Path syntax
just foo::build

# From another recipe
@all:
    just foo::build
    just bar::test
```

**Module namespacing:**

- Recipes inside modules are namespaced: `module::recipe`
- Variables inside modules are NOT accessible from parent
- Settings inside modules apply only to that module
- Modules can import/include other files

### Module Search Paths

When using `mod foo`:

1. `foo.just` in same directory
1. `foo/justfile` subdirectory
1. `foo/mod.just` subdirectory

## Attributes

Attributes modify recipe behavior. Place before recipe definition.

### Recipe Visibility

```just
# Private via underscore prefix
_helper:
    echo "private"

# Private via attribute
[private]
helper:
    echo "also private"
```

### Grouping

```just
[group("checks")]
lint:
    npm run lint

[group("checks")]
format:
    npm run format
```

Groups organize `just --list` output:

```
Available recipes:
    default

[checks]
    format
    lint
```

### Directory Control

```just
# Don't change to justfile directory
[no-cd]
status:
    git status

# Set specific working directory
[working-directory: "packages/core"]
build-core:
    npm run build
```

### Script Blocks

```just
# Default shell script
[script]
multiline:
    if [ -f "config.json" ]; then
        echo "Found config"
    else
        echo "No config"
    fi

# Specific interpreter
[script("python3")]
process:
    import json
    data = json.load(open("config.json"))
    print(data["name"])

[script("bash")]
deploy:
    set -e
    npm run build
    aws s3 sync dist/ s3://bucket/
```

### Confirmation

```just
# Default confirmation prompt
[confirm]
delete-all:
    rm -rf dist/

# Custom prompt
[confirm("Are you sure you want to deploy to production?")]
deploy-prod:
    ./deploy.sh production
```

### Documentation

```just
# Comment becomes doc (default)
# Build the project
build:
    npm run build

# Override with attribute
[doc("Compile TypeScript and bundle")]
build:
    npm run build

# Suppress documentation
[doc]
internal-helper:
    echo "hidden"
```

### Combining Attributes

```just
# Same line (comma-separated)
[no-cd, private]
helper:
    echo "helper"

# Multiple lines
[group("codegen")]
[script("bash")]
[confirm("Generate bindings?")]
codegen:
    ./generate.sh
```

### Per-Recipe Positional Arguments

```just
[positional-arguments]
@greet name:
    echo "Hello, $1!"
```

## Constants

### Terminal Colors

Available globally without definition:

| Constant             | ANSI Code |
| -------------------- | --------- |
| `BLACK`              | `\e[30m`  |
| `RED`                | `\e[31m`  |
| `GREEN`              | `\e[32m`  |
| `YELLOW`             | `\e[33m`  |
| `BLUE`               | `\e[34m`  |
| `PURPLE` / `MAGENTA` | `\e[35m`  |
| `CYAN`               | `\e[36m`  |
| `WHITE`              | `\e[37m`  |

### Text Styles

| Constant        | Effect             |
| --------------- | ------------------ |
| `BOLD`          | Bold text          |
| `ITALIC`        | Italic text        |
| `UNDERLINE`     | Underlined text    |
| `STRIKETHROUGH` | Strikethrough text |
| `INVERT`        | Invert colors      |
| `HIDE`          | Hidden text        |

### Reset

| Constant | Effect               |
| -------- | -------------------- |
| `NORMAL` | Reset all formatting |

### Background Colors

| Constant    | Description       |
| ----------- | ----------------- |
| `BG_BLACK`  | Black background  |
| `BG_RED`    | Red background    |
| `BG_GREEN`  | Green background  |
| `BG_YELLOW` | Yellow background |
| `BG_BLUE`   | Blue background   |
| `BG_PURPLE` | Purple background |
| `BG_CYAN`   | Cyan background   |
| `BG_WHITE`  | White background  |

### System Constants

| Constant   | Value                       |
| ---------- | --------------------------- |
| `HEX`      | `0123456789ABCDEF`          |
| `HEXLOWER` | `0123456789abcdef`          |
| `PATH_SEP` | `:` (Unix) or `;` (Windows) |

### Usage Examples

```just
@success:
    echo -e '{{ GREEN }}✓ Success!{{ NORMAL }}'

@error:
    echo -e '{{ RED + BOLD }}✗ Error!{{ NORMAL }}'

@highlight:
    echo -e '{{ BG_YELLOW + BLACK }}Warning{{ NORMAL }}'

@combined:
    echo -e '{{ BOLD + UNDERLINE + CYAN }}Important{{ NORMAL }}'
```

## Functions

### Executable Functions

```just
# Require executable (fail if not found)
jq := require("jq")
# Returns full path: /usr/bin/jq

# Check if executable exists
has_docker := `which docker > /dev/null 2>&1 && echo "true" || echo "false"`
```

### Environment Functions

```just
# Get env var (error if unset)
home := env("HOME")

# Get env var with default
log_level := env("LOG_LEVEL", "info")

# Export variable
export DATABASE_URL := env("DATABASE_URL", "postgres://localhost/dev")
```

### Path Functions

```just
# Justfile directory (absolute path)
root := justfile_dir()

# Justfile path
justfile := justfile()

# Source directory (for imported files)
source_dir := source_directory()
source_file := source_file()

# Invocation directory (where just was called from)
invocation_dir := invocation_directory()

# Parent directory
parent := parent_directory(justfile_dir())

# Join paths
config := join(justfile_dir(), "config")

# File operations
exists := path_exists("config.json")
stem := file_stem("config.json")      # "config"
name := file_name("path/config.json") # "config.json"
ext := extension("config.json")       # "json"
```

### String Functions

```just
# Case conversion
upper := uppercase("hello")      # "HELLO"
lower := lowercase("HELLO")      # "hello"
kebab := kebabcase("HelloWorld") # "hello-world"
snake := snakecase("HelloWorld") # "hello_world"
title := titlecase("hello")      # "Hello"

# String manipulation
trimmed := trim("  hello  ")     # "hello"
replaced := replace("foo-bar", "-", "_")  # "foo_bar"

# Quoting
quoted := quote("path with spaces")  # "'path with spaces'"
shell_escaped := shell("echo 'test'")
```

### System Functions

```just
# Operating system
os := os()              # "linux", "macos", "windows"
family := os_family()   # "unix" or "windows"
arch := arch()          # "x86_64", "aarch64", etc.

# Number of CPUs
cpus := num_cpus()

# UUID generation
id := uuid()

# SHA256 hash
hash := sha256("content")
file_hash := sha256_file("config.json")

# Date/time
now := datetime("%Y-%m-%d")
timestamp := datetime("%s")
```

### Conditional Functions

```just
# Error if condition false
_ := assert(path_exists("config.json"), "Config file required!")

# Conditional value
mode := if env("CI", "") != "" { "ci" } else { "local" }

# Error message
_ := error("This recipe is deprecated")
```

## Recipe Parameters

### Required Parameters

```just
greet name:
    echo "Hello, {{ name }}"
```

### Default Parameters

```just
greet name="World":
    echo "Hello, {{ name }}"
```

### Variadic Parameters

```just
# One or more arguments (required)
test +files:
    npm test {{ files }}

# Zero or more arguments (optional)
build *flags:
    npm run build {{ flags }}
```

### Parameter with Environment Variable

```just
# Set from env or use default
deploy env=env("DEPLOY_ENV", "staging"):
    ./deploy.sh {{ env }}
```

## Recipe Dependencies

### Simple Dependencies

```just
build: clean compile
    echo "Build complete"

clean:
    rm -rf dist/

compile:
    tsc
```

### Dependencies with Arguments

```just
deploy env: (build env)
    ./deploy.sh {{ env }}

build env:
    npm run build:{{ env }}
```

### Conditional Execution

```just
test: && lint
    npm test

# lint runs only if test succeeds
```

## Command Prefixes

| Prefix       | Effect             |
| ------------ | ------------------ |
| `@`          | Don't echo command |
| `-`          | Ignore errors      |
| `@-` or `-@` | Both               |

```just
@quiet:
    echo "Only output shown"

-ignore-error:
    false
    echo "Still runs"

@-both:
    false
    echo "Quiet and ignores error"
```

## Variables

### Assignment

```just
# Simple
name := "value"

# From environment
port := env("PORT", "3000")

# From shell command
version := `git describe --tags`

# Exported (available to recipes)
export NODE_ENV := "production"

# Conditional
mode := if os() == "windows" { "win" } else { "unix" }
```

### Variable Scope

- Variables defined at top level are global
- Recipe parameters shadow global variables
- Imported variables can be overridden with `allow-duplicate-variables`

## Shebang Recipes

Execute with specific interpreter:

```just
python-script:
    #!/usr/bin/env python3
    import sys
    print(f"Python {sys.version}")

node-script:
    #!/usr/bin/env node
    console.log(process.version)
```

## Backtick Evaluation

````just
# Single line
version := `git describe --tags`

# Multi-line (indented)
files := ```
    find src -name "*.ts" \
        | grep -v test \
        | head -10
````

````

## Just CLI Options

| Option | Description |
|--------|-------------|
| `just --list` | List available recipes |
| `just --list --unsorted` | List in source order |
| `just --summary` | Brief recipe list |
| `just --show RECIPE` | Show recipe source |
| `just --dry-run RECIPE` | Print commands without running |
| `just --evaluate` | Print all variables |
| `just --fmt` | Format justfile |
| `just --fmt --check` | Check formatting |
| `just --choose` | Interactive recipe selection (fzf) |
| `just -f PATH` | Use specific justfile |
| `just -d DIR` | Set working directory |

## Glob Patterns

Store glob patterns in variables with proper quoting:

```just
# Quote the pattern
GLOBS_TS := "\"**/*.{ts,tsx}\""
GLOBS_JSON := "\"**/*.{json,jsonc,yaml,yml}\""

# Use in recipes
lint:
    eslint {{ GLOBS_TS }}

format:
    prettier --check {{ GLOBS_JSON }}
````

## Error Handling

```just
# Fail on any error (in script block)
[script("bash")]
deploy:
    set -e
    npm run build
    npm run test
    npm publish

# Continue on error (line prefix)
cleanup:
    -rm -rf dist/
    -rm -rf node_modules/
    echo "Cleanup attempted"

# Assert condition
check:
    {{ assert(path_exists("package.json"), "Must run from project root") }}
```
