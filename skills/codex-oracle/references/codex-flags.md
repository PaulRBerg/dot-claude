# Codex CLI Configuration Options

## Model Selection (`-m` / `--model`)

| Model               | Description                                         |
| ------------------- | --------------------------------------------------- |
| `o3`                | OpenAI o3 reasoning model                           |
| `o4-mini`           | Lightweight reasoning model                         |
| `gpt-5.1-codex-max` | Maximum capability Codex model (default for oracle) |

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

## Common Flags

| Flag                      | Description                                                     |
| ------------------------- | --------------------------------------------------------------- |
| `--skip-git-repo-check`   | Bypass git repository requirement                               |
| `--json`                  | Output in JSON format                                           |
| `-o <file>`               | Write output to file                                            |
| `-C <dir>` / `--cd <dir>` | Set working directory                                           |
| `--full-auto`             | Shorthand for workspace-write with auto-approval                |
| `--profile <name>`        | Load profile from config (e.g., `quiet` disables notifications) |

## Example Commands

### Planning Query (High Complexity → `high`)

```bash
codex exec \
  -m gpt-5.1-codex-max \
  -c model_reasoning_effort=high \
  -s read-only \
  --skip-git-repo-check \
  2>/dev/null <<'EOF'
Analyze this codebase and design an implementation plan for [feature].
EOF
```

### Silent Profile Example (Maximum Complexity → `xhigh`)

```bash
codex --profile quiet exec \
  -m gpt-5.1-codex-max \
  -c model_reasoning_effort=xhigh \
  -s read-only \
  --skip-git-repo-check \
  2>/dev/null <<'EOF'
Comprehensive architecture review of the entire codebase.
EOF
```

*Codex-oracle uses `--profile quiet` by default; switch profiles only if the user explicitly asks for notifications or another profile.*

### Code Review Query (Moderate Complexity → `medium`)

```bash
codex exec \
  -m gpt-5.1-codex-max \
  -c model_reasoning_effort=medium \
  -s read-only \
  --skip-git-repo-check \
  2>/dev/null <<'EOF'
Review the following code for bugs, security issues, and improvements:
[code]
EOF
```

## User Configuration

Override defaults by specifying in the prompt:

- "Use model gpt-5.1-codex instead"
- "Use medium reasoning effort"
- "With high reasoning"
