---
argument-hint: '[--all] [--deep] [--push] [--stack]'
description: Create atomic git commits with smart heuristic analysis
model: sonnet
---

## Context

- Current branch: !`git branch --show-current`
- Git status: !`git status --short --branch`
- Initial staged diff: !`git diff --cached`
- Arguments: $ARGUMENTS

> **Note:** The staged diff above may become stale after STEP 1 modifies the index. Always re-read `git diff --cached` after staging operations.

## Task

### STEP 0: Pre-flight checks

Before proceeding, verify:

1. Inside a git worktree: `git rev-parse --is-inside-work-tree`
2. Not in detached HEAD state: `git symbolic-ref HEAD` (should succeed)
3. Not in rebase/merge/cherry-pick state: check for `.git/rebase-merge`, `.git/MERGE_HEAD`, `.git/CHERRY_PICK_HEAD`

If any check fails → error with clear message and suggested fix.

### STEP 1: Handle staging

IF `--all`:

- No changes at all → error "No changes to commit"
- Unstaged changes exist → auto-stage with `git add -A`
- Already staged → proceed
- Log staged files: list filenames with status (A/M/D)

OTHERWISE (default - atomic commits):

- Unstage all (`git reset`)
- **Chat-modified files** = files touched by tool calls (Write, Edit, NotebookEdit) in this session
- Stage only chat-modified files that have actual changes
- Log staged files: list filenames with status (A/M/D)
- If no chat-modified files with changes → error "No files modified in this chat"

**After staging:** Re-read `git diff --cached` to get the accurate staged diff for analysis.

### STEP 2: Parse arguments

**Flags:**

- `--all` → commit all changes (not just chat-modified files)
- `--deep` → deep code analysis, breaking changes, concise body
- `--push` → push after commit
- `--stack` → use `gt create` instead of `git commit` (requires Graphite CLI)

**Value arguments:**

- Type keyword (any conventional type) → override inferred type
- Quoted text → override inferred description

**Precedence (highest to lowest):**

1. Explicit type keyword in arguments → use that type
2. Heuristic inference from diff → fallback type
3. Quoted text in arguments → use as description
4. Heuristic inference from diff → fallback description

### STEP 3: Analyze changes

**Default mode:**

- Read the staged diff (post-STEP-1)
- Determine change type from what the code does:
  - New functionality → `feat`
  - Bug fix or error handling → `fix`
  - Code reorganization without behavior change → `refactor`
  - Documentation changes → `docs`
  - Test additions/changes → `test`
  - Build system (webpack, vite, esbuild configs) → `build`
  - CI/CD pipelines (.github/workflows, .gitlab-ci) → `ci`
  - Dependencies → `chore(deps)`
  - Formatting/whitespace only → `style`
  - Performance improvements → `perf`
  - Reverting previous commit → `revert`
  - Other maintenance → `chore`
  - AI config (CLAUDE.md, AGENTS.md, .claude/, .gemini/, .codex/) → `ai`
- Infer scope only when path makes it obvious (always lowercase):
  - `src/auth/*` → `auth`
  - `components/Button/*` → `button`
  - Multiple areas or unclear path → omit scope
- Extract a specific description of what changed (not just which files)

**IF `--deep`:**

- Deep semantic analysis of the code
- Detect breaking changes
- Infer scope from code structure even when path isn't clear
- Check for GitHub issues in chat transcript
- Keep output concise (avoid verbose explanations)

**Conventional types:** feat, fix, docs, style, refactor, test, chore, build, ci, perf, revert, ai

### STEP 4: Compose message

Subject line (≤50 chars): `type(scope): description` or `type: description`

- Imperative mood ("add" not "added")
- Lowercase, no period
- Describe what the change does, not which files changed

**Default mode:**

- Subject line (required)
- Body (smart): Use hyphens (`-`) when listing multiple distinct changes; one line per logical change
- Skip body for trivial changes (typos, single-line fixes, formatting, simple renames)

**IF `--deep`:**

- Body: 2-3 hyphenated lines max, focus on WHY (not implementation details)
- Breaking change: `BREAKING CHANGE:` + one-line migration note
- GitHub issues: `Closes #123`

### STEP 5: Commit

**IF `--stack`:**

- Check `command -v gt` → if missing, error "Graphite CLI (gt) not found. Install: https://graphite.dev/docs/installing-the-cli"
- Use `gt create -m "subject"` (add `-m "body"` only if body is non-empty)

**ELSE:**

- Use `git commit -m "subject"` (add `-m "body"` only if body is non-empty)

Output: commit hash + subject + file count summary

If failed: show error + suggest fix

### STEP 6: Push (if --push)

**IF `--push` + `--stack`:** run `gt stack submit`

**ELSE IF `--push`:**

- Check if upstream is set: `git rev-parse --abbrev-ref @{upstream}`
- If upstream exists → `git push`
- If no upstream → `git push -u origin HEAD`

If failed: show error + suggest fix (pull/rebase first, set upstream, check auth)

## Examples

**Trivial changes (subject only):**

```
fix: correct typo in error message
style: format config file
chore(deps): bump lodash to 4.17.21
```

**Default (subject + brief body):**

```
feat(auth): add OAuth2 login support

- Add Google and GitHub OAuth providers
- Integrate alongside existing password auth
```

```
refactor: extract validation logic into shared module

- Consolidate duplicate validation across API handlers
- Create reusable utils for common patterns
```

**Deep mode (concise, focused on WHY):**

```
feat(webhooks): add retry mechanism for failed deliveries

- Prevent data loss when downstream services are temporarily unavailable
```

**Deep mode with breaking change:**

```
feat(api): migrate to v2 authentication

BREAKING CHANGE: JWT required, session cookies removed. See docs/auth-v2.md.
```

**Deep mode with issue:**

```
fix(auth): resolve login timeout on slow connections

Closes #234
```
