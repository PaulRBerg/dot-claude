# Update README Workflow

Comprehensive workflow for updating README.md files based on current codebase structure. This reference documents the complete 8-step process used by the `/md-docs:update-readme` command.

## Guiding Principles

**README files are for humans, not documentation dumps.**

- **Balanced, not bloated**: Aim for 200-400 lines for most projects. A README should be informative but not overwhelming.
- **Show, don't tell**: Prefer concise code examples over lengthy prose explanations.
- **Every section must add value**: Don't include sections just for completeness. If a section would be empty or trivial, skip it.
- **Readability first**: Use clear headings, proper spacing, and visual hierarchy. Readers should scan and find what they need in under 30 seconds.
- **Respect the reader's time**: They want to understand what the project does, install it, and use it quickly.

**Target length by mode**:

- `--minimal`: 100-200 lines
- Default: 200-400 lines
- `--thorough`: 400-600 lines (only if the project genuinely needs it)

## Workflow Steps

### STEP 1: Validate Prerequisites

**CHECK repository state:**

- Run `git rev-parse --show-toplevel` to confirm we're in a git repository
- IF not a git repo: ERROR "Must be run from within a git repository. Initialize with 'git init' first."
- Store the repository root path

**Scope**: This command operates only on `README.md` at the repository root (the path from `git rev-parse --show-toplevel`). It won't touch nested README files in subdirectories or subpackages. If you're in a monorepo and want to update a package-specific README, the user should `cd` to that package directory first and run the command there.

**CHECK for README:**

- IF README.md doesn't exist in repo root: Note that we'll create a new README from scratch
- IF README.md exists: Proceed to analyze and update

### STEP 2: Parse Arguments

Interpret $ARGUMENTS for mode flags:

- `--preserve` → Keep existing custom sections (About, Features, Why X, Background), only update standard sections (Install, Usage, Structure)
- `--minimal` → Fast mode - generate basic structure only (badges, install, usage)
- `--thorough` → Deep analysis - read code examples, generate API documentation, comprehensive sections
- **Default** (no flags): Balanced update - standard sections with moderate detail

SET mode based on arguments parsed.

### STEP 3: Gather Codebase Intelligence

**Language/Stack Detection:**

- Look for `package.json` → Node.js/TypeScript/JavaScript project
- Look for `Cargo.toml` → Rust project
- Look for `pyproject.toml` or `setup.py` → Python project
- Look for `foundry.toml` → Solidity/Foundry smart contract project
- Look for `go.mod` → Go project
- Look for `Gemfile` → Ruby project
- Look for `composer.json` → PHP project

**Extract from detected metadata files:**

- Project name
- Version number
- Description
- License
- Dependencies (production and dev)
- Scripts/commands (build, test, lint, deploy)
- Repository URL (from git remote or package file)

**Discover project structure:**

```bash
# Get directory tree (2 levels deep) - use fd if available, ls otherwise
fd -t d -d 2 2>/dev/null | sort || find . -type d -maxdepth 2 | sort

# Count file types based on detected language
fd -e ts -e tsx -e js -e jsx 2>/dev/null | wc -l  # For JS/TS projects
fd -e rs 2>/dev/null | wc -l                       # For Rust
fd -e sol 2>/dev/null | wc -l                      # For Solidity
fd -e py 2>/dev/null | wc -l                       # For Python
fd -e go 2>/dev/null | wc -l                       # For Go
```

**Find key files:**

- LICENSE or LICENSE.md
- CONTRIBUTING.md
- CHANGELOG.md
- CODE_OF_CONDUCT.md
- .github/workflows/\*.yml (CI/CD)
- examples/ or example/ directory
- docs/ or doc/ directory

**Analyze entry points:**

- Search for main files based on detected language:
  - JavaScript/TypeScript: index.ts, index.js, src/index.ts, main.ts
  - Rust: src/main.rs, src/lib.rs
  - Python: __main__.py, main.py, src/__init__.py
  - Solidity: src/\*.sol contracts
  - Go: main.go, cmd/\*/main.go
- IF `--thorough`: Extract exports/public API from main files
- Find usage examples in tests/ or examples/ directories

### STEP 4: Read Existing README (If Preserving)

IF `--preserve` flag is set AND README.md exists:

- READ current README.md
- PARSE sections by extracting ## and ### headings with their content
- IDENTIFY sections to preserve (user-written custom content):
  - "About" or "Overview"
  - "Features" or "Why {Project}"
  - "Background" or "Motivation"
  - "Examples" (if manually written, not auto-generated)
  - "Acknowledgments" or "Credits" or "Thanks"
  - Custom sections with unique headings
- IDENTIFY sections to regenerate (standard, likely outdated):
  - "Installation" or "Install" or "Getting Started"
  - "Usage" or "Quick Start"
  - "API Reference" or "API"
  - "Project Structure" or "Structure"
  - Badges and shields
  - "Scripts" or "Commands" or "Available Scripts"
  - "Configuration" or "Config"

