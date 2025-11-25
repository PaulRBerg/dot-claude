#!/usr/bin/env python3
# NOTE: This hook is currently unused.
"""UserPromptSubmit hook that suggests skills based on prompt analysis.

Analyzes user prompts against skill-rules.json configuration files (global and
project-level), matching keywords and intent patterns to suggest relevant skills
that should be activated.

See https://github.com/diet103/claude-code-infrastructure-showcase
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, TypedDict


class PromptTriggers(TypedDict, total=False):
    keywords: List[str]
    intentPatterns: List[str]


class SkillRule(TypedDict, total=False):
    enforcement: str  # block | suggest | warn
    priority: str  # critical | high | medium | low
    promptTriggers: PromptTriggers
    type: str


class MatchedSkill(TypedDict):
    classification: str  # keyword | intent | both
    enforcement: str
    priority: str
    skill: str


def load_skill_rules(cwd: Path) -> Dict[str, SkillRule]:
    """Load and merge skill rules from global and project configs.

    Project rules take priority over global rules for duplicate skill names.
    """
    global_path = Path.home() / ".claude" / "skills" / "skill-rules.json"
    project_path = cwd / "skill-rules.json"

    rules: Dict[str, SkillRule] = {}

    # Load global rules
    if global_path.exists():
        try:
            with global_path.open() as f:
                rules.update(json.load(f))
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: Failed to load global skill-rules.json: {e}", file=sys.stderr)

    # Load and merge project rules (takes priority)
    if project_path.exists():
        try:
            with project_path.open() as f:
                rules.update(json.load(f))
        except (json.JSONDecodeError, OSError) as e:
            print(
                f"Warning: Failed to load project skill-rules.json: {e}",
                file=sys.stderr,
            )

    return rules


def match_keywords(prompt: str, keywords: List[str]) -> bool:
    """Check if any keywords match in prompt (case-insensitive)."""
    prompt_lower = prompt.lower()
    return any(keyword.lower() in prompt_lower for keyword in keywords)


def match_intent_patterns(prompt: str, patterns: List[str]) -> bool:
    """Check if any intent patterns match in prompt."""
    for pattern in patterns:
        try:
            if re.search(pattern, prompt, re.IGNORECASE):
                return True
        except re.error as e:
            print(f"Warning: Invalid regex pattern '{pattern}': {e}", file=sys.stderr)
    return False


def find_matches(prompt: str, rules: Dict[str, SkillRule]) -> List[MatchedSkill]:
    """Find all skills matching the prompt."""
    matches: List[MatchedSkill] = []

    for skill_name, rule in rules.items():
        # Only process rules with prompt triggers and suggest enforcement
        triggers = rule.get("promptTriggers")
        if not triggers or rule.get("enforcement") != "suggest":
            continue

        keywords = triggers.get("keywords", [])
        patterns = triggers.get("intentPatterns", [])

        keyword_match = match_keywords(prompt, keywords) if keywords else False
        intent_match = match_intent_patterns(prompt, patterns) if patterns else False

        if keyword_match or intent_match:
            classification = (
                "both"
                if keyword_match and intent_match
                else ("keyword" if keyword_match else "intent")
            )

            matches.append(
                {
                    "classification": classification,
                    "enforcement": rule.get("enforcement", "suggest"),
                    "priority": rule.get("priority", "medium"),
                    "skill": skill_name,
                }
            )

    return matches


def sort_matches(matches: List[MatchedSkill]) -> List[MatchedSkill]:
    """Sort matches by priority (critical > high > medium > low)."""
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return sorted(matches, key=lambda m: priority_order.get(m["priority"], 4))


def format_output(matches: List[MatchedSkill]) -> str:
    """Format matched skills as markdown context."""
    if not matches:
        return ""

    lines = ["## Skill Activation Suggestions", ""]
    lines.append("The following skills may be relevant to your request:")
    lines.append("")

    # Group by priority
    by_priority: Dict[str, List[MatchedSkill]] = {}
    for match in matches:
        priority = match["priority"]
        by_priority.setdefault(priority, []).append(match)

    # Output in priority order
    for priority in ["critical", "high", "medium", "low"]:
        if priority not in by_priority:
            continue

        priority_label = priority.upper()
        lines.append(f"**{priority_label} PRIORITY:**")

        for match in by_priority[priority]:
            skill = match["skill"]
            classification = match["classification"]
            lines.append(f"- `{skill}` (matched: {classification})")

        lines.append("")

    lines.append("Consider using the Skill tool to activate relevant skills.")

    return "\n".join(lines)


def main() -> None:
    """Main hook entry point."""
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(0)

    prompt = input_data.get("prompt", "")
    if not prompt:
        sys.exit(0)

    cwd = Path(input_data.get("cwd", "."))

    # Load and merge skill rules
    rules = load_skill_rules(cwd)
    if not rules:
        sys.exit(0)

    # Find and sort matches
    matches = find_matches(prompt, rules)
    if not matches:
        sys.exit(0)

    sorted_matches = sort_matches(matches)

    # Format output
    context = format_output(sorted_matches)
    if not context:
        sys.exit(0)

    # Output structured response
    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        }
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
