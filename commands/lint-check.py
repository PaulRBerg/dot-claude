#!/usr/bin/env python3
"""Dynamic linting command that reads lint-staged configuration.

This script:
1. Locates and parses lint-staged config (.lintstagedrc.js, .json, or package.json)
2. Gets modified files from git
3. Matches file patterns to linting commands
4. Executes appropriate linters
5. Returns results
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def find_git_root() -> Optional[Path]:
    """Find the git repository root."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        return None


def parse_lintstagedrc_js(file_path: Path) -> Optional[Dict[str, Any]]:
    """Parse .lintstagedrc.js file using Node.js."""
    try:
        # Use Node.js to evaluate the JS file and output JSON
        result = subprocess.run(
            ["node", "-e", f"console.log(JSON.stringify(require('{file_path}')))"],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
        return None


def parse_lintstagedrc_json(file_path: Path) -> Optional[Dict[str, Any]]:
    """Parse .lintstagedrc.json file."""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def parse_package_json_lint_staged(repo_root: Path) -> Optional[Dict[str, Any]]:
    """Parse lint-staged field from package.json."""
    package_json = repo_root / "package.json"
    try:
        with open(package_json, "r") as f:
            data = json.load(f)
            return data.get("lint-staged")
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def find_lint_staged_config(repo_root: Path) -> Optional[Dict[str, Any]]:
    """Find and parse lint-staged configuration."""
    # Try different config file locations in order of precedence
    config_files = [
        (repo_root / ".lintstagedrc.js", parse_lintstagedrc_js),
        (repo_root / ".lintstagedrc.json", parse_lintstagedrc_json),
        (repo_root / ".lintstagedrc", parse_lintstagedrc_json),
    ]

    for config_path, parser in config_files:
        if config_path.exists():
            config = parser(config_path)
            if config:
                print(f"✓ Found config: {config_path.name}", file=sys.stderr)
                return config

    # Try package.json
    config = parse_package_json_lint_staged(repo_root)
    if config:
        print("✓ Found config: package.json (lint-staged field)", file=sys.stderr)
        return config

    return None


def get_modified_files(repo_root: Path) -> List[str]:
    """Get list of modified files from git."""
    try:
        # Get staged files
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
            capture_output=True,
            text=True,
            check=True,
            cwd=repo_root,
        )
        staged = result.stdout.strip().split("\n") if result.stdout.strip() else []

        # Get unstaged files
        result = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMR"],
            capture_output=True,
            text=True,
            check=True,
            cwd=repo_root,
        )
        unstaged = result.stdout.strip().split("\n") if result.stdout.strip() else []

        # Get untracked files
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
            check=True,
            cwd=repo_root,
        )
        untracked = result.stdout.strip().split("\n") if result.stdout.strip() else []

        # Combine and deduplicate
        all_files = list(set(staged + unstaged + untracked))
        return [f for f in all_files if f]  # Remove empty strings
    except subprocess.CalledProcessError:
        return []


def glob_to_regex(pattern: str) -> str:
    """Convert glob pattern to regex pattern."""
    # Escape special regex characters except *, ?, and .
    pattern = pattern.replace(".", r"\.")
    pattern = pattern.replace("+", r"\+")
    pattern = pattern.replace("^", r"\^")
    pattern = pattern.replace("$", r"\$")

    # Convert glob wildcards to regex
    pattern = pattern.replace("**", "<!DOUBLESTAR!>")
    pattern = pattern.replace("*", "[^/]*")
    pattern = pattern.replace("<!DOUBLESTAR!>", ".*")
    pattern = pattern.replace("?", ".")

    # Handle character classes [...]
    pattern = re.sub(r"\{([^}]+)\}", lambda m: f"({m.group(1).replace(',', '|')})", pattern)

    return f"^{pattern}$"


def match_files_to_patterns(
    files: List[str], config: Dict[str, Any]
) -> Dict[str, List[str]]:
    """Match files to lint-staged patterns."""
    matches: Dict[str, List[str]] = {}

    for pattern, commands in config.items():
        regex = glob_to_regex(pattern)
        matched_files = [f for f in files if re.match(regex, f)]

        if matched_files:
            # Normalize commands to list
            if isinstance(commands, str):
                commands = [commands]
            matches[pattern] = matched_files

    return matches


def execute_lint_command(
    command: str, files: List[str], repo_root: Path
) -> Tuple[int, str, str]:
    """Execute a linting command with file arguments."""
    # Replace file placeholder if present
    if "[[ $FILENAMES ]]" in command or "{files}" in command:
        files_str = " ".join(f'"{f}"' for f in files)
        command = command.replace("[[ $FILENAMES ]]", files_str)
        command = command.replace("{files}", files_str)
    else:
        # Append files to command
        files_str = " ".join(f'"{f}"' for f in files)
        command = f"{command} {files_str}"

    print(f"\n→ Running: {command}", file=sys.stderr)

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=repo_root,
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def main() -> int:
    """Main entry point."""
    print("🔍 Lint Check - Dynamic Linting Based on Config\n", file=sys.stderr)

    # Find git root
    repo_root = find_git_root()
    if not repo_root:
        print("✗ Error: Not in a git repository", file=sys.stderr)
        return 1

    print(f"📁 Repository: {repo_root}\n", file=sys.stderr)

    # Find lint-staged config
    config = find_lint_staged_config(repo_root)
    if not config:
        print("✗ No lint-staged configuration found", file=sys.stderr)
        print("\nLooked for:", file=sys.stderr)
        print("  - .lintstagedrc.js", file=sys.stderr)
        print("  - .lintstagedrc.json", file=sys.stderr)
        print("  - .lintstagedrc", file=sys.stderr)
        print("  - package.json (lint-staged field)", file=sys.stderr)
        return 1

    # Get modified files
    modified_files = get_modified_files(repo_root)
    if not modified_files:
        print("✓ No modified files found - nothing to lint", file=sys.stderr)
        return 0

    print(f"\n📝 Found {len(modified_files)} modified file(s)\n", file=sys.stderr)

    # Match files to patterns
    matches = match_files_to_patterns(modified_files, config)
    if not matches:
        print("✓ No files match linting patterns", file=sys.stderr)
        return 0

    # Execute linting commands
    all_passed = True
    for pattern, matched_files in matches.items():
        commands = config[pattern]
        if isinstance(commands, str):
            commands = [commands]

        print(f"Pattern: {pattern}", file=sys.stderr)
        print(f"Matched {len(matched_files)} file(s)", file=sys.stderr)

        for command in commands:
            returncode, stdout, stderr = execute_lint_command(
                command, matched_files, repo_root
            )

            if stdout:
                print(stdout)
            if stderr:
                print(stderr, file=sys.stderr)

            if returncode != 0:
                all_passed = False
                print(f"✗ Failed with exit code {returncode}", file=sys.stderr)
            else:
                print("✓ Passed", file=sys.stderr)

    if all_passed:
        print("\n✓ All linting checks passed!", file=sys.stderr)
        return 0
    else:
        print("\n✗ Some linting checks failed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
