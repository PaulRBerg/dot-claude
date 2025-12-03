# Codex CLI Configuration Options

## Model Selection (`-m` / `--model`)

| Model               | Description                                         |
| ------------------- | --------------------------------------------------- |
| `o3`                | OpenAI o3 reasoning model                           |
| `o4-mini`           | Lightweight reasoning model                         |
| `gpt-5.1-codex-max` | Maximum capability Codex model (default for oracle) |

## Reasoning Effort (`-c model_reasoning_effort=`)

Configured via `-c model_reasoning_effort=<level>` or in `~/.codex/config.toml`.

| Level    | Description                                  |
| -------- | -------------------------------------------- |
| `low`    | Fast responses, minimal reasoning            |
| `medium` | Balanced speed and depth                     |
| `high`   | Deeper analysis, slower responses            |
| `xhigh`  | Maximum reasoning depth (default for oracle) |

## Sandbox Modes (`-s` / `--sandbox`)

| Mode                 | Description                   | Use Case                     |
| -------------------- | ----------------------------- | ---------------------------- |
| `read-only`          | No file modifications allowed | **Planning and code review** |
| `workspace-write`    | Can modify files in workspace | Implementation tasks         |
| `danger-full-access` | Full system access            | System-level operations      |

## Common Flags

| Flag                      | Description                                      |
| ------------------------- | ------------------------------------------------ |
| `--skip-git-repo-check`   | Bypass git repository requirement                |
| `--json`                  | Output in JSON format                            |
| `-o <file>`               | Write output to file                             |
| `-C <dir>` / `--cd <dir>` | Set working directory                            |
| `--full-auto`             | Shorthand for workspace-write with auto-approval |

## Example Commands

### Planning Query

```bash
codex exec \
  -m gpt-5.1-codex-max \
  -c model_reasoning_effort=xhigh \
  -s read-only \
  --skip-git-repo-check \
  2>/dev/null <<'EOF'
Analyze this codebase and design an implementation plan for [feature].
EOF
```

### Code Review Query

```bash
codex exec \
  -m gpt-5.1-codex-max \
  -c model_reasoning_effort=xhigh \
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
