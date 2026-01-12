# Workflows & Actions

Comprehensive guide for managing GitHub Actions workflows and runs using gh CLI.

## Viewing Workflows

```bash
# List workflows
gh workflow list

# View workflow runs
gh run list

# View specific run
gh run view 789

# Watch run
gh run watch 789

# View run logs
gh run view 789 --log
```

## Managing Workflows

```bash
# Trigger workflow
gh workflow run workflow.yml

# Cancel run
gh run cancel 789

# Rerun workflow
gh run rerun 789

# Download artifacts
gh run download 789
```

## Workflow Runs

Advanced commands for managing workflow runs.

### List and View Runs

```bash
# List recent workflow runs
gh run list

# List runs for specific workflow
gh run list --workflow=ci.yml

# List runs on specific branch
gh run list --branch=main

# List failed runs only
gh run list --status=failure

# Limit number of results
gh run list --limit=10

# View specific run details
gh run view 123456

# View run with logs
gh run view 123456 --log

# View run and open in browser
gh run view 123456 --web

# View specific job in a run
gh run view 123456 --job=123

# View run with exit status
gh run view 123456 --exit-status
```

### Monitor and Control Runs

```bash
# Watch a run in real-time
gh run watch 123456

# Watch with interval (default 3s)
gh run watch 123456 --interval=5

# Cancel running workflow
gh run cancel 123456

# Rerun failed jobs only
gh run rerun 123456 --failed

# Rerun all jobs in a workflow run
gh run rerun 123456

# Rerun specific job
gh run rerun 123456 --job=123
```

### Download Artifacts

```bash
# Download all artifacts from a run
gh run download 123456

# Download specific artifact by name
gh run download 123456 --name artifact-name

# Download to specific directory
gh run download 123456 --dir ./downloads

# Download artifacts from latest run
gh run download

# Download artifacts from specific workflow
gh run download --name=build-artifacts
```

## Workflow Dispatch

Trigger workflows with custom inputs.

```bash
# Trigger workflow with inputs
gh workflow run deploy.yml -f environment=production -f version=v1.2.3

# Trigger workflow on specific branch
gh workflow run ci.yml --ref feature-branch

# Trigger workflow and get the run ID
RUN_ID=$(gh workflow run ci.yml --json url --jq '.url | split("/") | .[-1]')
```

## GitHub Actions Cache

Manage GitHub Actions cache to optimize workflow performance.

```bash
# List caches in repository
gh cache list

# List caches for specific branch
gh cache list --ref refs/heads/main

# List caches with specific key
gh cache list --key npm-cache

# Sort caches by size
gh cache list --sort size

# Limit number of results
gh cache list --limit 10
```

## CI/CD Integration Patterns

### Trigger Workflow and Wait

```bash
# Trigger workflow and wait for completion
gh workflow run ci.yml --ref main && \
  sleep 5 && \
  gh run watch $(gh run list --workflow=ci.yml --limit 1 --json databaseId -q '.[0].databaseId')

# More robust version with retry
gh workflow run ci.yml --ref main
sleep 3
RUN_ID=$(gh run list --workflow=ci.yml --limit 1 --json databaseId -q '.[0].databaseId')
gh run watch $RUN_ID
```

### Check CI Status Before Merge

```bash
# Check all checks pass before merging
gh pr checks 123 && gh pr merge 123 --squash

# Wait for checks to complete
gh pr checks 123 --watch && gh pr merge 123 --squash

# Check specific required checks
gh pr view 123 --json statusCheckRollup --jq '.statusCheckRollup[] | select(.conclusion != "SUCCESS")'
```

### Auto-merge on Success

```bash
# Enable auto-merge when checks pass
gh pr merge 123 --auto --squash

# Enable auto-merge with specific merge method
gh pr merge 123 --auto --merge
gh pr merge 123 --auto --rebase

# Disable auto-merge
gh pr merge 123 --disable-auto
```

### Monitor Multiple Workflows

