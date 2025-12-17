# Init Context Reference

Generate project-specific CLAUDE.md files with custom context derived from project analysis or user description.

## Overview

The init-context workflow creates tailored CLAUDE.md files that provide project-specific instructions for AI agents. It operates in two modes: automatic inference (derives context from project files) or guided mode (uses user description to focus content).

## Workflow Steps

### 1. Check Arguments

Determine operating mode:

- **Automatic inference mode**: No arguments provided - derive context from project analysis
- **Guided mode**: Arguments provided - use description to focus content generation

Guided mode examples:

- `/init-context TypeScript monorepo with strict type safety and functional patterns`
- `/init-context Foundry smart contract project with security-first mindset`

### 2. Check Existing CLAUDE.md

Check for existing files:

- Run `test -f CLAUDE.md && echo "root" || test -f .claude/CLAUDE.md && echo "claude" || echo "none"`

If existing file found:

- Read the existing file
- Use `AskUserQuestion` with options:
  - **Overwrite**: Replace existing file completely
  - **Merge**: Append new context to existing file
  - **Abort**: Cancel operation
- Wait for user response before proceeding

### 3. Gather Project Context

Read available project files (skip if missing):

- `package.json` - stack, scripts, dependencies
- `README.md` - project overview, purpose
- `pyproject.toml`, `Cargo.toml`, `go.mod` - language-specific context
- `foundry.toml`, `hardhat.config.ts` - smart contract context
- `.gitignore` - exclusion patterns
- `fd -t f -d 2` - quick directory layout

Analyze to understand:

- Primary language/framework
- Project type (library, app, contracts, monorepo)
- Build/test tools
- Architecture hints

### 4. Generate CLAUDE.md Content

#### Writing Style Requirements

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

#### Content Structure

Adapt structure to context - no predefined template. Common patterns (use only if relevant):

- **Tech stack** - Languages, frameworks, tools
- **Architecture** - Patterns, conventions, structure
- **Commands** - Build, test, lint, deploy
- **Code style** - Naming, formatting, patterns
- **Constraints** - Security, performance, compliance
- **Workflows** - Git flow, PR process, testing

#### Content Patterns Example

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

#### Guided Mode (Arguments Provided)

Analyze arguments for:

- **Keywords** - "security", "testing", "monorepo", "contracts"
- **Constraints** - "strict", "functional", "minimal", "fast"
- **Tools** - "Foundry", "Next.js", "React", "Viem"
- **Priorities** - What matters most to the user

Generate sections matching intent. Example: "security-first Foundry project" emphasizes:

- Security tools (Slither, tests)
- Audit requirements
- Safe patterns
- Test coverage requirements

#### Automatic Inference Mode (No Arguments)

Derive context entirely from STEP 3 analysis:

- Primary language/framework → tech stack and code style sections
- Project type → architecture patterns
- Build/test tools detected → commands section
- Detected patterns → code style recommendations
- Dependencies and tooling → workflow suggestions

Infer priorities from project signals:

- `foundry.toml` or security deps → security focus
- Extensive test setup → testing emphasis
- Multiple packages → monorepo patterns
- Strict TypeScript config → type safety focus

### 5. Write CLAUDE.md

#### Location

- **Prefer**: `./CLAUDE.md` (root)
- **Only if user explicitly requests**: `./.claude/CLAUDE.md`

#### Write Operation

**Overwrite or no existing file**:

- Write complete new CLAUDE.md with generated content

**Merge mode**:

- Read existing content
- Append separator: `\n---\n\n# Auto-generated Context\n\n`
- Append generated content
- Write combined content

#### Confirmation

Success:

- Display file path
- Show first 10 lines as preview
- Success message: `✓ Created CLAUDE.md at ./CLAUDE.md`

Failure:

- Check permissions
- Suggest specific fix
- DO NOT retry automatically

### 6. Optional Project Import Suggestions

Check for commonly useful files:

- README.md exists → Suggest adding `@README.md`
- package.json exists → Suggest adding `@package.json`

Format suggestion:

```
💡 Tip: Consider importing project files into CLAUDE.md:

@README.md         # Project overview
@package.json      # Available scripts

Add these lines to CLAUDE.md to auto-load context.
```

## Key Principles

- **Case-by-case content** - No rigid template, adapt to user's description
- **Root location preferred** - `./CLAUDE.md` over `./.claude/CLAUDE.md` (easier discovery)
- **Import awareness** - CLAUDE.md can use `@path/to/file` syntax to import other files
- **Hierarchy context** - Project CLAUDE.md supplements (not replaces) user/enterprise CLAUDE.md
- **Writing style matches user** - Analyzed from existing agents/commands/skills

## Related Resources

- Memory docs: https://docs.anthropic.com/en/docs/claude-code/memory
- Command source: `~/.claude/commands/init-context.md`
