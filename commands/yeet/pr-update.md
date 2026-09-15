---
argument-hint: "[update-instructions]"
description: Update an existing GitHub pull request with semantic change analysis
---

## Context

- Current branch: !`git branch --show-current || echo "unknown"`
- Remote status: !`git status -b --porcelain | head -1 || echo "No remote tracking"`
- Recent commits: !`git log --oneline -5 || echo "No commits found"`
- Arguments: $ARGUMENTS

## Task

Activate the `yeet` skill to update an existing GitHub pull request. Follow the workflow in
`~/.agents/skills/yeet/references/update-pr.md`.