```bash
# Watch all active workflow runs
gh run list --status=in_progress --json databaseId,name,headBranch | \
  jq -r '.[] | "\(.databaseId) - \(.name) on \(.headBranch)"'

# Check status of all workflows for current commit
COMMIT=$(git rev-parse HEAD)
gh run list --commit=$COMMIT --json status,conclusion,name
```

### Workflow Run Analytics

```bash
# Get average duration for workflow
gh run list --workflow=ci.yml --limit=50 --json createdAt,updatedAt,conclusion | \
  jq '[.[] | select(.conclusion == "success") |
    ((.updatedAt | fromdateiso8601) - (.createdAt | fromdateiso8601))] |
    add / length / 60'

# Count failed runs in last 30 days
gh run list --created=">=$(date -v-30d +%Y-%m-%d)" --status=failure --json id | jq '. | length'

# List slowest workflow runs
gh run list --workflow=ci.yml --limit=20 --json databaseId,createdAt,updatedAt,conclusion | \
  jq 'sort_by((.updatedAt | fromdateiso8601) - (.createdAt | fromdateiso8601)) | reverse | .[:5]'
```

### Conditional Workflow Execution

```bash
# Trigger workflow only if tests pass locally
npm test && gh workflow run deploy.yml -f environment=staging

# Chain workflows
gh workflow run build.yml && \
  sleep 10 && \
  gh run watch $(gh run list --workflow=build.yml --limit 1 -q '.[0].databaseId') && \
  gh workflow run deploy.yml
```

### Retrieve Workflow Job Logs

```bash
# Download logs for a specific run
gh run view 123456 --log > workflow-logs.txt

# Download logs for failed jobs only
gh run view 123456 --log-failed > failed-jobs.txt

# View logs for specific job
gh api repos/:owner/:repo/actions/jobs/JOB_ID/logs > job.log
```

## Advanced Workflow Management

### Using JSON Output for Scripting

```bash
# Get workflow run details as JSON
gh run view 123456 --json status,conclusion,startedAt,url

# Parse specific fields
gh run view 123456 --json conclusion -q '.conclusion'

# List all failed runs with details
gh run list --status=failure --json databaseId,name,headBranch,conclusion,createdAt

# Get workflow run URL programmatically
gh run view 123456 --json url -q '.url'
```

### Workflow Environment Secrets

```bash
# List repository secrets (requires admin access)
gh secret list

# Set a secret
gh secret set SECRET_NAME < secret.txt
gh secret set SECRET_NAME --body "secret-value"

# List organization secrets
gh secret list --org organization-name
```

### Workflow Variables

```bash
# List repository variables
gh variable list

# Set a variable
gh variable set VAR_NAME --body "value"
```

## Troubleshooting

### Debug Failed Runs

```bash
# View failed run with logs
gh run view 123456 --log-failed

# List failed jobs in a run
gh run view 123456 --json jobs --jq '.jobs[] | select(.conclusion == "failure") | {name, conclusion}'

# Rerun failed jobs with debug logging
gh run rerun 123456 --failed --debug
```

### Check Workflow File Syntax

```bash
# View workflow file
gh workflow view ci.yml

# Download workflow file
gh api repos/:owner/:repo/contents/.github/workflows/ci.yml --jq '.content' | base64 -d

# List all workflow files
gh api repos/:owner/:repo/contents/.github/workflows --jq '.[] | .name'
```

## Best Practices

01. **Use specific workflow names** when triggering or listing runs to avoid ambiguity
02. **Enable auto-merge** for PRs to merge automatically when CI passes
03. **Monitor workflow cache** regularly to prevent cache bloat
04. **Use JSON output** for scripting and automation
05. **Watch runs interactively** during development to catch failures quickly
06. **Clean up old workflow runs** to keep repository tidy
07. **Use workflow dispatch inputs** for flexible, reusable workflows
08. **Set appropriate timeouts** to prevent workflows from running indefinitely
09. **Use artifacts judiciously** - they count against storage limits
10. **Leverage caching** to speed up workflows and reduce costs
