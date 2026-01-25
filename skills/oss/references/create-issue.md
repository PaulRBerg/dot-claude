# Issue Creation Workflow

Create GitHub issues with automatic labeling, template detection, and intelligent content generation.

## Validate Prerequisites

IF not authenticated: ERROR "Run `gh auth login` first"

## Parse Repository Argument

Determine repository from arguments:

- IF the first token matches "owner/repo": use it as repository and remove it from arguments
- ELSE: infer the current repository from the working directory (error if not in a repo)

Note: If you don't specify a repository, the command will infer the current repository (owner/repo) automatically.

## Parse Optional Flags

IF arguments contain `--check`:

- Remove `--check` from arguments
- Set `check_mode = true`
- Continue to check for similar issues

ELSE:

- Set `check_mode = false`
- Skip similarity check and continue to template detection

## Determine Authenticated User

Get the authenticated GitHub username for permission checks:

```bash
gh api user -q .login
```

Store as `$AUTHENTICATED_USER` for later comparisons.

## Check for Similar Issues

**ONLY if `check_mode = true`:**

1. Extract key terms from the remaining arguments (issue description)

2. Search for similar open issues (full-text search across title and body):

   ```bash
   gh search issues "{key_terms}" --repo "{owner}/{repo}" --state open --limit 10 --json number,title,url
   ```

3. **IF similar issues found:**

   - Display the list of potentially related issues to the user
   - Use `AskUserQuestion` to prompt: "Similar issues found. Do you want to proceed with creating a new issue?"
     - Options: "Yes, create new issue" / "No, cancel"
   - IF user selects "No": Exit command with message "Issue creation cancelled"
   - IF user selects "Yes": Continue to template detection

4. **IF no similar issues found:**

   - Inform user: "No similar issues found. Proceeding with issue creation."
   - Continue to template detection

## Check for Issue Templates

Check if the repository has issue templates:

```bash
gh api repos/{owner}/{repo}/contents/.github/ISSUE_TEMPLATE --jq '.[].name | select(endswith(".md") or endswith(".yml") or endswith(".yaml"))' 2>/dev/null
```

Note: Exclude `config.yml` from template selection - it's for GitHub configuration, not an issue template.

IF templates are found (`.yml`, `.yaml`, or `.md`):

### Select Template

Infer which template best matches the user's intent from arguments:

- Common patterns: `bug_report.yml`, `feature_request.yml`, `bug_report.md`, `feature_request.md`, etc.
- Consider keywords in user's description (bug, feature, docs, model, etc.)
- Prefer YAML templates over Markdown if both exist for same type (GitHub lists YAML first)

### Parse Template

Based on file extension:

**IF `.yml` or `.yaml` template:**

1. Fetch raw template content:

   ```bash
   gh api repos/{owner}/{repo}/contents/.github/ISSUE_TEMPLATE/{template_name} --jq '.content' | base64 -d
   ```

2. Parse YAML structure to extract:

   - `name`, `description` - template metadata
   - `title` - default issue title prefix (e.g., "[BUG] ")
   - `labels` - pre-defined labels to merge with auto-labels
   - `body` array - form fields with `type`, `id`, `attributes`

3. For each field in `body` array:

   - `markdown`: Skip (display-only, not submitted)
   - `textarea`/`input`: Use `attributes.label` as section header, `attributes.description` as guidance
   - `dropdown`: Select appropriate option based on arguments context
   - `checkboxes`: Auto-acknowledge as "Confirmed" (preflight attestations)

**IF `.md` template:**

- Fetch and populate the markdown template structure for the issue body (existing behavior)

ELSE:

- **USE DEFAULT TEMPLATE**: No templates found, use default structure (see Generate Title and Body section)

## Check if Labels Should Be Applied

Extract the owner from the repository (the part before the `/`).

IF owner matches `$AUTHENTICATED_USER`:

- **APPLY LABELS**: The user has permission to add labels
- Continue to apply labels

ELSE:

- **SKIP LABELS**: Do not apply labels for this repository
- Skip label generation

## Apply Labels

**ONLY if owner matches $AUTHENTICATED_USER:**

From content analysis, determine:

- **Type**: Primary category (bug, feature, docs, etc.)
- **Work**: Complexity via Cynefin (clear, complicated, complex, chaotic)
- **Priority**: Urgency (0=critical to 3=nice-to-have)
- **Effort**: Size (low, medium, high, epic)

### Label Reference

#### Type

- `type: bug` - Something isn't working
- `type: feature` - New feature or request
- `type: perf` - Performance or UX improvement
- `type: docs` - Documentation
- `type: test` - Test changes
- `type: refactor` - Code restructuring
- `type: build` - Build system or dependencies
- `type: ci` - CI configuration
- `type: chore` - Maintenance work
- `type: style` - Code style changes

