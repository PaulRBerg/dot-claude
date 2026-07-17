---
argument-hint: "[repo] [description]"
description: Create an issue in a sablier-labs repository
model: opus
---

## Context

- GitHub CLI auth: !`gh auth status 2>&1 | rg -q "Logged in" && echo "authenticated" || echo "not authenticated"`
- Arguments: $ARGUMENTS

## Task

Activate the `yeet` skill to create an issue in a `sablier-labs/*` Github repository. The first argument is the repo
name without the org prefix (e.g., `lockup` → `sablier-labs/lockup`). Follow the workflow in
`~/.agents/skills/yeet/references/issue-sablier.md`.
