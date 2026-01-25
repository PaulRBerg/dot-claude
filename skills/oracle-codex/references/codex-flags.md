# Codex CLI Configuration Options

## Model Selection (`-m` / `--model`)

| Model           | Description                          |
| --------------- | ------------------------------------ |
| `gpt-5.2-codex` | Latest frontier agentic coding model |

## Reasoning Effort (`-c model_reasoning_effort=`)

Configured via `-c model_reasoning_effort=<level>` or in `~/.codex/config.toml`.

| Level    | Description                       | When to Use                                      |
| -------- | --------------------------------- | ------------------------------------------------ |
| `low`    | Fast responses, minimal reasoning | Single file review, syntax check, quick question |
| `medium` | Balanced speed and depth          | Multi-file review, focused feature planning      |
| `high`   | Deeper analysis, slower responses | Architecture analysis, cross-cutting concerns    |
| `xhigh`  | Maximum reasoning depth           | Large codebase planning, comprehensive audit     |

**Selection**: Choose effort level based on task complexity (see SKILL.md Reasoning Effort Guidelines).

## Sandbox Modes (`-s` / `--sandbox`)

| Mode                 | Description                   | Use Case                     |
| -------------------- | ----------------------------- | ---------------------------- |
| `read-only`          | No file modifications allowed | **Planning and code review** |
| `workspace-write`    | Can modify files in workspace | Implementation tasks         |
| `danger-full-access` | Full system access            | System-level operations      |

## Global Flags

These flags work with all Codex commands:

| Flag                      | Description                                                   |
| ------------------------- | ------------------------------------------------------------- |
| `-C <dir>` / `--cd <dir>` | Set working directory                                         |
| `--search`                | Enable live web search (native Responses `web_search` tool)   |
| `--add-dir <DIR>`         | Additional directories that should be writable                |
| `--no-alt-screen`         | Disable alternate screen mode (preserves terminal scrollback) |
| `--full-auto`             | Shorthand for workspace-write with auto-approval              |

## Exec Subcommand Flags

These flags are specific to `codex exec`:

| Flag                     | Description                       |
| ------------------------ | --------------------------------- |
| `-o <file>`              | Write output to file              |
| `--json`                 | Output in JSONL event format      |
| `--output-schema <FILE>` | Structured output schema          |
| `--skip-git-repo-check`  | Bypass git repository requirement |

## Review Subcommand

The `codex review` subcommand provides a streamlined interface for code reviews:

```bash
codex review [OPTIONS] [PROMPT]
```

| Flag              | Description                             |
| ----------------- | --------------------------------------- |
| `--uncommitted`   | Review uncommitted working tree changes |
| `--base <BRANCH>` | Review changes compared to base branch  |
| `--commit <SHA>`  | Review a specific commit                |

**Examples:**

```bash
# Review uncommitted changes
codex review --uncommitted

# Review changes against main branch
codex review --base main

# Review with specific focus
codex review --base main "Focus on security vulnerabilities"

# Review a specific commit
codex review --commit abc1234
```

## Example Commands

### Planning Query (High Complexity → `high`)

```bash
CODEX_OUTPUT="/tmp/codex-${RANDOM}${RANDOM}.txt"
codex exec \
  -m gpt-5.2-codex \
  -c model_reasoning_effort=high \
  -s read-only \
  -o "$CODEX_OUTPUT" \
  2>/dev/null <<'EOF'
Analyze this codebase and design an implementation plan for [feature].
EOF
```

### Code Review with `codex review`

```bash
# Simple review of uncommitted changes
codex review --uncommitted

# Review against main with custom instructions
codex review --base main "Check for SQL injection and XSS vulnerabilities"
```

### Planning Query with Web Search

```bash
CODEX_OUTPUT="/tmp/codex-${RANDOM}${RANDOM}.txt"
codex exec \
  -m gpt-5.2-codex \
  -c model_reasoning_effort=medium \
  -s read-only \
  --search \
  -o "$CODEX_OUTPUT" \
  2>/dev/null <<'EOF'
Research current best practices for [topic] and recommend an approach.
EOF
```

## User Configuration

Override defaults by specifying in the prompt:

- "Use model gpt-5.2-codex"
- "Use medium reasoning effort"
- "With high reasoning"
- "Enable web search"