#### Work (Cynefin)

- `work: clear` - Known solution
- `work: complicated` - Requires analysis but solvable
- `work: complex` - Experimental, unclear outcome
- `work: chaotic` - Crisis mode

#### Priority

- `priority: 0` - Critical blocker
- `priority: 1` - Important
- `priority: 2` - Standard work
- `priority: 3` - Nice-to-have

#### Effort

- `effort: low` - \<1 day
- `effort: medium` - 1-3 days
- `effort: high` - Several days
- `effort: epic` - Weeks, multiple PRs

## Generate Title and Body

**Tone**: Write the issue body in an informal, casual style. Skip corporate speak and excessive formality. Be direct and conversational - write like you're explaining the issue to a colleague, not drafting a legal document.

From remaining arguments, create:

### Title

If YAML template has `title` field (e.g., "[BUG] "), prepend it to a clear, concise summary (5-10 words)

### Body

Generate based on template type:

**IF YAML template (`.yml`/`.yaml`):**

Generate markdown sections matching the template's `body` array fields:

```
### {field.attributes.label}

{Generated content based on arguments and field.attributes.description}
```

For each field type:

- `textarea`/`input`: Create a section with `### {label}` header, populate from arguments
- `dropdown`: Include selected option value (infer from context)
- `checkboxes`: Add "Confirmed" for preflight attestations
- `markdown`: Skip (not included in submitted issues)

Example for `feature_request.yml`:

```
### Problem Statement

Users cannot export their data in CSV format, limiting integration options.

### Proposed Solution

Add a CSV export button to the dashboard settings page.

### Alternative Solutions

Considered JSON export but CSV is more widely supported by spreadsheet tools.

### Priority

Medium - Would be very helpful

### Feature Category

CLI commands and flags
```

**IF Markdown template (`.md`):**

Populate the template structure with content from arguments (existing behavior).

**IF no template found:**

Use this default template:

```
## Problem

[Extracted from user description]

## Solution

[If provided, otherwise "TBD"]

## Files Affected

<details><summary>Toggle to see affected files</summary>
<p>

- [{filename1}](https://github.com/{owner}/{repo}/blob/main/{path1})
- [{filename2}](https://github.com/{owner}/{repo}/blob/main/{path2})
- [{filename3}](https://github.com/{owner}/{repo}/blob/main/{path3})

</p>
</details>
```

### Admonitions

Add GitHub-style admonitions when appropriate:

- `> [!NOTE]` - For context, dependencies, or implementation details users should notice
- `> [!TIP]` - For suggestions on testing, workarounds, or best practices
- `> [!IMPORTANT]` - For breaking changes, required migrations, or critical setup steps
- `> [!WARNING]` - For potential risks, known issues, or things that could go wrong
- `> [!CAUTION]` - For deprecated features, temporary solutions, or things to avoid

Place admonitions after the relevant section. Example:

```
## Solution

Refactor the authentication module to use JWT tokens.

> [!IMPORTANT]
> This change requires updating the environment variables. See `.env.example` for new required keys.
```

### File Links

- **MUST** use markdown format: `[{filename}](https://github.com/{owner}/{repo}/blob/main/{path})`
- **Link text** should be the relative file path (e.g., `src/file.ts`, `docusaurus.config.ts`)
- **URL** must be the full GitHub URL
- List one per line if multiple files
- **OMIT the entire "## Files Affected" section** if no files are specified (e.g., for feature requests or planning issues)

## Create the Issue

**Label handling:**

- If YAML template has `labels` field (e.g., `labels: ["bug"]`), merge with auto-generated labels
- Deduplicate labels (e.g., don't add "bug" twice if template and auto-labels both include it)
- Template labels always apply regardless of repository owner

**IF owner matches $AUTHENTICATED_USER:**

```bash
gh issue create \
  --repo "$repository" \
  --title "$title" \
  --body "$body" \
  --label "template-label1,auto-label1,auto-label2"
```

**IF owner does not match $AUTHENTICATED_USER:**

```bash
# If YAML template has labels defined:
gh issue create \
  --repo "$repository" \
  --title "$title" \
  --body "$body" \
  --label "template-label1,template-label2"

# If no template labels:
gh issue create \
  --repo "$repository" \
  --title "$title" \
  --body "$body"
```

Display: "✓ Created issue: $URL"

On failure: show specific error and fix

## Examples

```bash
# Basic usage (infers current repo)
"Bug in auth flow causing token expiration in src/auth/token.ts"

# Specify repository
PaulRBerg/dotfiles "Add zsh configuration for tmux startup"

# External repository
facebook/react "Add useDebounce hook to react-dom"

# With --check flag (searches for similar issues first)
--check "Bug in auth flow causing token expiration"

# External repo with --check
vercel/next.js --check "Improve error overlay for server components"
```
