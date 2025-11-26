---
argument-hint: <current-path> <new-name>
description: Rename work directory and update Claude Code paths
model: haiku
---

## Context

- Arguments: $ARGUMENTS
- Home directory: !`echo $HOME`

## Your Task

### STEP 1: Parse and validate arguments

PARSE arguments from `$ARGUMENTS`:
- Split on whitespace
- First argument: `CURRENT_PATH` (full path to directory)
- Second argument: `NEW_NAME` (desired new directory name)

IF missing arguments:
- ERROR "Usage: /rename-work-dir <current-path> <new-name>"
- Example: `/rename-work-dir ~/sablier/frontend/ui new-ui`
- EXIT

VALIDATE `CURRENT_PATH`:
- Expand tilde if present: `CURRENT_PATH=$(echo $CURRENT_PATH | sed "s|^~|$HOME|")`
- Check exists: `test -d "$CURRENT_PATH"`
- IF not exists: ERROR "Directory does not exist: $CURRENT_PATH" and EXIT

VALIDATE `NEW_NAME`:
- Must not contain slashes
- IF contains `/`: ERROR "NEW_NAME must be a simple name without slashes" and EXIT

### STEP 2: Calculate target paths

EXTRACT current directory name:
- `CURRENT_NAME=$(basename "$CURRENT_PATH")`
- `PARENT_DIR=$(dirname "$CURRENT_PATH")`

CALCULATE main target:
- `NEW_PATH="$PARENT_DIR/$NEW_NAME"`

CALCULATE Claude Code paths:

**Projects directory encoding:**
- Convert path to absolute: `ABSOLUTE_NEW_PATH=$(cd "$PARENT_DIR" && pwd)/$NEW_NAME`
- Encode: Replace `/` with `-`, prepend `-`
- Example: `/Users/prb/sablier/frontend/new-ui` → `-Users-prb-sablier-frontend-new-ui`
- Store as: `NEW_PROJECTS_NAME`

**Prompts directory encoding:**
- Extract relative path from common base (e.g., `~/sablier/`, `~/work/`, `~/projects/`)
- Replace `/` with `-`
- Example: `sablier/frontend/new-ui` → `sablier-frontend-new-ui`
- Store as: `NEW_PROMPTS_NAME`

CALCULATE old encoded names using same logic with `CURRENT_PATH`:
- `OLD_PROJECTS_NAME`
- `OLD_PROMPTS_NAME`

SET full paths:
- `OLD_PROJECTS_PATH="$HOME/.claude/projects/$OLD_PROJECTS_NAME"`
- `NEW_PROJECTS_PATH="$HOME/.claude/projects/$NEW_PROJECTS_NAME"`
- `OLD_PROMPTS_PATH="$HOME/.claude-prompts/$OLD_PROMPTS_NAME"`
- `NEW_PROMPTS_PATH="$HOME/.claude-prompts/$NEW_PROMPTS_NAME"`

### STEP 3: Check for conflicts

CHECK if target directories already exist:

```bash
test -e "$NEW_PATH" && echo "main-conflict" || echo "main-ok"
test -e "$NEW_PROJECTS_PATH" && echo "projects-conflict" || echo "projects-ok"
test -e "$NEW_PROMPTS_PATH" && echo "prompts-conflict" || echo "prompts-ok"
```

IF any conflict detected:
- ERROR "Target path already exists: [conflicting path]"
- List all conflicts found
- ABORT operation
- EXIT

### STEP 4: Rename main directory

EXECUTE rename:
```bash
mv "$CURRENT_PATH" "$NEW_PATH"
```

IF failed:
- ERROR "Failed to rename main directory"
- Show error details
- ABORT (no rollback needed yet)
- EXIT

CONFIRM success:
- "✓ Renamed: $CURRENT_PATH → $NEW_PATH"

### STEP 5: Rename projects directory

CHECK if projects directory exists:
```bash
test -d "$OLD_PROJECTS_PATH" && echo "exists" || echo "missing"
```

IF missing:
- NOTICE "⊘ Projects directory not found, skipping: $OLD_PROJECTS_PATH"
- CONTINUE to next step

IF exists:
- EXECUTE rename:
  ```bash
  mv "$OLD_PROJECTS_PATH" "$NEW_PROJECTS_PATH"
  ```
- IF failed:
  - ERROR "Failed to rename projects directory"
  - WARN "Main directory was renamed. To rollback: mv '$NEW_PATH' '$CURRENT_PATH'"
  - EXIT
- CONFIRM success:
  - "✓ Updated: ~/.claude/projects/$OLD_PROJECTS_NAME → $NEW_PROJECTS_NAME"

### STEP 6: Rename prompts directory

CHECK if prompts directory exists:
```bash
test -d "$OLD_PROMPTS_PATH" && echo "exists" || echo "missing"
```

IF missing:
- NOTICE "⊘ Prompts directory not found, skipping: $OLD_PROMPTS_PATH"
- CONTINUE to summary

IF exists:
- EXECUTE rename:
  ```bash
  mv "$OLD_PROMPTS_PATH" "$NEW_PROMPTS_PATH"
  ```
- IF failed:
  - ERROR "Failed to rename prompts directory"
  - WARN "Partial rename completed. To rollback:"
  - WARN "  mv '$NEW_PATH' '$CURRENT_PATH'"
  - IF projects was renamed: WARN "  mv '$NEW_PROJECTS_PATH' '$OLD_PROJECTS_PATH'"
  - EXIT
- CONFIRM success:
  - "✓ Updated: ~/.claude-prompts/$OLD_PROMPTS_NAME → $NEW_PROMPTS_NAME"

### STEP 7: Display summary

OUTPUT summary:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Rename Complete: $CURRENT_NAME → $NEW_NAME
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Main directory:
  $NEW_PATH

Claude Code paths:
  ~/.claude/projects/$NEW_PROJECTS_NAME
  ~/.claude-prompts/$NEW_PROMPTS_NAME

Next steps:
  - Update any scripts or configs referencing old path
  - Git remotes are unaffected (still tracked by inode)
  - Open new directory: cd $NEW_PATH
```

## Examples

### Example 1: Rename frontend module

```bash
/rename-work-dir ~/sablier/frontend/ui new-ui
```

**Result:**
- Main: `~/sablier/frontend/new-ui`
- Projects: `~/.claude/projects/-Users-prb-sablier-frontend-new-ui`
- Prompts: `~/.claude-prompts/sablier-frontend-new-ui`

### Example 2: Rename top-level project

```bash
/rename-work-dir ~/projects/old-name new-name
```

**Result:**
- Main: `~/projects/new-name`
- Projects: `~/.claude/projects/-Users-prb-projects-new-name`
- Prompts: `~/.claude-prompts/projects-new-name`

## Notes

**Path encoding rules:**
- **Projects**: Full absolute path, `/` → `-`, prepend `-`
- **Prompts**: Relative path from common base, `/` → `-`

**Common bases for prompts**: `~/sablier/`, `~/work/`, `~/projects/`, `~/.config/`, etc.

**Rollback guidance:**
- Command provides explicit rollback commands if partial failure occurs
- Git repositories are safe (tracked by inode, not path)

**Safety:**
- Pre-flight conflict checks prevent overwrites
- Sequential operations with clear error messages
- Missing Claude Code directories are skipped (not errors)

**Limitations:**
- Single directory per invocation
- NEW_NAME must be simple name (no slashes)
- Does not update hardcoded paths in project files
