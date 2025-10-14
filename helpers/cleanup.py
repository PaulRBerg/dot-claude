#!/usr/bin/env python3
"""
Clean up bloated ~/.claude.json file by removing conversation history
while preserving all configuration settings.

The Claude Code config file mixes configuration with conversation history,
causing it to grow to massive sizes (100+ MB) and slow down performance.
This script removes the history while keeping all important settings.

https://github.com/anthropics/claude-code/issues/5024#issuecomment-3267855856
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def clean_claude_json():
    """Clean the Claude Code JSON file by removing history."""

    # Path to the Claude JSON file
    claude_json_path = Path.home() / ".claude.json"

    if not claude_json_path.exists():
        print("❌ ~/.claude.json not found")
        return 1

    # Get original file size
    original_size = claude_json_path.stat().st_size
    print(f"📁 Original file size: {original_size / 1024 / 1024:.2f} MB")

    # Create backup
    backup_path = claude_json_path.with_suffix(
        f".json.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    print(f"💾 Creating backup: {backup_path}")

    try:
        # Read the file
        print("📖 Reading file...")
        with open(claude_json_path, "r") as f:
            data = json.load(f)

        # Backup original
        with open(backup_path, "w") as f:
            json.dump(data, f, indent=2)

        # Count items to clean
        history_count = 0
        history_size_total = 0

        # Clear history from all projects
        if "projects" in data:
            for proj_id in data["projects"]:
                if isinstance(data["projects"][proj_id], dict):
                    if "history" in data["projects"][proj_id]:
                        # Calculate size of this history
                        hist_size = len(
                            json.dumps(data["projects"][proj_id]["history"])
                        )
                        history_size_total += hist_size
                        history_count += 1

                        # Show progress for large histories
                        if hist_size > 1024 * 1024:  # > 1MB
                            print(
                                f"  🧹 Clearing large history for {proj_id[:30]}... ({hist_size / 1024 / 1024:.2f} MB)"
                            )

                        # Clear the history
                        data["projects"][proj_id]["history"] = []

        print(
            f"\n📊 Found {history_count} project histories totaling {history_size_total / 1024 / 1024:.2f} MB"
        )

        # Save cleaned data
        print("✍️  Writing cleaned file...")
        with open(claude_json_path, "w") as f:
            json.dump(data, f, indent=2)

        # Get new file size
        new_size = claude_json_path.stat().st_size
        reduction_pct = ((original_size - new_size) / original_size) * 100

        print("\n✅ Success!")
        print(f"   Original: {original_size / 1024 / 1024:.2f} MB")
        print(f"   New size: {new_size / 1024:.2f} KB")
        print(f"   Reduced by: {reduction_pct:.1f}%")
        print(f"\n💡 Backup saved to: {backup_path}")
        print(f"   You can delete it with: rm {backup_path}")

        return 0

    except json.JSONDecodeError as e:
        print("❌ Error: Invalid JSON in ~/.claude.json")
        print(f"   {e}")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        # Try to restore from backup if we created one
        if backup_path.exists() and not claude_json_path.exists():
            print("🔄 Restoring from backup...")
            backup_path.rename(claude_json_path)
        return 1


def main():
    """Main entry point."""
    print("🧹 Claude Code JSON Cleaner")
    print("=" * 40)

    # Check file before cleaning
    claude_json_path = Path.home() / ".claude.json"
    if claude_json_path.exists():
        size_mb = claude_json_path.stat().st_size / 1024 / 1024
        if size_mb < 1:
            print(f"✨ File is already small ({size_mb:.2f} MB), no cleaning needed!")
            response = input("Clean anyway? (y/N): ")
            if response.lower() != "y":
                return 0

    return clean_claude_json()


if __name__ == "__main__":
    sys.exit(main())
