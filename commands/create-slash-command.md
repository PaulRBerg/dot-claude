---
argument-hint: [COMMAND_DESCRIPTION="<what the new command should do>"]
description: Create a new command by analyzing requirements and generating a well-structured command file
---

## Context

- Working directory: !`pwd`
- Existing user commands: !`ls -1 ~/.claude/commands/ 2>/dev/null | head -10 || echo "none"`
- Existing project commands: !`ls -1 ./.claude/commands/ 2>/dev/null | head -10 || echo "none"`
- Arguments: $ARGUMENTS

## Your Task

### STEP 1: Read command documentation

**CRITICAL**: Read the Claude Code slash command documentation:

```bash
cat ~/.claude-code-docs/docs/slash-commands.md
```

IF documentation doesn't exist: WARN "Documentation not found. Proceeding with knowledge of command patterns."

### STEP 2: Understand the command requirements

From $ARGUMENTS, determine:

1. **Purpose**: What problem does this command solve?
2. **Users**: Who will use it and when?
3. **Output**: What's the expected result?
4. **Type**: Is it interactive or batch?
5. **Complexity**: Simple prompt or multi-step workflow?

IF requirements are unclear or incomplete:
- ASK clarifying questions:
  - "What specific problem should this command solve?"
  - "What inputs does it need?"
  - "What should the output look like?"
  - "Are there any similar existing commands I should reference?"

### STEP 3: Determine command location

🎯 **Critical Decision: Where should this command live?**

**Project Command** (`./.claude/commands/`)
- Specific to this project's workflow
- Uses project conventions
- References project documentation
- Integrates with project MCP tools

**User Command** (`~/.claude/commands/`)
- General-purpose utility
- Reusable across projects
- Personal productivity tool
- Not project-specific

ANALYZE the command's nature:

IF command references project-specific files, workflows, or conventions:
- RECOMMEND: Project command
- LOCATION: `./.claude/commands/{command-name}.md`

IF command is general-purpose or personal productivity:
- RECOMMEND: User command
- LOCATION: `~/.claude/commands/{command-name}.md`

IF uncertain:
- ASK: "Should this be a project command (specific to this codebase) or a user command (available in all projects)?"

### STEP 4: Analyze similar commands

READ existing commands for patterns:

```bash
# Sample 3-5 relevant commands
ls ~/.claude/commands/ | head -5 | xargs -I {} cat ~/.claude/commands/{}
```

IDENTIFY common patterns:
- Front matter format (YAML with `argument-hint`, `description`)
- Context section with shell outputs
- STEP-based workflow structure
- IF/ELSE conditionals for flow control
- Error handling patterns
- Examples section
- Notes section

### STEP 5: Generate command structure

CREATE command file with this structure:

```markdown
---
argument-hint: [PARAMETERS="<comma-separated parameter hints>"]
description: Brief one-line description
---

## Context

- Relevant data: !`COMMAND`
- Arguments: $ARGUMENTS

## Your Task

### STEP 1: Validate prerequisites

CHECK required conditions:
- IF prerequisite not met: ERROR "Clear error message with fix"

### STEP 2: Parse arguments

Interpret $ARGUMENTS:
- Extract flags and parameters
- Validate inputs
- Set defaults

### STEP 3: [Main logic]

Describe the core workflow:
- IF condition: action
- ELSE: alternative action
- Use clear imperatives: CHECK, EXECUTE, DISPLAY, etc.

### STEP 4: [Secondary logic]

Continue step-by-step flow...

### STEP N: Display results

Show output to user:
- Success indicators
- Error messages with fixes
- Next steps

## Examples

[Concrete usage examples]

## Notes

[Implementation details, caveats, references]
```

### STEP 6: Create the command file

WRITE the command to the chosen location:

IF location is user commands:
```bash
cat > ~/.claude/commands/{command-name}.md
```

IF location is project commands:
```bash
mkdir -p ./.claude/commands/
cat > ./.claude/commands/{command-name}.md
```

DISPLAY:
```
✓ Created command: {location}/{command-name}.md
```

### STEP 7: Summarize and test

DISPLAY command summary:

```
### Command Created

- Location: {chosen location}
- Name: {command-name}
- Type: {specialized/generic}

### Usage

/{prefix}:{command-name} {example-args}

Example:
/{prefix}:{command-name} {concrete-example}

### Next Steps

1. Test the command: /{prefix}:{command-name}
2. Refine based on usage
3. Add to command documentation if needed
```

SUGGEST testing the command immediately

## Command Pattern Reference

### Simple (no parameters)

```markdown
Audit this repository for security vulnerabilities:

1. Identify common CWE patterns in the code.
2. Flag third-party dependencies with known CVEs.
3. Output findings as a Markdown checklist.
```

Usage: `/project:audit-security`

### Parameterized

```markdown
Fix issue #$ARGUMENTS.

Steps:
1. Read the ticket description.
2. Locate the relevant code.
3. Implement a minimal fix with tests.
```

Usage: `/project:fix-issue 417`

Note: `$ARGUMENTS` is replaced by `417` at runtime.

### With Context Commands

```markdown
## Context

- Current branch: !`git branch --show-current`
- Git status: !`git status --short`
```

Note: Commands prefixed with `!` are executed before the prompt is sent.

## Notes

- This is a meta-command that creates other commands
- All commands should follow the STEP-based structure
- Use clear imperatives: CHECK, IF, EXECUTE, DISPLAY, ERROR
- Include front matter for tooling and discoverability
- Context section should provide relevant state with shell commands
- Keep descriptions minimal (3-5 sentences) unless complexity demands more
- When writing Markdown code snippets in Markdown files, use four backticks (````markdown) instead of three to properly escape nested code blocks
