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

### STEP 3: Check label permissions

Check if the authenticated user has permission to add labels:

```bash
gh api /repos/$repository/collaborators/$(gh api user -q .login)/permission -q .role_name
```

The user needs at least `triage` permission to add labels. Valid roles with label permissions: `triage`, `write`, `maintain`, `admin`.

IF role is `read` or permission check fails:
- **WARNING**: "You don't have permission to add labels to issues in $repository"
- **SKIP STEP 4** (do not apply labels)
- Continue with issue creation without labels

### STEP 4: Apply labels

**ONLY if user has triage+ permission** (from STEP 3):

From content analysis, determine:
- **Type**: Primary category (bug, feature, docs, etc.)
- **Work**: Complexity via Cynefin (clear, complicated, complex, chaotic)
- **Priority**: Urgency (0=critical to 3=nice-to-have)
- **Effort**: Size (low, medium, high, epic)
- **Scope**: Domain area (only for sablier-labs/command-center)

### STEP 5: Generate title and body

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

### STEP 6: Create the issue

**IF user has label permission**:
```bash
gh issue create \
  --repo "$repository" \
  --title "$title" \
  --body "$body" \
  --label "label1,label2,label3"
```

**IF user lacks label permission**:
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
