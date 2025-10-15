---
argument-hint: [--all]
description: Run linters on modified files using lint-staged configuration
---

## Context

- Working directory: !`pwd`
- Modified files: !`git diff --name-only --cached 2>/dev/null || git diff --name-only HEAD 2>/dev/null || echo "none"`
- Config: !`test -f .lintstagedrc.js && echo ".lintstagedrc.js" || test -f .lintstagedrc.json && echo ".lintstagedrc.json" || test -f package.json && grep -q "lint-staged" package.json && echo "package.json" || echo "not found"`
- Arguments: $ARGUMENTS

## Your Task

### STEP 1: Read configuration

CHECK for config in order: `.lintstagedrc.js`, `.lintstagedrc.json`, `package.json` "lint-staged" field

IF not found: ERROR "No lint-staged config found"

PARSE the config to extract pattern-command mappings.

### STEP 2: Get file list

IF `$ARGUMENTS` contains `--all`: USE all files matching config patterns
ELSE: USE modified files from git

IF no files: ERROR "No files to lint"

### STEP 3: Match files to commands

FOR each file, MATCH against config glob patterns.

CLASSIFY commands:
- **Formatters** (run first): contain `--write`, `--fix`, `-w`
- **Checkers** (run after): contain `--check`, `--verify`, or standalone

FILE ARGUMENTS:
- < 10 files: pass specific paths or globs
- ≥ 10 files: omit file arguments

### STEP 4: Execute formatters

RUN formatter commands with matched files.

IF any fail: DISPLAY error, SUGGEST fix, STOP

### STEP 5: Execute checkers

RUN checker commands with matched files.

IF any fail: DISPLAY error, SUGGEST fix, STOP

### STEP 6: Report results

DISPLAY:
```
✓ Formatters: {list}
✓ Checkers: {list}
```

## Examples

```bash
/lint-files           # modified files only
/lint-files --all     # all matching files
```

## Notes

**Execution order**: Formatters → check errors → Checkers → check errors

**Common patterns**:
- Formatters: `prettier --write`, `biome check --write`, `eslint --fix`
- Checkers: `prettier --check`, `biome check`, `tsc --noEmit`

**File args**: Project-wide checkers like `tsc --noEmit` never get file arguments.

**Config source**: Uses lint-staged config for convenience, not tied to git staging.
