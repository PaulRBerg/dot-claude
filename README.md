# Claude Code config

PRB's `.claude` directory.

## Settings

[settings.json](settings.json#L1) configures permissions, hooks, and environment:

- **Permissions**:
  - Pre-approved commands (e.g. `git`, `grep`, etc.) and tools (MCP servers, file ops) run without confirmation.
  - Destructive operations (`sudo`, `rm -rf`, system files) are blocked.
- **Hooks**: Event-driven automation, see the [docs](https://docs.claude.com/en/docs/claude-code/hooks) for more info.
- **Status Line**: Custom status via `ccstatusline`

## Context

Modular configuration system using `@` syntax for composable behavioral instructions:

```markdown
# Example: BASE.md
@CRITICAL_THINKING.md
@SENIOR_PROGRAMMER.md
@tools/JUST.md
```

Context files are organized by concern (languages, tools, etc.) and imported via `@filename.md` references. Base instructions cascade through specialized modules, creating layered behavioral policies without duplication.

## Commands

[Slash commands](https://docs.claude.com/en/docs/claude-code/slash-commands) are defined in `commands/*.md`.

Commands use semantic analysis to understand code changes rather than relying on filenames. They feature natural argument parsing (`/commit fix auth --short`), smart defaults (auto-stage changes, detect reviewers), and stateless execution without interactive prompts.

## Hooks

Custom hooks in `hooks/` extend Claude Code with event-driven automation.

### append-subagents.py

The most critical hook. Appends orchestration instructions when prompts end with `-s` flag, forcing Claude to delegate work to specialized subagents instead of doing everything itself.

**Why**: Claude often tries to handle complex tasks directly instead of spawning parallel agents. This hook guarantees orchestration mode by injecting [ORCHESTRATOR.md](hooks/UserPromptSubmit/ORCHESTRATOR.md) which mandates:
- Parallel delegation when possible (independent subtasks)
- Single agent for sequential work
- No direct implementation by orchestrator

**Usage**: `Add user analytics dashboard -s` → spawns frontend/backend/database agents in parallel

Other hooks handle notifications (`ccnotify`) and documentation helpers.


### Nice-to-Have Utilities

Some nice-to-have utilities:

- **[ccnotify](https://github.com/dazuiba/CCNotify)**: Custom notifications for Claude Code
- **[ccstatusline](https://github.com/sirmalloc/ccstatusline)**: Custom status line for Claude Code
- **[claude-code-docs](https://github.com/ericbuess/claude-code-docs)**: Local mirror of Claude Code documentation from
  Anthropic

## License

This project is licensed under MIT.
