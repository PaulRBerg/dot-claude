"""Tests for activate_skills.py hook."""

import importlib.util
import json
import sys
from io import StringIO
from pathlib import Path
from typing import Dict, List

import pytest

# Import functions from the hook script
hook_path = Path(__file__).parent / "activate_skills.py"
spec = importlib.util.spec_from_file_location("activate_skills", hook_path)
assert spec is not None, "Failed to load module spec"
assert spec.loader is not None, "Module spec has no loader"
activate_skills = importlib.util.module_from_spec(spec)
sys.modules["activate_skills"] = activate_skills
spec.loader.exec_module(activate_skills)

# Import specific functions and types
MatchedSkill = activate_skills.MatchedSkill
SkillRule = activate_skills.SkillRule
find_matches = activate_skills.find_matches
format_output = activate_skills.format_output
load_skill_rules = activate_skills.load_skill_rules
match_intent_patterns = activate_skills.match_intent_patterns
match_keywords = activate_skills.match_keywords
sort_matches = activate_skills.sort_matches


# Fixtures


@pytest.fixture
def sample_skill_rules() -> Dict[str, SkillRule]:
    """Sample skill rules for testing."""
    return {
        "typescript": {
            "type": "domain",
            "enforcement": "suggest",
            "priority": "high",
            "promptTriggers": {
                "keywords": ["typescript", "tsx", "type"],
                "intentPatterns": [
                    r"(write|create).*?typescript",
                    r"(fix|debug).*?type.*?error",
                ],
            },
        },
        "web3": {
            "type": "domain",
            "enforcement": "suggest",
            "priority": "high",
            "promptTriggers": {
                "keywords": ["web3", "ethereum", "viem"],
                "intentPatterns": [r"connect.*?wallet", r"(build|create).*?dapp"],
            },
        },
        "notes": {
            "type": "domain",
            "enforcement": "suggest",
            "priority": "medium",
            "promptTriggers": {
                "keywords": ["notes", "notebook", "nb"],
                "intentPatterns": [
                    r"(search|find).*?note",
                    r"in which.*?chat",
                ],
            },
        },
        "blocked-skill": {
            "type": "guardrail",
            "enforcement": "block",
            "priority": "critical",
            "promptTriggers": {
                "keywords": ["danger"],
            },
        },
    }


@pytest.fixture
def temp_skill_rules(tmp_path: Path) -> tuple[Path, Path]:
    """Create temporary skill-rules.json files."""
    global_dir = tmp_path / "global" / "skills"
    project_dir = tmp_path / "project"

    global_dir.mkdir(parents=True)
    project_dir.mkdir(parents=True)

    global_file = global_dir / "skill-rules.json"
    project_file = project_dir / "skill-rules.json"

    return global_file, project_file


# Tests for match_keywords()


class TestMatchKeywords:
    """Tests for keyword matching."""

    def test_exact_match(self):
        """Test exact keyword match."""
        assert match_keywords("typescript", ["typescript"])

    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        assert match_keywords("TypeScript is great", ["typescript"])
        assert match_keywords("typescript is great", ["TypeScript"])

    def test_partial_match(self):
        """Test substring matching."""
        assert match_keywords("I love typescript development", ["typescript"])

    def test_no_match(self):
        """Test when no keywords match."""
        assert not match_keywords("python programming", ["typescript", "javascript"])

    def test_empty_keywords(self):
        """Test with empty keyword list."""
        assert not match_keywords("any prompt", [])

    def test_multiple_keywords(self):
        """Test matching with multiple keywords."""
        assert match_keywords("web3 and ethereum", ["web3", "blockchain"])

    @pytest.mark.parametrize(
        "prompt,keywords,expected",
        [
            ("TypeScript", ["typescript"], True),
            ("TYPESCRIPT", ["typescript"], True),
            ("typescript", ["TYPESCRIPT"], True),
            ("Python", ["typescript"], False),
            ("type-script", ["typescript"], False),
        ],
    )
    def test_case_variations(self, prompt: str, keywords: List[str], expected: bool):
        """Test various case combinations."""
        assert match_keywords(prompt, keywords) == expected


# Tests for match_intent_patterns()


