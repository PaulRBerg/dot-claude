#!/usr/bin/env python3
"""Unit tests for detect_flags.py hook."""

import importlib.util
import io
import json
import sys
from pathlib import Path
from unittest.mock import mock_open

import pytest

# Dynamically import the detect_flags module
hook_path = Path(__file__).parent / "detect_flags.py"
spec = importlib.util.spec_from_file_location("detect_flags", hook_path)
detect_flags = importlib.util.module_from_spec(spec)
sys.modules["detect_flags"] = detect_flags
spec.loader.exec_module(detect_flags)


# ============================================================================
# Test parse_trailing_flags
# ============================================================================


class TestParseTrailingFlags:
    """Test the parse_trailing_flags function."""

    @pytest.mark.parametrize(
        "prompt,expected",
        [
            # Valid single flags
            ("my task -s", ("my task", ["s"])),
            ("my task -c", ("my task", ["c"])),
            ("my task -t", ("my task", ["t"])),
            ("my task -d", ("my task", ["d"])),
            ("my task -n", ("my task", ["n"])),
            # Valid multiple flags
            ("my task -s -c", ("my task", ["s", "c"])),
            ("my task -t -d -n", ("my task", ["t", "d", "n"])),
            ("my task -s -c -t -d -n", ("my task", ["s", "c", "t", "d", "n"])),
            # With extra whitespace
            ("my task  -s  -c", ("my task", ["s", "c"])),
            ("my task -s  ", ("my task", ["s"])),
            ("  my task -s", ("my task", ["s"])),
            # Complex prompts
            ("complex task with many words -s -c", ("complex task with many words", ["s", "c"])),
        ],
    )
    def test_valid_flags(self, prompt, expected):
        """Test parsing of valid flag patterns."""
        result = detect_flags.parse_trailing_flags(prompt)
        assert result == expected

    @pytest.mark.parametrize(
        "prompt",
        [
            # No flags
            "my task",
            "my task with no flags",
            "",
            "   ",
            # Flags in wrong position
            "-s my task",
            "my -s task",
            "my task -s more text",
            # Invalid flag format
            "my task -",
            "my task - s",
            "my task --s",
            "my task -S",  # uppercase
            "my task -1",  # number
            # No text before flags
            "-s",
        ],
    )
    def test_no_match(self, prompt):
        """Test cases where no flags should be detected."""
        result = detect_flags.parse_trailing_flags(prompt)
        assert result is None

    def test_flags_only_matches_as_valid(self):
        """Test that flags-only input (e.g., '-s -c') does match the pattern.

        This is a quirk of the regex - the first flag becomes the 'prompt'
        and remaining flags are parsed as flags. While unusual, this is
        acceptable behavior and will be filtered out by validation if needed.
        """
        result = detect_flags.parse_trailing_flags("-s -c")
        # This matches with "-s" as prompt and ["c"] as flags
        assert result is not None
        assert result[0] == "-s"
        assert result[1] == ["c"]


# ============================================================================
# Test validate_flags
# ============================================================================


class TestValidateFlags:
    """Test the validate_flags function."""

    @pytest.mark.parametrize(
        "flags",
        [
            ["s"],
            ["c"],
            ["t"],
            ["d"],
            ["n"],
            ["s", "c"],
            ["s", "c", "t", "d", "n"],
            [],  # empty list is valid (all flags are recognized)
        ],
    )
    def test_valid_flags(self, flags):
        """Test validation of recognized flags."""
        assert detect_flags.validate_flags(flags) is True

    @pytest.mark.parametrize(
        "flags",
        [
            ["x"],
            ["s", "x"],
            ["s", "c", "invalid"],
            ["S"],  # uppercase
            ["1"],  # number
        ],
    )
    def test_invalid_flags(self, flags):
        """Test validation of unrecognized flags."""
        assert detect_flags.validate_flags(flags) is False


# ============================================================================
# Test wrap_in_xml_tag
# ============================================================================


