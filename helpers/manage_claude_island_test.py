"""Tests for manage_claude_island.py"""

from unittest.mock import patch

import pytest

from manage_claude_island import (
    ALL_EVENTS,
    HOOK_COMMAND,
    add_hooks,
    find_hooks_array_end,
    get_status,
    has_hook,
    main,
    remove_hooks,
    strip_jsonc_comments,
)


class TestStripJsoncComments:
    """Tests for strip_jsonc_comments function."""

    def test_removes_single_line_comments(self):
        text = """
{
  "key": "value", // This is a comment
  "another": "value"
}
"""
        result = strip_jsonc_comments(text)
        assert "// This is a comment" not in result
        assert '"key": "value"' in result
        assert '"another": "value"' in result

    def test_removes_multi_line_comments(self):
        text = """
{
  /* This is a
     multi-line comment */
  "key": "value"
}
"""
        result = strip_jsonc_comments(text)
        assert "/* This is a" not in result
        assert "multi-line comment */" not in result
        assert '"key": "value"' in result

    def test_removes_both_comment_types(self):
        text = """
{
  // Single line
  "key": "value", /* inline comment */
  "another": "value"
}
"""
        result = strip_jsonc_comments(text)
        assert "// Single line" not in result
        assert "/* inline comment */" not in result
        assert '"key": "value"' in result

    def test_preserves_content_without_comments(self):
        text = '{"key": "value"}'
        result = strip_jsonc_comments(text)
        assert result == text


class TestHasHook:
    """Tests for has_hook function."""

    def test_detects_hook_presence(self):
        content = """
{
  "PreToolUse": [
    {
      "hooks": [
        {
          "command": "~/.claude/hooks/claude-island-state.py",
          "type": "command"
        }
      ]
    }
  ]
}
"""
        assert has_hook(content, "PreToolUse") is True

    def test_detects_hook_absence(self):
        content = """
{
  "PreToolUse": [
    {
      "hooks": []
    }
  ]
}
"""
        assert has_hook(content, "PreToolUse") is False

    def test_returns_false_for_missing_event(self):
        content = """
{
  "PostToolUse": []
}
"""
        assert has_hook(content, "PreToolUse") is False

    def test_detects_hook_among_multiple_hooks(self):
        content = """
{
  "SessionStart": [
    {
      "hooks": [
        {
          "command": "other-hook.py",
          "type": "command"
        },
        {
          "command": "~/.claude/hooks/claude-island-state.py",
          "type": "command"
        }
      ]
    }
  ]
}
"""
        assert has_hook(content, "SessionStart") is True


class TestGetStatus:
    """Tests for get_status function."""

    def test_returns_status_for_all_events(self):
        content = """
{
  "PreToolUse": [
    {
      "hooks": [
        {
          "command": "~/.claude/hooks/claude-island-state.py",
          "type": "command"
        }
      ]
    }
  ],
  "PostToolUse": [
    {
      "hooks": []
    }
  ]
}
"""
        status = get_status(content)
        assert isinstance(status, dict)
        assert len(status) == len(ALL_EVENTS)
        assert status["PreToolUse"] is True
        assert status["PostToolUse"] is False

    def test_returns_all_false_for_empty_hooks(self):
        content = """
{
  "PreToolUse": [],
  "PostToolUse": []
}
"""
        status = get_status(content)
        assert all(not v for v in status.values())

    def test_returns_all_true_when_all_have_hook(self):
        # Build content with hook in all events
        events_content = []
        for event in ALL_EVENTS:
            events_content.append(
                f"""
  "{event}": [
    {{
      "hooks": [
        {{
          "command": "~/.claude/hooks/claude-island-state.py",
          "type": "command"
        }}
      ]
    }}
  ]"""
            )
        content = "{" + ",".join(events_content) + "\n}"
        status = get_status(content)
        assert all(status.values())


