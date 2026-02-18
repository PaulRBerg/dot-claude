#!/usr/bin/env python3
"""Unit tests for sync_global_settings.py hook."""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import sync_global_settings


class TestStripJsoncComments:
    """Test strip_jsonc_comments() function."""

    def test_removes_full_line_comments(self):
        """Test removing // comments on their own line."""
        content = """{
  // This is a comment
  "key": "value"
}"""
        result = sync_global_settings.strip_jsonc_comments(content)
        assert "//" not in result
        assert '"key": "value"' in result

    def test_removes_trailing_comments(self):
        """Test removing // comments after values."""
        content = '{"key": "value"]  // trailing comment\n}'
        result = sync_global_settings.strip_jsonc_comments(content)
        assert "// trailing" not in result
        assert '"key": "value"' in result

    def test_preserves_urls_in_values(self):
        """Test that // in string values (like URLs) is preserved."""
        content = '{"$schema": "https://example.com/schema.json"}'
        result = sync_global_settings.strip_jsonc_comments(content)
        assert "https://example.com" in result

    def test_handles_empty_content(self):
        """Test handling empty string."""
        result = sync_global_settings.strip_jsonc_comments("")
        assert result == ""

    def test_handles_no_comments(self):
        """Test content without any comments."""
        content = '{"key": "value"}'
        result = sync_global_settings.strip_jsonc_comments(content)
        assert result == content


class TestReadJsonc:
    """Test read_jsonc() function."""

    @patch("pathlib.Path.read_text")
    def test_reads_and_parses_valid_jsonc(self, mock_read):
        """Test reading valid JSONC file."""
        mock_read.return_value = """{
  // Comment
  "key": "value"
}"""
        result = sync_global_settings.read_jsonc(Path("/fake/path.jsonc"))
        assert result == {"key": "value"}

    @patch("pathlib.Path.read_text")
    def test_raises_on_invalid_json(self, mock_read):
        """Test raising JSONDecodeError on invalid JSON."""
        mock_read.return_value = "{ not valid json"
        with pytest.raises(json.JSONDecodeError):
            sync_global_settings.read_jsonc(Path("/fake/path.jsonc"))


class TestDiscoverLocalSkills:
    """Test discover_skills() function."""

    @patch("pathlib.Path.glob")
    @patch("pathlib.Path.exists")
    def test_finds_skills_with_skill_md(self, mock_exists, mock_glob):
        """Test discovering skills with SKILL.md files."""
        mock_exists.return_value = True
        mock_skill1 = MagicMock()
        mock_skill1.parent.name = "typescript"
        mock_skill2 = MagicMock()
        mock_skill2.parent.name = "gh-cli"
        mock_glob.return_value = [mock_skill1, mock_skill2]

        result = sync_global_settings.discover_skills(Path("/fake/skills"))

        assert "Skill(typescript)" in result
        assert "Skill(gh-cli)" in result

    @patch("pathlib.Path.exists")
    def test_returns_empty_for_missing_directory(self, mock_exists):
        """Test returning empty list when directory doesn't exist."""
        mock_exists.return_value = False
        result = sync_global_settings.discover_skills(Path("/nonexistent"))
        assert result == []


class TestExtractPluginSkills:
    """Test extract_plugin_skills() function."""

    def test_extracts_skills_with_colon(self):
        """Test extracting plugin skills (those with ':' in name)."""
        config = {
            "permissions": {
                "allow": [
                    "Skill(local-skill)",
                    "Skill(plugin:remote-skill)",
                    "Skill(sablier:effect-ts)",
                ]
            }
        }
        result = sync_global_settings.extract_plugin_skills(config)
        assert "Skill(plugin:remote-skill)" in result
        assert "Skill(sablier:effect-ts)" in result
        assert "Skill(local-skill)" not in result

    def test_handles_empty_config(self):
        """Test handling empty configuration."""
        result = sync_global_settings.extract_plugin_skills({})
        assert result == []

    def test_handles_missing_permissions(self):
        """Test handling config without permissions key."""
        result = sync_global_settings.extract_plugin_skills({"other": "key"})
        assert result == []


class TestMergeAndDedupeSkills:
    """Test merge_and_dedupe_skills() function."""

    def test_merges_and_sorts(self):
        """Test merging and sorting skills."""
        local = ["Skill(z-skill)", "Skill(a-skill)"]
        plugin = ["Skill(m-skill)"]
        result = sync_global_settings.merge_and_dedupe_skills(local, plugin)
        assert result == ["Skill(a-skill)", "Skill(m-skill)", "Skill(z-skill)"]

    def test_deduplicates(self):
        """Test removing duplicates."""
        local = ["Skill(shared)", "Skill(local)"]
        plugin = ["Skill(shared)", "Skill(plugin)"]
        result = sync_global_settings.merge_and_dedupe_skills(local, plugin)
        assert result.count("Skill(shared)") == 1

    def test_handles_empty_lists(self):
        """Test handling empty input lists."""
        result = sync_global_settings.merge_and_dedupe_skills([], [])
        assert result == []