class TestWrapInXmlTag:
    """Test the wrap_in_xml_tag function."""

    def test_simple_tag(self):
        """Test wrapping content with a simple tag."""
        result = detect_flags.wrap_in_xml_tag("test", "content")
        assert result == "<test>\ncontent\n</test>"

    def test_multiline_content(self):
        """Test wrapping multiline content."""
        content = "line 1\nline 2\nline 3"
        result = detect_flags.wrap_in_xml_tag("instructions", content)
        assert result == "<instructions>\nline 1\nline 2\nline 3\n</instructions>"

    def test_empty_content(self):
        """Test wrapping empty content."""
        result = detect_flags.wrap_in_xml_tag("empty", "")
        assert result == "<empty>\n\n</empty>"

    def test_content_with_special_characters(self):
        """Test wrapping content with special characters."""
        content = "IMPORTANT: Use the /commit command"
        result = detect_flags.wrap_in_xml_tag("commit_instructions", content)
        assert result == "<commit_instructions>\nIMPORTANT: Use the /commit command\n</commit_instructions>"


# ============================================================================
# Test individual flag handlers
# ============================================================================


class TestFlagHandlers:
    """Test individual flag handler functions."""

    def test_handle_commit_flag(self, tmp_path):
        """Test the commit flag handler."""
        result = detect_flags.handle_commit_flag(tmp_path)
        assert "SlashCommand tool" in result
        assert "/commit" in result
        assert "git commit" in result

    def test_handle_test_flag(self, tmp_path):
        """Test the test flag handler."""
        result = detect_flags.handle_test_flag(tmp_path)
        assert "test coverage" in result
        assert "unit tests" in result
        assert "integration tests" in result

    def test_handle_debug_flag(self, tmp_path):
        """Test the debug flag handler."""
        result = detect_flags.handle_debug_flag(tmp_path)
        assert "Task tool" in result
        assert "debugger subagent" in result
        assert "root cause analysis" in result

    def test_handle_no_lint_flag(self, tmp_path):
        """Test the no-lint flag handler."""
        result = detect_flags.handle_no_lint_flag(tmp_path)
        assert "Do not lint" in result
        assert "type-check" in result
        assert "validation tools" in result

    def test_handle_subagent_flag_with_file(self, tmp_path):
        """Test subagent flag handler when SUBAGENTS.md exists."""
        subagents_file = tmp_path / "SUBAGENTS.md"
        subagents_content = "# Subagent Instructions\nUse subagents wisely."
        subagents_file.write_text(subagents_content)

        result = detect_flags.handle_subagent_flag(tmp_path)
        assert result == subagents_content

    def test_handle_subagent_flag_without_file(self, tmp_path, capsys):
        """Test subagent flag handler when SUBAGENTS.md is missing."""
        result = detect_flags.handle_subagent_flag(tmp_path)
        assert result == ""

        # Check warning message
        captured = capsys.readouterr()
        assert "Warning" in captured.err
        assert "SUBAGENTS.md not found" in captured.err


# ============================================================================
# Test execute_flag_handlers
# ============================================================================


class TestExecuteFlagHandlers:
    """Test the execute_flag_handlers function."""

    def test_single_flag(self, tmp_path):
        """Test executing a single flag handler."""
        flags = ["c"]
        contexts = detect_flags.execute_flag_handlers(flags, tmp_path)

        assert len(contexts) == 1
        assert "<commit_instructions>" in contexts[0]
        assert "</commit_instructions>" in contexts[0]
        assert "/commit" in contexts[0]

    def test_multiple_flags(self, tmp_path):
        """Test executing multiple flag handlers."""
        flags = ["c", "t"]
        contexts = detect_flags.execute_flag_handlers(flags, tmp_path)

        assert len(contexts) == 2
        assert any("<commit_instructions>" in ctx and "/commit" in ctx for ctx in contexts)
        assert any("<test_instructions>" in ctx and "test coverage" in ctx for ctx in contexts)

    def test_all_flags(self, tmp_path):
        """Test executing all flag handlers."""
        # Create SUBAGENTS.md for the -s flag
        subagents_file = tmp_path / "SUBAGENTS.md"
        subagents_file.write_text("Subagent content")

        flags = ["s", "c", "t", "d", "n"]
        contexts = detect_flags.execute_flag_handlers(flags, tmp_path)

        assert len(contexts) == 5
        assert any("<subagent_instructions>" in ctx and "Subagent content" in ctx for ctx in contexts)
        assert any("<commit_instructions>" in ctx and "/commit" in ctx for ctx in contexts)
        assert any("<test_instructions>" in ctx and "test coverage" in ctx for ctx in contexts)
        assert any("<debug_instructions>" in ctx and "debugger subagent" in ctx for ctx in contexts)
        assert any("<no_lint_instructions>" in ctx and "Do not lint" in ctx for ctx in contexts)

    def test_missing_subagents_file(self, tmp_path):
        """Test that missing SUBAGENTS.md doesn't break execution."""
        flags = ["s", "c"]
        contexts = detect_flags.execute_flag_handlers(flags, tmp_path)

        # Only commit context should be returned (subagent returns empty)
        assert len(contexts) == 1
        assert "<commit_instructions>" in contexts[0]
        assert "/commit" in contexts[0]

    def test_empty_flags(self, tmp_path):
        """Test executing with no flags."""
        flags = []
        contexts = detect_flags.execute_flag_handlers(flags, tmp_path)
        assert contexts == []

    def test_xml_wrapping_structure(self, tmp_path):
        """Test that all contexts are properly XML-wrapped."""
        flags = ["c", "t", "d"]
        contexts = detect_flags.execute_flag_handlers(flags, tmp_path)

        for ctx in contexts:
            # Each context should start with < and end with >
            assert ctx.startswith("<")
            assert ctx.endswith(">")
            # Each should have both opening and closing tags
            assert ctx.count("<") >= 2  # At least opening and closing
            assert ctx.count(">") >= 2


