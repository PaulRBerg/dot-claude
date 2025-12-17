---
argument-hint: '[--monorepo]'
description: Update Node.js dependencies with smart prompting
---

## Context

- Current directory: $PWD
- Package manager: !`[ -f pnpm-lock.yaml ] && echo "pnpm" || ([ -f yarn.lock ] && echo "yarn" || echo "npm")`
- Arguments: $ARGUMENTS

## Task

Activate the `node-deps` skill to update dependencies. If `--monorepo` is passed, use recursive mode (`-r` flag).
