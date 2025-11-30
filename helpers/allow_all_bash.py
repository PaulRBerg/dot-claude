#!/usr/bin/env python3
"""Add Bash permission to project's local Claude settings."""

import json
import sys
from pathlib import Path


def main():
    rel_path = ".claude/settings.local.json"
    settings_path = Path.cwd() / rel_path

    # Case 1: File doesn't exist
    if not settings_path.exists():
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"permissions": {"allow": ["Bash"]}}
        settings_path.write_text(json.dumps(data, indent=2) + "\n")
        print(f"✅ Created {rel_path} with Bash permission")
        return 0

    # Case 2: File exists - merge
    try:
        data = json.loads(settings_path.read_text())
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {rel_path}: {e}")
        return 1

    # Navigate/create nested structure
    permissions = data.setdefault("permissions", {})
    allow = permissions.setdefault("allow", [])

    if "Bash" in allow:
        print(f"ℹ️  Bash already in {rel_path}")
        return 0

    allow.append("Bash")
    settings_path.write_text(json.dumps(data, indent=2) + "\n")
    print(f"✅ Added Bash to {rel_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
