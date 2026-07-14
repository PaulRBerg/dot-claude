# Claude Code config

[![CI](https://github.com/PaulRBerg/dot-claude/actions/workflows/ci.yml/badge.svg)](https://github.com/PaulRBerg/dot-claude/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Configured-DE7356)](https://github.com/anthropics/claude-code)

PRB's personal Claude Code config, mounted at `~/.claude`.

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

`CLAUDE.md` is user-level context loaded by Claude Code across all projects. Keep repo-specific guidance in project
`CLAUDE.md` / `AGENTS.md` files; keep only durable personal workflow defaults here.

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
which enables namespaced patterns like `/yeet:issue-cc` and `/agents-context:brain-polish`.

### Skills

Skills are managed in [PaulRBerg/dot-agents](https://github.com/PaulRBerg/dot-agents) and installed via Vercel's
[skills CLI](https://github.com/vercel-labs/skills). This repo keeps symlinks from `skills/` to `~/.agents/skills/`.
See dot-agents for installation guidance.

Examples: **agents-context-management**, **commit**, **vitest**, **effect-ts**, **cli-gh**, **find-tool**, **yeet**.

### Agents

`agents/` includes specialized subagents.

Invoke via `-s` or the Task tool.

### MCP servers

MCP servers are configured in `.mcp.json` (currently none). Permission rules for MCP tools live in
`settings/permissions/mcp.jsonc`.

### Hooks

Hooks provide event-driven Claude Code automation. See [hooks/README.md](hooks/README.md).

Active hooks from `settings/hooks.jsonc`:

- **add_plan_frontmatter.py**: add YAML frontmatter to plan files (`PostToolUse`)
- **copy_prompt_to_clipboard.py**: copy submitted prompts to the macOS clipboard (`UserPromptSubmit`)

Available hook scripts also include settings sync helpers under `hooks/SessionEnd/`.

### Plugins

No plugins are enabled in `settings/plugins.jsonc`. `plugins/` stores marketplace metadata and caches; refresh them with
`just update-plugins`.

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
