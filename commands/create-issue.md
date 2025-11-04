---
argument-hint: [owner/repo] [description]
description: Create a GitHub issue with automatic labeling
---

## Context

- Current repository: !`gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "not a repository"`
- GitHub CLI auth: !`gh auth status 2>&1 | rg -q "Logged in" && echo "authenticated" || echo "not authenticated"`
- Arguments: $ARGUMENTS

## Your Task

### STEP 1: Validate prerequisites

IF not authenticated: ERROR "Run `gh auth login` first"

### STEP 2: Parse repository argument

Determine repository from $ARGUMENTS:
- IF the first token matches "owner/repo": use it as repository and remove it from $ARGUMENTS
- ELSE: infer the current repository from the working directory (error if not in a repo)

Note: If you don't specify a repository, the command will infer the current repository (owner/repo) automatically.

### STEP 3: Check for issue templates

Check if the repository has issue templates:
```bash
gh api repos/{owner}/{repo}/contents/.github/ISSUE_TEMPLATE --jq '.[].name' 2>/dev/null
```

IF markdown templates (*.md) are found:
- **SELECT TEMPLATE**: Infer which template best matches the user's intent from $ARGUMENTS
  - Common patterns: `bug_report.md`, `feature_request.md`, `enhancement.md`, `question.md`, etc.
  - Consider keywords in user's description (bug, feature, docs, etc.)
- **USE TEMPLATE**: Fetch and populate the selected template structure for the issue body
- Continue to STEP 4

ELSE:
- **USE DEFAULT TEMPLATE**: No templates found, use default structure (see STEP 6)
- Continue to STEP 4

### STEP 4: Check if labels should be applied

Extract the owner from the repository (the part before the `/`).

IF owner is `PaulRBerg` OR `sablier-labs`:
- **APPLY LABELS**: The user has permission to add labels
- Continue to STEP 5

ELSE:
- **SKIP LABELS**: Do not apply labels for this repository
- Skip STEP 5 and go directly to STEP 6

### STEP 5: Apply labels

**ONLY if owner is PaulRBerg or sablier-labs** (from STEP 4):

From content analysis, determine:
- **Type**: Primary category (bug, feature, docs, etc.)
- **Work**: Complexity via Cynefin (clear, complicated, complex, chaotic)
- **Priority**: Urgency (0=critical to 3=nice-to-have)
- **Effort**: Size (low, medium, high, epic)
- **Scope**: Domain area (only for sablier-labs/command-center)

### STEP 6: Generate title and body

From remaining $ARGUMENTS, create:
- **Title**: Clear, concise summary (5-10 words)
- **Body**: Use the selected template from STEP 3 if available, otherwise use this default template:

```
## Problem

[Extracted from user description]

## Solution

[If provided, otherwise "TBD"]

## Files Affected

<details><summary>Toggle to see affected files</summary>
<p>

- [{filename1}](https://github.com/{owner}/{repo}/blob/main/{path1})
- [{filename2}](https://github.com/{owner}/{repo}/blob/main/{path2})
- [{filename3}](https://github.com/{owner}/{repo}/blob/main/{path3})

</p>
</details>
```

**Admonitions**: Add GitHub-style admonitions when appropriate:
- `> [!NOTE]` - For context, dependencies, or implementation details users should notice
- `> [!TIP]` - For suggestions on testing, workarounds, or best practices
- `> [!IMPORTANT]` - For breaking changes, required migrations, or critical setup steps
- `> [!WARNING]` - For potential risks, known issues, or things that could go wrong
- `> [!CAUTION]` - For deprecated features, temporary solutions, or things to avoid

Place admonitions after the relevant section. Example:
```
## Solution

Refactor the authentication module to use JWT tokens.

> [!IMPORTANT]
> This change requires updating the environment variables. See `.env.example` for new required keys.
```

File links:
- **MUST** use markdown format: `[{filename}](https://github.com/{owner}/{repo}/blob/main/{path})`
- **Link text** should be the relative file path (e.g., `src/file.ts`, `docusaurus.config.ts`)
- **URL** must be the full GitHub URL
- List one per line if multiple files
- **OMIT the entire "## Files Affected" section** if no files are specified (e.g., for feature requests or planning issues)

### STEP 7: Create the issue

**IF owner is PaulRBerg or sablier-labs**:
```bash
gh issue create \
  --repo "$repository" \
  --title "$title" \
  --body "$body" \
  --label "label1,label2,label3"
```

**IF owner is neither PaulRBerg nor sablier-labs**:
```bash
gh issue create \
  --repo "$repository" \
  --title "$title" \
  --body "$body"
```

Display: "✓ Created issue: $URL"

On failure: show specific error and fix

## Label Reference

### Type
- `type: bug` - Something isn't working
- `type: feature` - New feature or request
- `type: perf` - Performance or UX improvement
- `type: docs` - Documentation
- `type: test` - Test changes
- `type: refactor` - Code restructuring
- `type: build` - Build system or dependencies
- `type: ci` - CI configuration
- `type: chore` - Maintenance work
- `type: style` - Code style changes

### Work (Cynefin)
- `work: clear` - Known solution
- `work: complicated` - Requires analysis but solvable
- `work: complex` - Experimental, unclear outcome
- `work: chaotic` - Crisis mode

### Priority
- `priority: 0` - Critical blocker
- `priority: 1` - Important
- `priority: 2` - Standard work
- `priority: 3` - Nice-to-have

### Effort
- `effort: low` - <1 day
- `effort: medium` - 1-3 days
- `effort: high` - Several days
- `effort: epic` - Weeks, multiple PRs

### Scope (sablier-labs/command-center only)
- `scope: frontend`
- `scope: backend`
- `scope: evm`
- `scope: solana`
- `scope: data`
- `scope: devops`
- `scope: integrations`
- `scope: marketing`
- `scope: business`
- `scope: other`

## Examples

```bash
/create-issue "Bug in auth flow causing token expiration in src/auth/token.ts"
/create-issue PaulRBerg/dotfiles "Add zsh configuration for tmux startup"
/create-issue sablier-labs/command-center "Implement dark mode for frontend dashboard"
```
