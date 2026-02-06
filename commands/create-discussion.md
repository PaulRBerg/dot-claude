---
argument-hint: '[repository] [description] [--check]'
description: Create a GitHub discussion with automatic category selection
model: opus
---

## Context

- Current repository: !`gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "not a repository"`
- GitHub CLI auth: !`gh auth status 2>&1 | rg -q "Logged in" && echo "authenticated" || echo "not authenticated"`
- OS: !`~/.agents/skills/oss/scripts/get-macos-version.sh`
- Arguments: $ARGUMENTS

## Task

Activate the `~/.claude/skills/oss` skill to create a GitHub discussion. Follow the workflow in `~/.claude/skills/oss/references/create-discussion.md`.
