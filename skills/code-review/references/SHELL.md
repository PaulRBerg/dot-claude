# Shell Script Security and Correctness

## Security

**Variable Quoting**

Always double-quote variable expansions: `"$var"` not `$var`. Unquoted variables undergo word splitting and glob expansion, enabling injection attacks. Use `"${var}"` for clarity when concatenating strings or when variables appear adjacent to other text.

**Command Injection**

Never pass user input to `eval`. Build commands using arrays instead of string concatenation. For dynamic argument construction, use arrays: `args=("$arg1" "$arg2"); command "${args[@]}"`. When escaping is unavoidable, use `printf '%q'` to shell-escape values.

**Privilege Escalation**

Avoid setuid scripts—the kernel ignores the setuid bit on scripts in most Unix systems. Use `mktemp -d` for temporary directories to prevent race conditions. Always check return values of privileged commands: `if sudo command; then` or `sudo command || exit 1`.

**Sensitive Data**

Don't pass secrets via command-line arguments—they're visible in `ps` output and process listings. Use environment variables or temporary files with restricted permissions instead. Clear sensitive variables after use: `unset PASSWORD`.

## Correctness

**Set Options**

Use `set -e` to exit immediately on error. Use `set -u` to treat undefined variables as errors. Use `set -o pipefail` to fail pipelines if any command fails (not just the last). Combine: `set -euo pipefail` at script start.

**Exit Codes**

Check exit status with `$?` or use `if command; then` directly. Trap EXIT for cleanup: `trap cleanup EXIT`. Return meaningful codes: 0 for success, 1 for general errors, 2 for misuse (invalid arguments), 126 for command not executable, 127 for command not found.

**Signal Handling**

Set up cleanup handlers: `trap cleanup EXIT INT TERM`. Clean up temporary files on interrupt. Don't trap SIGKILL (9) or SIGSTOP—they're uncatchable by design.

**Conditionals**

Prefer `[[ ]]` over `[ ]`—it's safer (no word splitting) and more powerful (regex matching, pattern matching). Use `-z` to test for empty strings, `-n` for non-empty. Use `==` for string comparison inside `[[ ]]`. Check file existence with `-e`, files with `-f`, directories with `-d`.

## Portability

**POSIX Compliance**

Use `#!/usr/bin/env sh` for portable scripts, `#!/usr/bin/env bash` for bash-specific features. Run ShellCheck to identify portability issues. Test on target shells before deployment.

**Avoid Bashisms in POSIX Scripts**

Don't use `[[ ]]` (use `[` instead). Use `.` instead of `source`. Arrays aren't POSIX. Process substitution (`<()`) isn't portable. `$()` is POSIX; backticks are older but work.

**Portable Patterns**

Use `command -v` instead of `which` (not always available). Use `printf` instead of `echo -e` (behavior varies). Prefer `$(...)` over backticks for readability and nesting. Use `[ -n "${var+x}" ]` to test if variable is set.
