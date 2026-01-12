# Discussion Creation Workflow

This reference document describes the workflow for creating GitHub discussions with automatic category selection and optional template support. The workflow intelligently selects the appropriate category, checks for similar discussions, and formats the discussion body according to repository templates.

## Validate Prerequisites

Check if GitHub CLI is authenticated:

```bash
gh auth status 2>&1 | rg -q "Logged in"
```

If not authenticated, error with: "Run `gh auth login` first"

## Parse Repository Argument

Determine the target repository:

- If the first token matches "owner/repo" format: use it as repository
- Otherwise: infer from the current working directory using `gh repo view --json nameWithOwner -q .nameWithOwner`
- Error if not in a repository and no explicit repository provided

## Check for Similar Discussions (Optional)

If the `--check` flag is present:

1. Extract key terms from the discussion description

2. Search for similar open discussions:

   ```bash
   gh search discussions "{key_terms}" --repo "{owner}/{repo}" --limit 10 --json number,title,url
   ```

3. **If similar discussions found:**

   - Display the list of potentially related discussions
   - Use `AskUserQuestion`: "Similar discussions found. Do you want to proceed with creating a new discussion?"
   - Options: "Yes, create new discussion" / "No, cancel"
   - If "No": Exit with message "Discussion creation cancelled"
   - If "Yes": Continue with creation

4. **If no similar discussions found:**

   - Inform user: "No similar discussions found. Proceeding with discussion creation."
   - Continue with creation

## Fetch Discussion Categories

Retrieve repository ID and available discussion categories via GraphQL:

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

## Select Discussion Category

Infer the best category based on the discussion description:

| Category Pattern                 | When to Use                                            |
| -------------------------------- | ------------------------------------------------------ |
| **Ideas** / **Feature Requests** | User wants to propose something new                    |
| **Q&A**                          | User is asking a question or seeking help              |
| **General**                      | General conversation, no specific category fits        |
| **Show and Tell**                | User is sharing something they built/created           |
| **Announcements**                | Official announcements (rarely used by external users) |
| **Polls**                        | User wants community input via voting                  |

If no obvious match, default to **General** or **Ideas** depending on context.

### Category Inference Keywords

Use these heuristics to select the best category:

| Keywords in Description                                   | Likely Category |
| --------------------------------------------------------- | --------------- |
| "idea", "proposal", "suggest", "would be nice", "feature" | Ideas           |
| "how do I", "help", "question", "why does", "what is"     | Q&A             |
| "built", "made", "created", "sharing", "check out"        | Show and Tell   |
| "vote", "poll", "which", "prefer"                         | Polls           |
| General conversation, feedback, meta-discussion           | General         |

## Check for Discussion Templates

Check if the repository has discussion category forms:

```bash
gh api repos/{owner}/{repo}/contents/.github/DISCUSSION_TEMPLATE --jq '.[].name | select(endswith(".yml") or endswith(".yaml"))' 2>/dev/null
```

### If Templates Found

1. **Select template**: Find template matching the selected category's slug (e.g., `ideas.yml` for the Ideas category)

2. **Fetch and parse template**:

   ```bash
   gh api repos/{owner}/{repo}/contents/.github/DISCUSSION_TEMPLATE/{template_name} --jq '.content' | base64 -d
   ```

3. **Parse YAML structure** to extract:

   - `title` - default discussion title prefix
   - `body` array - form fields with `type`, `id`, `attributes`

4. **Process each field** in `body` array:

   - `markdown`: Skip (display-only, not submitted)
   - `textarea`/`input`: Use `attributes.label` as section header, `attributes.description` as guidance
   - `dropdown`: Select appropriate option based on description context
   - `checkboxes`: Auto-acknowledge as "Confirmed" (preflight attestations)

### If No Templates Found

Use default structure (see next section)

## Generate Title and Body

**Tone**: Write the discussion body in an informal, casual style. Be direct and conversational.

### Title Generation

- If YAML template has `title` field, prepend it to the generated title
- Otherwise, create a clear, concise summary (5-10 words)

### Body Generation with Template

Generate markdown sections matching the template's `body` array fields:

```markdown
### {field.attributes.label}

{Generated content based on description and field.attributes.description}
```

### Body Generation without Template

Use this default template:

```markdown
## Context

[Extracted from user description - what is this discussion about?]

## Discussion Points

[Key points or questions to discuss]

## Additional Context

[Any relevant background information, if applicable]
```

### GitHub Admonitions

Add GitHub-style admonitions when appropriate:

- `> [!NOTE]` - For context or background information
- `> [!TIP]` - For suggestions or related ideas
- `> [!IMPORTANT]` - For key points that shouldn't be missed

## Create the Discussion

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

## Examples

```bash
# Simple discussion in current repository
"Proposal for adding dark mode support"

# Explicit repository
PaulRBerg/dotfiles "Ideas for improving the zsh setup"

# Another repository
vercel/next.js "Question about server components caching"

# With --check flag (searches for similar discussions first)
--check "How to configure custom routes"

# Explicit repository with --check
facebook/react --check "Proposal for new hook API"
```
