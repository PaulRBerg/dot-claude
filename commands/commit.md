---
argument-hint: '[--all] [--deep] [--push] [--stack]'
description: Create atomic git commits with smart heuristic analysis
model: sonnet
---

## Context

- Current branch: !`git branch --show-current`
- Git status: !`git status --short --branch`
- Staged diff: !`git diff --cached`
- Arguments: $ARGUMENTS

## Task

Activate the `~/.claude/skills/git-commit` skill to commit changes.
