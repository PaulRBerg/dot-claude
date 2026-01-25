# Pull Request Workflow

Create GitHub pull requests with semantic change analysis, intelligent defaults, and minimal friction.

## Validate Prerequisites

**Check GitHub authentication:**

- IF not authenticated: ERROR and exit with: "Run `gh auth login` first"

**Check git repository state:**

- Run `git remote get-url origin` to confirm remote exists
- Run `git rev-parse --show-toplevel` to confirm we're in a repo
- IF either fails: ERROR and exit with specific issue

**Update remote state:**

- Run `git fetch origin` silently

**Check commits to PR:**

- Get base branch: `git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@' 2>/dev/null || echo "main"`
- Count commits ahead: `git rev-list --count origin/$base_branch..HEAD 2>/dev/null`
- IF 0 commits ahead: ERROR "No commits to create PR from"

## Parse Arguments Naturally

Interpret arguments as natural language:

- "draft" or "--draft" anywhere → draft mode
- "test-plan" or "--test-plan" anywhere → include test plan section
- "to X" or "base=X" → target branch X (default: main)
- "review=X" or "reviewers=X" → add reviewer(s) X
- Quoted text → custom title
- Everything else → additional context for description

**Examples:**

- `draft` - Create draft PR
- `--test-plan` - Include test plan section
- `to staging` - Target staging branch
- `review by alice` - Add alice as reviewer
- `"Add user analytics dashboard"` - Custom title
- `draft to develop review by bob --test-plan` - Combined options

## Semantic Change Analysis

**Read the actual changes:**

- Run `git diff origin/$base_branch...HEAD` to get full diff
- Run `git diff --stat origin/$base_branch...HEAD` for summary
- Run `git log --pretty=format:"%s%n%b" origin/$base_branch...HEAD` for commit messages

**Analyze semantically what's changing:**

- What files are affected? What are their purposes?
- Are these bug fixes, features, refactors, or maintenance?
- What's the core purpose of these changes?
- Any breaking changes, migrations, or API changes?
- Read the actual code changes to understand intent

**Generate PR content intelligently:**

### Title

Concise summary of the primary change (not just "Update files"):

- Use conventional commit format if changes fit a clear type
- Example: "feat: add webhook retry mechanism" or "fix: prevent race condition in auth flow"
- If custom title provided in args, use that instead

### Description

Keep it MINIMAL. 3-5 sentences total:

1. One sentence: what changed
2. One sentence: why it matters
3. Optional: one sentence about notable implementation detail or follow-up

DO NOT write lengthy paragraphs. DO NOT explain every detail. PR descriptions should be scannable.

### Admonitions

Add GitHub-style admonitions when appropriate:

- `> [!NOTE]` - For context, dependencies, or implementation details reviewers should notice
- `> [!TIP]` - For suggestions on testing or reviewing specific aspects
- `> [!IMPORTANT]` - For breaking changes, migration requirements, or critical review points
- `> [!WARNING]` - For potential risks, edge cases, or areas needing extra scrutiny
- `> [!CAUTION]` - For temporary solutions, technical debt, or follow-up work needed

Keep admonitions concise (1-2 sentences). Place after main description. Example:

```
This PR refactors the payment processing pipeline to handle retries.

> [!IMPORTANT]
> Breaking change: `processPayment()` now returns a Promise. Update all callers.
```

### Test Plan (Optional)

Only if `--test-plan` flag present:

- Add a dedicated "## Test Plan" section describing testing/validation approach
- Include manual testing steps, automated test coverage, or validation checklist

**Detect issue references:**

- Extract issue numbers from branch name: `$(git branch --show-current | rg -o '#?\d+' || echo "")`
- Extract from commit messages
- Format as "Closes #123" if fix, "Related to #123" if reference only

**Identify reviewers intelligently:**

- Check for CODEOWNERS file: `git ls-files | rg CODEOWNERS`
- If exists, extract owners for changed files
- Otherwise use git blame to find frequent contributors to changed files
- Combine with any reviewers specified in arguments

## Check for Existing PR

Check for existing PR on current branch:

```bash
gh pr list --head $(git branch --show-current) --json number,url --jq '.[0]' 2>/dev/null
```

IF existing PR found (non-empty result):

- PARSE the number and URL from result
- ERROR and exit with: "PR already exists for this branch: $URL"
- DO NOT create or update anything

## Create New PR

**Ensure branch is pushed:**

```bash
git push -u origin $(git branch --show-current) 2>&1 || echo "Already pushed"
```

**Build PR creation command:**

```bash
gh pr create \
  --title "$generated_title" \
  --body "$generated_body" \
  --base "$base_branch" \
  $(test "$draft_mode" = "true" && echo "--draft") \
  $(test -n "$reviewers" && echo "--reviewer $reviewers")
```

**Execute and capture output:**

- Extract PR URL from command output
- Display: "✓ Created PR: $PR_URL"

IF command fails:

- Check specific error (auth, branch protection, validation)
- Provide specific fix for that error
- DO NOT retry automatically

## Implementation Notes

- Errors if PR already exists for the branch (prevents duplicates)
- Reads actual code changes to understand purpose, not just filenames
- Generates concise, meaningful descriptions
- Handles common errors with specific remediation steps
- No interactive prompts - makes intelligent defaults
