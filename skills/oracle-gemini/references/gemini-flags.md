# Gemini CLI Configuration Options

## Model Selection (`-m` / `--model`)

| Model                  | Description                              | Context Window |
| ---------------------- | ---------------------------------------- | -------------- |
| `gemini-3-pro-preview` | Latest model with cutting-edge reasoning | 1M tokens      |
| `gemini-2.5-pro`       | Advanced model with maximum capability   | 1M tokens      |
| `gemini-2.5-flash`     | Faster model with good reasoning ability | 1M tokens      |

## Output Format (`-o` / `--output-format`)

| Format        | Description                 | Use Case                     |
| ------------- | --------------------------- | ---------------------------- |
| `text`        | Plain text output (default) | General queries and analysis |
| `json`        | JSON-formatted output       | Programmatic consumption     |
| `stream-json` | Streaming JSON output       | Large responses, real-time   |

## Approval Mode (`--approval-mode`)

| Mode        | Description                             | Use Case                       |
| ----------- | --------------------------------------- | ------------------------------ |
| `default`   | Prompt for approval before file changes | Safe, controlled modifications |
| `auto_edit` | Automatically apply changes without ask | Trusted batch operations       |
| `yolo`      | Apply changes immediately, no approval  | Experimental or scripted tasks |

## Sandbox Mode (`--sandbox`)

| Flag        | Description                   | Use Case                     |
| ----------- | ----------------------------- | ---------------------------- |
| (not set)   | Full sandbox restrictions     | **Planning and code review** |
| `--sandbox` | Enable sandbox mode (boolean) | Safe execution environment   |

## Common Flags

| Flag                    | Description                           |
| ----------------------- | ------------------------------------- |
| `--yolo`                | Shorthand for `--approval-mode yolo`  |
| `--include-directories` | Include directory contents in context |
| `-h` / `--help`         | Display help information              |
| `--version`             | Display version information           |
| `-v` / `--verbose`      | Enable verbose output                 |

## Model Comparison

### gemini-3-pro-preview

- **Best for:** Critical decisions, maximum reasoning capability, cutting-edge analysis
- **Speed:** Slowest, optimized for accuracy and depth
- **Reasoning:** State-of-the-art multi-step reasoning
- **Context:** 1M token window
- **Note:** Preview model, requires `previewFeatures: true` in settings

### gemini-2.5-pro

- **Best for:** Complex analysis, comprehensive code review, architectural decisions
- **Speed:** Slower, optimized for accuracy
- **Reasoning:** Advanced multi-step reasoning
- **Context:** 1M token window

### gemini-2.5-flash

- **Best for:** Quick responses, single-file analysis, rapid iteration
- **Speed:** Fastest response times
- **Reasoning:** Good for most tasks, optimized for speed
- **Context:** 1M token window
