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
- **guard_rm** - Deny recursive `rm` of system, home-level, and git repository directories (PreToolUse)
- **git_guard** - Deny shared-worktree git sweeps and ask before force pushes, in any option order (PreToolUse)
- **command_guard** - Deny system-level commands such as `sudo`, `dd`, and `kill -9` (PreToolUse)
- **path_guard** - Deny reads and edits of secrets and user-owned files (PreToolUse)
- **enable_computer_use** - Enable the built-in `computer-use` MCP server for the session's project (SessionStart)
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
[ai-notify](https://github.com/PaulRBerg/agent-skills/tree/main/toolkit/notify).

### Monitored Events

- **UserPromptSubmit** - When you submit a prompt
- **PreToolUse** (`AskUserQuestion` matcher) - When Claude asks you a question
- **Notification** - When Claude sends a notification, including a permission prompt
- **Stop** - When session ends or is interrupted
- **StopFailure** - When the session stops on a failure

`PermissionRequest` is deliberately not hooked: a hook on that event with any matcher makes Claude Code ignore
`CLAUDE_CODE_EVEN_MORE_DANGEROUSLY_SKIP_PERMISSIONS` (see [guard_rm](#5-guard_rm-pretooluse-bash)).

### Prerequisites

See [ai-notify repository](https://github.com/PaulRBerg/agent-skills/tree/main/toolkit/notify) for installation
instructions.

### Features

- Desktop notifications for important events
- Configurable notification preferences
- Works system-wide across all Claude Code sessions

See the [ai-notify repository](https://github.com/PaulRBerg/agent-skills/tree/main/toolkit/notify) for setup
instructions and configuration options.

## 2. copy_prompt_to_clipboard (UserPromptSubmit)

Copies user prompts to the macOS clipboard via `pbcopy` for [Raycast](https://www.raycast.com) clipboard history. Skips
events with `agent_id`, subagent transcript paths, and internal notification envelopes. An `agent_type` alone does not
exclude a prompt because a user can select a top-level agent profile.

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

## 5. guard_rm (PreToolUse, `Bash`)

Sessions run in `bypassPermissions` mode, and `~/.zshenv` exports `CLAUDE_CODE_EVEN_MORE_DANGEROUSLY_SKIP_PERMISSIONS=1`
so that Claude Code no longer prompts for `rm` on critical paths. Claude Code reads the variable from the launch
environment only, and ignores it when any of these holds:

- a deny or ask rule in any settings file names Bash, Edit, or Read
- a `PermissionRequest` hook is registered
- a `PreToolUse` hook answers `ask` for a removal

So these guards (sections 5, 6, 8, and 9) replace permission rules, and each answers `deny`. A startup line that says
the variable `has no effect in this session` means one of the conditions above is back.

With the built-in prompt off, guard_rm denies a recursive `rm` of:

- the filesystem root and system top-level directories, such as `/usr` or `/Volumes/<drive>`
- the home directory, its visible top-level directories, and a fixed list of dot-directories, such as `~/.claude`
- a git repository root or its `.git` directory, outside temp, cache, and `node_modules` directories
- the whole contents of any of these through a `*` or `.*` glob, such as `repo/*`
- a path under an unset variable that lands on one of these when the variable is empty, such as `"$DIR"/*`

Every other `rm` runs unprompted. A denial cannot be approved from a prompt: Claude narrows the path or asks you to run
the command.

It tracks `cd` and plain assignments within the command and expands `~`, environment variables, `$(pwd)`, and globs.
`xargs rm`, `find -delete`, and other command substitutions pass through unchecked, so it guards against mistakes, not
adversarial commands.

## 6. git_guard (PreToolUse, `Bash`)

This hook parses every git invocation in a Bash command, including compound commands, `$(...)`, wrappers such as `env`,
and `bash -c` scripts, and checks its options in any order:

- denies bare `git stash` and stash push/save/clear, `git add -A`/`--all`/`.`/pathless `-u`, `git commit -a`/`--all`,
  `git checkout .`, `git restore .`, `git reset --hard`, `git clean`, and autostash on pull, rebase, or merge;
- asks before any force push, including `git -C repo push --force` and `+refspec` pushes.

`git stash list`/`show`/`pop` stay usable. Heredoc bodies are skipped unless they feed a shell, and a command that
cannot be lexed as a whole is checked line by line. That parsing lives in `shell_commands.py`, which all four guards
share.

## 7. enable_computer_use (SessionStart, `startup`)

The built-in `computer-use` MCP server is off until a project lists it in `~/.claude.json` →
`projects[<path>].enabledMcpServers`, which `/mcp` writes one project at a time. No settings.json key enables it
globally. This hook adds the entry for the session's project (git root, else cwd), and the CLI picks up the change. It
skips projects the CLI has not recorded yet, so a brand-new project gets it from its second session. Backfill every
known project with `hooks/SessionStart/enable_computer_use.py --all`.

## 8. command_guard (PreToolUse, `Bash`)

Denies system-level commands wherever they appear in a Bash command, including behind wrappers and in `bash -c` scripts:

- `sudo`, `doas`, `su`, `passwd`, `userdel`, `usermod`
- `dd`, `mkfs`, `reboot`, `shutdown`, `systemctl`
- `killall` and `kill -9`
- recursive `chmod` and `chown`
- `npm publish`

It matches the program a command names, so `xargs`, `eval`, or an interpreter can still hide one.

## 9. path_guard (PreToolUse, file tools and `Bash`)

Denies reads and edits of everything under `~/.ssh` and `~/Drive/Secrets`, and of any `PROMPT.md` or `TODO.md`. It
checks the path a file tool names, the directory Grep and Glob search, and in Bash the operands of file commands such as
`cat`, `sed`, and `cp`, plus redirection targets. It resolves symlinks.

It does not see a command that reads files without naming them, such as `grep -r pattern .`. Unlike the `Read` deny
rules it replaces, it does not filter `@file` mentions or the results of a Grep or Glob over a parent directory.

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

- [ai-notify](https://github.com/PaulRBerg/agent-skills/tree/main/toolkit/notify)
- [Claude Code Hooks Documentation](https://docs.anthropic.com/en/docs/claude-code/hooks) - Official Anthropic
  documentation
