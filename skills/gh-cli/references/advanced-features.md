# Advanced Features

Advanced gh CLI capabilities for power users and automation.

## Aliases

Create custom shortcuts for frequently used commands.

```bash
# Create alias
gh alias set pv "pr view"
gh alias set bugs "issue list --label bug"

# List aliases
gh alias list

# Use alias
gh pv 123
```

## API Access

Direct access to GitHub's REST API through gh CLI.

```bash
# Make API call
gh api repos/:owner/:repo/issues

# With JSON data
gh api repos/:owner/:repo/issues -f title="Bug" -f body="Description"

# Paginated results
gh api --paginate repos/:owner/:repo/issues
```

## Extensions

Extend gh CLI functionality with community extensions.

```bash
# List extensions
gh extension list

# Install extension
gh extension install owner/gh-extension

# Upgrade extensions
gh extension upgrade --all
```

## Secrets and Variables

Manage GitHub Actions secrets and variables.

### Secrets

```bash
# List secrets
gh secret list

# Set secret
gh secret set SECRET_NAME

# Set secret from file
gh secret set SECRET_NAME < secret.txt
```

### Variables

```bash
# List variables
gh variable list

# Set variable
gh variable set VAR_NAME --body "value"
```

## SSH and GPG Keys

### SSH Keys

```bash
# List SSH keys
gh ssh-key list

# Add SSH key
gh ssh-key add ~/.ssh/id_ed25519.pub --title "My laptop"
```

### GPG Keys

```bash
# List GPG keys
gh gpg-key list

# Add GPG key
gh gpg-key add <key-file>
```

## Organizations

Manage organization settings and resources.

```bash
# List organizations
gh org list

# View organization info
gh org view <org-name>
```

## Projects

Work with GitHub Projects (beta).

```bash
# List projects
gh project list --owner <org-name>

# View project
gh project view <project-number>

# Create project
gh project create --owner <org-name> --title "Project Name"
```

## Repository Rulesets

View information about repository rulesets.

```bash
# List rulesets
gh ruleset list

# View ruleset
gh ruleset view <ruleset-id>
```

## Attestations

Work with artifact attestations for supply chain security.

```bash
# Verify release attestation
gh release verify <tag>

# Verify specific asset
gh release verify-asset <file> --repo owner/repo
```

## Advanced Scripting Patterns

### Using jq with gh

```bash
# Extract specific fields from JSON output
gh pr list --json number,title,author --jq '.[] | select(.author.login=="username")'

# Count open PRs
gh pr list --json state --jq 'length'

# Get PR numbers only
gh pr list --json number --jq '.[].number'
```

### Error Handling in Scripts

```bash
# Check if PR exists before operating
if gh pr view 123 &>/dev/null; then
  gh pr merge 123
else
  echo "PR not found"
fi
```

### Batch Operations

```bash
# Add label to multiple issues
gh issue list --assignee @me --json number --jq '.[].number' | xargs -I {} gh issue edit {} --add-label "in-progress"
```
