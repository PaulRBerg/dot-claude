#!/usr/bin/env python3
"""Update all plugin marketplaces and refresh metadata.

This script:
1. Deletes the plugin cache directory
2. Updates each marketplace git repo to latest
3. Updates known_marketplaces.json and installed_plugins.json with new timestamps/SHAs
"""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def get_iso_timestamp() -> str:
    """Return current UTC timestamp in ISO format with milliseconds."""
    return (
        datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.")
        + f"{datetime.now(timezone.utc).microsecond // 1000:03d}Z"
    )


def delete_cache(cache_path: Path) -> bool:
    """Delete the plugin cache directory."""
    print("🗑️  Deleting cache directory...")
    if cache_path.exists():
        shutil.rmtree(cache_path)
        print("   ✅ Cache deleted")
        return True
    print("   ℹ️  Cache directory doesn't exist")
    return True


def get_default_branch(repo_path: Path) -> str | None:
    """Get the default branch name for a git repository."""
    try:
        result = subprocess.run(
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        # Output is like "refs/remotes/origin/main"
        return result.stdout.strip().split("/")[-1]
    except subprocess.CalledProcessError:
        # Fallback: try common branch names
        for branch in ["main", "master"]:
            result = subprocess.run(
                ["git", "rev-parse", "--verify", f"origin/{branch}"],
                cwd=repo_path,
                capture_output=True,
                check=False,
            )
            if result.returncode == 0:
                return branch
        return None


def get_commit_sha(repo_path: Path) -> str | None:
    """Get the current HEAD commit SHA."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def update_marketplace(marketplace_path: Path) -> tuple[bool, str | None, str | None]:
    """Update a marketplace git repo to latest.

    Returns:
        (success, branch, new_sha)
    """
    name = marketplace_path.name
    print(f"🔄 Updating {name}...")

    if not marketplace_path.is_dir():
        print("   ❌ Directory not found")
        return False, None, None

    if not (marketplace_path / ".git").exists():
        print("   ❌ Not a git repository")
        return False, None, None

    # Fetch latest
    result = subprocess.run(
        ["git", "fetch", "origin"],
        cwd=marketplace_path,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(f"   ❌ Failed to fetch: {result.stderr.strip()}")
        return False, None, None

    # Get default branch
    branch = get_default_branch(marketplace_path)
    if not branch:
        print("   ❌ Could not determine default branch")
        return False, None, None

    # Reset to origin/branch
    result = subprocess.run(
        ["git", "reset", "--hard", f"origin/{branch}"],
        cwd=marketplace_path,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(f"   ❌ Failed to reset: {result.stderr.strip()}")
        return False, None, None

    # Get new commit SHA
    new_sha = get_commit_sha(marketplace_path)
    if not new_sha:
        print("   ❌ Could not get commit SHA")
        return False, None, None

    print(f"   ✅ Updated to {new_sha[:7]} ({branch})")
    return True, branch, new_sha


def update_known_marketplaces(json_path: Path, updates: dict[str, str]) -> bool:
    """Update known_marketplaces.json with new timestamps."""
    if not json_path.exists():
        print("📝 known_marketplaces.json not found, skipping")
        return False

    with open(json_path) as f:
        data = json.load(f)

    timestamp = get_iso_timestamp()
    for marketplace_name in updates:
        if marketplace_name in data:
            data[marketplace_name]["lastUpdated"] = timestamp

    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    print("📝 Updated known_marketplaces.json")
    return True


def update_installed_plugins(json_path: Path, marketplace_updates: dict[str, str]) -> bool:
    """Update installed_plugins.json with new timestamps and commit SHAs."""
    if not json_path.exists():
        print("📝 installed_plugins.json not found, skipping")
        return False

    with open(json_path) as f:
        data = json.load(f)

    timestamp = get_iso_timestamp()
    plugins = data.get("plugins", {})

    for plugin_key, installs in plugins.items():
        # plugin_key is like "code-review@claude-code-plugins"
        if "@" not in plugin_key:
            continue
        marketplace = plugin_key.split("@")[-1]

        if marketplace in marketplace_updates:
            new_sha = marketplace_updates[marketplace]
            for install in installs:
                install["lastUpdated"] = timestamp
                install["gitCommitSha"] = new_sha

    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    print("📝 Updated installed_plugins.json")
    return True


def main() -> int:
    plugins_dir = Path.home() / ".claude" / "plugins"
    marketplaces_dir = plugins_dir / "marketplaces"
    cache_dir = plugins_dir / "cache"
    known_marketplaces_path = plugins_dir / "known_marketplaces.json"
    installed_plugins_path = plugins_dir / "installed_plugins.json"

    if not marketplaces_dir.exists():
        print("❌ Marketplaces directory not found")
        return 1

    # Delete cache
    delete_cache(cache_dir)
    print()

    # Update each marketplace
    marketplace_updates: dict[str, str] = {}  # name -> new_sha
    successes = 0
    failures = 0

    for marketplace_path in sorted(marketplaces_dir.iterdir()):
        if not marketplace_path.is_dir():
            continue
        if marketplace_path.name.startswith("."):
            continue

        success, _branch, new_sha = update_marketplace(marketplace_path)
        if success and new_sha:
            marketplace_updates[marketplace_path.name] = new_sha
            successes += 1
        else:
            failures += 1

    print()

    # Update JSON files
    if marketplace_updates:
        update_known_marketplaces(known_marketplaces_path, marketplace_updates)
        update_installed_plugins(installed_plugins_path, marketplace_updates)

    # Summary
    print()
    if failures == 0:
        print(f"✅ All {successes} marketplaces updated successfully")
        return 0
    else:
        print(f"⚠️  {successes} succeeded, {failures} failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