class TestBuildSkillsJsonc:
    """Test build_skills_jsonc() function."""

    def test_includes_schema_and_comment(self):
        """Test output includes schema and comment."""
        skills = ["Skill(test)"]
        result = sync_global_settings.build_skills_jsonc(skills)
        assert "// Skills and commands" in result
        assert "$schema" in result
        assert "https://json.schemastore.org/claude-code-settings.json" in result

    def test_includes_all_skills(self):
        """Test all skills are included in output."""
        skills = ["Skill(a)", "Skill(b)"]
        result = sync_global_settings.build_skills_jsonc(skills)
        assert '"Skill(a)"' in result
        assert '"Skill(b)"' in result


class TestSyncSkills:
    """Test sync_skills() function."""

    @patch.object(sync_global_settings, "SKILLS_SETTINGS")
    def test_returns_false_when_settings_missing(self, mock_path):
        """Test returning False when skills.jsonc doesn't exist."""
        mock_path.exists.return_value = False
        result = sync_global_settings.sync_skills()
        assert result is False

    @patch.object(sync_global_settings, "SKILLS_SETTINGS")
    @patch.object(sync_global_settings, "CLAUDE_DIR", Path("/fake"))
    @patch("sync_global_settings.discover_skills")
    @patch("sync_global_settings.read_jsonc")
    @patch("pathlib.Path.cwd")
    def test_syncs_skills_successfully(self, mock_cwd, mock_read, mock_discover, mock_settings):
        """Test successful skill synchronization."""
        mock_settings.exists.return_value = True
        mock_settings.write_text = MagicMock()
        mock_discover.return_value = ["Skill(local)"]
        mock_read.return_value = {"permissions": {"allow": ["Skill(plugin:remote)"]}}
        mock_cwd.return_value = Path("/project")

        result = sync_global_settings.sync_skills()

        assert result is True
        mock_settings.write_text.assert_called_once()


class TestDiscoverCommands:
    """Test discover_commands() function."""

    @patch("pathlib.Path.glob")
    @patch("pathlib.Path.exists")
    def test_finds_commands_with_md_files(self, mock_exists, mock_glob):
        """Test discovering commands from .md files."""
        mock_exists.return_value = True
        mock_cmd1 = MagicMock()
        mock_cmd1.stem = "commit"
        mock_cmd2 = MagicMock()
        mock_cmd2.stem = "create-pr"
        mock_glob.return_value = [mock_cmd1, mock_cmd2]

        result = sync_global_settings.discover_commands(Path("/fake/commands"))

        assert "Skill(commit)" in result
        assert "Skill(create-pr)" in result

    @patch("pathlib.Path.exists")
    def test_returns_empty_for_missing_directory(self, mock_exists):
        """Test returning empty list when directory doesn't exist."""
        mock_exists.return_value = False
        result = sync_global_settings.discover_commands(Path("/nonexistent"))
        assert result == []


class TestReadPluginsFromRoot:
    """Test read_plugins_from_root() function."""

    @patch.object(sync_global_settings, "ROOT_SETTINGS")
    def test_returns_empty_when_file_missing(self, mock_path):
        """Test returning empty dict when settings.json doesn't exist."""
        mock_path.exists.return_value = False
        result = sync_global_settings.read_plugins_from_root()
        assert result == {}

    @patch.object(sync_global_settings, "ROOT_SETTINGS")
    def test_reads_enabled_plugins(self, mock_path):
        """Test reading enabledPlugins from settings.json."""
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps(
            {"enabledPlugins": {"plugin-a": True, "plugin-b": False}}
        )
        result = sync_global_settings.read_plugins_from_root()
        assert result == {"plugin-a": True, "plugin-b": False}


class TestMergePlugins:
    """Test merge_plugins() function."""

    def test_local_wins_on_conflict(self):
        """Test that local plugins override root on conflict."""
        root = {"shared": False, "root-only": True}
        local = {"shared": True, "local-only": True}
        result = sync_global_settings.merge_plugins(root, local)
        assert result["shared"] is True  # Local wins

    def test_includes_all_plugins(self):
        """Test all plugins from both sources are included."""
        root = {"a": True}
        local = {"b": True}
        result = sync_global_settings.merge_plugins(root, local)
        assert "a" in result
        assert "b" in result

    def test_sorts_by_key(self):
        """Test output is sorted alphabetically."""
        root = {"z-plugin": True}
        local = {"a-plugin": True}
        result = sync_global_settings.merge_plugins(root, local)
        keys = list(result.keys())
        assert keys == ["a-plugin", "z-plugin"]


