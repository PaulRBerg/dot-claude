---
argument-hint: '[base-branch] [reviewers] [title] [--draft] [--test-plan]'
description: Create a GitHub pull request with semantic change analysis
model: opus
---

## Context

- Current branch: !`git branch --show-current || echo "unknown"`
- Remote status: !`git status -b --porcelain | head -1 || echo "No remote tracking"`
- Recent commits: !`git log --oneline -5 || echo "No commits found"`
- GitHub CLI auth: !`gh auth status 2>&1 | rg -q "Logged in" && echo "authenticated" || echo "not authenticated"`
- Arguments: $ARGUMENTS

## Task

Activate the `oss` skill to create a GitHub pull request. Follow the workflow in `references/pull-requests.md`.
