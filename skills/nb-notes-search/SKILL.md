---
name: nb-notes-search
description: Search and retrieve notes, bookmarks, and knowledge from nb CLI tool. Use when searching notes, finding chat logs, recalling conversations, or querying personal knowledge base. Supports natural language queries like "in which chat did I say X?" or "show me notes about Y".
---

# nb Notes Search Skill

## Purpose

This skill helps translate natural language queries into nb commands to search and retrieve notes, bookmarks, chats, and knowledge base content.

**nb** is a command-line note-taking, bookmarking, and knowledge base application that stores everything as plain text in a Git-backed system.

## When to Use This Skill

Activate when the user:
- Asks to find or search notes
- Wants to recall conversations or chat logs
- Queries "what did I say about X?" or "in which chat did I say Y?"
- Wants to list bookmarks, todos, or notes by criteria
- Mentions searching their knowledge base or notes

## Key nb Commands

### Search Content

```bash
# Basic search across current notebook
nb search "keyword"
nb q "keyword"  # shorthand

# Search all notebooks
nb search "keyword" --all

# Search with tags
nb search "keyword" --tag tag1,tag2

# Search by type
nb search "keyword" --type bookmark
nb search "keyword" --type note

# Boolean search
nb search "term1" --and "term2"
nb search "term1" --or "term2"
nb search "term1" --not "excluded"

# List filenames only (no excerpts)
nb search "keyword" --list
```

### List Items

```bash
# List with excerpts
nb list --excerpt

# List by type
nb list --type bookmark
nb list --type note

# List with tags
nb list --tags

# List specific notebook
nb claude:list
nb home:list
```

### Show Notes

```bash
# Show by ID
nb show 123

# Show by filename
nb show example.md

# Show by title (with quotes)
nb show "My Note Title"

# Show from specific notebook
nb claude:show 42
nb home:42  # shorthand
```

### Bookmarks & Todos

```bash
# Search bookmarks
nb bookmark search "topic"
nb search "topic" --type bookmark

# List todos
nb todos
nb tasks
nb tasks open  # open tasks only
```

### Notebooks

```bash
# List all notebooks
nb notebooks

# Switch notebook
nb use notebook_name

# Notebook-specific command
nb notebook_name:search "query"
```

## Common Query Patterns

### "In which chat did I say X?"

This is searching for past conversations or chat logs:

```bash
# Search all notebooks for the content
nb search "X" --all

# If you know it's in the claude notebook
nb claude:search "X"

# If tagged as chat
nb search "X" --tag chat

# Get just filenames to browse
nb search "X" --list --all
```

### "Show me all notes about Y"

```bash
# Search and list
nb search "Y" --list

# If using tags
nb list --tag Y

# Search all notebooks
nb search "Y" --all
```

### "What bookmarks do I have about Z?"

```bash
# Search bookmarks specifically
nb bookmark search "Z"

# Or filter by type
nb search "Z" --type bookmark

# List all bookmarks with tag
nb list --type bookmark --tag Z
```

### "Show my todos" or "What tasks do I have?"

```bash
# Show all todos
nb todos

# Show open tasks only
nb tasks open

# Show todos in specific notebook
nb claude:todos
```

### "Find notes from recent conversations"

```bash
# Search recent items
nb search "keyword" --limit 10

# List recent notes
nb list --limit 10 --reverse

# Browse recent items
nb browse
```

## Translation Strategy

When translating natural language to nb commands:

1. **Identify the intent**:
   - Search/find → `nb search`
   - List/show all → `nb list`
   - Specific note → `nb show`
   - Recall/remember → `nb search --all`

2. **Extract keywords**: Pull out the main search terms from the query

3. **Determine scope**:
   - "In which chat" → likely needs `--all` to search everywhere
   - "my bookmarks" → add `--type bookmark`
   - "about X" → tag or keyword search

4. **Add filters**:
   - Type: `--type bookmark|note|todo`
   - Tags: `--tag tagname`
   - Notebook: `notebook_name:search` or `--all`

5. **Choose output format**:
   - Want excerpts? → default `nb search`
   - Just filenames? → add `--list`
   - Full content? → use `nb show` after finding

## Tips for Effective Searches

- Use `--all` to search across all notebooks when location is uncertain
- Use `--list` for compact output when you have many results
- Tags are powerful for organization: filter with `--tag`
- Regex patterns work in search: `nb search "pattern.*"`
- Check available notebooks: `nb notebooks`
- Use `nb q` as shorthand for `nb search`
- Combine boolean operators: `--and`, `--or`, `--not`
- Browse interactively: `nb browse` opens web interface

## Example Workflows

### Finding a Past Conversation

```bash
# Step 1: Search for keywords
nb search "specific topic" --all

# Step 2: If too many results, narrow down
nb search "specific topic" --tag chat --list

# Step 3: Open the specific note
nb show claude:123
```

### Recalling What You Said About Something

```bash
# Search your notes
nb search "something" --all

# Or if you know the notebook
nb claude:search "something"
```

### Organizing Related Notes

```bash
# List all notes with a tag
nb list --tag project-name

# Search within tagged notes
nb search "detail" --tag project-name
```

## Important Notes

- All content is stored as plain text files in `~/.nb/`
- Each notebook is Git-backed for version control
- Search is powered by `git grep` (fast and powerful)
- Tags use `#hashtag` syntax in notes
- Links use `[[wiki-style]]` syntax
- Use `nb help <command>` for detailed command help
