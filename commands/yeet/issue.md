---
argument-hint: '[repository] [description] [--check]'
description: Create a GitHub issue with automatic labeling
---

## Context

- Current repository: !`gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "not a repository"`
- GitHub CLI auth: !`gh auth status 2>&1 | rg -q "Logged in" && echo "authenticated" || echo "not authenticated"`
- OS: !`~/.agents/skills/yeet/scripts/get-macos-version.sh`
- Arguments: $ARGUMENTS

## Task

Activate the `~/.claude/skills/yeet` skill to create a GitHub issue. Follow the workflow in `~/.claude/skills/yeet/references/create-issue.md`.

When writing issue bodies that include environment information, use the OS value from the Context section above (e.g., "macOS Tahoe 26.2"). Do not use raw system output like "Darwin 25.2.0".
