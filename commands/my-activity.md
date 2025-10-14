---
argument-hint: [period] [--format=json|text] [--transcripts]
description: Summarize your GitHub and Claude Code activity over a time period
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
- **Transcripts flag**: `--transcripts` to include Claude Code session analysis (default: false)

Examples:
- `/my-activity` → last 7 days, text format, GitHub only
- `/my-activity month` → last 30 days
- `/my-activity 14` → last 14 days
- `/my-activity week --format=json` → last 7 days as JSON
- `/my-activity --transcripts` → last 7 days with Claude Code session analysis
- `/my-activity month --transcripts --format=json` → last 30 days, all data as JSON

Convert period to days:
- "day" or "1" → 1
- "week" or "7" → 7
- "month" or "30" → 30
- numeric value → that number of days
- unrecognized → default to 7

**Validation**: IF the period exceeds 30 days, ERROR "Period cannot exceed 30 days (1 month). The GitHub Events API only provides data for the last 30 days."

### STEP 3: Analyze Claude Code transcripts (if --transcripts flag present)

IF `--transcripts` flag is NOT present, SKIP this step entirely and proceed to STEP 4.

OTHERWISE:

Analyze Claude Code session transcripts from `~/.claude/projects/` for the specified time period.

**Location**: Transcripts are stored as JSONL files at `~/.claude/projects/{project-dir}/{session-uuid}.jsonl`

**Strategy**: Use metadata + summaries approach (avoid loading full transcripts to conserve context):

```bash
# Find all transcript files modified in the time period
since_date=$(gdate -d "$DAYS days ago" +%s 2>/dev/null || date -v-${DAYS}d +%s)
fd -t f -e jsonl . ~/.claude/projects/ -x stat -f "%m %N" {} \; | \
  awk -v since="$since_date" '$1 >= since {print $2}'
```

For each relevant transcript file:
1. **Extract metadata** (first line only - fast):
   - Session ID, timestamp, project/cwd, git branch
   - Count lines in file (= message count)

2. **Extract summary** (if exists):
   - Parse JSONL for `type: "summary"` records
   - These contain AI-generated session summaries

3. **Count tool usage** (optional, lightweight):
   - Count lines matching `"type":"tool_use"` for tool usage patterns
   - Extract tool names from `"name"` field

**Aggregate data**:
- Total sessions in period
- Sessions per project/directory
- Total messages exchanged
- Most active days
- Most used tools
- Session summaries (group by project)
- Average session length (messages per session)

**IMPORTANT**: DO NOT read full transcript content or tool results. Only extract:
- Metadata from first/specific lines
- Summaries from `type: "summary"` records
- Line counts and tool names

This keeps context usage minimal while providing meaningful insights.

### STEP 4: Fetch GitHub activity

Calculate the date range (ISO 8601 format):
```bash
since_date=$(gdate -d "$DAYS days ago" -Iseconds 2>/dev/null || date -v-${DAYS}d -Iseconds)
```

Fetch events using GitHub CLI:
```bash
gh api "users/$(gh api user -q .login)/events?per_page=100" --paginate
```

**Note**: The API returns up to 300 recent events and only covers the last 30 days (as of Jan 2025).

### STEP 5: Aggregate and analyze GitHub events

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

### STEP 6: Generate summary

IF `--format=json`:
- Output structured JSON with:
  - `period_days`: number
  - `date_range`: {from, to}
  - `github`: {
      - `total_events`: number
      - `events_by_type`: {type: count}
      - `repositories`: [list of repos with activity]
      - `summary_stats`: {commits, prs, issues, reviews, etc.}
    }
  - `claude_code`: (if --transcripts) {
      - `total_sessions`: number
      - `total_messages`: number
      - `sessions_by_project`: {project: count}
      - `top_tools`: [list of most used tools]
      - `session_summaries`: [list of session summaries with timestamps]
    }

OTHERWISE (text format):
- Generate a readable summary:

```
Activity Summary (Last N days)
==============================

📊 GitHub Activity
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

IF `--transcripts` flag was present, ADD this section to text output:

```
🤖 Claude Code Activity
- Total sessions: X
- Total messages exchanged: Y
- Average messages per session: Z
- Projects worked on: A

💬 Recent Sessions
[For each session, show: timestamp, project, summary (if available)]

🔧 Top Tools Used
1. tool-name (X uses)
2. tool-name (Y uses)
3. tool-name (Z uses)

📁 Most Active Projects
1. project-name (X sessions)
2. project-name (Y sessions)
3. project-name (Z sessions)
```

### STEP 7: Optional AI enhancement

IF the activity is substantial (>20 GitHub events OR >10 Claude Code sessions):
- Provide a brief narrative insight combining both data sources:
  - "You've been focusing heavily on repository X this week"
  - "High PR review activity - you reviewed N pull requests"
  - "Busy week with X commits across Y repositories"
  - "Heavy Claude Code usage on project Z with X sessions"
  - "Most productive coding day was [date] with X GitHub events and Y Claude sessions"

## Error Handling

IF API returns no events:
- "No public GitHub activity found in the last N days"
- Note: Private repository activity may not be visible via this API

IF API rate limit exceeded:
- Show clear error with rate limit reset time
- Suggest: `gh api rate_limit` to check status

## Notes

**GitHub Activity:**
- Uses GitHub Events API (limited to last 30 days, max 300 events)
- Only public activity is returned by default
- Commit counts come from PushEvent payload
- Times are in UTC
- For more detailed analytics, consider GitHub's native insights/contribution graph

**Claude Code Transcripts (--transcripts flag):**
- Transcripts stored at `~/.claude/projects/{project-dir}/{session-uuid}.jsonl`
- Uses lightweight metadata extraction to avoid context window issues
- Does NOT read full conversation content, only:
  - Session metadata (timestamps, projects, message counts)
  - Session summaries (pre-generated by Claude Code)
  - Tool usage patterns
- A typical setup has 384MB of transcripts (953 files)
- Individual transcripts range from 19KB to 57MB
- The analysis strategy keeps context usage under 50KB regardless of transcript size
