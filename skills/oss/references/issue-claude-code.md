# Claude Code Issue Workflow

This reference document describes the workflow for creating issues in the `anthropics/claude-code` repository. The workflow automatically selects the appropriate issue template based on the issue description and generates structured issue content.

## Validate Authentication

Check if GitHub CLI is authenticated:

```bash
gh auth status 2>&1 | rg -q "Logged in"
```

If not authenticated, error with: "Run `gh auth login` first"

## Determine Issue Type

From the issue description, infer which template fits best:

| Keywords                                                      | Template              | Title Prefix |
| ------------------------------------------------------------- | --------------------- | ------------ |
| bug, broken, error, crash, fails, doesn't work                | `bug_report.yml`      | `[BUG] `     |
| feature, request, add, support, wish, would be nice           | `feature_request.yml` | `[FEATURE] ` |
| docs, documentation, unclear, confusing, readme               | `documentation.yml`   | `[DOCS] `    |
| model, claude did, unexpected, wrong files, reverted, ignored | `model_behavior.yml`  | `[MODEL] `   |

**If ambiguous or no strong match**: Use AskUserQuestion with these options:

- Bug Report - something's broken
- Feature Request - new idea or enhancement
- Documentation - docs are missing/unclear
- Model Behavior - Claude did something unexpected

## Generate Issue Body

Based on the template type, generate a body with these sections:

### Bug Report Template

```markdown
### What went wrong?

{describe the bug from description}

### What should happen?

{expected behavior}

### Steps to reproduce

1. {step 1}
2. {step 2}
3. ...

### Environment

- **Version**: {claude --version}
- **OS**: {operating system and version}
- **Terminal**: {terminal program}
- **Platform**: Anthropic API (assume unless stated otherwise)
- **Model**: Sonnet (assume unless stated otherwise)

### Is this a regression?

{Yes/No/Don't know - infer from context}
```

### Feature Request Template

```markdown
### Problem

{what problem does this solve?}

### Proposed solution

{how should it work?}

### Alternatives considered

{any workarounds or other approaches - or "None" if not mentioned}

### Priority

{Critical/High/Medium/Low - infer from urgency, default to Medium}

### Category

{infer from context: CLI commands and flags, Interactive mode (TUI), File operations, API and model interactions, MCP server integration, Performance and speed, Configuration and settings, Developer tools/SDK, Documentation, Other}
```

### Documentation Template

```markdown
### What type of docs issue?

{Missing/Unclear/Incorrect/Typo/Missing examples/Broken links/Other}

### Section or topic

{which part of the docs}

### What's wrong or missing?

{describe the issue}

### Suggested fix

{how to improve it}

### Impact

{High/Medium/Low}
```

### Model Behavior Template

```markdown
### What'd you ask Claude to do?

{the prompt or command}

### What did Claude actually do?

{step by step what happened}

### What should've happened?

{expected behavior}

### Files affected

{list files that were modified unexpectedly, if applicable}

### Environment

- **Version**: {claude --version}
- **OS**: {operating system and version}
- **Model**: {Sonnet/Opus/Haiku - infer or default to Sonnet}
- **Platform**: Anthropic API
- **Permission mode**: {Accept Edits ON/OFF - infer from context or "unknown"}

### Can you reproduce this?

{Yes/Sometimes/No/Haven't tried}

### Impact

{Critical/High/Medium/Low}
```

## Generate Title

Create a concise title (5-10 words) with the appropriate prefix:

- Bug: `[BUG] {what's broken}`
- Feature: `[FEATURE] {what you want}`
- Docs: `[DOCS] {what needs fixing}`
- Model: `[MODEL] {unexpected behavior}`

## Create the Issue

Use GitHub CLI to create the issue:

```bash
gh issue create \
  --repo "anthropics/claude-code" \
  --title "$title" \
  --body "$(cat <<'EOF'
$body
EOF
)"
```

**Note**: Template labels (`bug`, `enhancement`, `documentation`, `model`) are applied automatically by GitHub when matching the template format.

Display: "Created: $URL"

On failure: show error and suggest fix

## Environment Detection

Gather environment information for bug reports and model behavior issues:

- **Claude Code version**: `claude --version 2>/dev/null || echo "unknown"`
- **Operating System**: Detect macOS version from Setup Assistant RTF file or use `sw_vers`
- **Terminal**: `${TERM_PROGRAM:-${TERMINAL_EMULATOR:-unknown}}`

## Examples

```bash
# Bug report
"Claude crashes when I use special characters in file paths"

# Feature request
"Add support for .claud.toml config files"

# Docs issue
"The MCP server docs don't explain how to configure multiple servers"

# Model behavior
"Claude reverted my changes without asking when I said 'undo'"
```
