#!/usr/bin/env python3
"""Sync global Claude Code settings at session end.

Combines skill and plugin synchronization into a single hook
that runs at session end:
- Skills: Discovers from ~/.claude/skills and ~/.claude/commands (global only)
- Plugins: Merges enabledPlugins from settings.json

Local project settings (./.claude/) are handled by sync_local_settings.py.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

# === CONSTANTS ===

CLAUDE_DIR = Path.home() / ".claude"
SKILLS_SETTINGS = CLAUDE_DIR / "settings" / "permissions" / "skills.jsonc"
PLUGINS_SETTINGS = CLAUDE_DIR / "settings" / "plugins.jsonc"
ROOT_SETTINGS = CLAUDE_DIR / "settings.json"
MERGE_SCRIPT = CLAUDE_DIR / "helpers" / "merge_settings.sh"


# === JSONC PARSING ===


def strip_jsonc_comments(content: str) -> str:
    """Remove single-line // comments from JSONC content.

    Args:
        content: Raw JSONC file content

    Returns:
        JSON content with comments stripped

    Note:
        Only handles line comments (//), not block comments.
        Skips comment-only lines and removes trailing comments.
    """
    lines = []
    for line in content.split("\n"):
        # Skip comment-only lines
        if re.match(r"^\s*//", line):
            continue
        # Remove trailing comments (simple heuristic - after closing bracket/quote)
        line = re.sub(r'([\]\}"\d])\s*//[^"]*$', r"\1", line)
        lines.append(line)
    return "\n".join(lines)


def read_jsonc(path: Path) -> dict:
    """Read and parse a JSONC file.

    Args:
        path: Path to the JSONC file

    Returns:
        Parsed JSON as dictionary

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid after comment stripping
    """
    content = path.read_text()
    stripped = strip_jsonc_comments(content)
    return json.loads(stripped)


# === SKILL DISCOVERY ===


def discover_skills(base_path: Path) -> list[str]:
    """Find skills by looking for SKILL.md files.

    Args:
        base_path: Directory to search (e.g., ~/.claude/skills)

    Returns:
        List of skill names in Skill(name) format

    Note:
        Searches one level deep (*/SKILL.md).
    """
    if not base_path.exists():
        return []

    skills = []
    for skill_md in base_path.glob("*/SKILL.md"):
        skill_name = skill_md.parent.name
        skills.append(f"Skill({skill_name})")
    return skills


def extract_plugin_skills(skills_config: dict) -> list[str]:
    """Extract plugin skills (those with ':' in name) from config.

    Args:
        skills_config: Parsed skills.jsonc content

    Returns:
        List of plugin skill names (containing ':')
    """
    allow = skills_config.get("permissions", {}).get("allow", [])
    return [s for s in allow if ":" in s]


def merge_and_dedupe_skills(
    global_skills: list[str],
    plugin_skills: list[str],
) -> list[str]:
    """Merge skill lists, deduplicate, and sort.

    Args:
        global_skills: Skills discovered from global ~/.claude/skills
        plugin_skills: Skills extracted from existing config

    Returns:
        Sorted, deduplicated list of all skills
    """
    all_skills = set(global_skills + plugin_skills)
    return sorted(all_skills)


def build_skills_jsonc(skills: list[str]) -> str:
    """Generate skills.jsonc content with comment header.

    Args:
        skills: List of skill names to include

    Returns:
        JSONC string with schema and comment
    """
    config = {
        "$schema": "https://json.schemastore.org/claude-code-settings.json",
        "permissions": {"allow": skills},
    }
    json_str = json.dumps(config, indent=2)
    # Insert comment after opening brace (matching original format)
    lines = json_str.split("\n")
    lines.insert(1, "  // Skills and commands")
    return "\n".join(lines)


def sync_skills() -> bool:
    """Sync global skills and commands to skills.jsonc.

    Returns:
        True if sync succeeded, False otherwise
    """
    if not SKILLS_SETTINGS.exists():
        return False

    # 1. Discover global skills and commands (local handled by sync_local_settings.py)
    global_skills = discover_skills(CLAUDE_DIR / "skills")
    commands_dir = CLAUDE_DIR / "commands"
    global_commands = discover_commands(commands_dir) + discover_command_groups(commands_dir)

    # 2. Extract plugin skills from existing config
    try:
        current_config = read_jsonc(SKILLS_SETTINGS)
        plugin_skills = extract_plugin_skills(current_config)
    except (FileNotFoundError, json.JSONDecodeError):
        plugin_skills = []

    # 3. Merge skills and commands, dedupe, sort
    all_skills = merge_and_dedupe_skills(global_skills + global_commands, plugin_skills)

    # 4. Write skills.jsonc
    try:
        content = build_skills_jsonc(all_skills)
        SKILLS_SETTINGS.write_text(content + "\n")
        format_with_biome(SKILLS_SETTINGS)
        return True
    except OSError:
        return False


# === COMMAND DISCOVERY ===


def discover_commands(base_path: Path) -> list[str]:
    """Find commands by looking for .md files.

    Args:
        base_path: Directory to search (e.g., ~/.claude/commands)

    Returns:
        List of command names in Skill(name) format

    Note:
        Finds .md files directly in the commands directory.
        Commands are treated as skills for permission purposes.
    """
    if not base_path.exists():
        return []

    return [f"Skill({cmd_file.stem})" for cmd_file in base_path.glob("*.md")]


def discover_command_groups(base_path: Path) -> list[str]:
    """Find command groups by looking for subdirectories with .md files.

    Args:
        base_path: Directory to search (e.g., ~/.claude/commands)

    Returns:
        List of group names in Skill(group) format
    """
    if not base_path.exists():
        return []

    return [
        f"Skill({subdir.name})"
        for subdir in base_path.iterdir()
        if subdir.is_dir() and not subdir.name.startswith(".") and any(subdir.glob("*.md"))
    ]


# === PLUGIN SYNCHRONIZATION ===


def read_plugins_from_root() -> dict[str, bool]:
    """Read enabledPlugins from root settings.json.

    Returns:
        Dictionary of plugin_name -> enabled status
    """
    if not ROOT_SETTINGS.exists():
        return {}

    try:
        config = json.loads(ROOT_SETTINGS.read_text())
        return config.get("enabledPlugins", {})
    except (json.JSONDecodeError, OSError):
        return {}


def read_plugins_from_local() -> dict[str, bool]:
    """Read enabledPlugins from plugins.jsonc.

    Returns:
        Dictionary of plugin_name -> enabled status
    """
    if not PLUGINS_SETTINGS.exists():
        return {}

    try:
        config = read_jsonc(PLUGINS_SETTINGS)
        return config.get("enabledPlugins", {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def merge_plugins(
    root_plugins: dict[str, bool],
    local_plugins: dict[str, bool],
) -> dict[str, bool]:
    """Merge plugin configurations (local wins on conflicts).

    Args:
        root_plugins: Plugins from root settings.json
        local_plugins: Plugins from local plugins.jsonc

    Returns:
        Merged plugins dictionary, sorted by key
    """
    merged = {**root_plugins, **local_plugins}
    return dict(sorted(merged.items()))


def build_plugins_json(plugins: dict[str, bool]) -> str:
    """Generate plugins.jsonc content.

    Args:
        plugins: Dictionary of enabled plugins

    Returns:
        JSON string with schema
    """
    config = {
        "$schema": "https://json.schemastore.org/claude-code-settings.json",
        "enabledPlugins": plugins,
    }
    return json.dumps(config, indent=2)


def sync_plugins() -> bool:
    """Sync enabledPlugins from root to local config.

    Returns:
        True if sync succeeded, False otherwise
    """
    if not (ROOT_SETTINGS.exists() and PLUGINS_SETTINGS.exists()):
        return False

    root_plugins = read_plugins_from_root()
    local_plugins = read_plugins_from_local()
    merged = merge_plugins(root_plugins, local_plugins)

    try:
        content = build_plugins_json(merged)
        PLUGINS_SETTINGS.write_text(content + "\n")
        format_with_biome(PLUGINS_SETTINGS)
        return True
    except OSError:
        return False


# === FORMATTING ===


def format_with_biome(path: Path) -> bool:
    """Format file with Biome using global .claude as working directory.

    Args:
        path: Path to file to format

    Returns:
        True if formatted successfully, False on error
    """
    try:
        resolved_path = path.resolve()
        claude_root = CLAUDE_DIR.resolve()
        try:
            # Keep the path relative so Biome include globs like "settings/**/*.jsonc" match.
            target = resolved_path.relative_to(claude_root)
        except ValueError:
            target = resolved_path
        result = subprocess.run(
            ["biome", "format", "--write", str(target)],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=claude_root,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
        return False


# === MERGE SETTINGS ===


def run_merge_settings() -> bool:
    """Execute merge_settings.sh to combine all settings.

    Returns:
        True if script ran successfully, False otherwise
    """
    if not MERGE_SCRIPT.exists():
        return False

    try:
        subprocess.run(
            [str(MERGE_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return True
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
        return False


# === MAIN ===


def main() -> None:
    """Main hook entry point."""
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=2) as executor:
        # Run sync operations in parallel
        futures = [
            executor.submit(sync_skills),
            executor.submit(sync_plugins),
        ]
        # Wait for all to complete
        for f in futures:
            try:
                f.result()
            except Exception:
                pass  # Graceful - continue on failure

    # Run merge_settings after syncs complete
    if run_merge_settings():
        format_with_biome(ROOT_SETTINGS)

    sys.exit(0)


if __name__ == "__main__":
    main()
