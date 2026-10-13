---
argument-hint: "[skill-name]"
description: Create a project-local agent skill
---

## Context

- Working directory: !`pwd`
- Git repository root: !`git rev-parse --show-toplevel 2>/dev/null || echo "not a git repo"`
- Arguments: $ARGUMENTS

## Task

Activate the `agents-brain` skill. Run its `create-skill` workflow and follow `references/create-skill.md`.

Use `references/writing-great-skills.md` for skill authoring. Read `references/asd-ste100.md` completely before writing
agent-facing prose, and apply its review.

Create a project-local skill within the current working directory's scope. Preserve the installable catalog boundary and
do not route catalog skill creation through this workflow.
