---
argument-hint: '[repository] [description] [--check]'
description: Create a GitHub discussion with automatic category selection
model: opus
---

## Context

- Current repository: !`gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "not a repository"`
- GitHub CLI auth: !`gh auth status 2>&1 | rg -q "Logged in" && echo "authenticated" || echo "not authenticated"`
- Arguments: $ARGUMENTS
- OS: !`~/.claude/helpers/get-macos-version.sh`

## Your Task

### STEP 1: Validate prerequisites

IF not authenticated: ERROR "Run `gh auth login` first"

### STEP 2: Parse repository argument

Determine repository from $ARGUMENTS:

- IF the first token matches "owner/repo": use it as repository and remove it from $ARGUMENTS
- ELSE: infer the current repository from the working directory (error if not in a repo)

Note: If you don't specify a repository, the command will infer the current repository (owner/repo) automatically.

### STEP 2.5: Parse optional flags

IF `$ARGUMENTS` contains `--check`:

- Remove `--check` from `$ARGUMENTS`
- Set `check_mode = true`
- Continue to STEP 2.6

ELSE:

- Set `check_mode = false`
- Skip STEP 2.6 and continue to STEP 3

### STEP 2.6: Check for similar discussions (if `--check` flag present)

**ONLY if `check_mode = true`:**

1. Extract key terms from the remaining `$ARGUMENTS` (discussion description)

1. Search for similar open discussions:

   ```bash
   gh search discussions "{key_terms}" --repo "{owner}/{repo}" --limit 10 --json number,title,url
   ```

1. **IF similar discussions found:**

   - Display the list of potentially related discussions to the user
   - Use `AskUserQuestion` to prompt: "Similar discussions found. Do you want to proceed with creating a new discussion?"
     - Options: "Yes, create new discussion" / "No, cancel"
   - IF user selects "No": Exit command with message "Discussion creation cancelled"
   - IF user selects "Yes": Continue to STEP 3

1. **IF no similar discussions found:**

   - Inform user: "No similar discussions found. Proceeding with discussion creation."
   - Continue to STEP 3

### STEP 3: Get discussion categories and repository info

Fetch the repository ID and available discussion categories via GraphQL:

```bash
gh api graphql -f query='
  query($owner: String!, $name: String!) {
    repository(owner: $owner, name: $name) {
      id
      discussionCategories(first: 25) {
        nodes {
          id
          name
          slug
          description
          isAnswerable
        }
      }
    }
  }
' -f owner="{owner}" -f name="{repo}"
```

From the returned categories, **infer the best category** based on $ARGUMENTS content:

| Category Pattern                 | When to Use                                            |
| -------------------------------- | ------------------------------------------------------ |
| **Ideas** / **Feature Requests** | User wants to propose something new                    |
| **Q&A**                          | User is asking a question or seeking help              |
| **General**                      | General conversation, no specific category fits        |
| **Show and Tell**                | User is sharing something they built/created           |
| **Announcements**                | Official announcements (rarely used by external users) |
| **Polls**                        | User wants community input via voting                  |

IF no obvious match, default to **General** or **Ideas** depending on context.

### STEP 4: Check for discussion templates

Check if the repository has discussion category forms:

```bash
gh api repos/{owner}/{repo}/contents/.github/DISCUSSION_TEMPLATE --jq '.[].name | select(endswith(".yml") or endswith(".yaml"))' 2>/dev/null
```

IF templates are found:

1. **SELECT TEMPLATE**: Find template matching the selected category's slug (e.g., `ideas.yml` for the Ideas category)

1. **PARSE TEMPLATE**: Fetch and parse the YAML template:

   ```bash
   gh api repos/{owner}/{repo}/contents/.github/DISCUSSION_TEMPLATE/{template_name} --jq '.content' | base64 -d
   ```

1. Parse YAML structure to extract:

   - `title` - default discussion title prefix
   - `body` array - form fields with `type`, `id`, `attributes`

1. For each field in `body` array:

   - `markdown`: Skip (display-only, not submitted)
   - `textarea`/`input`: Use `attributes.label` as section header, `attributes.description` as guidance
   - `dropdown`: Select appropriate option based on $ARGUMENTS context
   - `checkboxes`: Auto-acknowledge as "Confirmed" (preflight attestations)

ELSE:

- **USE DEFAULT TEMPLATE**: No templates found, use default structure (see STEP 5)

### STEP 5: Generate title and body

**Tone**: Write the discussion body in an informal, casual style. Be direct and conversational.

From remaining $ARGUMENTS, create:

- **Title**: If YAML template has `title` field, prepend it. Otherwise, clear, concise summary (5-10 words)
- **Body**: Generate based on template or default structure

**IF YAML template found:**

Generate markdown sections matching the template's `body` array fields:

```
### {field.attributes.label}

{Generated content based on $ARGUMENTS and field.attributes.description}
```

**IF no template found:**

Use this default template:

```
## Context

[Extracted from user description - what is this discussion about?]

## Discussion Points

[Key points or questions to discuss]

## Additional Context

[Any relevant background information, if applicable]
```

**Admonitions**: Add GitHub-style admonitions when appropriate:

- `> [!NOTE]` - For context or background information
- `> [!TIP]` - For suggestions or related ideas
- `> [!IMPORTANT]` - For key points that shouldn't be missed

### STEP 6: Create the discussion

Create the discussion via GraphQL mutation:

```bash
gh api graphql -f query='
  mutation($repositoryId: ID!, $categoryId: ID!, $title: String!, $body: String!) {
    createDiscussion(input: {
      repositoryId: $repositoryId
      categoryId: $categoryId
      title: $title
      body: $body
    }) {
      discussion {
        url
      }
    }
  }
' -f repositoryId="$REPO_ID" -f categoryId="$CAT_ID" -f title="$TITLE" -f body="$BODY"
```

Extract the URL from the response and display: "✓ Created discussion: $URL"

On failure: show specific error and suggest fix

## Category Inference Guide

Use these heuristics to select the best category:

| Keywords in $ARGUMENTS                                    | Likely Category |
| --------------------------------------------------------- | --------------- |
| "idea", "proposal", "suggest", "would be nice", "feature" | Ideas           |
| "how do I", "help", "question", "why does", "what is"     | Q&A             |
| "built", "made", "created", "sharing", "check out"        | Show and Tell   |
| "vote", "poll", "which", "prefer"                         | Polls           |
| General conversation, feedback, meta-discussion           | General         |

## Examples

```bash
/create-discussion "Proposal for adding dark mode support"
/create-discussion PaulRBerg/dotfiles "Ideas for improving the zsh setup"
/create-discussion vercel/next.js "Question about server components caching"

# With --check flag (searches for similar discussions first)
/create-discussion --check "How to configure custom routes"
/create-discussion facebook/react --check "Proposal for new hook API"
```
