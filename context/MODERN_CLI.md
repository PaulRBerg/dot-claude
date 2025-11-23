## Modern CLI

Use these modern CLI tools in shells like Bash.

- **PREFER**: `rg`, `fd`, `bat`, `eza`, `jq`, `yq`, `fzf`, `delta`, `gh`
- **AVOID (use only if needed)**: `grep`, `find`, `cat`, `ls`, `df`, `top`, `xxd`

## IMPORTANT: Special Characters in File Paths

**This rule applies to all CLI tools and terminal commands - not just the examples shown.**

When file paths contain special characters (like parentheses, spaces, brackets, etc.), you MUST always escape them with
backslashes (`\`) in shell commands. Failure to do so will cause commands to fail.

**Common special characters that MUST be escaped include: `(` `)` `[` `]` `{` `}` and spaces.**

### Examples (applies to ALL tools: `bat`, `rg`, `fd`, `eza`, etc.):

Escaping parentheses in a `(shared)` directory:

```bash
bat src\(shared\)/Foo.tsx
rg "pattern" src/\(shared\)/
```

Escaping spaces in filenames:

```bash
bat my\ file\ name.txt
rg "pattern" path/to/my\ file\ name.txt
```

**Remember**: This escaping requirement applies to all CLI commands when running in a shell environment.
