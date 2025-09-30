---
allowed-tools: Bash(gh:*)
argument-hint: [owner/repo|this] [description]
description: Create a GitHub issue with automatic labeling using standard label set
---

## Context

- Current repository: !`gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "not a repository"`
- GitHub CLI auth: !`gh auth status 2>&1 | rg -q "Logged in" && echo "authenticated" || echo "not authenticated"`
- Arguments: $ARGUMENTS

## Your Task

### STEP 1: Validate prerequisites

CHECK GitHub authentication:
- IF Context shows "not authenticated": ERROR and exit with: "Run `gh auth login` first"

### STEP 2: Parse repository argument

EXTRACT repository from $ARGUMENTS:
- First word/token is the repository identifier
- IF "this": use current repository from Context
  - IF Context shows "not a repository": ERROR "Not in a git repository with GitHub remote"
  - ELSE: use the nameWithOwner value
- ELSE: treat as "owner/repo" format
- Remove repository from $ARGUMENTS for remaining description parsing

### STEP 3: Parse natural language description

EXTRACT from remaining $ARGUMENTS:
- **Issue Title**: Create a clear, concise title (5-10 words) that summarizes the main issue
- **Issue Body**: If description is detailed, create structured body with context
- If description is brief, use it as both title and body

### STEP 4: Analyze and determine labels

READ the parsed content and apply appropriate labels (see Label Reference below for complete definitions):

**Type:** Match keywords to determine primary type (`type: bug`, `type: feature`, `type: perf`, etc.)

**Work (Cynefin):** Assess complexity level (`work: clear`, `work: complicated`, `work: complex`, `work: chaotic`)

**Priority:** Evaluate urgency and impact (`priority: 0` to `priority: 3`)

**Effort:** Estimate work size (`effort: low`, `effort: medium`, `effort: high`, `effort: epic`)

**Scope (only for sablier-labs/command-center):** Identify domain area (`scope: frontend`, `scope: backend`, etc.)

### STEP 5: Create the issue

EXECUTE issue creation:
```bash
gh issue create \
  --repo "$repository" \
  --title "$extracted_title" \
  --body "$extracted_body" \
  --label "label1,label2,label3"
```

CAPTURE output:
- Extract issue URL from command output
- Display: "✓ Created issue: $ISSUE_URL"

IF command fails:
- Check specific error (auth, repo access, validation)
- Provide specific fix for that error

### STEP 6: Output summary

DISPLAY result showing:
- Extracted title and body
- Created issue URL
- Applied labels with reasoning
- Repository name

## Label Reference

### Type
- `type: bug` - Something isn't working (keywords: bug, error, broken, crash)
- `type: feature` - New feature or request (keywords: add, new, implement, create)
- `type: perf` - Performance or UX improvement (keywords: update, improve, optimize, enhance)
- `type: docs` - Documentation (keywords: docs, documentation, readme)
- `type: test` - Test changes (keywords: test, testing, spec)
- `type: refactor` - Code restructuring (keywords: refactor, cleanup, restructure)
- `type: build` - Build system or dependencies (keywords: build, dependency, package)
- `type: ci` - CI configuration (keywords: ci, workflow, pipeline)
- `type: chore` - Maintenance work (keywords: maintenance, chore, housekeeping)
- `type: style` - Code style changes (keywords: style, formatting, lint)

### Work (Cynefin Framework)
- `work: clear` - Sense-categorize-respond (clear requirements and known solution)
- `work: complicated` - Sense-analyze-respond (requires analysis or expertise but solution is findable)
- `work: complex` - Probe-sense-respond (experimental, research needed, unclear outcome)
- `work: chaotic` - Act-sense-respond (crisis mode, immediate response needed)

### Priority
- `priority: 0` - Critical blocker (production down)
- `priority: 1` - Important, deal with shortly (important feature or significant bug)
- `priority: 2` - Best effort (standard issue, part of regular work)
- `priority: 3` - Nice-to-have (low impact)

### Effort
- `effort: low` - Easy or tiny task, <1 day (quick fix)
- `effort: medium` - Default level of effort (standard task, 1-3 days)
- `effort: high` - Large or difficult task (several days of work)
- `effort: epic` - Multi-stage task, multiple PRs (weeks of work)

### Scope (sablier-labs/command-center only)
- `scope: frontend` - Frontend UI work
- `scope: backend` - Backend API work
- `scope: evm` - EVM smart contract work
- `scope: solana` - Solana smart contract work
- `scope: data` - Data pipeline work
- `scope: devops` - CI/CD infrastructure
- `scope: integrations` - Third-party integrations
- `scope: marketing` - Marketing content
- `scope: business` - Business strategy
- `scope: other` - Other scope

### Miscellaneous
- `duplicate` - Already exists
- `good first issue` - Good for newcomers
- `help` - Extra information needed
- `stale` - Inactive for long time

## Examples

```bash
# Current repository
/create-issue this "Bug in auth flow causing token expiration errors"

# Specific repository
/create-issue "PaulRBerg/dotfiles" "Add zsh configuration for tmux startup"

# Command-center with scope detection
/create-issue "sablier-labs/command-center" "Implement dark mode toggle for frontend dashboard"

# Documentation fix
/create-issue this "Update README with new installation steps"

# Performance issue
/create-issue "company/api-service" "API endpoints responding slowly, need optimization"
```

## Notes

- Automatically determines repository from "this" keyword
- Reads natural language to extract meaningful title and body
- Intelligently applies labels based on content analysis
- Scope labels only for sablier-labs/command-center
- Handles errors with specific remediation steps
