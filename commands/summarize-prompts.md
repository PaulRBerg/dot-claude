---
argument-hint: [START_DATE=<YYYY-MM-DD>] [END_DATE=<YYYY-MM-DD>]
description: Generate summaries for recent zk daily notes
---

## Context

- Today's date: !`gdate +%Y-%m-%d 2>/dev/null || date +%Y-%m-%d`
- zk notebook location: `~/.claude-prompts/`
- Arguments: $ARGUMENTS

## Your Task

### STEP 1: Parse date arguments

Parse $ARGUMENTS to extract dates:

IF $ARGUMENTS is empty:
- Calculate yesterday's date:
  ```bash
  gdate -d "yesterday" +%Y-%m-%d 2>/dev/null || date -v-1d +%Y-%m-%d
  ```
- Set TARGET_DATES to single-element array: [yesterday]

ELSE IF $ARGUMENTS contains two dates matching `YYYY-MM-DD YYYY-MM-DD`:
- Extract START_DATE and END_DATE
- Validate both dates are valid format
- Generate all dates in range (inclusive):
  ```bash
  # Using GNU date (gdate on macOS)
  current="$START_DATE"
  while [[ "$current" <= "$END_DATE" ]]; do
    dates+=("$current")
    current=$(gdate -d "$current + 1 day" +%Y-%m-%d 2>/dev/null || date -j -v+1d -f "%Y-%m-%d" "$current" +%Y-%m-%d)
  done
  ```
- Set TARGET_DATES to array of all dates in range

ELSE IF $ARGUMENTS matches single `YYYY-MM-DD` pattern:
- Set TARGET_DATES to single-element array: [$ARGUMENTS]

ELSE:
- ERROR "Invalid date format. Use: YYYY-MM-DD [YYYY-MM-DD] or leave empty for yesterday"

### STEP 2: Discover matching note files

FOR EACH date in TARGET_DATES:

FIND all note files matching date pattern:
```bash
fd -t f -e md "^${date}\.md$" ~/.claude-prompts/
```

- Add matching files to processing list
- Track which date each file corresponds to

AFTER processing all dates:

IF no files found for any date:
- Display "No notes found for specified date(s)"
- EXIT

ELSE:
- Display "Found N note(s) across M date(s)"

### STEP 3: Process each note file

FOR EACH matching file:

**Check for existing summary:**
- Read the file
- IF file starts with `## Summary` (check first 50 characters):
  - SKIP this file
  - Log "Skipping ${file} - summary already exists"
  - CONTINUE to next file

**Analyze content:**
- Extract all timestamp sections (lines starting with `##` followed by timestamps)
- Read prompts under each timestamp
- Identify 2-3 high-level themes across all prompts
- What topics were discussed?
- What was the user trying to accomplish?
- Any recurring patterns or focus areas?

**Generate summary:**
- Write 2-3 concise sentences capturing the day's themes
- Focus on "what" not "when"
- Use past tense
- Be specific but high-level

Example good summary:
```
Configured amp CLI settings, migrating from Claude Code. Explored MCP server setup and tool permissions. Reviewed modern CLI documentation for accuracy.
```

Example bad summary:
```
The user asked several questions about CLI tools and configuration files.
```

**Prepend summary:**
- Create new content: `## Summary\n\n${generated_summary}\n\n${original_content}`
- Write back to file
- Log "✓ Added summary to ${file}"

### STEP 4: Display results

Show summary of operations:
```
Processed notes for ${date_range_or_date}:
- ${updated_count} file(s) updated
- ${skipped_count} file(s) skipped (already had summaries)
```

## Examples

**Default usage (yesterday's notes):**
```
> /summarize-prompts

Found 3 note(s) across 1 date(s)
✓ Added summary to ~/.claude-prompts/claude/2025-11-16.md
Skipping ~/.claude-prompts/local-share-chezmoi/2025-11-16.md - summary already exists
✓ Added summary to ~/.claude-prompts/pad-biome/2025-11-16.md

Processed notes for 2025-11-16:
- 2 file(s) updated
- 1 file(s) skipped (already had summaries)
```

**Specific date:**
```
> /summarize-prompts 2025-11-15

Found 1 note(s) across 1 date(s)
✓ Added summary to ~/.claude-prompts/pad-biome/2025-11-15.md

Processed notes for 2025-11-15:
- 1 file(s) updated
- 0 file(s) skipped (already had summaries)
```

**Date range:**
```
> /summarize-prompts 2025-11-10 2025-11-12

Found 5 note(s) across 3 date(s)
✓ Added summary to ~/.claude-prompts/claude/2025-11-10.md
✓ Added summary to ~/.claude-prompts/claude/2025-11-11.md
✓ Added summary to ~/.claude-prompts/claude/2025-11-12.md
Skipping ~/.claude-prompts/local-share-chezmoi/2025-11-11.md - summary already exists
✓ Added summary to ~/.claude-prompts/pad-biome/2025-11-10.md

Processed notes for 2025-11-10 to 2025-11-12:
- 4 file(s) updated
- 1 file(s) skipped (already had summaries)
```

**No notes found:**
```
> /summarize-prompts 2025-10-01

No notes found for specified date(s)
```

## Notes

**Date handling:**
- Uses `gdate` (GNU date) if available, falls back to macOS `date -v` and `date -j`
- Default behavior: process yesterday's notes (assumes you run this daily)
- Single date: `/summarize-prompts 2025-11-15` processes one specific date
- Date range: `/summarize-prompts 2025-11-10 2025-11-12` processes all dates inclusive
- Range generation handles date arithmetic correctly across month boundaries

**File discovery:**
- Recursively searches all subdirectories in `~/.claude-prompts/`
- Matches exact filename pattern: `YYYY-MM-DD.md`
- Each project subdirectory may have its own daily note file

**Summary generation:**
- Idempotent: won't add duplicate summaries
- Analyzes actual prompt content, not just metadata
- Focuses on themes and accomplishments, not individual timestamps
- Uses past tense (prompts are historical)

**Integration with zk:**
- Compatible with zk note-taking workflow
- Preserves all existing note structure
- Summary section appears before timestamp sections
- Can be used standalone or as part of daily review routine
