---
argument-hint: '[description?]'
description: Generate project-specific CLAUDE.md file with custom context
model: opus
---

## Context

- Current directory: !`pwd`
- Existing CLAUDE.md (root): !`test -f CLAUDE.md && echo "exists" || echo "none"`
- Existing CLAUDE.md (.claude): !`test -f .claude/CLAUDE.md && echo "exists" || echo "none"`
- Git repository: !`git rev-parse --show-toplevel 2>/dev/null || echo "not a git repo"`
- Arguments: $ARGUMENTS

## Your Task

### STEP 1: Check arguments

DETERMINE mode:

- IF `$ARGUMENTS` is empty: **Automatic inference mode** - derive context from project analysis in STEP 3
- IF `$ARGUMENTS` is provided: **Guided mode** - use description to focus content generation

Examples of guided mode:

- `/init-context TypeScript monorepo with strict type safety and functional patterns`
- `/init-context Foundry smart contract project with security-first mindset`

### STEP 2: Check existing CLAUDE.md

CHECK for existing files:

- Run `test -f CLAUDE.md && echo "root" || test -f .claude/CLAUDE.md && echo "claude" || echo "none"`

IF result is "root" or "claude":

- Read the existing file
- ASK user: "CLAUDE.md already exists at [location]. Choose action:"
  - **Overwrite** - Replace existing file completely
  - **Merge** - Append new context to existing file
  - **Abort** - Cancel operation
- WAIT for user response before proceeding

### STEP 3: Gather project context

READ available project files (non-blocking - skip if missing):

- `package.json` → stack, scripts, dependencies
- `README.md` → project overview, purpose
- `pyproject.toml` or `Cargo.toml` or `go.mod` → language-specific context
- `foundry.toml` or `hardhat.config.ts` → smart contract context
- `.gitignore` → what to exclude
- File structure with `fd -t f -d 2` → quick directory layout

ANALYZE to understand:

- Primary language/framework
- Project type (library, app, contracts, monorepo)
- Build/test tools
- Architecture hints

### STEP 4: Generate CLAUDE.md content

**Writing Style Requirements:**

- **Terse and direct** - No fluff, straight to point
- **Expert-to-expert** - Assume high competency
- **Imperative mood** - Commands ("Use", "Follow", "Avoid")
- **Active voice** - "Run tests before committing" not "Tests should be run"
- **Minimal markdown**:
  - `##` for major sections
  - `###` for subsections
  - Bullet points for lists
  - Inline code for technical terms
  - **Bold** for emphasis

**Content Structure (adapt to context):**

Base your structure on `$ARGUMENTS` and project analysis. NO predefined template.

Common patterns (use only if relevant):

- **Tech stack** - Languages, frameworks, tools
- **Architecture** - Patterns, conventions, structure
- **Commands** - Build, test, lint, deploy
- **Code style** - Naming, formatting, patterns
- **Constraints** - Security, performance, compliance
- **Workflows** - Git flow, PR process, testing

**Examples of good sections:**

```markdown
## Stack

- TypeScript 5.x with strict mode
- pnpm workspaces
- Vitest for testing
- BiomeJS for linting

## Code Style

- Functional patterns over classes
- Explicit return types on exported functions
- No `any` types - use `unknown` and type guards
- Prefer `const` and immutability

## Commands

- `pnpm test` - Run tests across all packages
- `pnpm build` - Build all packages
- `pnpm lint` - Run BiomeJS
```

**Intelligent adaptation:**

**Guided mode** (when `$ARGUMENTS` provided):
Analyze `$ARGUMENTS` for:

- Keywords → "security", "testing", "monorepo", "contracts"
- Constraints → "strict", "functional", "minimal", "fast"
- Tools → "Foundry", "Next.js", "React", "Viem"
- Priorities → What matters most to the user

Generate sections that match the intent. If user says "security-first Foundry project", emphasize:

- Security tools (Slither, tests)
- Audit requirements
- Safe patterns
- Test coverage requirements

**Automatic inference mode** (when `$ARGUMENTS` empty):
Derive context entirely from STEP 3 analysis:

- Primary language/framework → dictates tech stack and code style sections
- Project type (library, app, contracts, monorepo) → determines architecture patterns
- Build/test tools detected → commands section
- Detected patterns (functional, OOP, etc.) → code style recommendations
- Dependencies and tooling → workflow suggestions

Infer priorities from project signals:

- `foundry.toml` or security deps → security focus
- Extensive test setup → testing emphasis
- Multiple packages → monorepo patterns
- Strict TypeScript config → type safety focus

### STEP 5: Write CLAUDE.md

DETERMINE write location:

- **Prefer**: `./CLAUDE.md` (root)
- **Only if user explicitly requests**: `./.claude/CLAUDE.md`

EXECUTE write operation:

IF user chose "Overwrite" or no existing file:

- Write complete new CLAUDE.md with generated content

IF user chose "Merge":

- Read existing content
- Append separator: `\n---\n\n# Auto-generated Context\n\n`
- Append generated content
- Write combined content

CONFIRM success:

- Display file path
- Show first 10 lines as preview
- Success message: `✓ Created CLAUDE.md at ./CLAUDE.md`

IF write fails:

- Check permissions
- Suggest specific fix
- DO NOT retry automatically

### STEP 6: Optional project import suggestions

CHECK for commonly useful files to import:

- README.md exists → Suggest adding `@README.md` to CLAUDE.md
- package.json exists → Suggest adding `@package.json` for script reference

FORMAT suggestion as:

```
💡 Tip: Consider importing project files into CLAUDE.md:

@README.md         # Project overview
@package.json      # Available scripts

Add these lines to CLAUDE.md to auto-load context.
```

## Notes

- **Case-by-case content** - No rigid template, adapt to user's description
- **Root location preferred** - `./CLAUDE.md` over `./.claude/CLAUDE.md` (easier discovery)
- **Import awareness** - CLAUDE.md can use `@path/to/file` syntax to import other files
- **Hierarchy context** - Project CLAUDE.md supplements (not replaces) user/enterprise CLAUDE.md
- **Memory docs** - See https://docs.anthropic.com/en/docs/claude-code/memory for details
- **Writing style matches user** - Analyzed from existing agents/commands/skills