# ============================================================================
# Test build_output_context
# ============================================================================


class TestBuildOutputContext:
    """Test the build_output_context function."""

    def test_single_flag_single_context(self):
        """Test building output with single flag and context."""
        flags = ["c"]
        clean_prompt = "my task"
        flag_contexts = ["<commit_instructions>Commit instruction</commit_instructions>"]

        result = detect_flags.build_output_context(flags, clean_prompt, flag_contexts)

        assert "<flag_metadata>" in result
        assert "</flag_metadata>" in result
        assert "Processed flags -c" in result
        assert "Your actual task (without flags): my task" in result
        assert "<commit_instructions>Commit instruction</commit_instructions>" in result

    def test_multiple_flags_multiple_contexts(self):
        """Test building output with multiple flags and contexts."""
        flags = ["c", "t"]
        clean_prompt = "my task"
        flag_contexts = [
            "<commit_instructions>Commit instruction</commit_instructions>",
            "<test_instructions>Test instruction</test_instructions>"
        ]

        result = detect_flags.build_output_context(flags, clean_prompt, flag_contexts)

        assert "<flag_metadata>" in result
        assert "Processed flags -c -t" in result
        assert "Your actual task (without flags): my task" in result
        assert "</flag_metadata>" in result
        assert "<commit_instructions>Commit instruction</commit_instructions>" in result
        assert "<test_instructions>Test instruction</test_instructions>" in result

    def test_empty_contexts(self):
        """Test building output with flags but no contexts."""
        flags = ["c"]
        clean_prompt = "my task"
        flag_contexts = []

        result = detect_flags.build_output_context(flags, clean_prompt, flag_contexts)

        assert "<flag_metadata>" in result
        assert "Processed flags -c" in result
        assert "Your actual task (without flags): my task" in result
        assert "</flag_metadata>" in result

    def test_output_formatting(self):
        """Test that output is properly formatted with newlines and XML structure."""
        flags = ["c", "t"]
        clean_prompt = "my task"
        flag_contexts = [
            "<commit_instructions>Context 1</commit_instructions>",
            "<test_instructions>Context 2</test_instructions>"
        ]

        result = detect_flags.build_output_context(flags, clean_prompt, flag_contexts)

        lines = result.split("\n")
        # Should have: <flag_metadata>, Note:, Your actual task:, </flag_metadata>, blank line, contexts
        assert "<flag_metadata>" in lines[0]
        assert "Note: Processed flags" in result
        assert "Your actual task" in result
        assert "</flag_metadata>" in result

    def test_metadata_wrapping(self):
        """Test that metadata is properly wrapped in XML tags."""
        flags = ["c"]
        clean_prompt = "implement feature"
        flag_contexts = ["<commit_instructions>Test</commit_instructions>"]

        result = detect_flags.build_output_context(flags, clean_prompt, flag_contexts)

        # Extract the metadata section
        assert result.startswith("<flag_metadata>")
        metadata_end = result.index("</flag_metadata>")
        metadata_section = result[:metadata_end + len("</flag_metadata>")]

        assert "Note: Processed flags -c" in metadata_section
        assert "Your actual task (without flags): implement feature" in metadata_section


