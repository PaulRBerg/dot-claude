# Troubleshooting

Common issues and solutions when using gh CLI.

## Authentication Issues

### Not Authenticated

**Error:** `gh: To get started with GitHub CLI, please run: gh auth login`

**Solution:**

```bash
# Login with web browser
gh auth login

# Login with token
gh auth login --with-token < token.txt

# Check auth status
gh auth status
```

### Token Expired

**Error:** `HTTP 401: Bad credentials (HTTP 401)`

**Solution:**

```bash
# Refresh authentication
gh auth refresh

# Re-login if refresh fails
gh auth logout
gh auth login
```

### Wrong Account

**Problem:** Authenticated as wrong user

**Solution:**

```bash
# Check current authentication
gh auth status

# Switch accounts
gh auth login --hostname github.com

# Use multiple accounts with different hosts
export GH_HOST=github.com
gh auth login
```

### Missing Scopes

**Error:** `HTTP 403: Resource not accessible by personal access token`

**Solution:**

```bash
# Add required scopes
gh auth refresh -h github.com -s repo,workflow,admin:org

# Common scopes needed:
# - repo: Full control of private repositories
# - workflow: Update GitHub Action workflows
# - admin:org: Full control of orgs and teams
# - write:packages: Upload packages to GitHub Package Registry
```

## Permission Issues

### Insufficient Permissions

**Error:** `HTTP 403: Resource not accessible by personal access token`

**Solution:**

- Ensure your token has required scopes (repo, workflow, admin:org, etc.)
- Re-run `gh auth refresh -h github.com -s <scope>` to add scopes
- Check if you're a member of the organization/repository

### Repository Access Denied

**Error:** `HTTP 404: Not Found` (when repo exists)

**Possible Causes:**

1. Repository is private and you don't have access
2. Repository name is incorrect
3. You're authenticated with wrong account

**Solution:**

```bash
# Verify repository access
gh repo view owner/repo

# Check if you're using correct repo name
gh repo list owner --limit 100 | grep repo-name

# Verify authentication
gh auth status
```

### Cannot Push to Repository

**Error:** `Permission to owner/repo denied to user`

**Solution:**

```bash
# Check if you have write access
gh api repos/owner/repo --jq '.permissions'

# Verify git remote uses correct authentication
gh auth setup-git

# Check remote URL
git remote -v
```

## Rate Limiting

### API Rate Limit Exceeded

**Error:** `API rate limit exceeded for user`

**Solution:**

```bash
# Check rate limit status
gh api rate_limit

# Use authenticated requests (higher limit: 5000/hr vs 60/hr)
gh auth login

# Wait for rate limit reset or use conditional requests
gh api rate_limit --jq '.rate.reset' | xargs -I {} date -r {}
```

### Secondary Rate Limit

**Error:** `You have exceeded a secondary rate limit`

**Solution:**

- Slow down request rate
- Add delays between API calls
- Use `--paginate` carefully with large result sets

## Common Command Errors

### PR Already Exists

**Error:** `pull request create failed: a pull request for branch "feature" into branch "main" already exists`

**Solution:**

```bash
# Find existing PR
gh pr list --head feature

# Update existing PR instead
gh pr edit <number> --title "New title" --body "New description"

# Or checkout and update the branch
gh pr checkout <number>
git commit --amend
git push --force-with-lease
```

### Cannot Merge PR

**Error:** `GraphQL: Pull Request is not mergeable`

**Causes & Solutions:**

- **Merge conflicts:**
  ```bash
  gh pr checkout <number>
  git merge main  # or base branch
  # Resolve conflicts
  git push
  ```
- **Required checks failing:**
  ```bash
  gh pr checks <number>  # View status
  # Wait for checks or fix failures
  ```
- **Required reviews missing:**
  ```bash
  gh pr view <number> --json reviewDecision
  # Get required approvals
  ```
- **Branch protection:**
  ```bash
  gh api repos/:owner/:repo/branches/main/protection
  # Ensure all rules are satisfied
  ```

### Workflow Not Found

**Error:** `could not resolve to a Workflow`

**Solution:**

```bash
# List available workflows
gh workflow list

# Use exact workflow file name (not display name)
gh workflow run ci.yml  # not "CI" or "ci"

# Use workflow ID
gh api repos/:owner/:repo/actions/workflows --jq '.workflows[] | "\(.id): \(.name)"'
gh workflow run <workflow-id>
```

### Cannot Checkout PR

**Error:** `failed to check out PR: could not find a branch for this pull request`

**Solution:**

