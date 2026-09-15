---
argument-hint: "[owner/repo#number | url | number] [update instructions] [--image <path>]... [--image-release]"
description: Update an existing GitHub issue (title, body, labels, assignees, state)
---

## Context

- OS: !`~/.agents/skills/yeet/scripts/get-macos-version.sh`
- Arguments: $ARGUMENTS

## Task

Activate the `yeet` skill to update an existing GitHub issue. Follow the workflow in
`~/.agents/skills/yeet/references/update-issue.md`.

When updating issue bodies that include environment information, use the OS value from the Context section above (e.g.,
"macOS Tahoe 26.2"). Do not use raw system output like "Darwin 25.2.0".
