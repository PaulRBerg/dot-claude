---
argument-hint: '[description]'
description: Create an issue in vercel-labs/skills
model: opus
---

## Context

- GitHub CLI auth: !`gh auth status 2>&1 | rg -q "Logged in" && echo "authenticated" || echo "not authenticated"`
- Skills version: !`npx skills --version 2>/dev/null || echo "unknown"`
- Node.js version: !`node --version 2>/dev/null || echo "unknown"`
- Platform: !`uname -mprs`
- Arguments: $ARGUMENTS

## Task

Activate the `~/.claude/skills/yeet` skill to create an issue in `vercel-labs/skills` Github repository. Follow the workflow in `~/.claude/skills/yeet/references/issue-skills-cli.md`.
