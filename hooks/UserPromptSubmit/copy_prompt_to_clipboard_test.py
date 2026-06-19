#!/usr/bin/env python3
"""Unit tests for copy_prompt_to_clipboard.py hook."""

import json
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

import copy_prompt_to_clipboard as hook


class TestSanitizePrompt:
    """Test sanitize_prompt() and its pipeline."""

    def test_preserves_normal_prompt(self):
        """Test that ordinary prose (incl. markdown) passes through untouched."""
        assert hook.sanitize_prompt("hello **world**") == "hello **world**"

    def test_preserves_non_ascii(self):
        """Test that non-ASCII text survives sanitization unchanged."""
        assert hook.sanitize_prompt("café — 日本語 → ✓") == "café — 日本語 → ✓"

    def test_normalizes_pasted_text_marker(self):
        """Test that a Pasted text marker becomes the word Pasted."""
        assert hook.sanitize_prompt("[Pasted text #1 +50 lines]") == "Pasted"

    def test_normalizes_image_marker(self):
        """Test that an Image marker becomes the word Pasted."""
        assert hook.sanitize_prompt("see [Image #2] here") == "see Pasted here"

    def test_normalizes_truncated_marker(self):
        """Test that a Truncated text marker is normalized."""
        assert hook.sanitize_prompt("[...Truncated text #3 +9 lines...]") == "Pasted"

    def test_strips_triple_backtick_fence(self):
        """Test that a complete triple-backtick fence collapses to [code]."""
        result = hook.sanitize_prompt("before\n```ts\nconst x = 1;\n```\nafter")
        assert result == "before\n[code]\nafter"
        assert "const x" not in result

    def test_strips_quad_backtick_fence(self):
        """Test that a quad-backtick fence wrapping inner fences collapses once."""
        result = hook.sanitize_prompt("````md\n```\nnested\n```\n````")
        assert result == "[code]"
        assert "nested" not in result

    def test_strips_unterminated_fence(self):
        """Test that an unterminated fence collapses from the fence to EOF."""
        result = hook.sanitize_prompt("see this:\n```python\nimport os\nprint(os)")
        assert result == "see this:\n[code]"
        assert "import os" not in result

    def test_collapses_long_line(self):
        """Test that a single over-long line becomes [Pasted]."""
        long_line = "x" * (hook.LONG_LINE_CHARS + 1)
        assert hook.sanitize_prompt(long_line) == "[Pasted]"

    def test_collapses_over_cap_prompt(self):
        """Test that a prompt with too many lines keeps a bounded head."""
        prompt = "\n".join(f"line{i}" for i in range(50))
        result = hook.sanitize_prompt(prompt)
        assert result.endswith("[Pasted]")
        assert "line0" in result
        assert "line20" not in result  # head is the first MAX_LINES (20) lines
        assert "line49" not in result

    def test_squeezes_blank_lines(self):
        """Test that runs of 3+ newlines collapse to a single blank line."""
        assert hook.sanitize_prompt("a\n\n\n\n\nb") == "a\n\nb"

    def test_empty_after_sanitize_returns_empty(self):
        """Test that whitespace-only input sanitizes to an empty string."""
        assert hook.sanitize_prompt("   \n\n   ") == ""


class TestMain:
    """Test main() entry point."""

    @patch("subprocess.run")
    @patch("sys.stdin", new_callable=StringIO)
    def test_copies_sanitized_prompt(self, mock_stdin, mock_run):
        """Test that the sanitized prompt is piped to pbcopy."""
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        mock_stdin.write(json.dumps({"prompt": "hello world"}))
        mock_stdin.seek(0)

        with pytest.raises(SystemExit) as exc_info:
            hook.main()

        assert exc_info.value.code == 0
        mock_run.assert_called_once()
        assert mock_run.call_args.args[0] == [hook.PBCOPY]
        assert mock_run.call_args.kwargs["input"] == "hello world"

    @patch("subprocess.run")
    @patch("sys.stdin", new_callable=StringIO)
    def test_writes_nothing_to_stdout(self, mock_stdin, mock_run, capsys):
        """Test stdout discipline — the hook must emit nothing on stdout."""
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        mock_stdin.write(json.dumps({"prompt": "hello world"}))
        mock_stdin.seek(0)

        with pytest.raises(SystemExit):
            hook.main()

        assert capsys.readouterr().out == ""

    @patch("subprocess.run")
    @patch("sys.stdin", new_callable=StringIO)
    def test_skips_pbcopy_when_empty(self, mock_stdin, mock_run):
        """Test that an empty-after-sanitize prompt does not touch the clipboard."""
        mock_stdin.write(json.dumps({"prompt": "   "}))
        mock_stdin.seek(0)

        with pytest.raises(SystemExit) as exc_info:
            hook.main()

        assert exc_info.value.code == 0
        mock_run.assert_not_called()

    @patch("subprocess.run")
    @patch("sys.stdin", new_callable=StringIO)
    def test_skips_pbcopy_when_prompt_missing(self, mock_stdin, mock_run):
        """Test that a missing prompt key is treated as empty and skipped."""
        mock_stdin.write(json.dumps({"session_id": "abc"}))
        mock_stdin.seek(0)

        with pytest.raises(SystemExit) as exc_info:
            hook.main()

        assert exc_info.value.code == 0
        mock_run.assert_not_called()

    @patch("sys.stdin", new_callable=StringIO)
    def test_exits_on_invalid_json(self, mock_stdin):
        """Test graceful exit on invalid JSON."""
        mock_stdin.write("not valid json{")
        mock_stdin.seek(0)

        with pytest.raises(SystemExit) as exc_info:
            hook.main()

        assert exc_info.value.code == 0

    @patch("subprocess.run")
    @patch("sys.stdin", new_callable=StringIO)
    def test_exits_on_non_object_json(self, mock_stdin, mock_run):
        """Test graceful exit when JSON is valid but not an object."""
        mock_stdin.write("123")
        mock_stdin.seek(0)

        with pytest.raises(SystemExit) as exc_info:
            hook.main()

        assert exc_info.value.code == 0
        mock_run.assert_not_called()

    @patch("subprocess.run")
    @patch("sys.stdin", new_callable=StringIO)
    def test_handles_pbcopy_failure(self, mock_stdin, mock_run):
        """Test graceful exit when pbcopy cannot be launched."""
        mock_run.side_effect = OSError("pbcopy not found")
        mock_stdin.write(json.dumps({"prompt": "hi"}))
        mock_stdin.seek(0)

        with pytest.raises(SystemExit) as exc_info:
            hook.main()

        assert exc_info.value.code == 0

    @patch("subprocess.run")
    @patch("sys.stdin", new_callable=StringIO)
    def test_handles_pbcopy_nonzero_exit(self, mock_stdin, mock_run):
        """Test graceful exit when pbcopy returns a non-zero status."""
        mock_run.return_value = MagicMock(returncode=1, stderr="nope")
        mock_stdin.write(json.dumps({"prompt": "hi"}))
        mock_stdin.seek(0)

        with pytest.raises(SystemExit) as exc_info:
            hook.main()

        assert exc_info.value.code == 0
