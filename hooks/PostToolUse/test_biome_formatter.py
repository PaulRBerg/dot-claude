#!/usr/bin/env python3
"""
Comprehensive tests for biome-formatter.py hook

Run with: python3 -m pytest test_biome_formatter.py -v
Or with unittest: python3 -m unittest test_biome_formatter.py -v
"""

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add current directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent))

import biome_formatter


class TestExtractFilePath(unittest.TestCase):
    """Test file path extraction from various sources."""

    def setUp(self):
        """Clear environment before each test."""
        for key in ["TOOL_INPUT_FILE_PATH", "TOOL_INPUT_RELATIVE_PATH",
                    "CLAUDE_PROJECT_DIR", "TOOL_CALL"]:
            os.environ.pop(key, None)

    def test_extract_from_tool_input_file_path(self):
        """Test extraction from TOOL_INPUT_FILE_PATH (Edit/Write tools)."""
        os.environ["TOOL_INPUT_FILE_PATH"] = "/path/to/file.ts"
        self.assertEqual(biome_formatter.extract_file_path(), "/path/to/file.ts")

    def test_extract_from_relative_path_with_project_dir(self):
        """Test extraction from TOOL_INPUT_RELATIVE_PATH + CLAUDE_PROJECT_DIR (Serena)."""
        os.environ["TOOL_INPUT_RELATIVE_PATH"] = "src/component.tsx"
        os.environ["CLAUDE_PROJECT_DIR"] = "/home/user/project"
        self.assertEqual(
            biome_formatter.extract_file_path(),
            "/home/user/project/src/component.tsx"
        )

    def test_extract_from_relative_path_without_project_dir(self):
        """Test extraction from TOOL_INPUT_RELATIVE_PATH without CLAUDE_PROJECT_DIR."""
        os.environ["TOOL_INPUT_RELATIVE_PATH"] = "src/component.tsx"
        self.assertEqual(biome_formatter.extract_file_path(), "src/component.tsx")

    def test_extract_from_tool_call_json_with_project_dir(self):
        """Test extraction from TOOL_CALL JSON with CLAUDE_PROJECT_DIR."""
        tool_call = json.dumps({"relative_path": "lib/utils.ts", "other": "data"})
        os.environ["TOOL_CALL"] = tool_call
        os.environ["CLAUDE_PROJECT_DIR"] = "/home/user/project"
        self.assertEqual(
            biome_formatter.extract_file_path(),
            "/home/user/project/lib/utils.ts"
        )

    def test_extract_from_tool_call_json_without_project_dir(self):
        """Test extraction from TOOL_CALL JSON without CLAUDE_PROJECT_DIR."""
        tool_call = json.dumps({"relative_path": "lib/utils.ts"})
        os.environ["TOOL_CALL"] = tool_call
        self.assertEqual(biome_formatter.extract_file_path(), "lib/utils.ts")

    def test_extract_with_invalid_json_in_tool_call(self):
        """Test graceful handling of invalid JSON in TOOL_CALL."""
        os.environ["TOOL_CALL"] = "not valid json {"
        self.assertIsNone(biome_formatter.extract_file_path())

    def test_extract_with_missing_relative_path_in_json(self):
        """Test handling of TOOL_CALL JSON without relative_path."""
        tool_call = json.dumps({"other_field": "value"})
        os.environ["TOOL_CALL"] = tool_call
        self.assertIsNone(biome_formatter.extract_file_path())

    def test_extract_with_no_env_vars(self):
        """Test extraction returns None when no env vars are set."""
        self.assertIsNone(biome_formatter.extract_file_path())

    def test_priority_order_tool_input_file_path_wins(self):
        """Test that TOOL_INPUT_FILE_PATH takes priority over other methods."""
        os.environ["TOOL_INPUT_FILE_PATH"] = "/priority/file.ts"
        os.environ["TOOL_INPUT_RELATIVE_PATH"] = "other/file.ts"
        os.environ["TOOL_CALL"] = json.dumps({"relative_path": "another/file.ts"})
        self.assertEqual(biome_formatter.extract_file_path(), "/priority/file.ts")


