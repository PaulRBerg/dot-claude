---
argument-hint: "[path?] [target ...] [--root-only] [--preserve] [--minimal] [--thorough|--full] [--dry-run]"
description: Polish README.md, AGENTS.md, CLAUDE.md symlinks, existing skills, and context docs
---

## Context

- Working directory: !`pwd`
- Git repository root: !`git rev-parse --show-toplevel 2>/dev/null || echo "not a git repo"`
- Existing READMEs: !`fd '^README\.md$' -t f | sort`
- Existing context files: !`fd '(CLAUDE|AGENTS)\.md' -t f -t l | sort`
- Project skills:
  !`fd --glob --full-path --hidden --no-ignore --follow --type f --exclude .git --exclude .claude '**/.agents/skills/*/SKILL.md' . 2>/dev/null | sort`
- Source-catalog skills: !`git ls-files 'skills/*/SKILL.md' 2>/dev/null | sort`
- Arguments: $ARGUMENTS

## Task

Activate the `agents-brain` skill and run the `polish` workflow. Follow `references/polish.md` from that skill.
