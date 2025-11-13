## Modern CLI

Use these modern CLI tools in shell like Bash or Zsh.

- **PREFER**: `rg`, `fd`, `bat`, `eza`, `jq`, `yq`, `fzf`, `delta`, `gh`
- **AVOID (use only if needed)**: `grep`, `find`, `cat`, `ls`, `df`, `top`, `xxd`

## IMPORTANT: Special Characters in File Paths

**THIS RULE APPLIES TO ALL CLI TOOLS AND TERMINAL COMMANDS - NOT JUST THE EXAMPLES SHOWN.**

When file paths contain special characters (like parentheses, spaces, brackets, etc.), you MUST always escape them with
backslashes (`\`) in shell commands. Failure to do so will cause commands to fail.

**Common special characters that MUST be escaped include: `(` `)` `[` `]` `{` `}` and spaces.**

### Examples (applies to ALL tools: `bat`, `rg`, `fd`, `eza`, `cat`, `grep`, `ls`, etc.):

Escaping parentheses in a `(shared)` directory:

```bash
bat apps/landing/app/\(shared\)/solutions/content-builders.ts
rg "pattern" apps/landing/app/\(shared\)/
fd file.txt apps/landing/app/\(shared\)/
```

Escaping brackets in a `[locale]` directory:

```bash
bat app/\[locale\]/route.ts
rg "pattern" app/\[locale\]/
eza app/\[locale\]/
```

Escaping spaces in filenames:

```bash
bat my\ file\ name.txt
rg "pattern" path/to/my\ file\ name.txt
```

Remember: This escaping requirement applies universally to all CLI commands when running in a shell environment.