class TestIsTypescriptFile(unittest.TestCase):
    """Test TypeScript file detection."""

    def test_ts_extension(self):
        """Test .ts files are recognized."""
        self.assertTrue(biome_formatter.is_typescript_file("file.ts"))
        self.assertTrue(biome_formatter.is_typescript_file("/path/to/file.ts"))
        self.assertTrue(biome_formatter.is_typescript_file("deeply/nested/file.ts"))

    def test_tsx_extension(self):
        """Test .tsx files are recognized."""
        self.assertTrue(biome_formatter.is_typescript_file("component.tsx"))
        self.assertTrue(biome_formatter.is_typescript_file("/src/component.tsx"))

    def test_non_typescript_files(self):
        """Test non-TypeScript files are rejected."""
        self.assertFalse(biome_formatter.is_typescript_file("file.js"))
        self.assertFalse(biome_formatter.is_typescript_file("file.jsx"))
        self.assertFalse(biome_formatter.is_typescript_file("file.py"))
        self.assertFalse(biome_formatter.is_typescript_file("file.md"))
        self.assertFalse(biome_formatter.is_typescript_file("README"))
        self.assertFalse(biome_formatter.is_typescript_file("file"))

    def test_edge_cases(self):
        """Test edge cases in file extensions."""
        # Multiple dots
        self.assertTrue(biome_formatter.is_typescript_file("file.test.ts"))
        self.assertTrue(biome_formatter.is_typescript_file("component.stories.tsx"))

        # Case sensitivity
        self.assertFalse(biome_formatter.is_typescript_file("file.TS"))
        self.assertFalse(biome_formatter.is_typescript_file("file.TSX"))

        # Partial matches shouldn't work
        self.assertFalse(biome_formatter.is_typescript_file("file.ts.bak"))
        self.assertFalse(biome_formatter.is_typescript_file("typescript"))


class TestRunBiome(unittest.TestCase):
    """Test Biome execution."""

    @patch("biome_formatter.subprocess.run")
    def test_run_biome_success(self, mock_run):
        """Test successful Biome execution."""
        biome_formatter.run_biome("/path/to/file.ts")

        mock_run.assert_called_once_with(
            ["biome", "check", "--apply", "/path/to/file.ts"],
            stdout=biome_formatter.subprocess.DEVNULL,
            stderr=biome_formatter.subprocess.DEVNULL,
            check=False,
            timeout=10,
        )

    @patch("biome_formatter.subprocess.run")
    def test_run_biome_handles_file_not_found(self, mock_run):
        """Test graceful handling when biome binary not found."""
        mock_run.side_effect = FileNotFoundError("biome not found")

        # Should not raise exception
        biome_formatter.run_biome("/path/to/file.ts")

    @patch("biome_formatter.subprocess.run")
    def test_run_biome_handles_timeout(self, mock_run):
        """Test graceful handling of timeout."""
        mock_run.side_effect = biome_formatter.subprocess.TimeoutExpired(
            cmd=["biome"], timeout=10
        )

        # Should not raise exception
        biome_formatter.run_biome("/path/to/file.ts")

    @patch("biome_formatter.subprocess.run")
    def test_run_biome_handles_generic_exception(self, mock_run):
        """Test graceful handling of any exception."""
        mock_run.side_effect = Exception("Something went wrong")

        # Should not raise exception
        biome_formatter.run_biome("/path/to/file.ts")


