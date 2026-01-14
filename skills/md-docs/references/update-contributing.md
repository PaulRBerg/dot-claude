# Update CONTRIBUTING Workflow

Comprehensive workflow for updating CONTRIBUTING.md files based on current codebase structure and contribution requirements. This reference documents the complete process used when a repository already has a CONTRIBUTING.md file.

## Prerequisite: File Must Exist

**This workflow only applies when CONTRIBUTING.md already exists in the repository.**

```bash
test -f CONTRIBUTING.md && echo "exists" || echo "missing"
```

- IF CONTRIBUTING.md exists: Proceed with update workflow
- IF CONTRIBUTING.md does NOT exist: Skip this workflow entirely. Do not create CONTRIBUTING.md unless explicitly requested by the user.

**Rationale**: CONTRIBUTING.md represents intentional decisions about how a project accepts contributions. These decisions (CLA requirements, code style enforcement, review processes) vary significantly by project and organization. Auto-generating this file could create misleading or incorrect contribution guidance.

## Guiding Principles

**CONTRIBUTING.md is the source of truth for contribution guidance.**

- **Defer to existing content**: The project maintainers made deliberate choices about contribution processes
- **Update, don't replace**: Fix outdated commands, paths, or tooling references while preserving the overall structure and policies
- **Verify accuracy**: Check that documented commands, links, and processes actually work
- **Keep it actionable**: Contributors should be able to follow the guide step-by-step

**Scope of updates:**

- Fix outdated CLI commands (npm → pnpm, yarn → bun, etc.)
- Update file paths that have moved
- Fix broken links to issues, discussions, or external docs
- Update tooling references (test frameworks, linters, formatters)
- Correct branch names (master → main, develop → dev)

**Do NOT change:**

- Contribution policies (CLA, DCO, licensing)
- Review processes
- Code of conduct references
- Governance or maintainer decisions
- Communication channel preferences

## Workflow Steps

### STEP 1: Validate Prerequisites

**CHECK repository state:**

```bash
git rev-parse --show-toplevel
```

Confirm we're in a git repository. Store the repository root path.

**CHECK for CONTRIBUTING.md:**

```bash
test -f CONTRIBUTING.md && echo "exists" || echo "missing"
```

- IF CONTRIBUTING.md does NOT exist: EXIT with message "CONTRIBUTING.md not found. This workflow only updates existing files. To create a new CONTRIBUTING.md, please do so manually or request explicit creation."
- IF CONTRIBUTING.md exists: Proceed to next step

### STEP 2: Parse Arguments

Interpret arguments for mode flags:

- `--dry-run` → Show what would change without writing files
- `--preserve` → Maximum preservation; only fix broken commands/links
- `--thorough` → Deep analysis; verify all links and commands work

SET mode based on arguments parsed.

### STEP 3: Read Existing CONTRIBUTING.md

```bash
cat CONTRIBUTING.md
```

**Parse the document structure:**

