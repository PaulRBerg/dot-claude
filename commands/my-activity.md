---
argument-hint: [period] [--format=json|text]
description: Summarize your GitHub activity over a time period
---

## Context

- GitHub CLI auth: !`gh auth status 2>&1 | rg -q "Logged in" && echo "authenticated" || echo "not authenticated"`
- Current user: !`gh api user --jq '.login' 2>/dev/null || echo "unknown"`
- Arguments: $ARGUMENTS

## Your Task

### STEP 1: Validate prerequisites

IF not authenticated: ERROR "Run `gh auth login` first"

### STEP 2: Parse arguments

Parse $ARGUMENTS for:
- **Time period**: Default is "week" (7 days). Other options: "day", "month", "30", "14", etc.
- **Format flag**: `--format=json` or `--format=text` (default: text)

Examples:
- `/my-activity` → last 7 days, text format
- `/my-activity month` → last 30 days
- `/my-activity 14` → last 14 days
- `/my-activity week --format=json` → last 7 days as JSON

Convert period to days:
- "day" or "1" → 1
- "week" or "7" → 7
- "month" or "30" → 30
- numeric value → that number of days
- unrecognized → default to 7

### STEP 3: Fetch GitHub activity

Calculate the date range (ISO 8601 format):
```bash
since_date=$(gdate -d "$DAYS days ago" -Iseconds 2>/dev/null || date -v-${DAYS}d -Iseconds)
```

Fetch events using GitHub CLI:
```bash
gh api "users/$(gh api user -q .login)/events?per_page=100" --paginate
```

**Note**: The API returns up to 300 recent events and only covers the last 30 days (as of Jan 2025).

### STEP 4: Aggregate and analyze events

Filter events within the date range and categorize by type:

**Event types to track:**
- `PushEvent` → Commits pushed
- `PullRequestEvent` → PRs opened/closed/merged
- `PullRequestReviewEvent` → PR reviews submitted
- `IssuesEvent` → Issues opened/closed
- `IssueCommentEvent` → Comments on issues
- `CreateEvent` → Repos/branches/tags created
- `DeleteEvent` → Branches/tags deleted
- `ForkEvent` → Repos forked
- `WatchEvent` → Repos starred
- `ReleaseEvent` → Releases published

For each event type, extract:
- Count of events
- Repositories involved
- Key actions (opened, closed, merged, etc.)
- Commit counts (for PushEvents, sum commits)

### STEP 5: Generate summary

IF `--format=json`:
- Output structured JSON with:
  - `period_days`: number
  - `date_range`: {from, to}
  - `total_events`: number
  - `events_by_type`: {type: count}
  - `repositories`: [list of repos with activity]
  - `summary_stats`: {commits, prs, issues, reviews, etc.}

OTHERWISE (text format):
- Generate a readable summary:

```
GitHub Activity Summary (Last N days)
=====================================

📊 Overview
- Total activity events: X
- Repositories active in: Y
- Most active repo: repo-name (Z events)

💻 Code Contributions
- Commits pushed: X (across Y repos)
- Pull requests: A opened, B merged, C closed
- Code reviews: X reviews on Y PRs

🐛 Issues & Discussions
- Issues: A opened, B closed
- Issue comments: X
- Discussions participated: Y

🔧 Repository Activity
- Repos created: X
- Repos forked: Y
- Stars given: Z
- Branches created: A
- Releases published: B

📈 Top Repositories
1. repo-name (X events)
2. repo-name (Y events)
3. repo-name (Z events)
```

### STEP 6: Optional AI enhancement

IF the activity is substantial (>20 events):
- Provide a brief narrative insight:
  - "You've been focusing heavily on repository X this week"
  - "High PR review activity - you reviewed N pull requests"
  - "Busy week with X commits across Y repositories"

## Error Handling

IF API returns no events:
- "No public GitHub activity found in the last N days"
- Note: Private repository activity may not be visible via this API

IF API rate limit exceeded:
- Show clear error with rate limit reset time
- Suggest: `gh api rate_limit` to check status

## Notes

- Uses GitHub Events API (limited to last 30 days, max 300 events)
- Only public activity is returned by default
- Commit counts come from PushEvent payload
- Times are in UTC
- For more detailed analytics, consider GitHub's native insights/contribution graph
