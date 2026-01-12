# UPDATE_AGENTS.md

Workflow for updating `CLAUDE.md`, `AGENTS.md`, and optionally `DOCS.md` files to match actual codebase state. DOCS.md is optional and only processed if it exists (for API/code documentation).

## Workflow

### Step 1: Parse Arguments

Check for `--dry-run` flag:

- If present: Show planned changes without writing files
- If absent: Apply changes and create backups

### Step 2: Extract Verifiable Claims

Read each context file (`CLAUDE.md`, `AGENTS.md`, and `DOCS.md` if present) and extract verifiable claims:

- File paths mentioned
- Directory structures described
- Commands referenced (build tools, scripts, package managers)
- Rules about what to edit/not edit
- Workflow descriptions
- Testing patterns
- Dependencies and integrations

**DOCS.md-specific claims (if file exists):**

- API endpoint paths and HTTP methods
- Function signatures and parameters
- Type definitions and interfaces
- Response schemas and examples
- Environment variables for API configuration

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

**API documentation claims (DOCS.md):**

- Verify documented endpoints exist in route files
- Verify function signatures match actual code
- Verify type definitions match actual types
- If endpoint removed: mark for removal
- If signature changed: update to match actual signature

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

**API patterns (for DOCS.md):**

- Scan for undocumented API routes
- Detect undocumented exported functions
- Find undocumented public types/interfaces
- If DOCS.md doesn't exist but APIs are detected, suggest creating it

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

1. Apply all fixes to the file directly
2. Report changes made

### Step 6: Report Summary

**Format for fixes:**

```
## Fixed

✓ {file}: Updated {claim} → {new_value}
✓ {file}: Removed outdated {claim}
✓ DOCS.md: Updated endpoint /api/users → /api/v2/users
✓ DOCS.md: Fixed function signature createUser()
```

**Format for suggestions:**

```
## Suggested Additions

{file}: Consider adding:

### [Section Name]

[Draft content based on discovered patterns]

---
Note: DOCS.md not found. Consider creating it to document:
- 5 API endpoints detected in src/routes/
- 12 exported functions in src/lib/
```

**If no changes needed:**

```
✓ All context files are up to date
⊘ DOCS.md not found (optional, skipped)
```

## Notes

- Focus on factual claims, not stylistic opinions
- Preserve user's writing style when making fixes
- Only suggest additions for genuinely useful patterns
- Adapt discovery to project type (web, CLI, library, etc.)
- DOCS.md is optional—skip gracefully if not present
- Suggest DOCS.md creation only if significant APIs/public interfaces detected
