---
argument-hint: [--all] [--thorough] [--push] [--stack]
description: Create atomic git commits with smart heuristic analysis
model: haiku
---

## Context

- Current branch: !`git branch --show-current`
- Git status: !`git status --short --branch`
- Staged diff: !`git diff --cached`
- Arguments: $ARGUMENTS

## Task

### STEP 1: Handle staging

IF `--all`:

- No changes at all → error "No changes to commit"
- Unstaged changes exist → auto-stage with `git add -A`, log what was staged
- Already staged → proceed

OTHERWISE (default - atomic commits):

- Unstage all (`git reset`)
- Stage only chat-modified files
- Log which files were staged
- If no chat-modified files → error "No files modified in this chat"

### STEP 2: Parse arguments

Flags:

- `--all` → commit all changes (not just chat-modified files)
- `--thorough` → deep code analysis, breaking changes, detailed body
- `--push` → push after commit
- `--stack` → use `gt create` instead of `git commit`
- Type keywords (`feat`, `fix`, `docs`) → use that type
- Quoted text → use as description

### STEP 3: Analyze changes

**Default mode:**

- Read the staged diff from context
- Determine change type from what the code does:
  - New functionality → `feat`
  - Bug fix or error handling → `fix`
  - Code reorganization without behavior change → `refactor`
  - Documentation changes → `docs`
  - Test additions/changes → `test`
  - Build/CI changes → `ci`
  - Dependencies → `chore(deps)`
  - AI config (CLAUDE.md, AGENTS.md, .claude/, .gemini/, .codex/) → `ai`
- Infer scope only when path makes it obvious:
  - `src/auth/*` → `auth`
  - `components/Button/*` → `Button`
  - Multiple areas or unclear path → omit scope
- Extract a specific description of what changed (not just which files)

**IF `--thorough`:**

- Deep semantic analysis of the code
- Detect breaking changes
- Infer scope from code structure even when path isn't clear
- Add detailed body explaining why the change was made
- Check for GitHub issues in chat transcript

**Conventional types:** feat, fix, docs, style, refactor, test, chore, ci, perf, revert, ai

### STEP 4: Compose message

Subject line (≤50 chars): `type(scope): description` or `type: description`

- Imperative mood ("add" not "added")
- Lowercase, no period
- Describe what the change does, not which files changed

**Default mode:** Subject only. Brief but specific.

**IF `--thorough`:**

- Add body (wrap 72 chars, explain WHY)
- Breaking change: `BREAKING CHANGE: description` + migration notes
- GitHub issues: `Closes #123` or `Closes #123, #456`

### STEP 5: Commit

**IF `--stack`:** use `gt create -m "subject" -m "body"`
**ELSE:** use `git commit -m "subject" -m "body"`

Output: hash + subject + brief summary

If failed: show error + suggest fix

### STEP 6: Push (if --push)

**IF `--push` + `--stack`:** run `gt stack submit`
**ELSE IF `--push`:** run `git push origin`

If failed: show error + suggest fix (pull first, set upstream, auth)

## Examples

**Subject lines:**

```
feat(auth): add OAuth2 login support
fix(api): handle null response from user endpoint
refactor: extract validation logic into shared module
docs: clarify installation requirements
chore(deps): bump lodash to 4.17.21
ai: add code review agent configuration
```

**With body (thorough mode):**

```
feat(webhooks): add retry mechanism for failed deliveries

Implements exponential backoff with max 5 retries. Retry intervals:
1m, 5m, 15m, 1h, 6h.
```

**Breaking change:**

```
feat(api): migrate to v2 authentication

BREAKING CHANGE: clients must use JWT. Session cookies removed.
See docs/auth-v2.md for migration.
```

**With issue:**

```
fix(auth): resolve login timeout on slow connections

Closes #234
```
