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

Context files are organized by concern (languages, tools, etc.) and imported via `@filename.md` references. Base
instructions cascade through specialized modules, creating layered behavioral policies without duplication.

## Commands

[Slash commands](https://docs.claude.com/en/docs/claude-code/slash-commands) are defined in `commands/*.md`.

Twelve custom commands cover GitHub workflows (PR/issue management), release automation, code quality validation, and
activity tracking. Commands use semantic analysis to understand code changes rather than relying on filenames. They
feature natural argument parsing (`/commit fix auth --short`), smart defaults (auto-stage changes, detect reviewers),
and stateless execution without interactive prompts.

## Skills

[Claude Skills](https://docs.claude.com/en/docs/claude-code/skills) in `skills/` auto-activate based on context:

- **typescript**: TypeScript engineering practices and patterns for `.ts`/`.tsx` files
- **web3-frontend**: Secure wallet interactions and production-grade dApp development with Viem/Wagmi
- **ui-ux-design**: Interface design, wireframes, and design system creation

Skills use imperative voice and trigger-rich descriptions, activating automatically when working with relevant file types, technologies, or domain concepts.

## Agents

Four specialized subagents in `agents/` handle domain-specific work: code review, debugging, web3 backend engineering, and tool discovery. Agents are invoked via the `-s` orchestration flag or directly through the Task tool.

## Hooks

Custom hooks in `hooks/` extend Claude Code with event-driven automation.

### prompt-flags.py

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

**Composability**: Flags combine naturally into complete workflows:

- `implement payment API -s -t -c` → delegate to agents, emphasize tests, commit when done
- `fix memory leak -d -c` → debug mode, commit fix
- `add OAuth flow -s -c` → orchestrate implementation, auto-commit

**Order independence**: `-s -c -t` works identically to `-t -c -s`.

Other hooks handle notifications (`ccnotify`) and documentation helpers.

### Nice-to-Have Utilities

Some nice-to-have utilities:

- **[ccnotify](https://github.com/dazuiba/CCNotify)**: Custom notifications for Claude Code
- **[ccstatusline](https://github.com/sirmalloc/ccstatusline)**: Custom status line for Claude Code
- **[claude-code-docs](https://github.com/ericbuess/claude-code-docs)**: Local mirror of Claude Code documentation from
  Anthropic

## License

This project is licensed under MIT.