class TestMatchIntentPatterns:
    """Tests for intent pattern matching."""

    def test_simple_pattern_match(self):
        """Test simple regex pattern match."""
        assert match_intent_patterns("create typescript project", [r"create.*?typescript"])

    def test_case_insensitive_pattern(self):
        """Test case-insensitive pattern matching."""
        assert match_intent_patterns("Create TypeScript Project", [r"create.*?typescript"])

    def test_multiple_patterns_one_match(self):
        """Test multiple patterns with one matching."""
        patterns = [r"python.*?code", r"typescript.*?project", r"rust.*?app"]
        assert match_intent_patterns("create typescript project", patterns)

    def test_no_pattern_match(self):
        """Test when no patterns match."""
        assert not match_intent_patterns("hello world", [r"typescript.*?error"])

    def test_empty_patterns(self):
        """Test with empty pattern list."""
        assert not match_intent_patterns("any prompt", [])

    def test_invalid_regex_pattern(self, capsys):
        """Test handling of invalid regex patterns."""
        result = match_intent_patterns("test prompt", [r"[invalid("])
        assert not result
        captured = capsys.readouterr()
        assert "Warning: Invalid regex pattern" in captured.err

    def test_complex_pattern(self):
        """Test complex regex pattern."""
        pattern = r"(find|search|locate).*?(note|chat)"
        assert match_intent_patterns("find my notes about python", [pattern])
        assert match_intent_patterns("search for chat logs", [pattern])
        assert not match_intent_patterns("create a new file", [pattern])


# Tests for load_skill_rules()


