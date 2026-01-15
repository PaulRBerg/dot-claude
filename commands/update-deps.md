---
argument-hint: '[--monorepo]'
description: Wrapper for node-deps skill with optional --monorepo flag for recursive updates
---

## Context

- Current directory: $PWD
- Package manager: !`[ -f pnpm-lock.yaml ] && echo "pnpm" || ([ -f yarn.lock ] && echo "yarn" || echo "npm")`
- Arguments: $ARGUMENTS

## Task

Activate the `~/.claude/skills/node-deps` skill to update dependencies. If `--monorepo` is passed, use recursive mode (`-r` flag).