### STEP 5: Generate README Sections

**Determine project type and section order:**

**For Libraries** (no main executable, exports modules/functions):

1. Title + Badges
2. Description
3. Features (if `--preserve` keeps it, or `--thorough` generates it)
4. Installation
5. Usage (with code examples)
6. API Reference (if `--thorough`)
7. Contributing
8. License

**For Applications** (has main entry point, runnable program):

01. Title + Badges
02. Description
03. Features
04. Installation
05. Usage/Getting Started
06. Configuration (if config files found)
07. Scripts/Commands
08. Project Structure (if `--thorough`)
09. Contributing
10. License

**For Smart Contracts** (Solidity/Foundry):

1. Title + Badges
2. Description
3. Installation (npm + forge install)
4. Usage (Solidity import examples)
5. Functions/API
6. Testing
7. Deployment
8. Contributing
9. License

**Generate each section based on mode:**

**REMEMBER**: Keep all sections concise and scannable. Each section should provide immediate value without overwhelming the reader. When in doubt, write less.

**Title + Badges:**

- Extract project name from package.json, Cargo.toml, or git repo name
- Add relevant badges based on what exists:
  - CI status badge (if .github/workflows/\*.yml exists)
  - License badge (if LICENSE file found)
  - Version badge (from package version)
  - Framework/tool badges (Foundry, React, Next.js, etc.)
- Format: `# {Project Name}` followed by badges on next line

**Description:**

- IF `--preserve` AND existing description exists: Keep it
- ELSE: Extract from package.json/Cargo.toml description field
- ELSE: Generate brief description (1-2 sentences) from codebase analysis
- **Keep it concise**: 1-3 sentences maximum. Answer "What does this do?" and move on.

**Features:**

- IF `--preserve`: Keep existing Features section
- IF `--thorough`: Generate feature list from code analysis (scan main APIs, exported functions). **Limit to 5-8 key features** - highlight what matters most.
- IF `--minimal`: Omit this section
- ELSE (default): Include 3-5 brief bullet points if easily identifiable. Skip if features are obvious from description.

**Installation:**

- Detect package manager from lock files:
  - package-lock.json → npm
  - pnpm-lock.yaml → pnpm
  - yarn.lock → yarn
  - bun.lockb → bun
  - Cargo.lock → cargo
  - requirements.txt or poetry.lock → pip/poetry
- Show install command for detected manager(s)
- For Solidity: Include both npm and forge install instructions
- Include git clone if no package registry
- Add remappings.txt example for Foundry projects

**Usage:**

- IF examples/ directory exists: Extract and show example code
- IF tests exist: Parse test files for usage patterns
- Show import/require statements for libraries
- Provide minimal working example (5-15 lines of code)
- IF `--thorough`: Show 2-3 examples covering different use cases. **Each example should be under 20 lines.**
- Use proper code blocks with language tags
- **Brevity matters**: Show the simplest possible working code. Let users explore docs for advanced usage.

**Scripts/Commands:**

- IF package.json scripts exist: Extract and list them
- Format as table or bulleted list with descriptions:
  ```markdown
  - `npm run build` - Build the project
  - `npm test` - Run tests
  - `npm run lint` - Lint code
  ```
- Include common commands (build, test, lint, dev, deploy)

**Project Structure:**

- IF `--minimal`: Omit this section
- IF `--thorough` OR default mode:
  - Generate tree showing src/, tests/, docs/, etc.
  - **Keep it minimal**: Show only 5-10 most important directories/files
  - Explain key directories in 1 line each (no more than 2-3 explanations total)
  - Keep depth to 2 levels max (3 only if absolutely necessary)
  - Format as code block with tree structure
  - **Skip this section entirely** if the structure is obvious (e.g., single src/ directory)

**API Reference:**

- ONLY if `--thorough` mode
- Extract exported functions/classes from main entry points
- Show function signatures with 1-line descriptions
- **Limit to 8-12 most important APIs** - link to full docs for the rest
- Skip internal/private APIs
- **Consider skipping** this section if there's separate API documentation - just link to it instead

**Configuration:**

- IF config files exist (.env.example, config.yaml, etc.): Document them
- Show example config structure
- Explain key configuration options
- ELSE: Omit this section

**Contributing:**

- IF `--preserve`: Keep existing Contributing section
- IF CONTRIBUTING.md exists: Link to it with brief note
- ELSE: Provide basic contribution guidelines:
  ```markdown
  ## Contributing

  Contributions are welcome! Please feel free to submit a Pull Request.
  ```

**License:**

- Extract license type from LICENSE file or package.json
- Show license name and link
- Format: `This project is licensed under the {LICENSE} - see the [LICENSE](LICENSE) file for details.`
- IF no license found: Suggest adding one

