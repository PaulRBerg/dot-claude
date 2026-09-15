---
argument-hint: "[owner/repo#number | url | number] [update instructions] [--image <path>]... [--image-release]"
description: Update an existing GitHub discussion (title, body, category, labels)
---

## Context

- OS: !`~/.agents/skills/yeet/scripts/get-macos-version.sh`
- Arguments: $ARGUMENTS

## Task

Activate the `yeet` skill to update an existing GitHub discussion. Follow the workflow in
`~/.agents/skills/yeet/references/update-discussion.md`.

When updating discussion bodies that include environment information, use the OS value from the Context section above
(e.g., "macOS Tahoe 26.2"). Do not use raw system output like "Darwin 25.2.0".