- Identify section headings (##, ###)
- Extract code blocks with commands and inline comments
- Find URLs and links
- Note file path references
- Identify mentioned tooling (test runners, linters, formatters, task runners)
- Preserve specialized sections (AI tooling, workflow diagrams, console filters, versioning/publishing notes)

### STEP 4: Gather Codebase Intelligence

**Detect current tooling:**

```bash
# Package manager (from lock files)
test -f pnpm-lock.yaml && echo "pnpm"
test -f yarn.lock && echo "yarn"
test -f bun.lockb && echo "bun"
test -f package-lock.json && echo "npm"

# Get actual scripts from package.json
cat package.json | jq '.scripts | keys'

# Check for tooling config files
ls -la .eslintrc* .prettierrc* biome.json tsconfig.json jest.config.* vitest.config.* 2>/dev/null
```

**Detect branch conventions:**

```bash
# Get default branch
git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@'

# Or check common names
git branch -r | grep -E 'origin/(main|master|develop)' | head -1
```

**Verify links (if --thorough):**

```bash
# Extract URLs from CONTRIBUTING.md and check each
grep -oE 'https?://[^)>"]+' CONTRIBUTING.md | while read url; do
  curl -sI "$url" | head -1
done
```

### STEP 5: Identify Discrepancies

Compare documented information against actual codebase:

**Command discrepancies:**

- `npm test` documented but pnpm-lock.yaml exists → Should be `pnpm test`
- `yarn lint` documented but lint script doesn't exist
- `npm run build` documented but build script is `npm run compile`

**Path discrepancies:**

- References to `src/` but code is in `lib/`
- Links to `.github/ISSUE_TEMPLATE.md` but templates are in `.github/ISSUE_TEMPLATE/`
- References to `docs/` but documentation is in `documentation/`

**Branch discrepancies:**

- "Submit PRs to `master`" but default branch is `main`
- "Base your work on `develop`" but branch doesn't exist

**Tooling discrepancies:**

- "Run ESLint" but project uses Biome
- "Format with Prettier" but no Prettier config exists
- "Test with Jest" but project uses Vitest

### STEP 6: Generate Updates

**For each discrepancy, prepare a fix:**

```markdown
# Example fixes

## Package manager update
- Old: `npm install`
+ New: `pnpm install`

## Script name fix
- Old: `npm run build`
+ New: `pnpm run compile`

## Branch name fix
- Old: Submit PRs to `master`
+ New: Submit PRs to `main`

## Tooling update
- Old: Run ESLint with `npm run lint`
+ New: Run Biome with `pnpm run lint`
```

**Preserve structure:**

- Keep the same section ordering
- Maintain formatting style (header levels, list styles)
- Preserve any custom sections or project-specific guidance
- Keep long-form sections intact (e.g., AI-assisted workflows, ASCII diagrams, checklists, admonitions)
- If present, keep sections like Prerequisites, Setup, Available Commands, Development Workflow, Quality Gates, Claude Code Setup, AI-Assisted Development, and Versioning/Publishing

### STEP 7: Write Updated CONTRIBUTING.md

IF `--dry-run`:

```bash
# Show diff without writing
diff -u CONTRIBUTING.md <(echo "$NEW_CONTENT")
```

ELSE:

- Use the Edit tool to make targeted replacements
- OR use the Write tool if extensive changes needed

### STEP 8: Display Summary

```markdown
✓ Updated CONTRIBUTING.md

**Mode**: {preserve/default/thorough}

**Changes Made:**
- Updated package manager: npm → pnpm
- Fixed branch reference: master → main
- Corrected test command: `npm test` → `pnpm test`
- Fixed broken link: .github/ISSUE_TEMPLATE.md → .github/ISSUE_TEMPLATE/bug.md

**Preserved:**
- Contribution policies (CLA, licensing)
- Code of conduct reference
- Review process guidelines

**Next Steps:**
1. Review CONTRIBUTING.md for accuracy
2. Verify commands work as documented
3. Commit changes: `git add CONTRIBUTING.md && git commit -m "docs: update CONTRIBUTING.md"`
```

## Usage Examples

**Basic update:**

```bash
/md-docs:update-contributing
```

Updates CONTRIBUTING.md with current tooling and paths. Only runs if file exists.

**Preview changes:**

```bash
/md-docs:update-contributing --dry-run
```

Shows what would change without writing.

**Maximum preservation:**

```bash
/md-docs:update-contributing --preserve
```

Only fixes clearly broken commands and links; preserves everything else.

**Thorough verification:**

```bash
/md-docs:update-contributing --thorough
```

Verifies all links, tests all commands, comprehensive analysis.

## Key Characteristics

**Conditional execution**: Only operates when CONTRIBUTING.md already exists. Never auto-creates.

**Non-destructive**: Preserves policies, processes, and intentional decisions. Only updates technical accuracy.

**Targeted edits**: Uses Edit tool for surgical changes rather than rewriting entire file.

**Verification-first**: Checks actual codebase state before suggesting changes.

**No policy changes**: Never modifies CLA requirements, code of conduct, or governance decisions.

**Monorepo aware**: Operates on CONTRIBUTING.md at repository root. For package-specific contribution guides, user should cd to that directory.