class TestLoadSkillRules:
    """Tests for skill rules loading and merging."""

    def test_load_global_only(self, tmp_path: Path, monkeypatch):
        """Test loading global rules only."""
        # Create proper directory structure: ~/.claude/skills/
        home_dir = tmp_path / "home"
        claude_dir = home_dir / ".claude" / "skills"
        claude_dir.mkdir(parents=True)

        global_file = claude_dir / "skill-rules.json"
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        rules = {"skill1": {"enforcement": "suggest", "priority": "high"}}
        global_file.write_text(json.dumps(rules))

        monkeypatch.setattr(Path, "home", lambda: home_dir)
        result = load_skill_rules(project_dir)

        assert result == rules

    def test_load_project_only(self, temp_skill_rules: tuple[Path, Path], monkeypatch):
        """Test loading project rules only."""
        global_file, project_file = temp_skill_rules
        rules = {"skill1": {"enforcement": "suggest", "priority": "high"}}
        project_file.write_text(json.dumps(rules))

        monkeypatch.setattr(Path, "home", lambda: global_file.parent.parent.parent)
        result = load_skill_rules(project_file.parent)

        assert result == rules

    def test_merge_rules_project_priority(self, tmp_path: Path, monkeypatch):
        """Test merging rules with project taking priority."""
        # Create proper directory structure
        home_dir = tmp_path / "home"
        claude_dir = home_dir / ".claude" / "skills"
        claude_dir.mkdir(parents=True)

        global_file = claude_dir / "skill-rules.json"
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        project_file = project_dir / "skill-rules.json"

        global_rules = {
            "skill1": {"enforcement": "suggest", "priority": "medium"},
            "skill2": {"enforcement": "suggest", "priority": "low"},
        }
        project_rules = {
            "skill1": {"enforcement": "block", "priority": "critical"},
            "skill3": {"enforcement": "suggest", "priority": "high"},
        }

        global_file.write_text(json.dumps(global_rules))
        project_file.write_text(json.dumps(project_rules))

        monkeypatch.setattr(Path, "home", lambda: home_dir)
        result = load_skill_rules(project_dir)

        assert result["skill1"]["enforcement"] == "block"  # Project overrides
        assert result["skill2"]["priority"] == "low"  # Global preserved
        assert result["skill3"]["priority"] == "high"  # Project added

    def test_no_rules_files(self, tmp_path: Path, monkeypatch):
        """Test when no rules files exist."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        result = load_skill_rules(tmp_path)
        assert result == {}

    def test_invalid_json_global(self, tmp_path: Path, monkeypatch, capsys):
        """Test handling invalid JSON in global file."""
        # Create proper directory structure
        home_dir = tmp_path / "home"
        claude_dir = home_dir / ".claude" / "skills"
        claude_dir.mkdir(parents=True)

        global_file = claude_dir / "skill-rules.json"
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        global_file.write_text("invalid json {")

        monkeypatch.setattr(Path, "home", lambda: home_dir)
        result = load_skill_rules(project_dir)

        assert result == {}
        captured = capsys.readouterr()
        assert "Warning: Failed to load global skill-rules.json" in captured.err

    def test_invalid_json_project_keeps_global(
        self, tmp_path: Path, monkeypatch, capsys
    ):
        """Test that valid global rules are kept when project file is invalid."""
        # Create proper directory structure
        home_dir = tmp_path / "home"
        claude_dir = home_dir / ".claude" / "skills"
        claude_dir.mkdir(parents=True)

        global_file = claude_dir / "skill-rules.json"
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        project_file = project_dir / "skill-rules.json"

        global_rules = {"skill1": {"enforcement": "suggest", "priority": "high"}}
        global_file.write_text(json.dumps(global_rules))
        project_file.write_text("invalid json")

        monkeypatch.setattr(Path, "home", lambda: home_dir)
        result = load_skill_rules(project_dir)

        assert result == global_rules
        captured = capsys.readouterr()
        assert "Warning: Failed to load project skill-rules.json" in captured.err


# Tests for find_matches()


class TestFindMatches:
    """Tests for finding skill matches."""

    def test_keyword_only_match(self, sample_skill_rules: Dict[str, SkillRule]):
        """Test matching by keywords only."""
        matches = find_matches("typescript project", sample_skill_rules)
        assert len(matches) == 1
        assert matches[0]["skill"] == "typescript"
        assert matches[0]["classification"] == "keyword"

    def test_intent_only_match(self, sample_skill_rules: Dict[str, SkillRule]):
        """Test matching by intent patterns only."""
        matches = find_matches("in which chat did I talk about hooks", sample_skill_rules)
        assert len(matches) == 1
        assert matches[0]["skill"] == "notes"
        assert matches[0]["classification"] == "intent"

    def test_both_keyword_and_intent_match(
        self, sample_skill_rules: Dict[str, SkillRule]
    ):
        """Test matching by both keywords and intent."""
        matches = find_matches("create typescript application", sample_skill_rules)
        assert len(matches) == 1
        assert matches[0]["skill"] == "typescript"
        assert matches[0]["classification"] == "both"

    def test_multiple_skills_match(self, sample_skill_rules: Dict[str, SkillRule]):
        """Test matching multiple skills."""
        matches = find_matches("typescript and web3 notes", sample_skill_rules)
        assert len(matches) == 3
        skill_names = {m["skill"] for m in matches}
        assert skill_names == {"typescript", "web3", "notes"}

    def test_no_matches(self, sample_skill_rules: Dict[str, SkillRule]):
        """Test when no skills match."""
        matches = find_matches("python programming", sample_skill_rules)
        assert len(matches) == 0

    def test_filters_block_enforcement(self, sample_skill_rules: Dict[str, SkillRule]):
        """Test that skills with 'block' enforcement are filtered out."""
        matches = find_matches("danger zone", sample_skill_rules)
        assert len(matches) == 0

    def test_rules_without_prompt_triggers(self):
        """Test rules without promptTriggers are skipped."""
        rules = {
            "no-triggers": {"enforcement": "suggest", "priority": "high"},
            "with-triggers": {
                "enforcement": "suggest",
                "priority": "high",
                "promptTriggers": {"keywords": ["test"]},
            },
        }
        matches = find_matches("test prompt", rules)
        assert len(matches) == 1
        assert matches[0]["skill"] == "with-triggers"

    def test_default_values(self):
        """Test default values for missing priority field."""
        rules = {
            "minimal": {
                "enforcement": "suggest",  # Required for match to work
                "promptTriggers": {"keywords": ["test"]},
            }
        }
        matches = find_matches("test", rules)
        assert len(matches) == 1
        assert matches[0]["enforcement"] == "suggest"
        assert matches[0]["priority"] == "medium"  # Default value


# Tests for sort_matches()


class TestSortMatches:
    """Tests for sorting matched skills."""

    def test_sort_by_priority(self):
        """Test sorting by priority levels."""
        matches: List[MatchedSkill] = [
            {
                "skill": "low1",
                "priority": "low",
                "enforcement": "suggest",
                "classification": "keyword",
            },
            {
                "skill": "critical1",
                "priority": "critical",
                "enforcement": "suggest",
                "classification": "keyword",
            },
            {
                "skill": "medium1",
                "priority": "medium",
                "enforcement": "suggest",
                "classification": "keyword",
            },
            {
                "skill": "high1",
                "priority": "high",
                "enforcement": "suggest",
                "classification": "keyword",
            },
        ]

        sorted_matches = sort_matches(matches)

        assert sorted_matches[0]["skill"] == "critical1"
        assert sorted_matches[1]["skill"] == "high1"
        assert sorted_matches[2]["skill"] == "medium1"
        assert sorted_matches[3]["skill"] == "low1"

    def test_unknown_priority_goes_last(self):
        """Test that unknown priorities are sorted last."""
        matches: List[MatchedSkill] = [
            {
                "skill": "unknown",
                "priority": "unknown",
                "enforcement": "suggest",
                "classification": "keyword",
            },
            {
                "skill": "high1",
                "priority": "high",
                "enforcement": "suggest",
                "classification": "keyword",
            },
        ]

        sorted_matches = sort_matches(matches)
        assert sorted_matches[0]["skill"] == "high1"
        assert sorted_matches[1]["skill"] == "unknown"

    def test_empty_list(self):
        """Test sorting empty list."""
        assert sort_matches([]) == []


# Tests for format_output()


class TestFormatOutput:
    """Tests for output formatting."""

    def test_empty_matches(self):
        """Test formatting empty matches."""
        assert format_output([]) == ""

    def test_single_match(self):
        """Test formatting single match."""
        matches: List[MatchedSkill] = [
            {
                "skill": "typescript",
                "priority": "high",
                "enforcement": "suggest",
                "classification": "keyword",
            }
        ]

        output = format_output(matches)

        assert "## Skill Activation Suggestions" in output
        assert "**HIGH PRIORITY:**" in output
        assert "`typescript` (matched: keyword)" in output
        assert "Consider using the Skill tool" in output

    def test_multiple_priorities(self):
        """Test formatting matches with multiple priorities."""
        matches: List[MatchedSkill] = [
            {
                "skill": "critical1",
                "priority": "critical",
                "enforcement": "suggest",
                "classification": "both",
            },
            {
                "skill": "high1",
                "priority": "high",
                "enforcement": "suggest",
                "classification": "keyword",
            },
            {
                "skill": "high2",
                "priority": "high",
                "enforcement": "suggest",
                "classification": "intent",
            },
        ]

        output = format_output(matches)

        assert "**CRITICAL PRIORITY:**" in output
        assert "**HIGH PRIORITY:**" in output
        assert "`critical1` (matched: both)" in output
        assert "`high1` (matched: keyword)" in output
        assert "`high2` (matched: intent)" in output

    def test_markdown_structure(self):
        """Test that output has proper markdown structure."""
        matches: List[MatchedSkill] = [
            {
                "skill": "test",
                "priority": "medium",
                "enforcement": "suggest",
                "classification": "keyword",
            }
        ]

        output = format_output(matches)

        assert output.startswith("## Skill Activation Suggestions")
        assert "**MEDIUM PRIORITY:**" in output
        assert output.count("- `") == 1  # One list item


# Integration tests for main()


class TestMainIntegration:
    """Integration tests for the main function."""

    def test_valid_input_with_matches(self, monkeypatch, capsys):
        """Test main with valid input that produces matches."""
        test_input = {
            "prompt": "typescript project",
            "cwd": str(Path(__file__).parent),
            "session_id": "test-123",
        }

        monkeypatch.setattr("sys.stdin", StringIO(json.dumps(test_input)))
        monkeypatch.setattr(
            "activate_skills.load_skill_rules",
            lambda cwd: {
                "typescript": {
                    "enforcement": "suggest",
                    "priority": "high",
                    "promptTriggers": {"keywords": ["typescript"]},
                }
            },
        )

        activate_skills.main()

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert "hookSpecificOutput" in output
        assert output["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
        assert "typescript" in output["hookSpecificOutput"]["additionalContext"]

    def test_valid_input_no_matches(self, monkeypatch, capsys):
        """Test main with valid input that produces no matches."""
        test_input = {
            "prompt": "hello world",
            "cwd": str(Path(__file__).parent),
            "session_id": "test-123",
        }

        monkeypatch.setattr("sys.stdin", StringIO(json.dumps(test_input)))
        monkeypatch.setattr("activate_skills.load_skill_rules", lambda cwd: {})

        with pytest.raises(SystemExit) as exc_info:
            activate_skills.main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_empty_prompt(self, monkeypatch):
        """Test main with empty prompt."""
        test_input = {"prompt": "", "cwd": "/tmp", "session_id": "test-123"}

        monkeypatch.setattr("sys.stdin", StringIO(json.dumps(test_input)))

        with pytest.raises(SystemExit) as exc_info:
            activate_skills.main()

        assert exc_info.value.code == 0

    def test_missing_prompt(self, monkeypatch):
        """Test main with missing prompt field."""
        test_input = {"cwd": "/tmp", "session_id": "test-123"}

        monkeypatch.setattr("sys.stdin", StringIO(json.dumps(test_input)))

        with pytest.raises(SystemExit) as exc_info:
            activate_skills.main()

        assert exc_info.value.code == 0

    def test_invalid_json_input(self, monkeypatch, capsys):
        """Test main with invalid JSON input."""
        monkeypatch.setattr("sys.stdin", StringIO("invalid json"))

        with pytest.raises(SystemExit) as exc_info:
            activate_skills.main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Error: Invalid JSON input" in captured.err
