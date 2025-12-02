#!/usr/bin/env python3
"""Sync Claude Code settings at session end.

Combines skill, command, and plugin synchronization into a single hook
that runs at session end:
- Skills: Discovers from ~/.claude/skills and ./.claude/skills
- Commands: Discovers from ~/.claude/commands and ./.claude/commands
- Plugins: Merges enabledPlugins from settings.json

Replaces sync_skills.sh and sync_plugins.sh.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

# === CONSTANTS ===

CLAUDE_DIR = Path.home() / ".claude"
SKILLS_SETTINGS = CLAUDE_DIR / "settings" / "permissions" / "skills.jsonc"
COMMANDS_SETTINGS = CLAUDE_DIR / "settings" / "permissions" / "commands.jsonc"
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


def discover_local_skills(base_path: Path) -> list[str]:
    """Find all local skills by looking for SKILL.md files.

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
    local_skills: list[str],
    plugin_skills: list[str],
) -> list[str]:
    """Merge skill lists, deduplicate, and sort.

    Args:
        local_skills: Skills discovered from filesystem
        plugin_skills: Skills extracted from existing config

    Returns:
        Sorted, deduplicated list of all skills
    """
    all_skills = set(local_skills + plugin_skills)
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
    lines.insert(1, "  // Claude Skills")
    return "\n".join(lines)


def sync_skills() -> bool:
    """Sync local skills to skills.jsonc.

    Returns:
        True if sync succeeded, False otherwise
    """
    if not SKILLS_SETTINGS.exists():
        return False

    # 1. Discover local skills from both directories
    global_skills = discover_local_skills(CLAUDE_DIR / "skills")
    project_skills = discover_local_skills(Path.cwd() / ".claude" / "skills")
    local_skills = global_skills + project_skills

    # 2. Extract plugin skills from existing config
    try:
        current_config = read_jsonc(SKILLS_SETTINGS)
        plugin_skills = extract_plugin_skills(current_config)
    except (FileNotFoundError, json.JSONDecodeError):
        plugin_skills = []

    # 3. Merge, dedupe, sort
    all_skills = merge_and_dedupe_skills(local_skills, plugin_skills)

    # 4. Write skills.jsonc
    try:
        content = build_skills_jsonc(all_skills)
        SKILLS_SETTINGS.write_text(content + "\n")
        return True
    except OSError:
        return False


# === COMMAND DISCOVERY ===


def discover_local_commands(base_path: Path) -> list[str]:
    """Find all local commands by looking for .md files.

    Args:
        base_path: Directory to search (e.g., ~/.claude/commands)

    Returns:
        List of command names in SlashCommand(/name:*) format

    Note:
        Finds .md files directly in the commands directory.
    """
    if not base_path.exists():
        return []

    commands = []
    for cmd_file in base_path.glob("*.md"):
        cmd_name = cmd_file.stem  # filename without .md
        commands.append(f"SlashCommand(/{cmd_name}:*)")
    return commands


def extract_plugin_commands(commands_config: dict) -> list[str]:
    """Extract plugin commands (those with : in path before :*) from config.

    Args:
        commands_config: Parsed commands.jsonc content

    Returns:
        List of plugin command names (path contains ':')

    Note:
        Plugin commands have format SlashCommand(/plugin:command:*)
        Local commands have format SlashCommand(/command:*)
    """
    allow = commands_config.get("permissions", {}).get("allow", [])
    plugin_commands = []
    for cmd in allow:
        # Extract path between / and :*
        match = re.match(r"SlashCommand\(/([^)]+):\*\)", cmd)
        if match and ":" in match.group(1):  # has : in path = plugin
            plugin_commands.append(cmd)
    return plugin_commands


def merge_and_dedupe_commands(
    local_commands: list[str],
    plugin_commands: list[str],
) -> list[str]:
    """Merge command lists, deduplicate, and sort.

    Args:
        local_commands: Commands discovered from filesystem
        plugin_commands: Commands extracted from existing config

    Returns:
        Sorted, deduplicated list of all commands
    """
    all_commands = set(local_commands + plugin_commands)
    return sorted(all_commands)


def build_commands_jsonc(commands: list[str]) -> str:
    """Generate commands.jsonc content with comment header.

    Args:
        commands: List of command names to include

    Returns:
        JSONC string with schema and comment
    """
    config = {
        "$schema": "https://json.schemastore.org/claude-code-settings.json",
        "permissions": {"allow": commands},
    }
    json_str = json.dumps(config, indent=2)
    # Insert comment after opening brace (matching original format)
    lines = json_str.split("\n")
    lines.insert(1, "  // Slash commands")
    return "\n".join(lines)


def sync_commands() -> bool:
    """Sync local commands to commands.jsonc.

    Returns:
        True if sync succeeded, False otherwise
    """
    if not COMMANDS_SETTINGS.exists():
        return False

    # 1. Discover local commands from both directories
    global_commands = discover_local_commands(CLAUDE_DIR / "commands")
    project_commands = discover_local_commands(Path.cwd() / ".claude" / "commands")
    local_commands = global_commands + project_commands

    # 2. Extract plugin commands from existing config
    try:
        current_config = read_jsonc(COMMANDS_SETTINGS)
        plugin_commands = extract_plugin_commands(current_config)
    except (FileNotFoundError, json.JSONDecodeError):
        plugin_commands = []

    # 3. Merge, dedupe, sort
    all_commands = merge_and_dedupe_commands(local_commands, plugin_commands)

    # 4. Write commands.jsonc
    try:
        content = build_commands_jsonc(all_commands)
        COMMANDS_SETTINGS.write_text(content + "\n")
        return True
    except OSError:
        return False


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
        return True
    except OSError:
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
    # Sync skills (graceful - continue on failure)
    sync_skills()

    # Sync commands (graceful - continue on failure)
    sync_commands()

    # Sync plugins (graceful - continue on failure)
    sync_plugins()

    # Run merge_settings.sh once at the end
    run_merge_settings()

    # Always exit cleanly
    sys.exit(0)


if __name__ == "__main__":
    main()
