---
argument-hint: '[description] [--check]'
description: Create a discussion in biomejs/biome
model: opus
---

## Context

- GitHub CLI auth: !`gh auth status 2>&1 | rg -q "Logged in" && echo "authenticated" || echo "not authenticated"`
- Arguments: $ARGUMENTS

## Task

Activate the `~/.claude/skills/oss` skill to create a discussion in `biomejs/biome` Github repository. Follow the workflow in `~/.claude/skills/oss/references/discussions.md`.
