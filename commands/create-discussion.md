---
argument-hint: '[repository] [description] [--check]'
description: Create a GitHub discussion with automatic category selection
model: opus
---

## Context

- Current repository: !`gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "not a repository"`
- GitHub CLI auth: !`gh auth status 2>&1 | rg -q "Logged in" && echo "authenticated" || echo "not authenticated"`
- OS: !`~/.claude/helpers/get-macos-version.sh`
- Arguments: $ARGUMENTS

## Task

Activate the `oss` skill to create a GitHub discussion. Follow the workflow in `references/DISCUSSIONS.md`.
