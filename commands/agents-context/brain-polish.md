---
argument-hint: "[path?] [skill-name ...] [--root-only] [--preserve] [--minimal] [--thorough] [--dry-run]"
description: Polish README.md, AGENTS.md, CLAUDE.md symlinks, and existing project skills
model: opus
---

## Context

- Working directory: !`pwd`
- Git repository root: !`git rev-parse --show-toplevel 2>/dev/null || echo "not a git repo"`
- Existing READMEs: !`fd '^README\.md$' -t f | sort`
- Existing context files: !`fd '(CLAUDE|AGENTS)\.md' -t f -t l | sort`
- Project skills:
  !`fd --glob --full-path --hidden --no-ignore --follow --type f --exclude .git --exclude .claude '**/.agents/skills/*/SKILL.md' . 2>/dev/null | sort`
- Arguments: $ARGUMENTS

## Task

Activate the `agents-context` skill and run the `polish` workflow. Follow `references/brain-polish.md` from that skill.
