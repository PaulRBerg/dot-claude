# Claude Code config

PRB's `.claude` directory.

## Settings

I use a **modular architecture** for my Claude Code settings: all JSONC files in `settings/*` automatically merge into
`settings.json` via Husky + lint-staged on every commit. See the `merge_settings` recipe in the `justfile` for more
details.

**Editing:** Modify `settings/**/*.jsonc` files (never edit `settings.json` directly). Changes auto-merge on commit, or
manually via `just merge_settings`.

**Rationale:** Separation of concerns improves maintainability. Modular files support comments and focused editing.
Alphabetical merge order ensures deterministic, conflict-free composition.

**Key configurations:**

- **Permissions**: Pre-approved commands (`git`, `grep`, etc.) and tools run without confirmation. Destructive
  operations (`sudo`, `rm -rf`, system files) are blocked.
- **Hooks**: Event-driven automation, see the [docs](https://docs.claude.com/en/docs/claude-code/hooks) for more info.
- **Status Line**: Custom status via `ccstatusline`

## Context

Modular configuration system using `@` syntax for composable behavioral instructions:

```markdown
@context/CRITICAL_THINKING.md

@context/SENIOR_PROGRAMMER.md
```

Context files are organized by concern and imported via `@filename.md` references. Base instructions cascade through
specialized modules, creating layered behavioral policies without duplication.

## Usage

### Prerequisites

- **Node.js** - For Husky/lint-staged automation (`npm install`)
- **Just** - Command runner for build scripts (`brew install just`)
- **Python 3.12+** and [uv](https://github.com/astral-sh/uv) - Python package and project manager

### Installation

Clone or copy this repository to `~/.claude`:

```bash
git clone <repository-url> ~/.claude
cd ~/.claude
```

Then, install the dependencies:

```bash
bun install          # Install Node dependencies (Husky, lint-staged)
uv sync --all-extras # Install Python dependencies
```

### CLI Dependencies

- [`bat`](https://github.com/sharkdp/bat) - Modern cat replacement
- [`delta`](https://github.com/dandavison/delta) - Git diff viewer
- [`eza`](https://github.com/eza-community/eza) - Modern ls replacement
- [`fd`](https://github.com/sharkdp/fd) - Fast file finder
- [`fzf`](https://github.com/junegunn/fzf) - Fuzzy finder
- [`gh`](https://github.com/cli/cli) - GitHub CLI
- [`gum`](https://github.com/charmbracelet/gum) - UI components for spinners
- [`jq`](https://github.com/jqlang/jq) - JSON processor
- [`rg`](https://github.com/BurntSushi/ripgrep) (ripgrep) - Fast search
- [`ruff`](https://github.com/astral-sh/ruff) - Python linter/formatter
- [`yq`](https://github.com/mikefarah/yq) - YAML processor

On macOS, you can install all dependencies using Homebrew:

```bash
# Required
brew install bat delta eza fd fzf gh gum jq just rg ruff uv yq
```

After installing `gh` for the first time, authenticate with GitHub:

```bash
gh auth login
```

### Optional Dependencies

**Utilities** (gracefully degrade if unavailable):

- **[claude-code-docs](https://github.com/ericbuess/claude-code-docs)** - Local mirror of Claude Code documentation from
  Anthropic. Provides `claude-docs-helper.sh` for quick doc lookups.
- **[ccnotify](https://github.com/dazuiba/CCNotify)** - macOS notifications for Claude Code events (`UserPromptSubmit`,
  `PermissionRequest`, `Stop`). Uses SQLite for session tracking.
  [terminal-notifier](https://github.com/julienXX/terminal-notifier): `brew install terminal-notifier`
- **[zk](https://github.com/zk-org/zk)** - Zettelkasten note-taking system. Required for `log_prompts` hook. Install via
  `brew install zk`, then initialize `~/.claude-prompts/` as a zk notebook.

**Optional Features:**

- **log_prompts hook** - Logs conversation prompts to zk notebook at `~/.claude-prompts/`. Requires `zk` CLI and
  initialized notebook. Exits gracefully if prerequisites missing.
- **MCP servers** - Configured in `.mcp.json`

### Configuration

**Editing settings:**

- Modify `settings/**/*.jsonc` files (human-editable with comments)
- Never edit `settings.json` directly (auto-generated)
- Changes auto-merge via lint-staged on commit
- Manual merge: `just merge_settings` or `just ms`

**Testing:**

```bash
just test           # Run all tests
just test-hooks     # Run hook tests specifically
```

## Commands

[Slash commands](https://docs.claude.com/en/docs/claude-code/slash-commands) are defined in `commands/*.md`.

The commands cover GitHub workflows (PR/issue management), release automation, code quality validation, task management,
and activity tracking. Commands use semantic analysis to understand code changes rather than relying on filenames. They
feature natural argument parsing (`/commit fix auth --short`), smart defaults (auto-stage changes, detect reviewers),
and stateless execution without interactive prompts.

**Examples:**

- `/commit` - Create atomic git commits with smart heuristic analysis
- `/create-pr` - Create GitHub pull requests with semantic change analysis
- `/fix-issue <number>` - Fetch, analyze, fix, and commit GitHub issue resolutions
- `/bump-release` - Roll out new releases with changelog updates and version bumping

## Skills

[Claude Skills](https://docs.claude.com/en/docs/claude-code/skills) in `skills/` auto-activate based on context:

- **typescript**: TypeScript engineering practices and patterns for `.ts`/`.tsx` files
- **web3-frontend**: Secure wallet interactions and production-grade dApp development with Viem/Wagmi
- **ui-ux-design**: Interface design, wireframes, and design system creation
- **skill-creator**: Create and manage Claude Code skills following best practices
- **dry-refactor**: DRY refactoring patterns and techniques

Skills use imperative voice and trigger-rich descriptions, activating automatically when working with relevant file
types, technologies, or domain concepts. Configuration in `skills/skill-rules.json` defines activation triggers and
priorities.

### External Plugins

- **[code-review](https://github.com/claude-code-plugins/code-review)** (`code-review@claude-code-plugins`) - Code
  review automation
- **[playwright-skill](https://github.com/playwright-skill/playwright-skill)** (`playwright-skill@playwright-skill`) -
  Browser automation and testing

## Agents

Four specialized subagents in `agents/` handle domain-specific work: code review, debugging, web3 backend engineering,
and tool discovery. Agents are invoked via the `-s` orchestration flag or directly through the Task tool.

## MCP Servers

Three Model Context Protocol servers configured in `.mcp.json` extend Claude's capabilities:

**Active Servers:**

- **[context7](https://github.com/upstash/context7-mcp)** (`@upstash/context7-mcp`) - Fetches up-to-date library
  documentation and code examples. Resolves package names to Context7-compatible IDs and retrieves relevant docs on
  demand.

- **[serena](https://github.com/oraios/serena)** (`serena` via uvx) - IDE assistant with semantic code navigation.
  Provides symbol-based search, referencing, editing, and memory management for token-efficient codebase exploration.

- **[sequential-thinking](https://github.com/modelcontextprotocol/servers)**
  (`@modelcontextprotocol/server-sequential-thinking`) - Chain-of-thought reasoning tool for complex problem-solving.
  Supports dynamic thought adjustment, revision, and branching.

**Configuration:** Enable/disable servers in `settings/permissions/mcp.jsonc`.

## Utilities

> [!NOTE]
>
> While it is not required, I highly recommend installing these utilities, especially the `claude` wrapper that runs
> Claude with the `--dangerously-skip-permissions` flag and loads MCP servers from `.mcp.json` (if present). See this
> this [GitHub issue](https://github.com/anthropics/claude-code/issues/3321).

Shell utilities for Claude Code workflows are provided in `utils.sh`. These utilities are optional but can improve your
command-line experience with Claude Code. Add them to your shell configuration (e.g., `~/.zshrc` or `~/.bashrc`).

**Key Functions:**

- **`ccc [args]`** - Streamlined git commit using `/commit` command with automatic cleanup. Defaults to `--all` if no
  args provided. Uses `gum` spinner if available.
- **`ccbump [args]`** - Quick release bumping using `/bump-release` command with `gum` spinner integration.
- **`claude [args]`** - Enhanced CLI wrapper that auto-loads `.mcp.json` if present in current directory. Adds `gum`
  spinner for `-p` flag operations.

**Aliases:**

- Navigation: `cd_claude`, `cd_codex`, `cd_gemini`
- Editing: `edit_claude`, `edit_codex`, `edit_gemini`

**Usage:**

Source in your shell configuration (zsh-specific):

```zsh
# In ~/.zshrc
source ~/.claude/utils.sh
```

Then use functions directly:

```bash
claude                 # Run Claude with `--dangerously-skip-permissions` flag
ccc                    # Commit all changes
ccc --quick            # Quick commit mode
ccbump --beta          # Bump to beta release
claude_allow_bash npm  # Add npm to allowed Bash tools
```

## Hooks

Five custom hooks in `hooks/` extend Claude Code with event-driven automation:

### 1. detect_flags.py (UserPromptSubmit)

General-purpose flag parser that processes trailing flags in prompts to trigger different behaviors. Flags must appear
at the end of prompts with no other text after them.

**Supported flags:**

- **`-s`** (subagent): Injects [SUBAGENTS.md](hooks/UserPromptSubmit/SUBAGENTS.md) instructions, forcing Claude to
  delegate work to specialized subagents instead of doing everything itself. Mandates parallel delegation for
  independent subtasks, single agent for sequential work.

- **`-c`** (commit): Instructs Claude to execute `/commit` slash command after completing the task.

- **`-t`** (test): Adds testing emphasis context, requiring comprehensive test coverage including unit tests,
  integration tests, and edge cases.

- **`-d`** (debug): Invokes the debugger subagent for systematic root cause analysis with a 5-step debugging workflow.

- **`-n`** (no-lint): Skip linting and type-checking during development.

**Composability**: Flags combine naturally into complete workflows:

- `implement payment API -s -t -c` → delegate to agents, emphasize tests, commit when done
- `fix memory leak -d -c` → debug mode, commit fix
- `add OAuth flow -s -c` → orchestrate implementation, auto-commit

**Order independence**: `-s -c -t` works identically to `-t -c -s`.

### 2. activate_skills.py (UserPromptSubmit)

Analyzes user prompts and suggests relevant skills based on keywords, intent patterns, file patterns, and content
patterns. Configuration in `skills/skill-rules.json` defines trigger conditions and priority levels (critical, high,
medium, low).

### 3. log_prompts.py (UserPromptSubmit) - Optional

Logs conversation prompts to a [zk](https://github.com/zk-org/zk) notebook at `~/.claude-prompts/`. Requires:

- `zk` CLI installed (`brew install zk`)
- `~/.claude-prompts/` initialized as a zk notebook

Exits gracefully if prerequisites are missing.

### 4. ccnotify (All Events) - Optional

Desktop notifications for Claude Code events via [CCNotify](https://github.com/dazuiba/CCNotify). Tracks sessions in
SQLite database. Monitors:

- UserPromptSubmit
- PermissionRequest
- Notification
- Stop

**Prerequisites:**

- [terminal-notifier](https://github.com/julienXX/terminal-notifier) (macOS): `brew install terminal-notifier`
- Gracefully degrades if terminal-notifier is unavailable (logs warning instead of failing)

### 5. claude-code-docs Helper (PreToolUse:Read) - Optional

Quick documentation lookups via [claude-code-docs](https://github.com/ericbuess/claude-code-docs). Provides
`claude-docs-helper.sh` for local doc searches.

## License

This project is licensed under MIT.
