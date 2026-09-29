# Hooks

Custom event-driven automation hooks for Claude Code. These hooks extend Claude's behavior by responding to specific
events during execution.

## Overview

Several hooks provide event-driven automation across different Claude Code events:

- **ai-notify** - Desktop notifications for events (All events, optional)
- **copy_prompt_to_clipboard** - Copy each submitted prompt to the macOS clipboard (UserPromptSubmit)
- **agent presence context line** - Show other agents, finding counts, and the scope-acquisition reminder in the prompt
  context (UserPromptSubmit)
- **add_plan_frontmatter** - Add YAML frontmatter to plan files (PostToolUse)
- **git_guard** - Deny shared-worktree git sweeps and ask before force pushes, in any option order (PreToolUse)
- **guard_rm** - Ask before recursive `rm` of home-level entries and git repositories (PreToolUse)
- **ai-coord** - Track lifecycle and presence across Claude Code and Codex

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
- **StopFailure** - When the session stops on a failure

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

Injects a compact line such as:

```text
ai-coord: Findings: pending=1; triaging=0; handed-off=0. Peers: 2; queued work: 1; unread messages: 1. Acquire scopes with `ai-coord start` before the first edit.
```

It is built from up to three fragments, in this order:

- `Findings: pending=N; triaging=N; handed-off=N.` when the repository has any recorded findings
- `Peers: N; queued work: N; unread messages: N.` when other sessions share the repository, work is queued, or messages
  are unread
- The reminder ``Acquire scopes with `ai-coord start` before the first edit.`` when the coordination gate applies
  (another session has active or queued work, or uncommitted changes belong to no claim) and the line still fits

The line is sanitized before it reaches the prompt context: whitespace is collapsed, control characters are stripped,
and the whole line is capped at 200 characters.

Findings are represented only by state counts; their text is never injected, by design, as a prompt-injection guard. The
hook is silent when there are no findings, peers, queued work, unread messages, or gate reminder, and on any error.
Claude Code and Codex both invoke the installed `ai-coord` CLI for lifecycle and presence updates.

## 4. add_plan_frontmatter (PostToolUse)

Intercepts Write tool executions and adds YAML frontmatter (metadata such as the creation timestamp and git branch) to
plan files in any `.claude/plans/` directory — both `~/.claude/plans/` and project-local ones. See
[claude-code#12378](https://github.com/anthropics/claude-code/issues/12378).

## 5. guard_rm (PreToolUse, `Bash(rm *)`)

Sessions run in `bypassPermissions` mode, where Claude Code's built-in critical-path check only prompts for the
filesystem root, its top-level directories, the home directory, and the working directory with its parents. This hook
returns an `ask` decision, which still prompts in bypass mode, when a recursive `rm` targets:

- the home directory or one of its direct children, such as `~/work` or `~/Library`
- a git repository root or `.git` directory outside temp directories
- the contents of any of these through a trailing glob, such as `repo/*`

It tracks `cd` within the command and expands `~`, `$HOME`, and globs. Other variables, `xargs rm`, and commands it
cannot tokenize pass through unchecked, so it guards against mistakes, not adversarial commands.

## 6. git_guard (PreToolUse, `Bash`)

The git entries in `settings/permissions/bash.jsonc` match options only in fixed positions, so `git commit -m x -a`,
`git add -v .`, `git reset HEAD~1 --hard`, or `git -C repo stash` slip past them. This hook parses every git invocation
in a Bash command, including compound commands, `$(...)`, wrappers such as `env` or `sudo`, and `bash -c` scripts, and:

- denies bare `git stash` and stash push/save/clear, `git add -A`/`--all`/`.`/pathless `-u`, `git commit -a`/`--all`,
  `git checkout .`, `git restore .`, `git reset --hard`, `git clean`, and autostash on pull, rebase, or merge;
- asks before any force push, including `git -C repo push --force` and `+refspec` pushes.

`git stash list`/`show`/`pop` stay usable. It runs without an `if` filter because git can follow wrappers that prefix
patterns miss. Commands it cannot tokenize pass through to the permission rules.

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
