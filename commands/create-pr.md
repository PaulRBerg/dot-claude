---
argument-hint: [--draft] [--test-plan] [base=X] [review by Y] [title "Z"]
description: Create a GitHub pull request with semantic change analysis
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

UPDATE remote state:
- Run `git fetch origin` silently

CHECK commits to PR:
- Get base branch: `git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@' 2>/dev/null || echo "main"`
- Count commits ahead: `git rev-list --count origin/$base_branch..HEAD 2>/dev/null`
- IF 0 commits ahead: ERROR "No commits to create PR from"

### STEP 2: Parse arguments naturally

Interpret $ARGUMENTS as natural language:
- "draft" or "--draft" anywhere → draft mode
- "test-plan" or "--test-plan" anywhere → include test plan section
- "to X" or "base=X" → target branch X (default: main)
- "review by X" or "reviewers=X" → add reviewer(s) X
- Quoted text → custom title
- Everything else → additional context for description

Examples:

- `/create-pr draft` - Create draft PR
- `/create-pr --test-plan` - Include test plan section
- `/create-pr to staging` - Target staging branch
- `/create-pr review by alice` - Add alice as reviewer
- `/create-pr "Add user analytics dashboard"` - Custom title
- `/create-pr draft to develop review by bob --test-plan` - Combined options

### STEP 3: Semantic change analysis

READ the actual changes:
- Run `git diff origin/$base_branch...HEAD` to get full diff
- Run `git diff --stat origin/$base_branch...HEAD` for summary
- Run `git log --pretty=format:"%s%n%b" origin/$base_branch...HEAD` for commit messages

ANALYZE semantically what's changing:
- What files are affected? What are their purposes?
- Are these bug fixes, features, refactors, or maintenance?
- What's the core purpose of these changes?
- Any breaking changes, migrations, or API changes?
- Read the actual code changes to understand intent

GENERATE PR content intelligently:
- **Title**: Concise summary of the primary change (not just "Update files")
  - Use conventional commit format if changes fit a clear type
  - Example: "feat: add webhook retry mechanism" or "fix: prevent race condition in auth flow"
  - If custom title provided in args, use that instead

- **Description**: 2-4 short paragraphs maximum:
  1. What changed and why
  2. Key implementation details worth noting
  3. Any follow-up work or considerations

- **Test Plan** (only if `--test-plan` flag present):
  - Add a dedicated "## Test Plan" section describing testing/validation approach
  - Include manual testing steps, automated test coverage, or validation checklist

DETECT issue references:
- Extract issue numbers from branch name: `$(git branch --show-current | rg -o '#?\d+' || echo "")`
- Extract from commit messages
- Format as "Closes #123" if fix, "Related to #123" if reference only

IDENTIFY reviewers intelligently:
- Check for CODEOWNERS file: `git ls-files | rg CODEOWNERS`
- If exists, extract owners for changed files
- Otherwise use git blame to find frequent contributors to changed files
- Combine with any reviewers specified in arguments

### STEP 4: Check for existing PR

CHECK for existing PR on current branch:
```bash
gh pr list --head $(git branch --show-current) --json number,url --jq '.[0]' 2>/dev/null
```

IF existing PR found (non-empty result):
- PARSE the number and URL from result
- LOG: "PR #X already exists: URL"
- UPDATE existing PR instead of creating new one:
  ```bash
  gh pr edit $PR_NUMBER \
    --title "$generated_title" \
    --body "$generated_body"
  ```
- EXIT with success message

### STEP 5: Create new PR

ENSURE branch is pushed:
```bash
git push -u origin $(git branch --show-current) 2>&1 || echo "Already pushed"
```

BUILD pr creation command:
```bash
gh pr create \
  --title "$generated_title" \
  --body "$generated_body" \
  --base "$base_branch" \
  $(test "$draft_mode" = "true" && echo "--draft") \
  $(test -n "$reviewers" && echo "--reviewer $reviewers")
```

EXECUTE and capture output:
- Extract PR URL from command output
- Display: "✓ Created PR: $PR_URL"

IF command fails:
- Check specific error (auth, branch protection, validation)
- Provide specific fix for that error
- DO NOT retry automatically

## Notes

- Automatically updates existing PRs instead of creating duplicates
- Reads actual code changes to understand purpose, not just filenames
- Generates concise, meaningful descriptions
- Handles common errors with specific remediation steps
- No interactive prompts - makes intelligent defaults
