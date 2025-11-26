---
argument-hint: [update-instructions]
description: Update an existing GitHub pull request with semantic change analysis
model: sonnet
---

## Context

- Current branch: !`git branch --show-current || echo "unknown"`
- Remote status: !`git status -b --porcelain | head -1 || echo "No remote tracking"`
- Recent commits: !`git log --oneline -5 || echo "No commits found"`
- GitHub CLI auth: !`gh auth status 2>&1 | rg -q "Logged in" && echo "authenticated" || echo "not authenticated"`
- Arguments: $ARGUMENTS

## Your Task

### STEP 1: Validate prerequisites

CHECK GitHub authentication:
- IF Context shows "not authenticated": ERROR and exit with: "Run `gh auth login` first"

CHECK git repository state:
- Run `git remote get-url origin` to confirm remote exists
- Run `git rev-parse --show-toplevel` to confirm we're in a repo
- IF either fails: ERROR and exit with specific issue

### STEP 2: Check for existing PR

CHECK for existing PR on current branch:
```bash
gh pr view --json number,url,title,baseRefName 2>/dev/null
```

IF no PR found (command fails):
- ERROR and exit with: "No PR exists for this branch. Use `/create-pr` to create one first."
- DO NOT proceed with update

IF PR found:
- PARSE the number, URL, title, and base branch from result
- Display: "Found PR #$number: $title"

### STEP 3: Parse arguments naturally

Interpret $ARGUMENTS as natural language instructions about what to update:
- References to "title" → update title
- References to "description" or "body" → regenerate description from changes
- Specific quoted text → use as new title or append to description based on context
- Everything else → treat as additional context for description

Examples:

- `/update-pr regenerate the description` - Update description from recent changes
- `/update-pr change title to "Fix authentication bug"` - Update title
- `/update-pr update description with new context` - Update description
- `/update-pr add this context: "Added retry logic for webhooks"` - Append to description

### STEP 4: Semantic change analysis

UPDATE remote state:
- Run `git fetch origin` silently

READ the actual changes since PR creation:
- Get base branch from Step 2
- Run `git diff origin/$base_branch...HEAD` to get full diff
- Run `git diff --stat origin/$base_branch...HEAD` for summary
- Run `git log --pretty=format:"%s%n%b" origin/$base_branch...HEAD` for commit messages

ANALYZE semantically what's changing:
- What files are affected? What are their purposes?
- Are these bug fixes, features, refactors, or maintenance?
- What's the core purpose of these changes?
- Any breaking changes, migrations, or API changes?
- Read the actual code changes to understand intent

GENERATE updated content intelligently:

- **Title** (if title update requested):
  - Concise summary of the primary change
  - Use conventional commit format if changes fit a clear type
  - Example: "feat: add webhook retry mechanism" or "fix: prevent race condition in auth flow"

- **Description** (if description update requested):
  - Keep it MINIMAL. 3-5 sentences total:
    1. One sentence: what changed
    2. One sentence: why it matters
    3. Optional: one sentence about notable implementation detail or follow-up

  DO NOT write lengthy paragraphs. DO NOT explain every detail. PR descriptions should be scannable.
  - IF additional context provided in args, append it naturally
  - PRESERVE any existing issue references (Closes #X, Related to #X)

DETECT issue references:
- Extract issue numbers from branch name: `$(git branch --show-current | rg -o '#?\d+' || echo "")`
- Extract from commit messages
- Format as "Closes #123" if fix, "Related to #123" if reference only

### STEP 5: Execute update

BUILD update command based on what's requested:

IF title update:
```bash
gh pr edit --title "$generated_title"
```

IF description update:
```bash
gh pr edit --body "$generated_body"
```

IF both:
```bash
gh pr edit --title "$generated_title" --body "$generated_body"
```

EXECUTE and capture output:
- Display: "✓ Updated PR #$number: $PR_URL"
- IF multiple updates, show what was updated: "Updated: title, description"

IF command fails:
- Check specific error (permissions, validation, network)
- Provide specific fix for that error
- DO NOT retry automatically

PUSH any local commits:
```bash
git push 2>&1 || echo "No new commits to push"
```

## Notes

- Errors if no PR exists for the branch (directs user to create-pr)
- Reads actual code changes to understand purpose, not just filenames
- Generates concise, meaningful descriptions
- Can update title, description, or both
- Preserves existing issue references
- No interactive prompts - makes intelligent defaults