```bash
# Fetch PR branch manually
gh pr view <number> --json headRefName,headRepository --jq '.headRefName'

# Checkout with fetch
git fetch origin pull/<number>/head:pr-<number>
git checkout pr-<number>
```

### Issue/PR Not Found

**Error:** `could not resolve to a PullRequest/Issue with the number of <number>`

**Solution:**

```bash
# Verify you're in correct repository
gh repo view

# Set default repository
gh repo set-default owner/repo

# Specify repository explicitly
gh pr view <number> --repo owner/repo
```

## Installation Issues

### gh Command Not Found

**Solutions:**

```bash
# macOS with Homebrew
brew install gh

# Update Homebrew if gh is outdated
brew upgrade gh

# Update PATH (if installed but not in PATH)
export PATH="/usr/local/bin:$PATH"

# Verify installation
which gh
gh --version
```

### Extension Installation Fails

**Error:** `failed to install extension`

**Solution:**

```bash
# Check extension name is correct
gh extension search <keyword>

# Install with full repository path
gh extension install owner/gh-extension-name

# Update existing extension
gh extension upgrade extension-name

# Reinstall if corrupted
gh extension remove extension-name
gh extension install owner/gh-extension-name
```

### Upgrade Issues

**Error:** `failed to upgrade gh`

**Solution:**

```bash
# macOS
brew upgrade gh

# Check for conflicts
brew doctor

# Reinstall if needed
brew reinstall gh
```

## Configuration Issues

### Default Repository Not Set

**Error:** `no default repository has been set`

**Solution:**

```bash
# Set default repository interactively
gh repo set-default

# Set default repository explicitly
gh repo set-default owner/repo

# Or use --repo flag
gh pr list --repo owner/repo
```

### Editor Not Opening

**Problem:** `gh pr create` doesn't open editor

**Solution:**

```bash
# Set default editor
gh config set editor vim
gh config set editor "code --wait"  # VS Code
gh config set editor "nano"

# Or use EDITOR environment variable
export EDITOR=vim
```

### Git Protocol Issues

**Error:** Issues with SSH/HTTPS

**Solution:**

```bash
# Set preferred protocol
gh config set git_protocol https
# or
gh config set git_protocol ssh

# Setup git credentials
gh auth setup-git
```

## Debugging Tips

### Enable Verbose Output

```bash
# Debug mode - shows API calls
GH_DEBUG=api gh pr list

# Trace OAuth flow
GH_DEBUG=oauth gh auth login

# Full debugging
GH_DEBUG=api,oauth gh <command>
```

### Check Configuration

```bash
# View current config
gh config list

# Check git remotes
git remote -v

# Verify default repository
gh repo view

# Check authentication
gh auth status
```

### Inspect JSON Output

```bash
# Get full JSON response
gh pr view <number> --json

# Pretty print with jq
gh pr view <number> --json | jq .

# Inspect specific fields
gh pr view <number> --json state,title,number
```

### Clear Cache

```bash
# If experiencing odd behavior, re-authenticate to refresh state
gh auth logout
gh auth login

# Or restart gh by closing all terminals and reopening
# Note: Cache will be automatically refreshed on next use
```

## Network Issues

### Connection Timeout

**Error:** `dial tcp: i/o timeout`

**Solution:**

```bash
# Check network connectivity
ping github.com

# Test GitHub API
curl -I https://api.github.com

# Use different network or VPN
# Check firewall/proxy settings
```

### SSL Certificate Issues

**Error:** `x509: certificate signed by unknown authority`

**Solution:**

```bash
# Update ca-certificates
# macOS
brew install ca-certificates

# Set custom CA bundle if needed
export GH_CA_BUNDLE=/path/to/ca-bundle.crt
```

## Getting Additional Help

### Built-in Help

```bash
# Command-specific help
gh pr create --help
gh pr --help
gh --help

# View manual pages
man gh
man gh-pr
```

### Check Version

```bash
# Current version
gh --version

# Check for updates
gh extension upgrade gh
brew upgrade gh  # macOS
```

### Community Resources

- **Official Manual:** https://cli.github.com/manual
- **GitHub CLI Repository:** https://github.com/cli/cli
- **Discussions:** https://github.com/cli/cli/discussions
- **Report Bugs:** https://github.com/cli/cli/issues
- **Stack Overflow:** Tag `github-cli`

### Common Error Codes

- **401:** Authentication failed
- **403:** Forbidden / insufficient permissions
- **404:** Not found / no access
- **422:** Validation failed / malformed request
- **500:** GitHub server error
