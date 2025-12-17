# UPDATE_CONTEXT.md

Workflow for updating `CLAUDE.md` and `AGENTS.md` files to match actual codebase state.

## Workflow

### Step 1: Parse Arguments

Check for `--dry-run` flag:

- If present: Show planned changes without writing files
- If absent: Apply changes and create backups

### Step 2: Extract Verifiable Claims

Read each context file (`CLAUDE.md`, `AGENTS.md`) and extract verifiable claims:

- File paths mentioned
- Directory structures described
- Commands referenced (build tools, scripts, package managers)
- Rules about what to edit/not edit
- Workflow descriptions
- Testing patterns
- Dependencies and integrations

### Step 3: Verify and Fix Claims

Check each claim against actual codebase and auto-fix discrepancies:

**File/Directory claims:**

- Use `ls`, `fd`, or `tree` to verify paths exist
- If path changed: update to new path
- If path deleted: mark section for removal or update

**Command claims:**

- Verify commands exist in `justfile`, `package.json`, `Makefile`, or scripts
- If command syntax changed: update to match actual command
- If command removed: mark for removal

**Linting configuration:**

- Locate lint-staged config (`.lintstagedrc.js`, `.lintstagedrc.json`, `lint-staged` in `package.json`)
- Extract lint commands for each file pattern
- If linting instructions don't match: update to match config

**Code structure claims:**

- Read actual files to verify patterns described
- Update outdated patterns to match current code

### Step 4: Discover Undocumented Patterns

Scan for patterns not mentioned in context files:

**Task runners:**

- Read `justfile` and list recipes not documented
- Read `package.json` scripts not documented
- Read `Makefile` targets not documented

**Lint configuration:**

- If lint-staged exists but no linting section in CLAUDE.md, draft one

**Build/test commands:**

- Check for undocumented build, test, or deploy commands

### Step 5: Apply Updates

**If --dry-run:**

Show preview of all changes without writing:

```
## Planned Changes

{file}:
  - Line X: "{old}" → "{new}"
  - Section Y: [REMOVE - path no longer exists]

## Suggested Additions

{file}: Consider adding section:
[Draft section content]
```

**If NOT --dry-run:**

1. Create backup: `{file}.backup`
1. Apply all fixes to the file
1. Report changes made

### Step 6: Report Summary

**Format for fixes:**

```
## Fixed

✓ {file}: Updated {claim} → {new_value}
✓ {file}: Removed outdated {claim}
```

**Format for suggestions:**

```
## Suggested Additions

{file}: Consider adding:

### [Section Name]

[Draft content based on discovered patterns]
```

**If no changes needed:**

```
✓ All context files are up to date
```

## Notes

- Focus on factual claims, not stylistic opinions
- Preserve user's writing style when making fixes
- Only suggest additions for genuinely useful patterns
- Backup files before modifying (unless --dry-run)
- Adapt discovery to project type (web, CLI, library, etc.)
