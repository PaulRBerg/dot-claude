---
argument-hint: [--only-this] [--short] [--push]
description: Create a git commit with semantic analysis
---

## Context

- Current branch: !`git branch --show-current`
- Git status: !`git status --short --branch`
- Staged changes: !`git diff --cached`
- Arguments: $ARGUMENTS

## Your Task

### STEP 1: Handle staging

IF `--only-this` flag is present:
- IDENTIFY files modified/created in this chat session
- UNSTAGE all currently staged changes: `git reset`
- STAGE only the chat-modified files: `git add <file1> <file2> ...`
- LOG which files were staged from this chat session
- PROCEED to STEP 2 with these staged changes

OTHERWISE, CHECK current state from Context:

IF no staged changes AND no unstaged changes:
- ERROR "No changes to commit. Working tree is clean."

IF no staged changes BUT unstaged changes exist:
- IDENTIFY modified/new files from git status
- STAGE them automatically: `git add -A`
- LOG what was staged for transparency

IF staged changes exist:
- PROCEED with those changes

### STEP 2: Parse arguments naturally

Interpret $ARGUMENTS for commit hints and flags:
- `--only-this` flag → stage and commit only changes from this chat session
- `--short` flag → single-line commit only (no body)
- `--push` flag → push to remote after committing
- Commit type keywords (`feat`, `fix`, `docs`, etc.) → use that type
- Quoted text → use as commit description
- Everything else → context for understanding intent

Examples:
- `/commit --only-this` → commit only changes from this chat
- `/commit --only-this --short` → single-line commit of chat changes only
- `/commit --only-this --push` → commit chat changes and push
- `/commit --short` → single-line commit
- `/commit --push` → commit and push to remote
- `/commit --short --push` → single-line commit and push
- `/commit fix auth bug` → type:fix, scope:auth
- `/commit "add webhook support"` → use as description
- `/commit docs --short --push` → single-line docs commit and push

### STEP 3: Semantic change analysis

READ the staged changes from Context:
- What files changed? What's their purpose in the codebase?
- What's the actual code doing differently?
- Is this adding functionality, fixing bugs, or refactoring?
- Any breaking changes or API modifications?
- Look at the actual code changes, not just filenames

CATEGORIZE using conventional commit types:
- `feat` - New feature or functionality
- `fix` - Bug fix or issue resolution
- `docs` - Documentation only
- `style` - Code style/formatting (no logic change)
- `refactor` - Code restructuring (no behavior change)
- `test` - Adding or modifying tests
- `chore` - Maintenance (deps, build, config)
- `ci` - CI/CD changes
- `perf` - Performance improvements
- `revert` - Reverting previous commits

IDENTIFY scope:
- Component, module, or area affected
- Examples: `auth`, `api`, `ui`, `core`, `config`, `deps`
- Omit scope if change spans multiple areas

### STEP 4: Compose commit message

GENERATE subject line (≤50 characters):
- Format: `type(scope): description` or `type: description`
- Use imperative mood: "add" not "added" or "adds"
- Start with lowercase
- No period at end
- Be specific but concise

IF `--short` flag present:
- Use ONLY the subject line
- No body, no footer

OTHERWISE, for complex changes:
- ADD body (wrap at 72 characters):
  - Explain WHY the change was made
  - Include important implementation details
  - Separate from subject with blank line
- IF breaking change:
  - ADD footer: `BREAKING CHANGE: description`
  - Explain impact and migration

### STEP 5: Create the commit

EXECUTE the commit:
```bash
git commit -m "subject line" -m "body paragraph 1" -m "body paragraph 2"
```
Or for single-line:
```bash
git commit -m "subject line"
```

DISPLAY result:
- Show commit hash and full message
- Summarize what was committed

IF commit fails:
- Show the actual error
- Suggest specific fix based on error type

### STEP 6: Push to remote (if --push flag present)

IF `--push` flag was set:
- EXECUTE: `git push origin`
- DISPLAY result showing branch pushed
- IF push fails:
  - Show the actual error
  - Suggest specific fix (e.g., pull first, set upstream, auth issues)

## Examples

**Subject lines:**
- `feat(auth): add OAuth2 login support`
- `fix(api): resolve null pointer in user endpoint`
- `docs: update installation instructions`
- `chore(deps): bump lodash to 4.17.21`
- `refactor(core): extract user validation logic`
- `perf(db): add index on user_id column`
- `test: add integration tests for payment flow`

**With body:**
```
feat(webhooks): add retry mechanism for failed deliveries

Implements exponential backoff with max 5 retries. Failed webhooks
are logged to separate table for debugging. Retry intervals: 1m, 5m,
15m, 1h, 6h.
```

**Breaking change:**
```
feat(api): migrate to v2 authentication

Updates auth flow to use JWT instead of session cookies for better
scalability and mobile support.

BREAKING CHANGE: clients must update to JWT authentication. Session
cookies no longer supported. See migration guide in docs/auth-v2.md
```

## Notes

- Reads actual code to understand semantic meaning
- Generates concise, meaningful commit messages
- Follows conventional commits specification
- Breaking changes properly flagged in footer
