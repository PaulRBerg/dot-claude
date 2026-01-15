---
argument-hint: '[repository] [description] [--check]'
description: Create a GitHub issue with automatic labeling
model: opus
---

## Context

- Current repository: !`gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "not a repository"`
- GitHub CLI auth: !`gh auth status 2>&1 | rg -q "Logged in" && echo "authenticated" || echo "not authenticated"`
- OS: !`~/.claude/helpers/get_macos_version.sh`
- Arguments: $ARGUMENTS

## Task

Activate the `~/.claude/skills/oss` skill to create a GitHub issue. Follow the workflow in `~/.claude/skills/oss/references/issues.md`.
