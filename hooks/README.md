# Hooks

Custom event-driven automation hooks for Claude Code. These hooks extend Claude's behavior by responding to specific
events during execution.

## Overview

Several hooks provide event-driven automation across different Claude Code events:

- **ai-notify** - Desktop notifications for events (All events, optional)
- **copy_prompt_to_clipboard** - Copy each submitted prompt to the macOS clipboard (UserPromptSubmit)

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

## 2. copy_prompt_to_clipboard (UserPromptSubmit)

Copies every submitted prompt to the macOS clipboard via `pbcopy` so it shows up in
[Raycast](https://www.raycast.com)'s clipboard history — a searchable log of what you asked.

### Sanitization

Raw prompts are noisy, so the text is sanitized before it reaches the clipboard:

- **Claude Code markers** (`[Pasted text #N +M lines]`, `[Image #N]`, `[...Truncated text #N]`) are normalized to
  `Pasted`.
- **Fenced code blocks** (3+ backticks, terminated or not) collapse to `[code]`.
- **Oversized content** — any line longer than `LONG_LINE_CHARS` collapses to `[Pasted]`; prompts exceeding `MAX_LINES`
  or `MAX_CHARS` keep a bounded head and mark the rest `[Pasted]`.
- Excess blank lines are squeezed; an empty result skips `pbcopy` so the clipboard is never clobbered.

After sanitizing, a compact provenance prefix such as `[repo:dot-claude session:00893aaf]` is prepended so each
clipboard entry is traceable to its source repo and session.

The thresholds are module-level constants at the top of the script, easy to tune.

### Notes

- `UserPromptSubmit` hooks inject **stdout** into the model context, so this hook writes nothing to stdout — it only
  copies as a side effect and always exits 0.
- Set `CLAUDE_CLIP_DEBUG=1` to append raw stdin to `UserPromptSubmit/.debug.jsonl` for a one-shot check of how a paste
  is represented.

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
