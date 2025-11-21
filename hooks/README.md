# Hooks

Custom event-driven automation hooks for Claude Code. These hooks extend Claude's behavior by responding to specific
events during execution.

## Overview

Five custom hooks provide event-driven automation across different Claude Code events:

- **detect_flags.py** - Parse flags from prompts to trigger behaviors (UserPromptSubmit)
- **activate_skills.py** - Auto-suggest skills based on context (UserPromptSubmit)
- **log_prompts.py** - Log conversations to zk notebook (UserPromptSubmit, optional)
- **ccnotify** - Desktop notifications for events (All events, optional)
- **claude-code-docs** - Quick documentation lookups (PreToolUse:Read, optional)

## Hook Events

Hooks can respond to these events:

- **UserPromptSubmit** - User submits a prompt
- **PreToolUse** - Before a tool is executed
- **PostToolUse** - After a tool is executed
- **PermissionRequest** - Permission requested for an action
- **Notification** - Claude sends a notification
- **Stop** - Session ends or is interrupted

## 1. detect_flags.py (UserPromptSubmit)

General-purpose flag parser that processes trailing flags in prompts to trigger different behaviors. Flags must appear
at the end of prompts with no other text after them.

### Supported Flags

- **`-s`** (subagent): Injects [SUBAGENTS.md](UserPromptSubmit/SUBAGENTS.md) instructions, forcing Claude to delegate
  work to specialized subagents instead of doing everything itself. Mandates parallel delegation for independent
  subtasks, single agent for sequential work.

- **`-c`** (commit): Instructs Claude to execute `/commit` slash command after completing the task.

- **`-t`** (test): Adds testing emphasis context, requiring comprehensive test coverage including unit tests,
  integration tests, and edge cases.

- **`-d`** (debug): Invokes the debugger subagent for systematic root cause analysis with a 5-step debugging workflow.

- **`-n`** (no-lint): Skip linting and type-checking during development.

### Composability

Flags combine naturally into complete workflows:

- `implement payment API -s -t -c` → delegate to agents, emphasize tests, commit when done
- `fix memory leak -d -c` → debug mode, commit fix
- `add OAuth flow -s -c` → orchestrate implementation, auto-commit

**Order independence**: `-s -c -t` works identically to `-t -c -s`.

### Usage Examples

```bash
# Use subagents for complex task
claude "refactor authentication system -s"

# Add tests and commit when done
claude "implement user validation -t -c"

# Full workflow: delegate, test, and commit
claude "add payment integration -s -t -c"

# Debug mode with auto-commit
claude "fix memory leak in cache -d -c"

# Skip linting during rapid development
claude "prototype new feature -n"
```

## 2. activate_skills.py (UserPromptSubmit)

Analyzes user prompts and suggests relevant skills based on keywords, intent patterns, file patterns, and content
patterns.

### Configuration

Configuration in `skills/skill-rules.json` defines:

- **Trigger conditions**: Keywords, intent patterns, file patterns, content patterns
- **Priority levels**: critical, high, medium, low
- **Activation rules**: When to suggest or enforce skill activation

### How It Works

1. User submits a prompt
2. Hook analyzes prompt for skill triggers
3. Matches against skill-rules.json configuration
4. Suggests relevant skills based on priority
5. Claude can activate suggested skills automatically

### Example

If you mention "TypeScript refactoring" or work with `.ts` files, the hook suggests activating the `typescript` skill.

## 3. log_prompts.py (UserPromptSubmit) - Optional

Logs conversation prompts to a [zk](https://github.com/zk-org/zk) notebook at `~/.claude-prompts/` for tracking and
analysis.

### Prerequisites

- `zk` CLI installed: `brew install zk`
- `~/.claude-prompts/` initialized as a zk notebook:
  ```bash
  mkdir -p ~/.claude-prompts
  cd ~/.claude-prompts
  zk init
  ```

### Behavior

- Exits gracefully if prerequisites are missing
- Creates dated entries in zk notebook
- Logs user prompts and context for future reference
- Useful for tracking conversations and patterns over time

### Setup

```bash
# Install zk
brew install zk

# Initialize notebook
mkdir -p ~/.claude-prompts
cd ~/.claude-prompts
zk init
```

## 4. ccnotify (All Events) - Optional

Desktop notifications for Claude Code events via [CCNotify](https://github.com/dazuiba/CCNotify). Tracks sessions in
SQLite database.

### Monitored Events

- **UserPromptSubmit** - When you submit a prompt
- **PermissionRequest** - When Claude requests permission
- **Notification** - When Claude sends a notification
- **Stop** - When session ends or is interrupted

### Prerequisites

- [terminal-notifier](https://github.com/julienXX/terminal-notifier) (macOS): `brew install terminal-notifier`
- Gracefully degrades if terminal-notifier is unavailable (logs warning instead of failing)

### Features

- Desktop notifications for important events
- SQLite session tracking
- Configurable notification preferences
- Works system-wide across all Claude Code sessions

### Setup

```bash
# Install terminal-notifier
brew install terminal-notifier

# ccnotify will automatically set up on first use
```

## 5. claude-code-docs Helper (PreToolUse:Read) - Optional

Quick documentation lookups via [claude-code-docs](https://github.com/ericbuess/claude-code-docs). Provides
`claude-docs-helper.sh` for local doc searches.

### Features

- Local mirror of Claude Code documentation
- Fast doc lookups without network requests
- Integrates with Read tool
- Helpful for offline development

### Setup

```bash
# Clone claude-code-docs
git clone https://github.com/ericbuess/claude-code-docs ~/.claude-code-docs

# Update documentation regularly
cd ~/.claude-code-docs
git pull
```

## Development

### Testing Hooks

Run hook tests with pytest:

```bash
# Run all tests
just test

# Run hook tests specifically
just test-hooks
```

## Troubleshooting

### Hook Not Firing

1. Check hook is enabled in `settings/hooks.jsonc`
2. Verify hook script is executable: `ls -la hooks/*/your-hook`
3. Check hook output in Claude Code logs
4. Test hook independently: `python hooks/UserPromptSubmit/your-hook/your-hook.py`

### Permission Errors

Hooks must be executable:

```bash
chmod +x hooks/**/*.py
chmod +x hooks/**/*.sh
```

### Optional Dependencies Missing

Hooks with optional dependencies (zk, terminal-notifier, claude-code-docs) gracefully degrade if dependencies are
unavailable. Check installation:

```bash
# Check zk
which zk

# Check terminal-notifier
which terminal-notifier

# Check claude-code-docs
ls -la ~/.claude-code-docs
```

## Resources

- [Claude Code Hooks Documentation](https://docs.anthropic.com/en/docs/claude-code/hooks) - Official Anthropic
  documentation
- [zk - Zettelkasten CLI](https://github.com/zk-org/zk)
- [CCNotify](https://github.com/dazuiba/CCNotify)
- [claude-code-docs](https://github.com/ericbuess/claude-code-docs)
- [terminal-notifier](https://github.com/julienXX/terminal-notifier)
