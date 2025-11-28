---
argument-hint: '[description]'
description: Create an issue in anthropics/claude-code
model: opus
---

## Context

- GitHub CLI auth: !`gh auth status 2>&1 | rg -q "Logged in" && echo "authenticated" || echo "not authenticated"`
- Claude Code version: !`claude --version 2>/dev/null || echo "unknown"`
- OS: !`uname -s`
- Terminal: !`echo "${TERM_PROGRAM:-${TERMINAL_EMULATOR:-unknown}}"`
- Arguments: $ARGUMENTS

## Your Task

Create an issue in `anthropics/claude-code`.

### STEP 1: Validate

IF not authenticated: ERROR "Run `gh auth login` first"

### STEP 2: Figure out issue type

From `$ARGUMENTS`, infer which template fits best:

| Keywords                                                      | Template              | Title Prefix |
| ------------------------------------------------------------- | --------------------- | ------------ |
| bug, broken, error, crash, fails, doesn't work                | `bug_report.yml`      | `[BUG] `     |
| feature, request, add, support, wish, would be nice           | `feature_request.yml` | `[FEATURE] ` |
| docs, documentation, unclear, confusing, readme               | `documentation.yml`   | `[DOCS] `    |
| model, claude did, unexpected, wrong files, reverted, ignored | `model_behavior.yml`  | `[MODEL] `   |

**IF ambiguous or no strong match**: Use AskUserQuestion with these options:

- Bug Report - something's broken
- Feature Request - new idea or enhancement
- Documentation - docs are missing/unclear
- Model Behavior - Claude did something unexpected

### STEP 3: Generate issue body

Based on the template type, generate a body with these sections:

______________________________________________________________________

#### For `bug_report.yml`:

```markdown
### What went wrong?

{describe the bug from $ARGUMENTS}

### What should happen?

{expected behavior}

### Steps to reproduce

1. {step 1}
2. {step 2}
3. ...

### Environment

- **Version**: {from context}
- **OS**: {from context}
- **Terminal**: {from context}
- **Platform**: Anthropic API (assume unless stated otherwise)
- **Model**: Sonnet (assume unless stated otherwise)

### Is this a regression?

{Yes/No/Don't know - infer from context}
```

______________________________________________________________________

#### For `feature_request.yml`:

```markdown
### Problem

{what problem does this solve?}

### Proposed solution

{how should it work?}

### Alternatives considered

{any workarounds or other approaches - or "None" if not mentioned}

### Priority

{Critical/High/Medium/Low - infer from urgency in $ARGUMENTS, default to Medium}

### Category

{infer from context: CLI commands and flags, Interactive mode (TUI), File operations, API and model interactions, MCP server integration, Performance and speed, Configuration and settings, Developer tools/SDK, Documentation, Other}
```

______________________________________________________________________

#### For `documentation.yml`:

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

______________________________________________________________________

#### For `model_behavior.yml`:

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

- **Version**: {from context}
- **OS**: {from context}
- **Model**: {Sonnet/Opus/Haiku - infer or default to Sonnet}
- **Platform**: Anthropic API
- **Permission mode**: {Accept Edits ON/OFF - infer from context or "unknown"}

### Can you reproduce this?

{Yes/Sometimes/No/Haven't tried}

### Impact

{Critical/High/Medium/Low}
```

______________________________________________________________________

### STEP 4: Generate title

Create a concise title (5-10 words) with the appropriate prefix:

- Bug: `[BUG] {what's broken}`
- Feature: `[FEATURE] {what you want}`
- Docs: `[DOCS] {what needs fixing}`
- Model: `[MODEL] {unexpected behavior}`

### STEP 5: Create the issue

```bash
gh issue create \
  --repo "anthropics/claude-code" \
  --title "$title" \
  --body "$(cat <<'EOF'
$body
EOF
)"
```

Note: Template labels (`bug`, `enhancement`, `documentation`, `model`) are applied automatically by GitHub when matching the template format.

Display: "Created: $URL"

On failure: show error and suggest fix

## Examples

```bash
# Bug report
/create-cc-issue "Claude crashes when I use special characters in file paths"

# Feature request
/create-cc-issue "Add support for .claud.toml config files"

# Docs issue
/create-cc-issue "The MCP server docs don't explain how to configure multiple servers"

# Model behavior
/create-cc-issue "Claude reverted my changes without asking when I said 'undo'"
```
