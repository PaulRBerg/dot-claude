## Modern CLI

Use these modern CLI tools in shell like Bash or Zsh.

- **PREFER**: `rg`, `fd`, `bat`, `eza`, `jq`, `yq`, `fzf`, `delta`, `gh`
- **AVOID (use only if needed)**: `grep`, `find`, `cat`, `ls`, `df`, `top`, `xxd`

### Special Characters in File Paths

When file paths contain special characters (like parentheses, spaces, or brackets), escape them with backslashes (`\`).

Example escaping parentheses in a `(shared)` directory:

```bash
bat apps/landing/app/\(shared\)/solutions/content-builders.ts
```

Example escaping brackets in a `[locale]` directory:

```bash
bat app/\[locale\]/route.ts
```
