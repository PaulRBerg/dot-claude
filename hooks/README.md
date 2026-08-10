# Hooks

Custom event-driven automation hooks for Claude Code. These hooks extend Claude's behavior by responding to specific
events during execution.

## Overview

Several hooks provide event-driven automation across different Claude Code events:

- **ai-notify** - Desktop notifications for events (All events, optional)
- **copy_prompt_to_clipboard** - Copy each submitted prompt to the macOS clipboard (UserPromptSubmit)
- **agent presence context line** - Show other agents and pending-note counts in the prompt context (UserPromptSubmit)
- **add_plan_frontmatter** - Add YAML frontmatter to plan files (PostToolUse)
- **ai-coord** - Track lifecycle, presence, and approved plan intent across Claude Code and Codex

## Hook Events

Hooks can respond to events like these:

- **UserPromptSubmit** - User submits a prompt
- **PreToolUse** - Before a tool is executed
- **PostToolUse** - After a tool has executed
- **PermissionRequest** - Permission requested for an action
- **Notification** - Claude sends a notification
- **Stop** - Session ends or is interrupted

## 1. ai-notify (All Events) - Optional

Desktop notifications for Claude Code events via
[ai-notify](https://github.com/PaulRBerg/agent-toolkit/tree/main/notify).

### Monitored Events

- **UserPromptSubmit** - When you submit a prompt
- **PreToolUse** (`AskUserQuestion` matcher) - When Claude asks you a question
- **PermissionRequest** - When Claude requests permission
- **Notification** - When Claude sends a notification
- **Stop** - When session ends or is interrupted

### Prerequisites

See [ai-notify repository](https://github.com/PaulRBerg/agent-toolkit/tree/main/notify) for installation instructions.

### Features

- Desktop notifications for important events
- Configurable notification preferences
- Works system-wide across all Claude Code sessions

See the [ai-notify repository](https://github.com/PaulRBerg/agent-toolkit/tree/main/notify) for setup instructions and
configuration options.

## 2. copy_prompt_to_clipboard (UserPromptSubmit)

Copies every submitted prompt to the macOS clipboard via `pbcopy` so it shows up in [Raycast](https://www.raycast.com)'s
clipboard history — a searchable log of what you asked.

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

## 3. agent presence context line (UserPromptSubmit)

Injects a compact line such as
`agents: 2 other sessions in this repo (refactor, codex/abcd1234); 1 note pending — run agents-status` when other
sessions share the repository or pending notes exist. Session labels and names are sanitized before they reach the
prompt context: whitespace is collapsed, control characters are stripped, and identifiers are capped at 80 characters.

Pending notes are represented only by a count; their text is never injected, by design, as a prompt-injection guard. The
hook is silent when this is a solo session with no notes, and on any error. Claude Code and Codex both invoke the
installed `ai-coord` CLI for lifecycle and presence updates.

## 4. add_plan_frontmatter (PostToolUse)

Intercepts Write tool executions and adds YAML frontmatter (metadata such as the creation timestamp and git branch) to
plan files in any `.claude/plans/` directory — both `~/.claude/plans/` and project-local ones. See
[claude-code#12378](https://github.com/anthropics/claude-code/issues/12378).

## 5. ai-coord plan intent (PostToolUse, `ExitPlanMode`)

The `ai-coord hook claude` handler records the approved plan's first H1, capped at 80 characters, as a pathless intent
label. The handler is silent and fail-open; path ownership still requires `ai-coord start` before editing.

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
4. Test hook independently: `python hooks/<Event>/<hook>.py`

### Permission Errors

Hooks must be executable:

```bash
chmod +x hooks/**/*.py
```

### Optional Dependencies Missing

Hooks with optional dependencies (ai-notify) gracefully degrade if dependencies are unavailable. Check installation:

```bash
which ai-notify
```

## Resources

- [ai-notify](https://github.com/PaulRBerg/agent-toolkit/tree/main/notify)
- [Claude Code Hooks Documentation](https://docs.anthropic.com/en/docs/claude-code/hooks) - Official Anthropic
  documentation
