---
argument-hint: [--all] [--thorough] [--quick] [--push] [--stack]
description: Create atomic git commits with smart heuristic analysis
model: haiku
---

## Context

- Current branch: !`git branch --show-current`
- Git status: !`git status --short --branch`
- Staged changes: !`git diff --cached --stat`
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
- `--quick` → fastest (filename-only, generic messages)
- `--thorough` → slowest (deep code analysis, breaking changes, scope)
- `--push` → push after commit
- `--stack` → use `gt create` instead of `git commit`
- Type keywords (`feat`, `fix`, `docs`) → use that type
- Quoted text → use as description

### STEP 3: Analyze changes

**IF `--quick`:**
- Categorize by extension only (.md→docs, .test.→test)
- AI config changes (CLAUDE.md, AGENTS.md, .claude/, .gemini/, .codex/) → ai
- Generic type, no validation, single-line

**ELSE IF `--thorough`:**
- Request full diff: `git diff --cached`
- Read code, detect breaking changes
- Identify scope (component/module)

**ELSE (default):**
- Use --stat from context (paths/filenames only)
- Pattern-match on paths and file types
- AI config changes (CLAUDE.md, AGENTS.md, .claude/, .gemini/, .codex/) → ai
- Omit scope unless obvious
- No deep code reading

**Conventional types:** feat, fix, docs, style, refactor, test, chore, ci, perf, revert, ai

### STEP 4: Compose message

Subject line (≤50 chars): `type(scope): description` or `type: description`
- Imperative mood ("add" not "added")
- Lowercase, no period
- Specific but concise

**IF `--quick`:** subject only, minimal refinement, generic descriptions
**ELSE IF default:** subject only, quick refinement, accurate descriptions
**ELSE IF `--thorough`:** add body (wrap 72 chars, explain WHY)

Footers (thorough mode only):
- Breaking change: `BREAKING CHANGE: description` + migration notes
- GitHub issues: `Closes #123` or `Closes #123, #456`

### STEP 5: Commit

**IF `--stack`:** use `gt create -m "subject" -m "body"`
**ELSE:** use `git commit -m "subject" -m "body"`

Output:
- `--quick`: hash only
- Default: hash + subject + basic summary
- `--thorough`: hash + full message + detailed summary

If failed: show error + suggest fix

### STEP 6: Push (if --push)

**IF `--push` + `--stack`:** run `gt stack submit`
**ELSE IF `--push`:** run `git push origin`

If failed: show error + suggest fix (pull first, set upstream, auth)

## Examples

**Subject lines:**
```
feat(auth): add OAuth2 login support
fix(api): resolve null pointer in user endpoint
docs: update installation instructions
chore(deps): bump lodash to 4.17.21
ai: update agent configuration for code review
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

## Notes

**Performance modes:**
- Default: Fast, pattern-based heuristics using `--stat` output only (no deep code reading)
- `--quick`: Fastest mode with minimal validation (filename-only analysis)
- `--thorough`: Deep semantic analysis with full code reading and breaking change detection

**Features:**
- Generates concise, meaningful commit messages
- Follows conventional commits specification
- Breaking changes properly flagged in footer (thorough mode)
- Auto-detects GitHub issues from chat transcript and adds "Closes #N" footer
- Supports multiple issue references (e.g., "Closes #123, #456")
- Optimized for speed by default while maintaining good accuracy
