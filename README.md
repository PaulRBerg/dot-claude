# Claude Code config

[![CI](https://github.com/PaulRBerg/dot-claude/actions/workflows/ci.yml/badge.svg)](https://github.com/PaulRBerg/dot-claude/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Configured-DE7356)](https://github.com/anthropics/claude-code)

PRB's `.claude` directory.

## Quick Start

```bash
git clone git@github.com:PaulRBerg/dot-claude.git ~/.claude
cd ~/.claude
just install
ccc  # Make your first commit with the claude wrapper
```

See [Installation](#installation) for full setup and [Configuration](#configuration) for customization.

## Installation

### Prerequisites

- **Node.js**: Husky/lint-staged automation (`npm install`)
- **Just**: command runner for build scripts (`brew install just`)
- **Python 3.13+** and [uv](https://github.com/astral-sh/uv): Python package/project manager

### Setup

```bash
git clone git@github.com:PaulRBerg/dot-claude.git ~/.claude
cd ~/.claude
just install  # Node deps, Python deps, and CLI utilities
```

### Verify

```bash
just full-check  # Run all code checks
just test-hooks  # Run hook tests
claude           # Run Claude
```

## Configuration

### Settings

All JSONC files in `settings/*` merge into `settings.json` on commit via Husky + lint-staged.

Edit only `settings/**/*.jsonc` (never `settings.json` directly). Merging happens on commit, or run `just merge-settings`
manually.

Settings layout:

- `basics.jsonc`: core config, env vars, status line
- `hooks.jsonc`: event hooks
- `plugins.jsonc`: enabled plugins
- `permissions/*.jsonc`: permission rules (bash, mcp, read, write, tools)

### Context

Global instructions are in `CLAUDE.md` (communication style, code preferences, scope preservation, git safety, shell
escaping).

### Flags

Append flags to prompts to trigger behavior:

- `-s`: subagents
- `-c`: auto-commit
- `-t`: testing
- `-d`: debug
- `-n`: skip linting

Flags compose, e.g. `implement API -s -t -c`.

### Justfile

Use `just` for common tasks like `just full-check`, `just merge-settings`, and `just test`. See `justfile` for the full
command list.

## Features

### Commands

`commands/` contains thin entry points that invoke skills. Commands still matter because they support directory nesting,
which enables namespaced patterns like `/yeet:issue-cc` and `/md-docs:update-readme`.

### Skills

Skills are managed in [PaulRBerg/dot-agents](https://github.com/PaulRBerg/dot-agents) and installed via Vercel's
[skills CLI](https://github.com/vercel-labs/skills). This repo keeps symlinks to `~/.agents/skills/`. See dot-agents for
installation guidance.

Examples: **commit**, **code-review**, **code-polish**, **vitest**, **effect-ts**, **web3-foundry**, **biome-js**,
**cli-gh**, **yeet**.

### Agents

`agents/` includes specialized subagents:

- **tool-finder**: discover tools and packages for any task
- **docs-finder**: find library/framework documentation

Invoke via `-s` or the Task tool.

### MCP servers

Three MCP servers are configured in `.mcp.json`:

- **context7**: library docs and code examples
- **filesystem**: filesystem access and manipulation
- **sequential-thinking**: chain-of-thought reasoning

Enable or disable them in `settings/permissions/mcp.jsonc`.

### Hooks

Hooks provide event-driven Claude Code automation. See [hooks/README.md](hooks/README.md).

Active hooks:

- **add_plan_frontmatter.py**: add YAML frontmatter to plan files (`PostToolUse`)
- **commit_prompts.py**: commit logged prompts to zk notebook (`SessionEnd`)
- **sync_global_settings.py**: sync global settings across machines (`SessionEnd`)
- **sync_local_settings.py**: sync local project settings (`SessionEnd`)
- **log_prompts.py**: log conversations to zk notebook (`UserPromptSubmit`, optional)

Optional (commented out): **ai-flags** (prompt flag parsing), **ai-notify** (desktop notifications).

### Plugins

Two official plugins are enabled via `settings/plugins.jsonc`:

- **claude-md-management**: CLAUDE.md auditing and improvement
- **plugin-dev**: plugin development tools (commands, skills, hooks, agents)

## Utilities

> [!NOTE]
> The `claude` wrapper runs Claude with `--dangerously-skip-permissions` and auto-loads MCP servers from `.mcp.json`.
> See [this issue](https://github.com/anthropics/claude-code/issues/3321).

Optional shell utilities from `utils.sh`:

- **`ccc [args]`**: streamlined commits via `/commit` (defaults to `--all`)
- **`cccp`**: commit and push (feature branches)
- **`ccbump [args]`**: quick release bumping via `/bump-release`
- **`claude [args]`**: enhanced CLI wrapper with MCP auto-loading

Source them in your shell config:

```zsh
source ~/.claude/utils.sh
```

## License

MIT. See [LICENSE.md](LICENSE.md).