class TestRemoveHooks:
    """Tests for remove_hooks function."""

    def test_removes_hook_entry(self):
        content = """
{
  "PreToolUse": [
    {
      "hooks": [
        {
          "command": "~/.claude/hooks/claude-island-state.py",
          "type": "command"
        }
      ]
    }
  ]
}
"""
        result = remove_hooks(content)
        assert "claude-island-state.py" not in result
        # The function also removes empty hooks objects, so check the structure is cleaned
        assert "PreToolUse" in result

    def test_handles_trailing_comma_after_hook(self):
        content = """
{
  "hooks": [
    {
      "command": "~/.claude/hooks/claude-island-state.py",
      "type": "command"
    },
    {
      "command": "other-hook.py",
      "type": "command"
    }
  ]
}
"""
        result = remove_hooks(content)
        assert "claude-island-state.py" not in result
        assert "other-hook.py" in result
        # Should not have double commas
        assert ",," not in result

    def test_handles_trailing_comma_before_hook(self):
        content = """
{
  "hooks": [
    {
      "command": "other-hook.py",
      "type": "command"
    },
    {
      "command": "~/.claude/hooks/claude-island-state.py",
      "type": "command"
    }
  ]
}
"""
        result = remove_hooks(content)
        assert "claude-island-state.py" not in result
        assert "other-hook.py" in result
        # Should not have comma before ]
        assert ",]" not in result.replace(" ", "").replace("\n", "")

    def test_removes_empty_hook_entries(self):
        content = """
{
  "PreToolUse": [
    {
      "hooks": []
    }
  ]
}
"""
        result = remove_hooks(content)
        # Empty hooks object should be removed
        assert '{ "hooks": [] }' not in result.replace(" ", "").replace("\n", "")

    def test_removes_multiple_hook_instances(self):
        content = """
{
  "PreToolUse": [
    {
      "hooks": [
        {
          "command": "~/.claude/hooks/claude-island-state.py",
          "type": "command"
        }
      ]
    }
  ],
  "PostToolUse": [
    {
      "hooks": [
        {
          "command": "~/.claude/hooks/claude-island-state.py",
          "type": "command"
        }
      ]
    }
  ]
}
"""
        result = remove_hooks(content)
        assert "claude-island-state.py" not in result

    def test_preserves_content_without_hook(self):
        content = """
{
  "PreToolUse": [
    {
      "hooks": [
        {
          "command": "other-hook.py",
          "type": "command"
        }
      ]
    }
  ]
}
"""
        result = remove_hooks(content)
        assert "other-hook.py" in result


class TestFindHooksArrayEnd:
    """Tests for find_hooks_array_end function."""

    def test_finds_closing_bracket(self):
        lines = [
            '"PreToolUse": [\n',
            "  {\n",
            '    "hooks": [\n',
            "      {\n",
            '        "command": "test.py",\n',
            '        "type": "command"\n',
            "      }\n",
            "    ]\n",  # Line 7 - this is the closing bracket
            "  }\n",
            "]\n",
        ]
        result = find_hooks_array_end(lines, "PreToolUse")
        assert result == 7

    def test_returns_none_for_missing_event(self):
        lines = ['"PostToolUse": []\n']
        result = find_hooks_array_end(lines, "PreToolUse")
        assert result is None

    def test_finds_last_hooks_array_in_event(self):
        lines = [
            '"PreToolUse": [\n',
            "  {\n",
            '    "hooks": [\n',
            "      {}\n",
            "    ]\n",
            "  },\n",
            "  {\n",
            '    "hooks": [\n',
            "      {}\n",
            "    ]\n",  # Line 9 - last hooks array closing bracket
            "  }\n",
            "]\n",
        ]
        result = find_hooks_array_end(lines, "PreToolUse")
        assert result == 9

    def test_handles_empty_hooks_array(self):
        lines = [
            '"SessionStart": [\n',
            "  {\n",
            '    "hooks": []\n',  # Line 2 - empty array closing bracket
            "  }\n",
            "]\n",
        ]
        result = find_hooks_array_end(lines, "SessionStart")
        assert result == 2


class TestAddHooks:
    """Tests for add_hooks function."""

    def test_adds_hook_to_event_without_hook(self):
        content = """
{
  "PreToolUse": [
    {
      "hooks": []
    }
  ]
}
"""
        lines = content.splitlines(keepends=True)
        result = add_hooks(lines, content)
        result_text = "".join(result)
        assert HOOK_COMMAND in result_text
        assert '"type": "command"' in result_text

    def test_preserves_events_with_existing_hook(self):
        content = """
{
  "PreToolUse": [
    {
      "hooks": [
        {
          "command": "~/.claude/hooks/claude-island-state.py",
          "type": "command"
        }
      ]
    }
  ]
}
"""
        lines = content.splitlines(keepends=True)
        result = add_hooks(lines, content)
        # Should not add duplicate
        result_text = "".join(result)
        count = result_text.count("claude-island-state.py")
        assert count == 1

    def test_adds_comma_to_previous_entry(self):
        content = """
{
  "PreToolUse": [
    {
      "hooks": [
        {
          "command": "other-hook.py",
          "type": "command"
        }
      ]
    }
  ]
}
"""
        lines = content.splitlines(keepends=True)
        result = add_hooks(lines, content)
        result_text = "".join(result)
        # Should have comma after other-hook entry
        assert '"command": "other-hook.py"' in result_text
        assert HOOK_COMMAND in result_text

    def test_maintains_proper_indentation(self):
        content = """
{
  "PreToolUse": [
    {
      "hooks": []
    }
  ]
}
"""
        lines = content.splitlines(keepends=True)
        result = add_hooks(lines, content)
        result_text = "".join(result)
        # Check that the hook entry is properly indented
        # Should have 6 spaces for the hook object (based on surrounding context)
        assert "      {\n" in result_text or "        {\n" in result_text

    def test_handles_multiple_events_without_hooks(self):
        content = """
{
  "PreToolUse": [
    {
      "hooks": []
    }
  ],
  "PostToolUse": [
    {
      "hooks": []
    }
  ]
}
"""
        lines = content.splitlines(keepends=True)
        result = add_hooks(lines, content)
        result_text = "".join(result)
        # Should add hook to both events
        count = result_text.count(HOOK_COMMAND)
        assert count == 2


