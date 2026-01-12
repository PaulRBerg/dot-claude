# Biome Issue Workflow

This reference document describes the workflow for creating issues in the `biomejs/biome` repository. The workflow automatically selects the appropriate issue template based on the issue description and generates structured issue content.

## Validate Authentication

Check if GitHub CLI is authenticated:

```bash
gh auth status 2>&1 | rg -q "Logged in"
```

If not authenticated, error with: "Run `gh auth login` first"

## Determine Issue Type

From the issue description, infer which template fits best:

| Keywords                                    | Template           | Title Prefix |
| ------------------------------------------- | ------------------ | ------------ |
| format, formatter, formatting, prettier     | `01_formatter_bug` | `📝 `        |
| lint, linter, rule, diagnostic, warning     | `02_lint_bug`      | `💅 `        |
| bug, broken, error, crash, panic, fails     | `03_bug`           | `🐛 `        |
| task, implement, add support (contributors) | `04_task`          | `📎 `        |

**If ambiguous or no strong match**: Use AskUserQuestion with these options:

- Formatter Bug - formatting isn't working correctly
- Linter Bug - lint rule misbehaving
- General Bug - other issues (CLI, parser, etc.)
- Task - specific implementation task (contributors only)

## Create Playground Link

Bug reports require a playground reproduction. Create one at https://biomejs.dev/playground/:

### Steps

1. Open https://biomejs.dev/playground/
2. Paste the minimal code that reproduces the issue
3. Select the appropriate language (JavaScript, TypeScript, JSX, TSX, JSON, CSS, GraphQL)
4. Configure relevant settings in the sidebar:
   - For formatter bugs: line width, indent style, quote style, etc.
   - For linter bugs: enable/disable specific rules
5. Copy the URL from the browser address bar (auto-updates as you type)

### URL Structure

The playground URL uses query parameters:

- `code=<base64_encoded>` - the reproduction code
- `language=<tsx|ts|js|jsx|json|css|graphql>` - file type
- Settings: `lineWidth=80`, `indentStyle=tab`, `quoteStyle=single`, etc.

Only non-default values appear in the URL for compact links.

### Alternative Reproduction

If the playground cannot reproduce the issue (e.g., multi-file scenarios, CLI-specific bugs):

```bash
npm create @biomejs/biome-reproduction
```

This scaffolds a reproduction repository that can be shared.

## Generate Issue Body

Based on the template type, generate a body with these sections:

### Formatter Bug Template

```markdown
### Environment information

{biome rage --formatter output}

### Configuration

{contents of biome.json if relevant, or "Default configuration"}

### Playground link

{playground URL}

### Expected result

{describe what the formatter should output}
```

### Linter Bug Template

```markdown
### Environment information

{biome rage --linter output}

### Rule name

{rule name, e.g., "noUnusedVariables" or "suspicious/noExplicitAny"}

### Playground link

{playground URL}

### Expected result

{describe what should happen - should it error? not error? different message?}
```

### General Bug Template

```markdown
### Environment information

{biome rage output}

### What happened?

{describe the bug}

1. {step 1}
2. {step 2}
3. ...

{playground link if applicable, or reproduction repo}

### Expected result

{describe what should happen}
```

### Task Template

```markdown
### Description

{summary of the task}
```

## Generate Title

Create a concise title (5-10 words) with the appropriate emoji prefix:

- Formatter: `📝 {formatting issue description}`
- Linter: `💅 {lint rule issue description}`
- General: `🐛 {bug description}`
- Task: `📎 {task description}`

## Create the Issue

Use GitHub CLI to create the issue:

```bash
gh issue create \
  --repo "biomejs/biome" \
  --title "$title" \
  --body "$(cat <<'EOF'
$body
EOF
)"
```

**Note**: The label `S-Needs triage` is applied automatically by GitHub when using bug templates.

Display: "Created: $URL"

On failure: show error and suggest fix

## Environment Detection

Gather environment information for bug reports using the appropriate `biome rage` variant:

```bash
# Formatter bugs
biome rage --formatter

# Linter bugs
biome rage --linter

# General bugs
biome rage
```

The `biome rage` command outputs:

- Biome version
- Platform information
- Configuration file location and contents
- Active plugins/rules

## Examples

```bash
# Formatter bug
"Biome formatter adds trailing comma in single-line arrays unlike Prettier"

# Linter bug
"noUnusedVariables false positive when variable is used in template literal"

# General bug
"biome check crashes with panic on valid TypeScript file"

# CLI issue
"biome migrate command doesn't handle nested extends in config"
```
