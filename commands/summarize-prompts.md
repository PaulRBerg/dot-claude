---
argument-hint: [start-date] [end-date]
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
- Extract start-date and end-date
- Validate both dates are valid format
- Generate all dates in range (inclusive):
  ```bash
  # Using GNU date (gdate on macOS)
  current="$START_DATE"
  while [[ "$current" < "$END_DATE" || "$current" == "$END_DATE" ]]; do
    dates+=("$current")
    current=$(gdate -d "$current + 1 day" +%Y-%m-%d 2>/dev/null || date -j -v+1d -f "%Y-%m-%d" "$current" +%Y-%m-%d)
  done
  ```
- Set TARGET_DATES to array of all dates in range

ELSE IF $ARGUMENTS matches single `YYYY-MM-DD` pattern:
- Set TARGET_DATES to single-element array: [$ARGUMENTS]

ELSE:
- ERROR "Invalid date format. Use: YYYY-MM-DD [YYYY-MM-DD] or leave empty for yesterday"

### STEP 2: Parallelization decision

Calculate `total_dates = length(TARGET_DATES)`

IF `total_dates == 1`:
- Proceed with SEQUENTIAL PROCESSING (skip to STEP 3)
- No agent spawning needed

ELSE IF `total_dates > 1`:
- Proceed with PARALLEL PROCESSING using Task tool
- Calculate batch distribution:
  ```
  max_agents = 10
  agent_count = min(total_dates, max_agents)
  dates_per_agent = ceil(total_dates / agent_count)
  ```
- Create batches by splitting TARGET_DATES into `agent_count` groups
- Each batch should have approximately `dates_per_agent` dates
- Example distributions:
  - 5 dates → 5 agents (1 date each)
  - 15 dates → 5 agents (3 dates each)
  - 25 dates → 10 agents (2-3 dates each)
  - 100 dates → 10 agents (10 dates each)

**Spawn agents in parallel:**
- Use a SINGLE message with MULTIPLE Task tool calls
- Each Task agent receives:
  - Subagent type: "general-purpose"
  - Prompt: Full processing instructions (see STEP 3) + assigned date batch
  - Expected return: JSON with `{updated_count, skipped_count, processed_files[]}`

Example Task prompt structure:
```
Process daily note summaries for dates: [2025-11-10, 2025-11-11, 2025-11-12]

For each date:
1. Find note files: fd -t f -e md "^${date}\.md$" ~/.claude-prompts/
2. For each file: [full processing logic from STEP 3]
3. Track statistics

Return JSON: {"updated": N, "skipped": M, "files": ["path1", "path2"]}
```

- Proceed to STEP 4 for result aggregation

### STEP 3: Processing logic (sequential OR per-agent)

**NOTE:** This step describes the core processing logic used either:
- Directly by main command (if total_dates == 1)
- By each spawned Task agent (if total_dates > 1)

#### 3A. Discover matching note files

FOR EACH date in assigned dates:

FIND all note files matching date pattern:
```bash
fd -t f -e md "^${date}\.md$" ~/.claude-prompts/
```

- Add matching files to processing list
- Track which date each file corresponds to

AFTER processing all dates:

IF no files found for any date:
- IF sequential: Display "No notes found for specified date(s)" and EXIT
- IF agent: Return `{"updated": 0, "skipped": 0, "files": []}`

ELSE:
- Continue to file processing

#### 3B. Process each note file

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

#### 3C. Return results

IF running as agent (parallel mode):
- Return JSON object:
  ```json
  {
    "updated": <count of files updated>,
    "skipped": <count of files skipped>,
    "files": ["path/to/file1.md", "path/to/file2.md"]
  }
  ```

IF running sequentially:
- Track `updated_count` and `skipped_count` internally
- Proceed to STEP 5

### STEP 4: Aggregate results (parallel mode only)

**NOTE:** This step only applies when agents were spawned (total_dates > 1)

AFTER all Task agents complete:
- Collect JSON responses from each agent
- Calculate totals:
  ```
  total_updated = sum(agent.updated for all agents)
  total_skipped = sum(agent.skipped for all agents)
  all_files = concatenate(agent.files for all agents)
  ```
- Determine date range string:
  - IF TARGET_DATES spans multiple dates: "${first_date} to ${last_date}"
  - ELSE: "${single_date}"
- Proceed to STEP 5 with aggregated values

### STEP 5: Display results

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

**Date range (parallel processing):**
```
> /summarize-prompts 2025-11-10 2025-11-12

Spawning 3 agents to process 3 dates in parallel...

[Agent 1] Processing 2025-11-10...
[Agent 2] Processing 2025-11-11...
[Agent 3] Processing 2025-11-12...

[Agent 1] ✓ Added summary to ~/.claude-prompts/claude/2025-11-10.md
[Agent 1] ✓ Added summary to ~/.claude-prompts/pad-biome/2025-11-10.md
[Agent 2] ✓ Added summary to ~/.claude-prompts/claude/2025-11-11.md
[Agent 2] Skipping ~/.claude-prompts/local-share-chezmoi/2025-11-11.md - summary already exists
[Agent 3] ✓ Added summary to ~/.claude-prompts/claude/2025-11-12.md

All agents completed. Aggregating results...

Processed notes for 2025-11-10 to 2025-11-12:
- 4 file(s) updated
- 1 file(s) skipped (already had summaries)
```

**Large date range (intelligent batching):**
```
> /summarize-prompts 2025-10-01 2025-10-31

Processing 31 dates with 10 agents (3-4 dates per agent)...

[Agent 1] Processing dates: 2025-10-01 to 2025-10-04
[Agent 2] Processing dates: 2025-10-05 to 2025-10-07
...
[Agent 10] Processing dates: 2025-10-29 to 2025-10-31

All agents completed. Aggregating results...

Processed notes for 2025-10-01 to 2025-10-31:
- 42 file(s) updated
- 8 file(s) skipped (already had summaries)
```

**No notes found:**
```
> /summarize-prompts 2025-10-01

No notes found for specified date(s)
```

## Notes

**Parallelization:**
- Single date or yesterday: processes sequentially (no agent overhead)
- Date range: spawns Task agents for parallel processing
- Agent count: min(date_count, 10) — never more than 10 agents
- Batch distribution: dates evenly split across agents
  - 3 dates → 3 agents (1 date each)
  - 15 dates → 5 agents (3 dates each)
  - 50 dates → 10 agents (5 dates each)
- Performance: ~3-5x faster for large date ranges (20+ days)
- All agents spawn in parallel using single message with multiple Task calls

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
