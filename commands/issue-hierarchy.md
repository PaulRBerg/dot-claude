---
argument-hint: <issue-url>
description: Display GitHub issue hierarchy with sub-issues
---

## Context

- GitHub CLI auth: !`gh auth status 2>&1 | rg -q "Logged in" && echo "authenticated" || echo "not authenticated"`
- Issue reference: $ARGUMENTS

## Your Task

### STEP 1: Validate prerequisites

CHECK GitHub authentication:
- IF Context shows "not authenticated": ERROR and exit with: "❌ Not authenticated. Run `gh auth login` first"

CHECK issue reference provided:
- IF $ARGUMENTS is empty: ERROR and exit with: "❌ Usage: /issue-hierarchy <issue-url>"

### STEP 2: Parse issue reference

PARSE the issue reference from $ARGUMENTS:

Supported formats:
- Full URL: `https://github.com/owner/repo/issues/123`
- Org/repo format: `owner/repo#123`
- Just number: `#123` (uses current repo if in git directory)

EXTRACT owner, repo, and issue number:
```bash
# Example parsing logic:
# - If contains "github.com/", extract from URL
# - If contains "/", split on "/" and "#"
# - If starts with "#", use git remote to get owner/repo
```

VALIDATE extracted values are not empty

### STEP 3: Get issue ID

FETCH the issue ID using gh CLI:
```bash
gh issue view "https://github.com/$owner/$repo/issues/$number" --json id --jq '.id'
```

IF command fails:
- Check error message for specific issue (not found, no access, etc.)
- ERROR with clear message and exit

STORE the issue ID for GraphQL queries

### STEP 4: Query root issue and check for sub-issues

EXECUTE GraphQL query to get issue details and sub-issue summary:
```bash
gh api graphql \
  -H "GraphQL-Features: sub_issues" \
  -f query='
    query($id: ID!) {
      node(id: $id) {
        ... on Issue {
          number
          title
          url
          subIssuesSummary {
            total
            completed
          }
        }
      }
    }
  ' \
  -f id="$issue_id"
```

PARSE the response with jq:
```bash
# Extract total sub-issues count
total=$(echo "$response" | jq -r '.data.node.subIssuesSummary.total')
```

IF total == 0 or null:
- DISPLAY: "ℹ️  Issue #$number has no sub-issues"
- EXIT successfully (this is not an error)

IF total > 0:
- DISPLAY: "📊 Found issue hierarchy with $total sub-issue(s)"
- PROCEED to STEP 5

### STEP 5: Recursively fetch complete hierarchy

BUILD the complete issue tree by recursively fetching sub-issues:

DEFINE GraphQL query for fetching issue with children:
```graphql
query($id: ID!) {
  node(id: $id) {
    ... on Issue {
      id
      number
      title
      url
      subIssuesSummary {
        total
      }
      subIssues(first: 100) {
        nodes {
          id
          number
          title
          url
        }
      }
    }
  }
}
```

IMPLEMENT breadth-first traversal:
1. Create queue with root issue ID
2. While queue not empty:
   - Dequeue issue ID
   - Query for issue details and sub-issues
   - Store issue data in tree structure
   - Enqueue all sub-issue IDs
3. Continue until all issues fetched

STORE results in a structured format (e.g., JSON) for rendering

### STEP 6: Render ASCII tree diagram

GENERATE ASCII tree visualization:

Use tree characters:
- `├──` for non-last child
- `└──` for last child
- `│   ` for continuation line
- `    ` for empty space

EXAMPLE output format:
```
Issue #123: Implement user authentication
├── Issue #124: Design authentication flow (✓)
│   ├── Issue #126: Create login page
│   └── Issue #127: Add OAuth providers
├── Issue #125: Backend API endpoints
│   ├── Issue #128: JWT token generation (✓)
│   └── Issue #129: Session management
└── Issue #130: Security testing
```

INCLUDE in each line:
- Issue number
- Issue title (truncate if > 80 chars)
- Completion indicator (✓) if closed

### STEP 7: Display the hierarchy

PRINT the complete tree diagram to the terminal

ADD summary footer:
```
─────────────────────────────────────────
Total issues: X | Completed: Y | Progress: Z%
```

## Error Handling

IF GraphQL query fails:
- Parse error message
- Common errors:
  - Rate limit exceeded → suggest waiting
  - Resource not accessible → check permissions
  - Feature not available → might need opt-in for sub-issues beta
- Display clear error message

IF issue has > 100 sub-issues at any level:
- WARN: "⚠️  Some sub-issues may be truncated (max 100 per level)"
- Still render what was fetched

## Implementation Notes

- Use `jq` for all JSON parsing
- Handle closed issues by checking `state` field
- Preserve tree structure even with deep nesting (up to 8 levels)
- Keep API calls efficient by batching where possible
- Use bash arrays/associative arrays for tree structure
- Process recursively but with depth limit (8 levels per GitHub constraints)

## Example Usage

```bash
# Full URL
/issue-hierarchy https://github.com/microsoft/vscode/issues/12345

# Short form
/issue-hierarchy microsoft/vscode#12345

# Current repo (if in git directory)
/issue-hierarchy #123
```
