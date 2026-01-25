# Claude Code config

[![CI](https://github.com/PaulRBerg/dot-claude/actions/workflows/ci.yml/badge.svg)](https://github.com/PaulRBerg/dot-claude/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Configured-DE7356)](https://github.com/anthropics/claude-code)

PRB's `.claude` directory.

## 🚀 Quick Start

Get up and running in 3 steps:

```bash
# 1. Clone to ~/.claude
git clone git@github.com:PaulRBerg/dot-claude.git ~/.claude
cd ~/.claude

# 2. Install dependencies
just install

# 3. Try it out
ccc                  # Make your first commit with the claude wrapper
```

See [Installation](#-installation) for detailed setup and [Configuration](#-configuration) for customization.

## 📦 Installation

### Prerequisites

- **Node.js** - For Husky/lint-staged automation (`npm install`)
- **Just** - Command runner for build scripts (`brew install just`)
- **Python 3.13+** and [uv](https://github.com/astral-sh/uv) - Python package and project manager

### Clone Repository

Clone or copy this repository to `~/.claude`:

```bash
git clone git@github.com:PaulRBerg/dot-claude.git ~/.claude
cd ~/.claude
```

### Install Dependencies

```bash
just install  # Node deps, Python deps, and CLI utilities
```

### Verify Installation

```bash
just full-check      # Run all code checks
just test-hooks      # Run hook tests
claude               # Run Claude
```

## ⚙️ Configuration

### Settings

**Modular architecture**: All JSONC files in `settings/*` automatically merge into `settings.json` on commit via Husky +
lint-staged.

**Editing**: Modify `settings/**/*.jsonc` files (never edit `settings.json` directly). Changes auto-merge on commit, or
run `just merge-settings` manually.

### Context

Global instructions live in `CLAUDE.md`. Sections cover communication style, code preferences, scope preservation, git
safety, and shell escaping rules.

### Flags

Add flags at the end of prompts to trigger behaviors (`-s` for subagents, `-c` for auto-commit, `-t` for testing, `-d`
for debug, `-n` to skip linting). Flags are composable: `implement API -s -t -c`.

### Justfile

Run common tasks like `just full-check` (all code checks), `just merge-settings` (merge JSONC files), or `just test`
(run tests). See `justfile` for all commands.

## ✨ Features

### Commands

Slash commands in `commands/*.md` handle GitHub workflows, releases, and task management:

- `/create-pr` - Create PRs with semantic analysis
- `/create-issue` - Create GitHub issues
- `/update-pr` - Update existing PRs
- `/create-discussion` - Start GitHub discussions
- `/update-deps` - Update Node.js dependencies
- `/md-docs:update-readme` - Sync README with codebase
- `/md-docs:update-agents` - Update AI context files

### Skills

Activatable skills live in [`~/.agents/skills`](https://github.com/PaulRBerg/dot-agents). Examples: **typescript**,
**gh-cli**, **code-review**.

### Agents

Specialized subagents in `agents/`: code review, debugging, tool discovery, docs finding. Invoke via `-s` flag or Task
tool.

### MCP Servers

Two servers extend Claude's capabilities (configured in `.mcp.json`):

- **context7** - Library documentation and code examples
- **sequential-thinking** - Chain-of-thought reasoning

Enable/disable in `settings/permissions/mcp.jsonc`.

### Hooks

Event-driven automation for Claude Code events. See [hooks/README.md](hooks/README.md) for details.

Key hooks:

- **ai-flags** - Parse flags from prompts to trigger behaviors
- **ai-notify** - Desktop notifications for events (optional)
- **log_prompts.py** - Log conversations to zk notebook (optional)

## 🛠️ Utilities

> [!NOTE]
> The `claude` wrapper runs Claude with `--dangerously-skip-permissions` and auto-loads MCP servers from `.mcp.json`.
> See [this issue](https://github.com/anthropics/claude-code/issues/3321).

Optional shell utilities in `utils.sh`:

- **`ccc [args]`** - Streamlined commits via `/commit` (defaults to `--all`)
- **`cccp`** - Commit and push (for feature branches)
- **`ccbump [args]`** - Quick release bumping via `/bump-release`
- **`claude [args]`** - Enhanced CLI wrapper with MCP auto-loading

Source in your shell config:

```zsh
# In ~/.zshrc
source ~/.claude/utils.sh
```

## 📄 License

This project is licensed under MIT - see the [LICENSE.md](LICENSE.md) file for details.