### STEP 6: Compose Final README

BUILD complete markdown content:

**Structure:**

```markdown
# {project-name}

{badges row}

{description paragraph}

{features section if applicable}

## 📦 Installation

{installation instructions}

## 🚀 Usage

{usage examples with code blocks}

{scripts/commands section if applicable}

{project structure section if applicable}

{API reference if --thorough}

{configuration section if applicable}

## 🤝 Contributing

{contributing guidelines or link}

## 📄 License

{license information}
```

**Formatting rules:**

- Use emoji section headers for visual clarity (📦 Install, 🚀 Usage, 📖 Docs, 🤝 Contributing, etc.)
- Consistent heading levels: ## for main sections, ### for subsections
- Code blocks should have language specifiers (`bash, `typescript, \`\`\`solidity, etc.)
- Use tables for scripts/commands if there are 5+ items
- Use admonitions for important notes:
  ```markdown
  > [!NOTE]
  > Important context or helpful information

  > [!WARNING]
  > Breaking changes or critical notices
  ```
- Keep line length reasonable (wrap at ~100-120 chars in paragraphs)
- Add blank lines between sections for readability

**IF `--preserve` mode:**

- MERGE preserved sections with regenerated sections
- Maintain section order from original README where it makes sense
- Insert regenerated sections (Install, Usage, etc.) in their standard positions
- Keep custom sections in their original positions
- Avoid duplicating content between preserved and generated sections

### STEP 7: Write Updated README

WRITE the new README:

- Use the Write tool to create/overwrite README.md with the composed content
- Ensure content is complete and properly formatted

IF write succeeds:

- Note which sections were updated

IF write fails:

- Show specific error message
- Suggest fixes:
  - Check file permissions: `ls -la README.md`
  - Check disk space: `df -h .`
  - Verify write access to directory

### STEP 8: Display Summary

SHOW what changed:

```markdown
✓ Updated README.md

**Mode**: {minimal/default/thorough/preserve}

**Project Type**: {Library/Application/Smart Contract/etc.}
**Language/Stack**: {JavaScript/TypeScript/Rust/Solidity/Python/etc.}

**Sections Added/Updated:**
- Title + Badges
- Installation instructions
- Usage examples
- {list other updated sections}

{IF --preserve mode:}
**Sections Preserved:**
- {list preserved custom sections}

**Next Steps:**
1. Review README.md for accuracy
2. Customize any auto-generated content if needed
3. Commit changes: `git add README.md && git commit -m "docs: update README"`
```

IF errors occurred during generation:

- List specific issues encountered
- Suggest running with different flags (e.g., `--minimal` for simpler output)
- Note which sections may need manual review

## Usage Examples

**Basic update (default mode):**

```bash
/md-docs:update-readme
```

Generates a balanced README with standard sections and moderate detail.

**Preserve custom sections:**

```bash
/md-docs:update-readme --preserve
```

Keeps your hand-written Features, About, and other custom sections; only updates Install, Usage, Structure.

**Minimal README (fast):**

```bash
/md-docs:update-readme --minimal
```

Creates basic README with badges, installation, and usage only. Completes in ~3 seconds.

**Thorough analysis with API docs:**

```bash
/md-docs:update-readme --thorough
```

Deep codebase analysis, extracts API documentation, generates comprehensive sections. Takes ~20-30 seconds.

**Create new README from scratch:**

```bash
# In a repo without README.md
/md-docs:update-readme
```

Analyzes codebase and creates complete README from scratch.

## Key Characteristics

**Language-agnostic**: Works with Node.js, Rust, Python, Solidity, Go, Ruby, PHP, and other common stacks.

**Non-destructive**: Overwrites README.md in place (use git to restore if needed).

**Smart defaults**: Automatically detects project type (library vs application vs smart contract) and adjusts sections accordingly.

**Preserves manual work**: Use `--preserve` to keep custom sections like Features, About, Background while updating standard sections.

**Idempotent**: Running multiple times produces consistent results (same input → same output).

**Performance**:

- `--minimal`: ~3 seconds
- Default: ~10 seconds
- `--thorough`: ~20-30 seconds for large repos

**No git operations**: Only updates README.md file, never auto-commits. User reviews and commits manually.

**Monorepo handling**: Operates ONLY on README.md at the repository root (via `git rev-parse --show-toplevel`). Never touches nested README files. For package-specific READMEs in a monorepo, `cd` to that package directory and run the command there.

**Edge cases handled**:

- Non-standard project structures
- Multiple languages in one repo
- Private repositories (omits public-only badges)
- Missing metadata files (graceful degradation)
- No license file (suggests adding one)

**Restoration**: If you don't like the generated README, restore via git:

```bash
git checkout README.md
```
