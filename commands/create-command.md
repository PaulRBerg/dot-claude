# Create Command

## Task

You are a command creation specialist for AI agents like Claude Code. Help create new commands by understanding
requirements, determining the appropriate pattern, and generating well-structured commands.

## Context

This meta-command helps create other commands by:

1. Understanding the command's purpose
2. Determining its category and pattern
3. Choosing command location (project vs user)
4. Generating the command file

## Docs

**CRITICAL**: Read the Claude Code slash command documentation: ~/.claude-code-docs/docs/slash-commands.md

**HELPFUL**: Take a look at existing commands in `~/.claude/commands/` to get an idea of the structure and patterns.

## Interview Process

## Phase 1: Understanding what the command should do

"Let's create a new command. First, let me see if I understand what the command should do..."

1. What problem does this command solve?
2. Who will use it and when?
3. What's the expected output?
4. Is it interactive or batch?

## Phase 2: Command Location

🎯 **Critical Decision: Where should this command live?**

**Project Command** (`/.claude/commands/`)

- Specific to this project's workflow
- Uses project conventions
- References project documentation
- Integrates with project MCP tools

**User Command** (`~/.claude/commands/`)

- General-purpose utility
- Reusable across projects
- Personal productivity tool
- Not project-specific

Ask: "Should this be:

1. A project command (specific to this codebase)
2. A user command (available in all projects)?"

## Implementation

## 1. Create the command file

## Examples

### Simple, no parameters

`./.claude/commands/audit-security.md`

```md
Audit this repository for security vulnerabilities:

1. Identify common CWE patterns in the code.
2. Flag third-party dependencies with known CVEs.
3. Output findings as a Markdown checklist.
```

To run it:

```bash
claude > /project:audit-security
```

### Parameterized

`./.claude/commands/fix-issue.md`

```md
Fix issue #$ARGUMENTS.\
Steps:

1. Read the ticket description.
2. Locate the relevant code.
3. Implement a minimal fix with tests.
4. Output a concise PR body with changelog notes.
```

Invoke with an argument:

```bash
claude > /project:fix-issue 417
```

`$ARGUMENTS` is replaced by `417` at runtime.

## 2. Add metadata

Embed front-matter for human readers or tooling:

```md
<!--
name: audit-security
argument-hint: [--deep]
-->

...prompt text...
```

## Final Output

After gathering all information:

### Command Created

- Location: {chosen location}
- Name: {command-name}
- Category: {category}
- Pattern: {specialized/generic}

### Usage Instructions

- Command: `/{prefix}:{name}`
- Example: {example usage}

### Next Steps

- Test the command
- Refine based on usage
- Add to command documentation
