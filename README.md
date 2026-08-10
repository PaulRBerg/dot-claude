# Claude Code config

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

- **Bun**: JS dependencies and Husky/lint-staged automation (`bun install`)
- **Just**: command runner for build scripts (`brew install just`)
- **Python 3.13+** and [uv](https://github.com/astral-sh/uv): Python package/project manager

### Setup

```bash
git clone git@github.com:PaulRBerg/dot-claude.git ~/.claude
cd ~/.claude
just install  # JS deps, Python deps, and CLI utilities
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

Edit only `settings/**/*.jsonc` (never `settings.json` directly). Merging happens on commit, or run
`just merge-settings` manually.

Settings layout:

- `basics.jsonc`: core config, env vars, status line
- `hooks.jsonc`: event hooks
- `plugins.jsonc`: enabled plugins
- `permissions/*.jsonc`: permission rules (additional-dirs, bash, read)

### Context

`CLAUDE.md` is user-level context loaded by Claude Code across all projects. It is generated from
[PaulRBerg/dot-agents](https://github.com/PaulRBerg/dot-agents)'s `AGENTS.md` — the canonical source — via that repo's
Husky + lint-staged pre-commit hook; do not hand-edit it here. Keep repo-specific guidance in project `CLAUDE.md` /
`AGENTS.md` files.

### Justfile

Use `just` for common tasks like `just full-check`, `just merge-settings`, and `just test`. See `justfile` for the full
command list.

## Features

### Commands

`commands/` contains thin entry points that invoke skills. Commands still matter because they support directory nesting,
which enables namespaced patterns like `/yeet:issue-cc` and `/agents-brain:brain-polish`.

### Skills

Skills are managed in [PaulRBerg/dot-agents](https://github.com/PaulRBerg/dot-agents) and installed via Vercel's
[skills CLI](https://github.com/vercel-labs/skills). This repo keeps symlinks from `skills/` to `~/.agents/skills/`. See
dot-agents for installation guidance.

Examples: **agents-brain**, **commit**, **vitest**, **effect-ts**, **cli-gh**, **tool-finder**, **yeet**.

### Agents

`agents/` can hold specialized subagents invoked via the Task tool (currently none).

### MCP servers

MCP servers are configured in `.mcp.json` (currently none).

### Hooks

Hooks provide event-driven Claude Code automation. See [hooks/README.md](hooks/README.md).

Active hooks from `settings/hooks.jsonc`:

- **add_plan_frontmatter.py**: add YAML frontmatter to plan files (`PostToolUse`)
- **ai-notify**: desktop notifications via the external
  [ai-notify](https://github.com/PaulRBerg/agent-toolkit/tree/main/notify) CLI (`Notification`, `PermissionRequest`,
  `PreToolUse`, `Stop`, `UserPromptSubmit`)
- **copy_prompt_to_clipboard.py**: copy submitted prompts to the macOS clipboard (`UserPromptSubmit`)

### Plugins

No plugins are enabled in `settings/plugins.jsonc`. `plugins/` stores marketplace metadata and caches.

## Utilities

Shell utilities are maintained in the chezmoi-managed `~/.config/prb/agents.sh` module and loaded automatically by
`~/.zshrc`:

- **`ccc [args]`**: streamlined commits via `/commit` (defaults to `--all`)
- **`cccp`**: commit and push (feature branches)
- **`ccs [args]`**: commit only staged changes
- **`ccsp [args]`**: commit staged changes and push
- **`ccbump [args]`**: quick release bumping via `/release-bumper`
- **`ccta [args]`**: archive TODOs via `$todo-archive`

## License

MIT. See [LICENSE.md](LICENSE.md).
