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

IF not authenticated: ERROR "Run `gh auth login` first"

### STEP 2: Parse repository argument

First token in $ARGUMENTS is the repository:
- IF "this": use current repository (error if not in a repo)
- ELSE: treat as "owner/repo" format

### STEP 3: Generate title and body

From remaining $ARGUMENTS, create:
- **Title**: Clear, concise summary (5-10 words)
- **Body**: Use this template:

```
## Problem

[Extracted from user description]

## Solution

[If provided, otherwise "TBD"]

## Files Affected

<details><summary>Toggle to see affected files</summary>
<p>

- https://github.com/{owner}/{repo}/blob/main/{path1}
- https://github.com/{owner}/{repo}/blob/main/{path2}
- https://github.com/{owner}/{repo}/blob/main/{path3}

</p>
</details>
```

File links:
- **MUST** use full GitHub URLs: `https://github.com/{owner}/{repo}/blob/main/{path}`
- **NEVER** use relative paths (e.g., `src/file.ts`)
- List one per line if multiple files
- Use "TBD" if none specified

### STEP 4: Apply labels

From content analysis, determine:
- **Type**: Primary category (bug, feature, docs, etc.)
- **Work**: Complexity via Cynefin (clear, complicated, complex, chaotic)
- **Priority**: Urgency (0=critical to 3=nice-to-have)
- **Effort**: Size (low, medium, high, epic)
- **Scope**: Domain area (only for sablier-labs/command-center)

### STEP 5: Create the issue

```bash
gh issue create \
  --repo "$repository" \
  --title "$title" \
  --body "$body" \
  --label "label1,label2,label3"
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
/create-issue this "Bug in auth flow causing token expiration in src/auth/token.ts"
/create-issue PaulRBerg/dotfiles "Add zsh configuration for tmux startup"
/create-issue sablier-labs/command-center "Implement dark mode for frontend dashboard"
```