class TestSyncPlugins:
    """Test sync_plugins() function."""

    @patch.object(sync_global_settings, "ROOT_SETTINGS")
    @patch.object(sync_global_settings, "PLUGINS_SETTINGS")
    def test_returns_false_when_files_missing(self, mock_plugins, mock_root):
        """Test returning False when required files don't exist."""
        mock_root.exists.return_value = False
        mock_plugins.exists.return_value = True
        result = sync_global_settings.sync_plugins()
        assert result is False

    @patch.object(sync_global_settings, "PLUGINS_SETTINGS")
    @patch.object(sync_global_settings, "ROOT_SETTINGS")
    @patch("sync_global_settings.read_plugins_from_root")
    @patch("sync_global_settings.read_plugins_from_local")
    def test_syncs_plugins_successfully(
        self, mock_local, mock_root_plugins, mock_root, mock_plugins
    ):
        """Test successful plugin synchronization."""
        mock_root.exists.return_value = True
        mock_plugins.exists.return_value = True
        mock_plugins.write_text = MagicMock()
        mock_root_plugins.return_value = {"plugin-a": True}
        mock_local.return_value = {"plugin-b": True}

        result = sync_global_settings.sync_plugins()

        assert result is True
        mock_plugins.write_text.assert_called_once()


class TestRunMergeSettings:
    """Test run_merge_settings() function."""

    @patch.object(sync_global_settings, "MERGE_SCRIPT")
    def test_returns_false_when_script_missing(self, mock_path):
        """Test returning False when merge script doesn't exist."""
        mock_path.exists.return_value = False
        result = sync_global_settings.run_merge_settings()
        assert result is False

    @patch("subprocess.run")
    @patch.object(sync_global_settings, "MERGE_SCRIPT")
    def test_runs_script_successfully(self, mock_path, mock_run):
        """Test running merge script successfully."""
        mock_path.exists.return_value = True
        mock_path.__str__ = MagicMock(return_value="/fake/merge.sh")
        mock_run.return_value = MagicMock(returncode=0)

        result = sync_global_settings.run_merge_settings()

        assert result is True
        mock_run.assert_called_once()

    @patch("subprocess.run")
    @patch.object(sync_global_settings, "MERGE_SCRIPT")
    def test_handles_timeout(self, mock_path, mock_run):
        """Test handling script timeout gracefully."""
        mock_path.exists.return_value = True
        mock_run.side_effect = subprocess.TimeoutExpired("script", 30)

        result = sync_global_settings.run_merge_settings()

        assert result is False


class TestFormatWithBiome:
    """Test format_with_biome() function."""

    @patch.object(sync_global_settings, "CLAUDE_DIR", Path("/home/dev/.claude"))
    @patch("subprocess.run")
    def test_formats_with_relative_path_in_claude_dir(self, mock_run):
        """Test formatting with relative paths for include matching."""
        mock_run.return_value = MagicMock(returncode=0)

        result = sync_global_settings.format_with_biome(Path("/home/dev/.claude/settings.json"))

        assert result is True
        expected_cwd = Path("/home/dev/.claude").resolve()
        mock_run.assert_called_once_with(
            ["biome", "format", "--write", "settings.json"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=expected_cwd,
        )

    @patch.object(sync_global_settings, "CLAUDE_DIR", Path("/home/dev/.claude"))
    @patch("subprocess.run")
    def test_returns_false_on_nonzero_exit(self, mock_run):
        """Test returning False when biome exits with failure."""
        mock_run.return_value = MagicMock(returncode=1)

        result = sync_global_settings.format_with_biome(Path("/home/dev/.claude/settings.json"))

        assert result is False


class TestMain:
    """Test main() entry point."""

    @patch("sync_global_settings.run_merge_settings")
    @patch("sync_global_settings.sync_plugins")
    @patch("sync_global_settings.sync_skills")
    def test_runs_all_sync_operations(self, mock_skills, mock_plugins, mock_merge):
        """Test that main runs all sync operations."""
        mock_skills.return_value = True
        mock_plugins.return_value = True
        mock_merge.return_value = True

        with pytest.raises(SystemExit) as exc_info:
            sync_global_settings.main()

        assert exc_info.value.code == 0
        mock_skills.assert_called_once()
        mock_plugins.assert_called_once()
        mock_merge.assert_called_once()

    @patch("sync_global_settings.run_merge_settings")
    @patch("sync_global_settings.sync_plugins")
    @patch("sync_global_settings.sync_skills")
    def test_continues_on_skill_sync_failure(self, mock_skills, mock_plugins, mock_merge):
        """Test that main continues even if skill sync fails."""
        mock_skills.return_value = False
        mock_plugins.return_value = True
        mock_merge.return_value = True

        with pytest.raises(SystemExit) as exc_info:
            sync_global_settings.main()

        assert exc_info.value.code == 0
        mock_plugins.assert_called_once()
        mock_merge.assert_called_once()

    @patch("sync_global_settings.run_merge_settings")
    @patch("sync_global_settings.sync_plugins")
    @patch("sync_global_settings.sync_skills")
    def test_always_exits_zero(self, mock_skills, mock_plugins, mock_merge):
        """Test graceful exit even when all operations fail."""
        mock_skills.return_value = False
        mock_plugins.return_value = False
        mock_merge.return_value = False

        with pytest.raises(SystemExit) as exc_info:
            sync_global_settings.main()

        assert exc_info.value.code == 0
