Run project-specific linters on modified files by dynamically parsing lint-staged configuration.

This command:
1. Reads `.lintstagedrc.js`, `.lintstagedrc.json`, or `lint-staged` field in `package.json`
2. Detects modified files using `git diff`
3. Matches file patterns to linting commands
4. Executes appropriate linters on relevant files
5. Reports results to Claude

This eliminates the need to hardcode linting commands in CLAUDE.md - the command adapts to each repository's specific linting setup.