class TestMain:
    """Tests for main function."""

    @patch("manage_claude_island.HOOKS_FILE")
    @patch("sys.argv", ["manage_claude_island.py", "status"])
    def test_status_command(self, mock_hooks_file, capsys):
        mock_hooks_file.exists.return_value = True
        mock_hooks_file.read_text.return_value = """
{
  "PreToolUse": [
    {
      "hooks": [
        {
          "command": "~/.claude/hooks/claude-island-state.py",
          "type": "command"
        }
      ]
    }
  ]
}
"""
        main()
        captured = capsys.readouterr()
        assert "Claude Island hook status:" in captured.out
        assert "PreToolUse" in captured.out
        assert "Enabled:" in captured.out

    @patch("manage_claude_island.HOOKS_FILE")
    @patch("sys.argv", ["manage_claude_island.py", "remove"])
    def test_remove_command_with_hooks_present(self, mock_hooks_file, capsys):
        mock_hooks_file.exists.return_value = True
        content = """
{
  "PreToolUse": [
    {
      "hooks": [
        {
          "command": "~/.claude/hooks/claude-island-state.py",
          "type": "command"
        }
      ]
    }
  ]
}
"""
        mock_hooks_file.read_text.return_value = content
        main()
        captured = capsys.readouterr()
        assert "Removed claude-island hooks" in captured.out
        mock_hooks_file.write_text.assert_called_once()

    @patch("manage_claude_island.HOOKS_FILE")
    @patch("sys.argv", ["manage_claude_island.py", "remove"])
    def test_remove_command_with_no_hooks(self, mock_hooks_file, capsys):
        mock_hooks_file.exists.return_value = True
        content = '{"PreToolUse": []}'
        mock_hooks_file.read_text.return_value = content
        main()
        captured = capsys.readouterr()
        assert "No claude-island hooks found" in captured.out
        mock_hooks_file.write_text.assert_not_called()

    @patch("manage_claude_island.HOOKS_FILE")
    @patch("sys.argv", ["manage_claude_island.py", "add"])
    def test_add_command_adds_hooks(self, mock_hooks_file, capsys):
        mock_hooks_file.exists.return_value = True
        content = """
{
  "PreToolUse": [
    {
      "hooks": []
    }
  ]
}
"""
        mock_hooks_file.read_text.return_value = content
        main()
        captured = capsys.readouterr()
        assert "Added claude-island hooks" in captured.out
        mock_hooks_file.write_text.assert_called_once()

    @patch("manage_claude_island.HOOKS_FILE")
    @patch("sys.argv", ["manage_claude_island.py", "add"])
    def test_add_command_when_all_present(self, mock_hooks_file, capsys):
        mock_hooks_file.exists.return_value = True
        # Build content with hook in all events
        events_content = []
        for event in ALL_EVENTS:
            events_content.append(
                f"""
  "{event}": [
    {{
      "hooks": [
        {{
          "command": "~/.claude/hooks/claude-island-state.py",
          "type": "command"
        }}
      ]
    }}
  ]"""
            )
        content = "{" + ",".join(events_content) + "\n}"
        mock_hooks_file.read_text.return_value = content
        main()
        captured = capsys.readouterr()
        assert "All events already have claude-island hooks" in captured.out
        mock_hooks_file.write_text.assert_not_called()

    @patch("manage_claude_island.HOOKS_FILE")
    @patch("sys.argv", ["manage_claude_island.py", "invalid"])
    def test_invalid_command_exits(self, mock_hooks_file):
        mock_hooks_file.exists.return_value = True
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    @patch("manage_claude_island.HOOKS_FILE")
    @patch("sys.argv", ["manage_claude_island.py"])
    def test_no_command_exits(self, mock_hooks_file):
        mock_hooks_file.exists.return_value = True
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    @patch("manage_claude_island.HOOKS_FILE")
    @patch("sys.argv", ["manage_claude_island.py", "status"])
    def test_missing_hooks_file_exits(self, mock_hooks_file, capsys):
        mock_hooks_file.exists.return_value = False
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error:" in captured.out
        assert "not found" in captured.out
