---
argument-hint: '[base-branch] [title] [--reviewers <name>] [--draft]'
description: Create a GitHub pull request with semantic change analysis
---

## Context

- Current branch: !`git branch --show-current || echo "unknown"`
- Remote status: !`git status -b --porcelain | head -1 || echo "No remote tracking"`
- Recent commits: !`git log --oneline -5 || echo "No commits found"`
- GitHub CLI auth: !`gh auth status 2>&1 | rg -q "Logged in" && echo "authenticated" || echo "not authenticated"`
- Arguments: $ARGUMENTS

## Task

Activate the `yeet` skill to create a GitHub pull request. Follow the workflow in `~/.agents/skills/yeet/references/create-pr.md`.
