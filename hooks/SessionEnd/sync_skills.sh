#!/usr/bin/env bash
# Sync local skills from ~/.claude/skills and ./.claude/skills to permissions

set -euo pipefail

SKILLS_SETTINGS="$HOME/.claude/settings/permissions/skills.jsonc"

[[ -f "$SKILLS_SETTINGS" ]] || exit 0

# ---------------------------------------------------------------------------- #
#                            1. DISCOVER LOCAL SKILLS                          #
# ---------------------------------------------------------------------------- #

local_skills=()

# Global skills: directories containing SKILL.md
if [[ -d "$HOME/.claude/skills" ]]; then
  while IFS= read -r skill_dir; do
    skill_name=$(basename "$skill_dir")
    local_skills+=("Skill($skill_name)")
  done < <(find "$HOME/.claude/skills" -maxdepth 2 -name "SKILL.md" -exec dirname {} \; 2>/dev/null)
fi

# Project skills: directories containing SKILL.md (if ./.claude/skills exists)
if [[ -d "./.claude/skills" ]]; then
  while IFS= read -r skill_dir; do
    skill_name=$(basename "$skill_dir")
    local_skills+=("Skill($skill_name)")
  done < <(find "./.claude/skills" -maxdepth 2 -name "SKILL.md" -exec dirname {} \; 2>/dev/null)
fi

# ---------------------------------------------------------------------------- #
#                          2. EXTRACT PLUGIN SKILLS                            #
# ---------------------------------------------------------------------------- #

# Parse existing permissions, keeping only plugin skills (those with ':')
plugin_skills=$(grep -v '^\s*//' "$SKILLS_SETTINGS" | jq -r '
  .permissions.allow // [] | .[] | select(contains(":"))
' 2>/dev/null)

# ---------------------------------------------------------------------------- #
#                               3. MERGE SKILLS                                #
# ---------------------------------------------------------------------------- #

# Combine plugin skills + local skills, deduplicate, and sort
all_skills=()

# Add plugin skills
while IFS= read -r skill; do
  [[ -n "$skill" ]] && all_skills+=("$skill")
done <<< "$plugin_skills"

# Add local skills
for skill in "${local_skills[@]}"; do
  all_skills+=("$skill")
done

# Convert to JSON array, deduplicate, and sort
skills_json=$(printf '%s\n' "${all_skills[@]}" | sort -u | jq -R -s 'split("\n") | map(select(length > 0))') || {
  echo "Error: Failed to build skills JSON" >&2
  exit 1
}

# ---------------------------------------------------------------------------- #
#                             4. WRITE SKILLS.JSONC                            #
# ---------------------------------------------------------------------------- #

jq -n --argjson skills "$skills_json" '{
  "// Claude Skills": "",
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  permissions: {
    allow: $skills
  }
}' | sed 's/"\/\/ Claude Skills": "",/\/\/ Claude Skills/' > "$SKILLS_SETTINGS"

# ---------------------------------------------------------------------------- #
#                            5. RUN MERGE SETTINGS                             #
# ---------------------------------------------------------------------------- #

"$HOME/.claude/helpers/merge_settings.sh" >/dev/null 2>&1 || true
