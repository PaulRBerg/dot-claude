---
argument-hint: [issue-number]
description: Fetch GitHub issue, analyze, fix, and commit with "Closes #N"
---

## Context

- Current repository: !`gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "not a repository"`
- GitHub CLI auth: !`gh auth status 2>&1 | rg -q "Logged in" && echo "authenticated" || echo "not authenticated"`
- Current branch: !`git branch --show-current`
- Issue number: $ARGUMENTS
- Issue details: !`gh issue view $ARGUMENTS --json title,body,labels,state --template '# {{.title}}\n\nState: {{.state}}\n\nLabels: {{range .labels}}{{.name}}, {{end}}\n\n## Description\n\n{{.body}}' 2>&1`

## Your Task

### STEP 1: Validate prerequisites

IF not authenticated: ERROR "Run `gh auth login` first"

IF not in a repository: ERROR "Must be run from within a git repository"

IF issue details show error: ERROR "Could not fetch issue #$ARGUMENTS. Verify the issue exists and you have access."

IF current branch is `main` or `master`: SUGGEST creating a feature branch first:
- Recommend: `git checkout -b fix/issue-$ARGUMENTS` or similar descriptive name
- Explain: Working on a branch allows for PR workflow and keeps main clean
- Ask if user wants to proceed on current branch or create a new one

### STEP 2: Analyze the issue

From the issue details above:
- **Problem**: What is the core issue that needs fixing?
- **Affected areas**: Which files or modules are involved?
- **Type**: Is this a bug fix, feature, refactor, or something else?
- **Complexity**: Simple fix or requires architectural changes?

### STEP 3: Propose implementation plan

Create a clear, concise plan:

1. Files that need to be examined
2. Changes required (be specific)
3. Tests to add or modify (if applicable)
4. Potential side effects or breaking changes

**Present this plan to the user and ask for approval before proceeding.**

### STEP 4: Implement the fix

After receiving approval:

1. **Locate relevant code**
   - Use Grep/Glob to find affected files
   - Read necessary files to understand current implementation

2. **Make changes**
   - Edit files to implement the fix
   - Follow the project's coding standards and patterns
   - Keep changes minimal and focused

3. **Verify the fix**
   - Run tests if they exist: `npm test`, `cargo test`, etc.
   - Check for obvious issues
   - Ensure the fix addresses the issue

### STEP 5: Commit the changes

Use the `/commit` command with proper formatting:

```
/commit
```

**CRITICAL**: When composing the commit message body, you MUST include:

```
Closes #$ARGUMENTS
```

This will automatically close the issue when the commit is merged.

The commit should follow conventional commit format:
- Type: `fix` for bugs, `feat` for features, etc.
- Scope: The module/component affected (if applicable)
- Description: Clear, imperative mood summary
- Body: Include "Closes #$ARGUMENTS" and any additional context

### STEP 6: Summarize completion

Display:
- ✅ Issue #$ARGUMENTS analyzed and fixed
- 📝 Files modified: [list files]
- 💾 Commit created: [commit hash]
- 🔗 Issue will close when merged: [issue URL]

## Error Handling

IF at any point you cannot proceed:
- Explain the blocker clearly
- Suggest specific next steps
- Don't make partial commits

## Notes

- Always present the plan before implementing
- Keep changes focused on the issue
- Include "Closes #$ARGUMENTS" in commit body
- Follow project conventions for code style
- Run tests before committing if available