class TestMain(unittest.TestCase):
    """Test main function integration."""

    def setUp(self):
        """Clear environment before each test."""
        for key in ["TOOL_INPUT_FILE_PATH", "TOOL_INPUT_RELATIVE_PATH",
                    "CLAUDE_PROJECT_DIR", "TOOL_CALL"]:
            os.environ.pop(key, None)

    @patch("biome_formatter.run_biome")
    @patch("biome_formatter.Path.is_file")
    def test_main_with_valid_typescript_file(self, mock_is_file, mock_run_biome):
        """Test main with valid TypeScript file."""
        mock_is_file.return_value = True
        os.environ["TOOL_INPUT_FILE_PATH"] = "/path/to/file.ts"

        result = biome_formatter.main()

        self.assertEqual(result, 0)
        mock_run_biome.assert_called_once_with("/path/to/file.ts")

    @patch("biome_formatter.run_biome")
    def test_main_with_no_file_path(self, mock_run_biome):
        """Test main returns 0 when no file path found."""
        result = biome_formatter.main()

        self.assertEqual(result, 0)
        mock_run_biome.assert_not_called()

    @patch("biome_formatter.run_biome")
    def test_main_with_non_typescript_file(self, mock_run_biome):
        """Test main skips non-TypeScript files."""
        os.environ["TOOL_INPUT_FILE_PATH"] = "/path/to/file.js"

        result = biome_formatter.main()

        self.assertEqual(result, 0)
        mock_run_biome.assert_not_called()

    @patch("biome_formatter.run_biome")
    @patch("biome_formatter.Path.is_file")
    def test_main_with_nonexistent_file(self, mock_is_file, mock_run_biome):
        """Test main skips files that don't exist."""
        mock_is_file.return_value = False
        os.environ["TOOL_INPUT_FILE_PATH"] = "/path/to/missing.ts"

        result = biome_formatter.main()

        self.assertEqual(result, 0)
        mock_run_biome.assert_not_called()

    @patch("biome_formatter.run_biome")
    @patch("biome_formatter.Path.is_file")
    def test_main_with_serena_tool(self, mock_is_file, mock_run_biome):
        """Test main works with Serena MCP tool input."""
        mock_is_file.return_value = True
        os.environ["TOOL_INPUT_RELATIVE_PATH"] = "src/component.tsx"
        os.environ["CLAUDE_PROJECT_DIR"] = "/project"

        result = biome_formatter.main()

        self.assertEqual(result, 0)
        mock_run_biome.assert_called_once_with("/project/src/component.tsx")

    @patch("biome_formatter.run_biome")
    @patch("biome_formatter.Path.is_file")
    def test_main_always_returns_zero(self, mock_is_file, mock_run_biome):
        """Test main always returns 0, even if biome fails."""
        mock_is_file.return_value = True
        mock_run_biome.side_effect = Exception("Biome crashed")
        os.environ["TOOL_INPUT_FILE_PATH"] = "/path/to/file.ts"

        result = biome_formatter.main()

        self.assertEqual(result, 0)


class TestEndToEndScenarios(unittest.TestCase):
    """End-to-end integration tests."""

    def setUp(self):
        """Clear environment before each test."""
        for key in ["TOOL_INPUT_FILE_PATH", "TOOL_INPUT_RELATIVE_PATH",
                    "CLAUDE_PROJECT_DIR", "TOOL_CALL"]:
            os.environ.pop(key, None)

    @patch("biome_formatter.subprocess.run")
    @patch("biome_formatter.Path.is_file", return_value=True)
    def test_edit_tool_workflow(self, mock_is_file, mock_run):
        """Simulate Edit tool workflow."""
        os.environ["TOOL_INPUT_FILE_PATH"] = "/home/user/project/src/app.ts"

        result = biome_formatter.main()

        self.assertEqual(result, 0)
        mock_run.assert_called_once()

    @patch("biome_formatter.subprocess.run")
    @patch("biome_formatter.Path.is_file", return_value=True)
    def test_serena_replace_symbol_workflow(self, mock_is_file, mock_run):
        """Simulate Serena replace_symbol_body workflow."""
        os.environ["TOOL_INPUT_RELATIVE_PATH"] = "lib/utils.ts"
        os.environ["CLAUDE_PROJECT_DIR"] = "/home/user/project"

        result = biome_formatter.main()

        self.assertEqual(result, 0)
        mock_run.assert_called_once()

    @patch("biome_formatter.subprocess.run")
    @patch("biome_formatter.Path.is_file", return_value=True)
    def test_serena_tool_call_json_workflow(self, mock_is_file, mock_run):
        """Simulate Serena tool with TOOL_CALL JSON."""
        tool_call = json.dumps({
            "name_path": "MyClass/myMethod",
            "relative_path": "src/class.tsx",
            "body": "// new code"
        })
        os.environ["TOOL_CALL"] = tool_call
        os.environ["CLAUDE_PROJECT_DIR"] = "/project"

        result = biome_formatter.main()

        self.assertEqual(result, 0)
        mock_run.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
