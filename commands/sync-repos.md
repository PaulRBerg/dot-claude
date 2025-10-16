---
description: Sync all nested repos by fetching latest main from upstream
---

## Your Task

### STEP 1: Find all git repositories

DEFINE target directories (edit this list to add/remove directories):

```bash
# Target directories to search for git repositories
SEARCH_DIRS=(
  ~/Projects
  ~/Sablier
  ~/Workspace/templates
)
```

SEARCH for git repositories in the target directories:

```bash
# Find all .git directories recursively (excluding common bloat dirs)
fd -H '.git$' --type d \
  --exclude node_modules \
  --exclude vendor \
  --exclude .cache \
  --exclude .npm \
  --exclude .pnpm-store \
  --exclude lib \
  --exclude repos \
  "${SEARCH_DIRS[@]}" 2>/dev/null | sed 's/\.git$//'
```

IF no repositories found:
- ERROR "No git repositories found in target directories"

STORE list of repository paths for processing

### STEP 2: Fetch latest changes from origin

FOR EACH repository:

1. **Change to repository directory**
2. **Check if remote exists**:
   ```bash
   git remote get-url origin 2>/dev/null
   ```
   - IF no remote: SKIP with message "⊘ Skipped (no remote): {repo}"

3. **Fetch all refs from origin**:
   ```bash
   git fetch origin 2>&1
   ```
   - IF fetch fails: LOG error and continue to next repo

### STEP 3: Sync main branch

FOR EACH repository with successful fetch:

1. **Store current branch**:
   ```bash
   current_branch=$(git branch --show-current)
   ```

2. **Check working tree status**:
   ```bash
   git status --porcelain
   ```
   - IF working tree is dirty: SKIP with message "⊘ Skipped (uncommitted changes): {repo}"

3. **Determine main branch name**:
   ```bash
   # Get the default branch from remote
   main_branch=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
   # Fallback to 'main' if not set
   main_branch=${main_branch:-main}
   ```

4. **Pull main branch**:
   ```bash
   git pull origin "$main_branch" 2>&1
   ```
   - IF pull succeeds: DISPLAY "✓ Synced: {repo} (on branch: {current_branch})"
   - IF pull fails: DISPLAY "✗ Failed: {repo} - {error_message}"

### STEP 4: Display summary

AGGREGATE results and display:

```
Repository Sync Summary
=======================

✓ Synced: 12 repositories
  - ~/Projects/dotfiles (on branch: feature/zsh)
  - ~/Sablier/lockup (on branch: main)
  - ~/Workspace/templates/typescript (on branch: develop)
  ...

⊘ Skipped: 3 repositories (2 dirty, 1 no remote)
✗ Failed: 1 repository
```

INCLUDE:
- Total count of synced/skipped/failed repos
- Full list of all synced repositories with their current branch
- Brief reason for skips/failures

## Examples

```bash
# Sync all repos
/sync-repos
```

Sample output:
```
Syncing repositories...

✓ Synced: ~/Projects/dotfiles (on branch: feature/zsh)
✓ Synced: ~/Sablier/lockup (on branch: main)
⊘ Skipped (uncommitted changes): ~/Projects/scripts
✓ Synced: ~/Workspace/templates/typescript (on branch: develop)

Repository Sync Summary
=======================
✓ Synced: 3 repositories
⊘ Skipped: 1 repository
✗ Failed: 0 repositories
```

## Notes

- Uses `fd` for fast directory traversal
- Explicitly excludes `node_modules`, `vendor`, `.cache`, `.npm`, `.pnpm-store`, `lib`, `repos` for performance
- Skips submodules (they have `.git` files, not directories) and dependency repos
- Fetches latest from origin before pulling
- Respects working tree status (won't pull with uncommitted changes)
- Pulls main branch regardless of current checkout
- Safe operation - won't modify uncommitted changes
- Recursively scans all nested directories
- Handles missing remotes gracefully
