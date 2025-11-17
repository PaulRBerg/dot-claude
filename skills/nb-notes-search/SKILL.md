---
name: nb-cli
description: Comprehensive nb CLI tool support for note-taking, bookmarking, and knowledge management. Use for creating, editing, searching, browsing, and organizing notes. Supports operations like "create a note", "search for X", "open in browser", "add bookmark", and natural language queries.
---

# nb CLI Skill

## Purpose

This skill provides comprehensive support for the nb command-line tool, enabling note creation, editing, searching, browsing, bookmarking, and knowledge base management.

**nb** is a command-line note-taking, bookmarking, and knowledge base application that stores everything as plain text in a Git-backed system.

## When to Use This Skill

Activate when the user:
- Creates, edits, or deletes notes
- Searches, finds, or recalls notes and conversations
- Opens notes in browser or web interface
- Adds or manages bookmarks
- Lists, organizes, or browses notes by criteria
- Queries their knowledge base ("what did I say about X?", "show notes about Y")
- Manages todos or tasks in nb

## Basic Operations

### Create Notes

```bash
# Create note with editor
nb add
nb a  # shorthand

# Create note with title
nb add "Note Title"

# Create with content from stdin
echo "Content" | nb add

# Create in specific notebook
nb notebook_name:add "Title"

# Add quick note
nb add --title "Title" --content "Content here"
```

### Edit Notes

```bash
# Edit by ID
nb edit 123
nb e 123  # shorthand

# Edit by title
nb edit "Note Title"

# Edit in specific notebook
nb notebook:123
nb notebook:edit "Title"
```

### Show/View Notes

```bash
# Show by ID
nb show 123
nb s 123  # shorthand

# Show by title
nb show "Note Title"

# Show with pager
nb show 123 --print

# Show from specific notebook
nb notebook:show 123
nb notebook:123  # shorthand
```

### Delete Notes

```bash
# Delete by ID (prompts for confirmation)
nb delete 123
nb d 123  # shorthand

# Delete by title
nb delete "Note Title"

# Force delete without confirmation
nb delete 123 --force
```

## Browser Interface

nb includes a powerful web interface for browsing and managing notes:

```bash
# Open interactive web UI
nb browse
nb b  # shorthand

# Browse specific note in web UI
nb browse 123

# Browse specific notebook
nb browse notebook_name:

# Browse and search
nb browse --query "search term"

# Open note in external browser
nb open 123

# Peek at note in terminal browser
nb peek 123
```

The browser interface provides:
- Visual note browsing and navigation
- Full-text search
- Tag and notebook filtering
- Note editing in browser
- Markdown rendering

## Search & Discovery

### Search

```bash
# Basic search
nb search "keyword"
nb q "keyword"  # shorthand

# Search all notebooks
nb search "keyword" --all

# Boolean operators
nb search "term1" --and "term2"
nb search "term1" --or "term2"
nb search "term1" --not "excluded"

# Filter by type or tags
nb search "keyword" --type bookmark
nb search "keyword" --tag tag1,tag2

# List filenames only
nb search "keyword" --list
```

### List

```bash
# List notes with excerpts
nb list --excerpt

# Filter by type or tags
nb list --type bookmark
nb list --tag project-name
nb list --tags  # show all tags

# List from specific notebook
nb notebook:list
```

## Bookmarks

### Add Bookmarks

```bash
# Add bookmark by URL
nb <url>
nb https://example.com

# Add bookmark with comment
nb <url> --comment "Description here"

# Add with tags
nb <url> --tags tag1,tag2

# Add to specific notebook
nb notebook:<url>
```

### Search Bookmarks

```bash
# Search bookmarks
nb bookmark search "topic"
nb search "topic" --type bookmark

# List all bookmarks
nb list --type bookmark
```

## Todos & Tasks

```bash
# List todos
nb todos
nb tasks

# List open tasks only
nb tasks open

# Add todo
nb todo add "Task description"

# Mark todo done
nb todo do 123
```

## Notebooks

```bash
# List all notebooks
nb notebooks

# Switch notebook
nb use notebook_name

# Notebook-specific commands
nb notebook_name:search "query"
nb notebook_name:add "Note"
```

## Common Patterns

### Finding Past Conversations

```bash
# Search everywhere: "In which chat did I say X?"
nb search "X" --all

# Narrow by notebook or tag
nb claude:search "X"
nb search "X" --tag chat --list
```

### Listing by Topic or Type

```bash
# "Show me notes about Y"
nb search "Y" --list
nb list --tag Y

# "What bookmarks about Z?"
nb search "Z" --type bookmark
```

### Working with Recent Items

```bash
# Recent notes
nb list --limit 10 --reverse

# Search with limit
nb search "keyword" --limit 10
```

## Usage Tips

**Translation strategy:**
- Search/find → `nb search` (use `--all` for everywhere)
- Create/add → `nb add` (URL for bookmarks)
- View/show → `nb show` or `nb browse`
- Edit → `nb edit`
- Filter by type → `--type bookmark|note|todo`
- Filter by tag → `--tag tagname`

**Power features:**
- Boolean search: `--and`, `--or`, `--not`
- Regex patterns: `nb search "pattern.*"`
- Web UI: `nb browse` (interactive browsing)
- Shortcuts: `nb q` (search), `nb a` (add), `nb e` (edit)
- Content stored in `~/.nb/` as plain text, Git-backed
- Tags use `#hashtag`, links use `[[wiki-style]]`
