# Common Patterns

Shared conventions and patterns used across all documentation workflows.

## Argument Parsing

Standard arguments supported across workflows:

- `--dry-run`: Preview changes without writing files
- `--preserve`: Maintain existing structure, only fix inaccuracies
- `--minimal`: Generate minimal documentation
- `--thorough`/`--full`: Generate comprehensive documentation
- `--force`: Override safety checks

Parse arguments from user input and set appropriate flags for workflow execution.

## Backup File Handling

Always create backups before overwriting existing files:

```bash
cp CLAUDE.md CLAUDE.md.backup
cp AGENTS.md AGENTS.md.backup
test -f DOCS.md && cp DOCS.md DOCS.md.backup                 # only if exists
test -f CONTRIBUTING.md && cp CONTRIBUTING.md CONTRIBUTING.md.backup  # only if exists
```

Inform the user when backups are created:

```
Created backup: CLAUDE.md.backup
Created backup: AGENTS.md.backup
Created backup: DOCS.md.backup (optional file)
Created backup: CONTRIBUTING.md.backup (optional file)
```

Never delete backups automatically. Let users manage backup cleanup manually. Note that DOCS.md and CONTRIBUTING.md are optional—skip backup and update operations if they don't exist.

## Writing Style

Documentation should follow these conventions:

- **Terse**: Omit needless words, lead with the answer
- **Imperative**: Use command form ("Build the project") not descriptive ("The project is built")
- **Expert-to-expert**: Skip basic explanations, assume competence
- **Scannable**: Use headings, lists, and code blocks for easy navigation
- **Accurate**: Verify all commands and paths against actual codebase

**Good:**

```markdown
## Build

Build the project:

\`\`\`bash
npm run build
\`\`\`

Run tests:

\`\`\`bash
npm test
\`\`\`
```

**Bad:**

```markdown
## Building the Project

In order to build the project, you will need to use the npm build command. This command will compile all of the TypeScript files and generate the output in the dist directory. First, make sure you have installed all dependencies by running npm install.
```

## Report Formatting

After completing operations, display a clear summary:

```
✓ Updated CLAUDE.md
  - Fixed build command
  - Added new directory structure

✓ Updated README.md
  - Added installation section
  - Updated badges

✓ Updated DOCS.md
  - Updated API endpoint documentation
  - Fixed function signature

✗ AGENTS.md not found
  - Skipped update

⊘ DOCS.md not found
  - Skipped (optional file)

⊘ CONTRIBUTING.md not found
  - Skipped (optional file)
```

Use checkmarks (✓) for successful operations, crosses (✗) for failed operations, and ⊘ for skipped optional files. Include indented details showing specific changes made.

## File Detection

Detect project type and structure by checking for characteristic files:

```bash
# Node.js/JavaScript
test -f package.json

# Python
test -f pyproject.toml || test -f setup.py

# Rust
test -f Cargo.toml

# Go
test -f go.mod
```

Use detection results to customize documentation templates and commands.

## Metadata Extraction

Read package configuration files to extract accurate metadata:

```bash
# Node.js
cat package.json | grep -E '"name"|"version"|"description"'

# Python
cat pyproject.toml | grep -E 'name|version|description'
```

Parse JSON or TOML appropriately to extract values. Never hardcode or guess metadata when it can be read directly from configuration files.
