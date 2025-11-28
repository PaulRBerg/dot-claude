# Automation Workflows

Common workflow patterns and automation examples using gh CLI.

## Common Workflows

### Code Review Workflow

```bash
# List PRs assigned to you
gh pr list --assignee @me

# Checkout PR for testing
gh pr checkout 123

# Run tests, review code...

# Approve PR
gh pr review 123 --approve --body "LGTM!"

# Merge PR
gh pr merge 123 --squash
```

### Quick PR Creation

```bash
# Create feature branch, make changes, commit
git checkout -b feature/new-feature
# ... make changes ...
git add .
git commit -m "Add new feature"
git push -u origin feature/new-feature

# Create PR from commits
gh pr create --fill

# View PR
gh pr view --web
```

### Issue Triage

```bash
# List open issues
gh issue list

# Add labels to issues
gh issue edit 456 --add-label needs-triage
gh issue edit 456 --add-label bug

# Assign issue
gh issue edit 456 --add-assignee @developer
```

## Advanced Automation Patterns

### Daily Standup Report

```bash
#!/bin/bash
# Generate daily activity report

echo "## My GitHub Activity - $(date +%Y-%m-%d)"
echo ""
echo "### PRs Created"
gh pr list --author @me --search "created:$(date +%Y-%m-%d)"
echo ""
echo "### PRs Reviewed"
gh search prs "reviewed-by:@me created:$(date +%Y-%m-%d)"
echo ""
echo "### Issues Closed"
gh issue list --author @me --state closed --search "closed:$(date +%Y-%m-%d)"
```

### Auto-label PRs by Files Changed

```bash
#!/bin/bash
# Auto-label PR based on changed files

PR_NUMBER=$1
FILES=$(gh pr diff $PR_NUMBER --name-only)

if echo "$FILES" | grep -q "^docs/"; then
  gh pr edit $PR_NUMBER --add-label "documentation"
fi

if echo "$FILES" | grep -q "\.test\."; then
  gh pr edit $PR_NUMBER --add-label "tests"
fi

if echo "$FILES" | grep -q "package\.json"; then
  gh pr edit $PR_NUMBER --add-label "dependencies"
fi
```

### Sync Fork with Upstream

```bash
#!/bin/bash
# Keep fork in sync with upstream

gh repo sync owner/fork --source upstream/repo --branch main
git fetch origin main
git merge origin/main
```

### Release Checklist Automation

```bash
#!/bin/bash
# Automated release checklist

VERSION=$1

# 1. Ensure on main branch
git checkout main && git pull

# 2. Run tests
npm test || exit 1

# 3. Create release tag
git tag -a "v$VERSION" -m "Release $VERSION"
git push origin "v$VERSION"

# 4. Create GitHub release
gh release create "v$VERSION" --generate-notes

# 5. Upload artifacts
gh release upload "v$VERSION" dist/*
```

### Bulk PR Operations

```bash
#!/bin/bash
# Approve all PRs from dependabot

gh pr list --author app/dependabot --json number --jq '.[].number' | \
  xargs -I {} gh pr review {} --approve --body "Auto-approved dependency update"
```

### Monitor CI Status

```bash
#!/bin/bash
# Monitor all active PRs for CI failures

gh pr list --json number,title,statusCheckRollup --jq '.[] |
  select(.statusCheckRollup.state == "FAILURE") |
  "\(.number): \(.title)"'
```

## Notifications and Monitoring

### Watch for PR Reviews

```bash
# Monitor PR for new reviews
while true; do
  REVIEWS=$(gh pr view 123 --json reviews --jq '.reviews | length')
  echo "Reviews: $REVIEWS"
  sleep 60
done
```

### Get Notified on Workflow Completion

```bash
#!/bin/bash
# Wait for workflow and send notification

RUN_ID=$1
gh run watch $RUN_ID
STATUS=$(gh run view $RUN_ID --json conclusion --jq '.conclusion')

if [ "$STATUS" = "success" ]; then
  osascript -e 'display notification "Workflow passed!" with title "GitHub Actions"'
else
  osascript -e 'display notification "Workflow failed!" with title "GitHub Actions"'
fi
```

### PR Staleness Check

```bash
#!/bin/bash
# Find stale PRs (no activity in 30 days)

gh pr list --json number,title,updatedAt --jq '.[] |
  select((now - (.updatedAt | fromdateiso8601)) > (30*86400)) |
  "\(.number): \(.title)"'
```

## Team Collaboration Patterns

### Assign PR Reviewers by Team

```bash
# Auto-assign team members as reviewers
gh pr create --reviewer team/backend,team/security --assignee @me
```

### Bulk Issue Assignment

```bash
# Assign all bugs to triage team
gh issue list --label bug --json number --jq '.[].number' | \
  xargs -I {} gh issue edit {} --add-assignee @triager
```

### Weekly Team Report

```bash
#!/bin/bash
# Generate weekly team activity summary

TEAM="myteam"
SINCE=$(date -v-7d +%Y-%m-%d)

echo "# Team Activity Report - Week of $(date +%Y-%m-%d)"
echo ""
echo "## PRs Merged"
gh search prs "team:$TEAM is:merged merged:>=$SINCE" --limit 100
echo ""
echo "## Issues Closed"
gh search issues "team:$TEAM is:closed closed:>=$SINCE" --limit 100
```

## Repository Management

### Batch Repository Creation

```bash
#!/bin/bash
# Create multiple repositories from template

TEMPLATE="org/template-repo"
REPOS=("project-a" "project-b" "project-c")

for repo in "${REPOS[@]}"; do
  gh repo create "org/$repo" --template "$TEMPLATE" --private
done
```

### Clone All Organization Repos

```bash
#!/bin/bash
# Clone all repos from an organization

ORG="myorg"
gh repo list "$ORG" --limit 1000 --json name --jq '.[].name' | \
  xargs -I {} gh repo clone "$ORG/{}"
```

### Sync Multiple Forks

```bash
#!/bin/bash
# Sync all your forks with upstream

gh repo list @me --fork --json name,parent --jq '.[] |
  "\(.name) \(.parent.owner.login)/\(.parent.name)"' | \
  while read fork upstream; do
    gh repo sync "$fork" --source "$upstream"
  done
```
