---
argument-hint: "[path?] [--root-only] [--dry-run] [--force]"
description: Initialize AGENTS.md files, with nested files only where a subtree needs them
---

## Context

- Working directory: !`pwd`
- Git repository root: !`git rev-parse --show-toplevel 2>/dev/null || echo "not a git repo"`
- Arguments: $ARGUMENTS

## Task

Activate the `agents-brain` skill. Run its `create-agents-md` workflow and follow `references/create-agents-md.md`.

Read `references/asd-ste100.md` completely before writing agent-facing prose, and apply its review. Use
`references/create-docs.md` for the AGENTS.md content and CLAUDE.md rules that the workflow names.

Create the scope-root AGENTS.md. Judge each subtree on its evidence, and create a nested AGENTS.md only where the
workflow's decision rule holds. Keep writes inside the selected scope.
