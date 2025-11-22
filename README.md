# Claude Code config

[![CI](https://github.com/PaulRBerg/dot-claude/actions/workflows/ci.yml/badge.svg)](https://github.com/PaulRBerg/dot-claude/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Configured-DE7356)](https://github.com/anthropics/claude-code)

PRB's `.claude` directory.

## Quick Start

Get up and running in 3 steps:

```bash
# 1. Clone to ~/.claude
git clone git@github.com:PaulRBerg/dot-claude.git ~/.claude
cd ~/.claude

# 2. Install dependencies
bun install          # Node dependencies (Husky, lint-staged)
uv sync --all-extras # Python dependencies

# 3. Try it out
ccc                  # Make your first commit with the claude wrapper
```

See [Installation](#installation) for detailed setup and [Configuration](#configuration) for customization.

## Settings

**Modular architecture**: All JSONC files in `settings/*` automatically merge into `settings.json` on commit via Husky +
lint-staged.

**Editing**: Modify `settings/**/*.jsonc` files (never edit `settings.json` directly). Changes auto-merge on commit, or
run `just merge_settings` manually.

## Context

Modular configuration system using `@` syntax for composable behavioral instructions:

```markdown
@context/CRITICAL_THINKING.md

@context/SENIOR_PROGRAMMER.md
```

Context files are organized by concern and imported via `@filename.md` references. Base instructions cascade through
specialized modules, creating layered behavioral policies without duplication.

## Installation

### Prerequisites

- **Node.js** - For Husky/lint-staged automation (`npm install`)
- **Just** - Command runner for build scripts (`brew install just`)
- **Python 3.12+** and [uv](https://github.com/astral-sh/uv) - Python package and project manager

### Clone Repository

Clone or copy this repository to `~/.claude`:

```bash
git clone git@github.com:PaulRBerg/dot-claude.git ~/.claude
cd ~/.claude
```

### Install Dependencies

```bash
bun install          # Install Node dependencies (Husky, lint-staged)
uv sync --all-extras # Install Python dependencies
```

### CLI Dependencies

Install via Homebrew on macOS:

```bash
brew install bat delta eza fd fzf gh gum jq just rg ruff uv yq
```

### Verify Installation

```bash
just full-check      # Run all code checks
just test-hooks      # Run hook tests
claude                # Run Claude
```

## Configuration

**Flags**: Add flags at the end of prompts to trigger behaviors (`-s` for subagents, `-c` for auto-commit, `-t` for
testing, `-d` for debug, `-n` to skip linting). Flags are composable: `implement API -s -t -c`.

**Justfile**: Run common tasks like `just full-check` (all code checks), `just merge_settings` (merge JSONC files), or
`just test` (run tests). See `justfile` for all commands.

## Features

### Commands

Slash commands in `commands/*.md` handle GitHub workflows, releases, and task management. Examples: `/commit` (atomic
commits), `/create-pr` (PRs with semantic analysis), `/fix-issue` (fetch and fix issues), `/bump-release` (version
bumping).

### Skills

Auto-activating skills in `skills/`: **typescript**, **web3-frontend**, **ui-ux-design**, **dry-refactor**. See
`skills/skill-rules.json` for activation triggers.

External plugins: **code-review**, **playwright-skill**.

### Agents

Specialized subagents in `agents/`: code review, debugging, web3 backend engineering, tool discovery. Invoke via `-s`
flag or Task tool.

### MCP Servers

Three servers extend Claude's capabilities (configured in `.mcp.json`):

- **context7** - Library documentation and code examples
- **serena** - Semantic code navigation and editing
- **sequential-thinking** - Chain-of-thought reasoning

Enable/disable in `settings/permissions/mcp.jsonc`.

### Hooks

Event-driven automation. See [hooks/README.md](hooks/README.md) for details.

## Utilities

> [!NOTE] Highly recommended: The `claude` wrapper runs Claude with `--dangerously-skip-permissions` and auto-loads MCP
> servers from `.mcp.json`. See [this issue](https://github.com/anthropics/claude-code/issues/3321).

Optional shell utilities in `utils.sh`:

- **`ccc [args]`** - Streamlined commits via `/commit` (defaults to `--all`)
- **`ccbump [args]`** - Quick release bumping via `/bump-release`
- **`claude [args]`** - Enhanced CLI wrapper with MCP auto-loading

Source in your shell config:

```zsh
# In ~/.zshrc
source ~/.claude/utils.sh
```

## License

This project is licensed under MIT.
