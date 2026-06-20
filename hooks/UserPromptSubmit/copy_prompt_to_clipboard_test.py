#!/usr/bin/env python3
"""Unit tests for copy_prompt_to_clipboard.py hook."""

import json
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

import copy_prompt_to_clipboard as hook

# A prompt that survives sanitization unchanged and clears MIN_CHARS (120), so it
# exercises the copy path rather than the short-prompt floor.
LONG_PROMPT = (
    "Please review the authentication refactor and confirm the session handling, "
    "token refresh, and error paths behave correctly across every supported provider "
    "before we merge this into the main branch and cut the next release."
)


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


class TestMetadataPrefix:
    """Test compact clipboard provenance metadata."""

    def test_builds_metadata_with_session_id(self):
        """Test that Claude's session_id is shortened into the prefix."""
        data = {
            "cwd": "/tmp/work/my repo/subdir",
            "session_id": "00893aaf-19fa-41d2-8238-13269b9b3ca0",
        }

        with patch.object(hook, "_git_output", side_effect=["/tmp/work/my repo", ""]):
            assert hook.build_metadata_prefix(data) == "[repo:my-repo session:00893aaf]"

    def test_prefers_remote_repo_name(self):
        """Test that git remote names beat ambiguous folder names."""
        data = {
            "cwd": "/tmp/work/.claude",
            "session_id": "00893aaf-19fa-41d2-8238-13269b9b3ca0",
        }

        with patch.object(
            hook,
            "_git_output",
            side_effect=[
                "/tmp/work/.claude",
                "git@github.com:PaulRBerg/dot-claude.git",
            ],
        ):
            assert hook.build_metadata_prefix(data) == "[repo:dot-claude session:00893aaf]"

    def test_builds_metadata_with_nested_session_id(self):
        """Test that one-level nested metadata is accepted."""
        data = {
            "cwd": "/tmp/work/demo",
            "session": {"sessionId": "claude-session-1234567890"},
        }

        with patch.object(hook, "_git_output", side_effect=["/tmp/work/demo", ""]):
            assert hook.build_metadata_prefix(data) == "[repo:demo session:claude-s]"

    def test_builds_metadata_with_transcript_path_when_session_missing(self):
        """Test transcript path stem is a useful session fallback."""
        data = {
            "cwd": "/tmp/work/demo",
            "transcript_path": "/Users/me/.claude/projects/demo/00893aaf-19fa.jsonl",
        }

        with patch.object(hook, "_git_output", side_effect=["/tmp/work/demo", ""]):
            assert hook.build_metadata_prefix(data) == "[repo:demo session:00893aaf]"

    def test_builds_metadata_with_git_ref_when_session_missing(self):
        """Test git HEAD is used when no session-like id exists."""
        data = {"cwd": "/tmp/work/demo"}

        with patch.object(
            hook,
            "_git_output",
            side_effect=["/tmp/work/demo", "", "dd66016a"],
        ):
            assert hook.build_metadata_prefix(data) == "[repo:demo ref:dd66016a]"

    def test_builds_metadata_with_path_ref_when_git_unavailable(self):
        """Test non-git directories still get a short stable reference."""
        data = {"cwd": "/tmp/work/demo"}

        with patch.object(hook, "_git_output", return_value=""):
            with patch.object(hook, "_path_reference", return_value="deadbeef"):
                assert hook.build_metadata_prefix(data) == "[repo:demo ref:deadbeef]"

    def test_formats_clipboard_prompt_with_metadata(self):
        """Test formatter prepends metadata to sanitized prompt."""
        with patch.object(
            hook,
            "build_metadata_prefix",
            return_value="[repo:demo session:00893aaf]",
        ):
            assert (
                hook.format_clipboard_prompt(LONG_PROMPT, {})
                == f"[repo:demo session:00893aaf]\n{LONG_PROMPT}"
            )

    def test_format_skips_short_prompt(self):
        """Test that prompts under MIN_CHARS are dropped before metadata."""
        with patch.object(hook, "build_metadata_prefix") as mock_prefix:
            assert hook.format_clipboard_prompt("hello **world**", {}) == ""
            mock_prefix.assert_not_called()

    def test_format_skips_metadata_when_prompt_is_empty(self):
        """Test empty prompts never build metadata or touch clipboard text."""
        with patch.object(hook, "build_metadata_prefix") as mock_prefix:
            assert hook.format_clipboard_prompt("   \n", {}) == ""
            mock_prefix.assert_not_called()