# ============================================================================
# Test main function (integration tests)
# ============================================================================


class TestMain:
    """Integration tests for the main function."""

    def test_valid_single_flag(self, monkeypatch):
        """Test main with a valid single flag."""
        input_data = {"prompt": "my task -c"}
        stdin_mock = io.StringIO(json.dumps(input_data))
        stdout_mock = io.StringIO()

        monkeypatch.setattr("sys.stdin", stdin_mock)
        monkeypatch.setattr("sys.stdout", stdout_mock)

        with pytest.raises(SystemExit) as exc_info:
            detect_flags.main()

        assert exc_info.value.code == 0

        output = json.loads(stdout_mock.getvalue())
        assert "hookSpecificOutput" in output
        assert output["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"

        context = output["hookSpecificOutput"]["additionalContext"]
        assert "<flag_metadata>" in context
        assert "</flag_metadata>" in context
        assert "<commit_instructions>" in context
        assert "</commit_instructions>" in context
        assert "/commit" in context
        assert "my task" in context

    def test_valid_multiple_flags(self, monkeypatch):
        """Test main with multiple valid flags."""
        input_data = {"prompt": "my task -s -c -t"}
        stdin_mock = io.StringIO(json.dumps(input_data))
        stdout_mock = io.StringIO()

        # Mock the file reading for SUBAGENTS.md
        subagent_content = "Subagent instructions from test"
        mock_file = mock_open(read_data=subagent_content)

        monkeypatch.setattr("sys.stdin", stdin_mock)
        monkeypatch.setattr("sys.stdout", stdout_mock)
        monkeypatch.setattr("builtins.open", mock_file)

        with pytest.raises(SystemExit) as exc_info:
            detect_flags.main()

        assert exc_info.value.code == 0

        output = json.loads(stdout_mock.getvalue())
        context = output["hookSpecificOutput"]["additionalContext"]
        assert "<flag_metadata>" in context
        assert "Processed flags -s -c -t" in context
        assert "my task" in context
        assert "</flag_metadata>" in context
        assert "<subagent_instructions>" in context
        assert "Subagent instructions from test" in context
        assert "</subagent_instructions>" in context
        assert "<commit_instructions>" in context
        assert "/commit" in context
        assert "</commit_instructions>" in context
        assert "<test_instructions>" in context
        assert "test coverage" in context
        assert "</test_instructions>" in context

    def test_no_flags(self, monkeypatch):
        """Test main with no flags in prompt."""
        input_data = {"prompt": "my task"}
        stdin_mock = io.StringIO(json.dumps(input_data))
        stdout_mock = io.StringIO()

        monkeypatch.setattr("sys.stdin", stdin_mock)
        monkeypatch.setattr("sys.stdout", stdout_mock)

        with pytest.raises(SystemExit) as exc_info:
            detect_flags.main()

        assert exc_info.value.code == 0
        assert stdout_mock.getvalue() == ""  # No output

    def test_unrecognized_flags(self, monkeypatch):
        """Test main with unrecognized flags."""
        input_data = {"prompt": "my task -x"}
        stdin_mock = io.StringIO(json.dumps(input_data))
        stdout_mock = io.StringIO()

        monkeypatch.setattr("sys.stdin", stdin_mock)
        monkeypatch.setattr("sys.stdout", stdout_mock)

        with pytest.raises(SystemExit) as exc_info:
            detect_flags.main()

        assert exc_info.value.code == 0
        assert stdout_mock.getvalue() == ""  # Exit silently

    def test_empty_prompt(self, monkeypatch):
        """Test main with empty prompt."""
        input_data = {"prompt": ""}
        stdin_mock = io.StringIO(json.dumps(input_data))
        stdout_mock = io.StringIO()

        monkeypatch.setattr("sys.stdin", stdin_mock)
        monkeypatch.setattr("sys.stdout", stdout_mock)

        with pytest.raises(SystemExit) as exc_info:
            detect_flags.main()

        assert exc_info.value.code == 0
        assert stdout_mock.getvalue() == ""  # No output

    def test_missing_prompt_field(self, monkeypatch):
        """Test main with missing prompt field."""
        input_data = {"other_field": "value"}
        stdin_mock = io.StringIO(json.dumps(input_data))
        stdout_mock = io.StringIO()

        monkeypatch.setattr("sys.stdin", stdin_mock)
        monkeypatch.setattr("sys.stdout", stdout_mock)

        with pytest.raises(SystemExit) as exc_info:
            detect_flags.main()

        assert exc_info.value.code == 0
        assert stdout_mock.getvalue() == ""  # No output

    def test_invalid_json_input(self, monkeypatch, capsys):
        """Test main with invalid JSON input."""
        stdin_mock = io.StringIO("not valid json")
        monkeypatch.setattr("sys.stdin", stdin_mock)

        with pytest.raises(SystemExit) as exc_info:
            detect_flags.main()

        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Error: Invalid JSON input" in captured.err

    def test_all_recognized_flags(self, monkeypatch):
        """Test main with all recognized flags."""
        input_data = {"prompt": "my task -s -c -t -d -n"}
        stdin_mock = io.StringIO(json.dumps(input_data))
        stdout_mock = io.StringIO()

        # Mock the file reading for SUBAGENTS.md
        subagent_content = "Subagent test content"
        mock_file = mock_open(read_data=subagent_content)

        monkeypatch.setattr("sys.stdin", stdin_mock)
        monkeypatch.setattr("sys.stdout", stdout_mock)
        monkeypatch.setattr("builtins.open", mock_file)

        with pytest.raises(SystemExit) as exc_info:
            detect_flags.main()

        assert exc_info.value.code == 0

        output = json.loads(stdout_mock.getvalue())
        context = output["hookSpecificOutput"]["additionalContext"]

        # Verify all flags are processed with XML wrapping
        assert "<flag_metadata>" in context
        assert "Processed flags -s -c -t -d -n" in context
        assert "</flag_metadata>" in context
        assert "<subagent_instructions>" in context
        assert "Subagent test content" in context
        assert "</subagent_instructions>" in context
        assert "<commit_instructions>" in context
        assert "/commit" in context
        assert "</commit_instructions>" in context
        assert "<test_instructions>" in context
        assert "test coverage" in context
        assert "</test_instructions>" in context
        assert "<debug_instructions>" in context
        assert "debugger subagent" in context
        assert "</debug_instructions>" in context
        assert "<no_lint_instructions>" in context
        assert "Do not lint" in context
        assert "</no_lint_instructions>" in context

    def test_output_json_structure(self, monkeypatch):
        """Test that output JSON has the correct structure."""
        input_data = {"prompt": "my task -c"}
        stdin_mock = io.StringIO(json.dumps(input_data))
        stdout_mock = io.StringIO()

        monkeypatch.setattr("sys.stdin", stdin_mock)
        monkeypatch.setattr("sys.stdout", stdout_mock)

        with pytest.raises(SystemExit) as exc_info:
            detect_flags.main()

        assert exc_info.value.code == 0

        output = json.loads(stdout_mock.getvalue())

        # Verify JSON structure
        assert "hookSpecificOutput" in output
        assert "hookEventName" in output["hookSpecificOutput"]
        assert "additionalContext" in output["hookSpecificOutput"]
        assert output["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
        assert isinstance(output["hookSpecificOutput"]["additionalContext"], str)

    def test_xml_structure_integrity(self, monkeypatch):
        """Test that the entire XML structure is well-formed."""
        input_data = {"prompt": "my task -c -t"}
        stdin_mock = io.StringIO(json.dumps(input_data))
        stdout_mock = io.StringIO()

        monkeypatch.setattr("sys.stdin", stdin_mock)
        monkeypatch.setattr("sys.stdout", stdout_mock)

        with pytest.raises(SystemExit) as exc_info:
            detect_flags.main()

        assert exc_info.value.code == 0

        output = json.loads(stdout_mock.getvalue())
        context = output["hookSpecificOutput"]["additionalContext"]

        # Verify all opening tags have matching closing tags
        assert context.count("<flag_metadata>") == context.count("</flag_metadata>") == 1
        assert context.count("<commit_instructions>") == context.count("</commit_instructions>") == 1
        assert context.count("<test_instructions>") == context.count("</test_instructions>") == 1

        # Verify flag_metadata comes before instruction tags
        metadata_start = context.index("<flag_metadata>")
        metadata_end = context.index("</flag_metadata>")
        commit_start = context.index("<commit_instructions>")

        assert metadata_start < metadata_end < commit_start
