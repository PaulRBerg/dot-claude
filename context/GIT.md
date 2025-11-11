## Git

- **ABSOLUTELY NEVER** run destructive git operations (e.g., `git reset --hard`, `rm`, `git checkout`/`git restore` to
  an older commit) unless the user gives an explicit, written instruction in this conversation. Treat these commands as
  catastrophic; if you are even slightly unsure, stop and ask before touching them.
- Quote any git paths containing brackets or parentheses (e.g., `src/app/[candidate]/**`) when staging or committing so
  the shell does not treat them as globs or subshells.
- When running `git rebase`, use the `--no-edit` flag to avoid opening editors and use the default messages
  automatically.
