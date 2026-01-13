---
argument-hint: '[description]'
description: Create an issue in biomejs/biome
model: opus
---

## Context

- GitHub CLI auth: !`gh auth status 2>&1 | rg -q "Logged in" && echo "authenticated" || echo "not authenticated"`
- Biome rage: !`biome rage 2>/dev/null | head -20 || echo "biome not installed"`
- Arguments: $ARGUMENTS

## Task

Activate the `oss` skill to create an issue in `biomejs/biome`. Follow the workflow in the skill's `references/issues-biome.md`.
