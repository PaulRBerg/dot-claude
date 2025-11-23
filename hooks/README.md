# Hooks

Custom event-driven automation hooks for Claude Code. These hooks extend Claude's behavior by responding to specific
events during execution.

## Overview

Several hooks provide event-driven automation across different Claude Code events:

- **ai-notify** - Desktop notifications for events (All events, optional)
- **ai-flags** - Parse flags from prompts to trigger behaviors (UserPromptSubmit)
- **activate_skills.py** - Auto-suggest skills based on context (UserPromptSubmit)
- **log_prompts.py** - Log conversations to zk notebook (UserPromptSubmit, optional)

## Hook Events

Hooks can respond to events like these:

- **UserPromptSubmit** - User submits a prompt
- **PreToolUse** - Before a tool is executed
- **PermissionRequest** - Permission requested for an action
- **Notification** - Claude sends a notification
- **Stop** - Session ends or is interrupted

## 1. ai-notify (All Events) - Optional

Desktop notifications for Claude Code events via [ai-notify](https://github.com/PaulRBerg/ai-notify).

### Monitored Events

- **UserPromptSubmit** - When you submit a prompt
- **PermissionRequest** - When Claude requests permission
- **Notification** - When Claude sends a notification
- **Stop** - When session ends or is interrupted

### Prerequisites

See [ai-notify repository](https://github.com/PaulRBerg/ai-notify) for installation instructions.

### Features

- Desktop notifications for important events
- Configurable notification preferences
- Works system-wide across all Claude Code sessions

See the [ai-notify repository](https://github.com/PaulRBerg/ai-notify) for setup instructions and configuration options.

## 2. ai-flags (UserPromptSubmit)

Standalone CLI tool that parses trailing flags from prompts to trigger different behaviors. Distributed as a Python
package and installed globally via uv. Flags must appear at the end of prompts with no other text after them.

### Prerequisites

- Python 3.12 or higher
- Installed via uv: `uv tool install ai-flags`
- See [ai-flags repository](https://github.com/PaulRBerg/ai-flags) for installation instructions

### Supported Flags

- **`-s`** (subagent): Injects [SUBAGENTS.md](UserPromptSubmit/SUBAGENTS.md) instructions, forcing Claude to delegate
  work to specialized subagents instead of doing everything itself. Mandates parallel delegation for independent
  subtasks, single agent for sequential work.

- **`-c`** (commit): Instructs Claude to execute `/commit` slash command after completing the task.

- **`-t`** (test): Adds testing emphasis context, requiring comprehensive test coverage including unit tests,
  integration tests, and edge cases.

- **`-d`** (debug): Invokes the debugger subagent for systematic root cause analysis with a 5-step debugging workflow.

- **`-n`** (no-lint): Skip linting and type-checking during development.

### Configuration

Configuration is managed via `~/.config/ai-flags/config.yaml`. Each flag can be enabled/disabled or customized:

```bash
# View current configuration
ai-flags config show

# Enable or disable a flag
ai-flags config set s enabled
ai-flags config set n disabled

# Edit configuration in your editor
ai-flags config edit

# Reset to defaults
ai-flags config reset
```

Users can override default flag instructions by setting custom `content` in the YAML configuration file.

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

### Testing

Test flag parsing and behavior using the CLI:

```bash
# Test flag parsing (displays parsed flags and injected context)
ai-flags handle "implement feature -s -c"

# Test with hook mode (JSON input/output for integration testing)
echo '{"prompt": "my task -t -c"}' | ai-flags handle

# Verify current configuration
ai-flags config show
```

## 3. activate_skills.py (UserPromptSubmit)

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

## 4. log_prompts.py (UserPromptSubmit) - Optional

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

Hooks with optional dependencies (zk, ai-notify) gracefully degrade if dependencies are unavailable. Check installation:

```bash
# Check zk
which zk

# Check ai-notify
which ai-notify

```

## Resources

- [ai-notify](https://github.com/PaulRBerg/ai-notify)
- [Claude Code Hooks Documentation](https://docs.anthropic.com/en/docs/claude-code/hooks) - Official Anthropic
  documentation
- [zk - Zettelkasten CLI](https://github.com/zk-org/zk)