class TestMain:
    """Test main() entry point."""

    @patch("subprocess.run")
    @patch("sys.stdin", new_callable=StringIO)
    def test_copies_sanitized_prompt(self, mock_stdin, mock_run):
        """Test that the sanitized prompt is piped to pbcopy."""
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        mock_stdin.write(json.dumps({"prompt": LONG_PROMPT}))
        mock_stdin.seek(0)

        with patch.object(
            hook,
            "build_metadata_prefix",
            return_value="[repo:demo session:00893aaf]",
        ):
            with pytest.raises(SystemExit) as exc_info:
                hook.main()

        assert exc_info.value.code == 0
        mock_run.assert_called_once()
        assert mock_run.call_args.args[0] == [hook.PBCOPY]
        assert mock_run.call_args.kwargs["input"] == f"[repo:demo session:00893aaf]\n{LONG_PROMPT}"

    @patch("subprocess.run")
    @patch("sys.stdin", new_callable=StringIO)
    def test_writes_nothing_to_stdout(self, mock_stdin, mock_run, capsys):
        """Test stdout discipline — the hook must emit nothing on stdout."""
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        mock_stdin.write(json.dumps({"prompt": LONG_PROMPT}))
        mock_stdin.seek(0)

        with patch.object(
            hook,
            "build_metadata_prefix",
            return_value="[repo:demo session:00893aaf]",
        ):
            with pytest.raises(SystemExit):
                hook.main()

        assert capsys.readouterr().out == ""

    @patch("subprocess.run")
    @patch("sys.stdin", new_callable=StringIO)
    def test_skips_pbcopy_when_empty(self, mock_stdin, mock_run):
        """Test that an empty-after-sanitize prompt does not touch the clipboard."""
        mock_stdin.write(json.dumps({"prompt": "   "}))
        mock_stdin.seek(0)

        with patch.object(hook, "build_metadata_prefix") as mock_prefix:
            with pytest.raises(SystemExit) as exc_info:
                hook.main()

        assert exc_info.value.code == 0
        mock_run.assert_not_called()
        mock_prefix.assert_not_called()

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
        mock_stdin.write(json.dumps({"prompt": LONG_PROMPT}))
        mock_stdin.seek(0)

        with patch.object(
            hook,
            "build_metadata_prefix",
            return_value="[repo:demo session:00893aaf]",
        ):
            with pytest.raises(SystemExit) as exc_info:
                hook.main()

        assert exc_info.value.code == 0

    @patch("subprocess.run")
    @patch("sys.stdin", new_callable=StringIO)
    def test_handles_pbcopy_nonzero_exit(self, mock_stdin, mock_run):
        """Test graceful exit when pbcopy returns a non-zero status."""
        mock_run.return_value = MagicMock(returncode=1, stderr="nope")
        mock_stdin.write(json.dumps({"prompt": LONG_PROMPT}))
        mock_stdin.seek(0)

        with patch.object(
            hook,
            "build_metadata_prefix",
            return_value="[repo:demo session:00893aaf]",
        ):
            with pytest.raises(SystemExit) as exc_info:
                hook.main()

        assert exc_info.value.code == 0

    @patch("subprocess.run")
    @patch("sys.stdin", new_callable=StringIO)
    def test_metadata_failure_copies_sanitized_prompt(self, mock_stdin, mock_run, capsys):
        """Test provenance errors do not prevent copying the prompt."""
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        mock_stdin.write(json.dumps({"prompt": LONG_PROMPT}))
        mock_stdin.seek(0)

        with patch.object(
            hook,
            "build_metadata_prefix",
            side_effect=RuntimeError("boom"),
        ):
            with pytest.raises(SystemExit) as exc_info:
                hook.main()

        assert exc_info.value.code == 0
        assert mock_run.call_args.kwargs["input"] == LONG_PROMPT
        assert "Warning: metadata prefix failed" in capsys.readouterr().err
