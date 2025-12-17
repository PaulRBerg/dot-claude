# Codex CLI Issue Workflow

This reference document describes the workflow for creating issues in the `openai/codex` repository. The workflow automatically selects the appropriate issue template based on the issue description and generates structured issue content.

## Validate Authentication

Check if GitHub CLI is authenticated:

```bash
gh auth status 2>&1 | rg -q "Logged in"
```

If not authenticated, error with: "Run `gh auth login` first"

## Determine Issue Type

From the issue description, infer which template fits best:

| Keywords                                                 | Template                  | Title Prefix   |
| -------------------------------------------------------- | ------------------------- | -------------- |
| bug, broken, error, crash, fails, doesn't work           | `2-bug-report.yml`        | `[BUG] `       |
| feature, request, add, support, wish, would be nice      | `4-feature-request.yml`   | `[FEATURE] `   |
| docs, documentation, unclear, confusing, readme, example | `3-docs-issue.yml`        | `[DOCS] `      |
| vscode, extension, cursor, windsurf, ide                 | `5-vs-code-extension.yml` | `[EXTENSION] ` |

**If ambiguous or no strong match**: Use AskUserQuestion with these options:

- Bug Report - something's broken in the CLI
- Feature Request - new idea or enhancement
- Documentation - docs are missing/unclear
- VS Code Extension - issue with the IDE extension

## Generate Issue Body

Based on the template type, generate a body with these sections:

### Bug Report Template

```markdown
### What version of Codex is running?

{codex --version}

### What subscription do you have?

{Plus/Pro/Team/Enterprise - infer from context or ask}

### Which model were you using?

{gpt-4.1/o4-mini/o3/etc. - infer from context or default to "Not specified"}

### What platform is your computer?

{uname -mprs output}

### What issue are you seeing?

{describe the bug from description}

### What steps can reproduce the bug?

1. {step 1}
2. {step 2}
3. ...

### What is the expected behavior?

{expected behavior}

### Additional information

{any other relevant context}
```

### Feature Request Template

```markdown
### What feature would you like to see?

{describe the feature and the problem it solves}

### Additional information

{any other relevant context, workarounds, or alternatives - or "None" if not mentioned}
```

### Documentation Template

```markdown
### What is the type of issue?

{Documentation is missing/Documentation is incorrect/Documentation is confusing/Example code is not working/Something else}

### What is the issue?

{describe the documentation problem}

### Where did you find it?

{URL or location in docs - if known}
```

### VS Code Extension Template

```markdown
### What version of the VS Code extension are you using?

{extension version}

### What subscription do you have?

{Plus/Pro/Team/Enterprise - infer from context or ask}

### Which IDE are you using?

{VS Code/Cursor/Windsurf/etc.}

### What platform is your computer?

{uname -mprs output}

### What issue are you seeing?

{describe the issue}

### What steps can reproduce the bug?

1. {step 1}
2. {step 2}
3. ...

### What is the expected behavior?

{expected behavior}

### Additional information

{any other relevant context}
```

## Generate Title

Create a concise title (5-10 words) with the appropriate prefix:

- Bug: `[BUG] {what's broken}`
- Feature: `[FEATURE] {what you want}`
- Docs: `[DOCS] {what needs fixing}`
- Extension: `[EXTENSION] {what's wrong with the IDE extension}`

## Create the Issue

Use GitHub CLI to create the issue:

```bash
gh issue create \
  --repo "openai/codex" \
  --title "$title" \
  --body "$(cat <<'EOF'
$body
EOF
)"
```

**Note**: Template labels (`bug`, `enhancement`, `docs`, `extension`) are applied automatically by GitHub when matching the template format.

Display: "Created: $URL"

On failure: show error and suggest fix

## Environment Detection

Gather environment information for bug reports and extension issues:

- **Codex CLI version**: `codex --version 2>/dev/null || echo "unknown"`
- **Platform**: `uname -mprs` (macOS/Linux) or PowerShell command for Windows
- **IDE** (for extension issues): Ask user or infer from context

## Examples

```bash
# Bug report
"Codex crashes when processing large files"

# Feature request
"Add support for custom system prompts"

# Docs issue
"The installation docs don't mention npm prerequisites"

# Extension issue
"The Cursor extension doesn't connect to the API"
```
