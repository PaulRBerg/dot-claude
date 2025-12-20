#!/usr/bin/env python3
"""
Tests for sync_context_section.py
Run with: uv run pytest sync_context_section_test.py -v
"""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from sync_context_section import (
    extract_section,
    has_uncommitted_changes,
    insert_section_after_first_heading,
    main,
    print_table,
    remove_section,
    update_file,
)


class TestHasUncommittedChanges:
    """Tests for has_uncommitted_changes function."""

    @patch("sync_context_section.subprocess.run")
    def test_returns_true_when_file_has_changes(self, mock_run):
        """Should return True when git diff shows changes."""
        mock_run.return_value = Mock(stdout="path/to/file.md\n")
        file_path = Path("/test/file.md")

        result = has_uncommitted_changes(file_path)

        assert result is True
        mock_run.assert_called_once_with(
            ["git", "diff", "--name-only", str(file_path)],
            capture_output=True,
            text=True,
            cwd=file_path.parent,
        )

    @patch("sync_context_section.subprocess.run")
    def test_returns_false_when_no_changes(self, mock_run):
        """Should return False when git diff is empty."""
        mock_run.return_value = Mock(stdout="")
        file_path = Path("/test/file.md")

        result = has_uncommitted_changes(file_path)

        assert result is False

    @patch("sync_context_section.subprocess.run")
    def test_returns_false_on_git_error(self, mock_run):
        """Should return False when subprocess raises exception."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        file_path = Path("/test/file.md")

        result = has_uncommitted_changes(file_path)

        assert result is False

    @patch("sync_context_section.subprocess.run")
    def test_handles_generic_exception(self, mock_run):
        """Should return False on any exception."""
        mock_run.side_effect = OSError("Permission denied")
        file_path = Path("/test/file.md")

        result = has_uncommitted_changes(file_path)

        assert result is False


class TestExtractSection:
    """Tests for extract_section function."""

    def test_extracts_section_from_middle_of_file(self):
        """Should extract section between ## headings."""
        content = """# Main Heading

## Section One
Content of section one.

## Section Two
Content of section two.
More content.

## Section Three
Content of section three.
"""
        result = extract_section(content, "## Section Two")

        assert (
            result
            == """## Section Two
Content of section two.
More content.

"""
        )

    def test_extracts_section_at_end_of_file(self):
        """Should extract section that extends to EOF."""
        content = """# Main Heading

## Section One
Content of section one.

## Section Two
Content of section two.
More content."""

        result = extract_section(content, "## Section Two")

        assert (
            result
            == """## Section Two
Content of section two.
More content."""
        )

    def test_returns_none_for_missing_section(self):
        """Should return None when section not found."""
        content = """# Main Heading

## Section One
Content of section one.
"""
        result = extract_section(content, "## Nonexistent Section")

        assert result is None

    def test_preserves_section_heading(self):
        """Should include the section heading in result."""
        content = """## Test Section
Line 1
Line 2

## Next Section
"""
        result = extract_section(content, "## Test Section")

        assert result is not None
        assert result.startswith("## Test Section\n")

    def test_handles_section_with_special_characters(self):
        """Should handle section titles with regex special characters."""
        content = """## Section (with) [brackets] & stuff
Content here.

## Next Section
"""
        result = extract_section(content, "## Section (with) [brackets] & stuff")

        assert (
            result
            == """## Section (with) [brackets] & stuff
Content here.

"""
        )


class TestRemoveSection:
    """Tests for remove_section function."""

    def test_removes_section_from_middle(self):
        """Should remove section and preserve other content."""
        content = """# Main Heading

## Section One
Content one.

## Section Two
Content two.

## Section Three
Content three.
"""
        result = remove_section(content, "## Section Two")

        assert "## Section Two" not in result
        assert "Content two" not in result
        assert "## Section One" in result
        assert "## Section Three" in result

    def test_removes_section_at_end(self):
        """Should remove last section."""
        content = """## Section One
Content one.

## Section Two
Content two.
"""
        result = remove_section(content, "## Section Two")

        assert "## Section Two" not in result
        assert "Content two" not in result
        assert "## Section One" in result

    def test_cleans_excessive_blank_lines(self):
        """Should reduce 3+ consecutive newlines to 2."""
        content = """## Section One
Content.



## Section Two
To remove.

## Section Three
Content.
"""
        result = remove_section(content, "## Section Two")

        # Should not have 3+ consecutive newlines
        assert "\n\n\n" not in result

    def test_handles_nonexistent_section(self):
        """Should return original content if section not found."""
        content = """## Section One
Content.
"""
        result = remove_section(content, "## Nonexistent")

        assert result == content


class TestInsertSectionAfterFirstHeading:
    """Tests for insert_section_after_first_heading function."""

    def test_inserts_after_first_heading_with_intro(self):
        """Should insert after first heading and preserve intro text."""
        content = """# Main Title

This is intro text.
More intro.

## First Section
Content.
"""
        section = """## New Section
New content.
"""
        result = insert_section_after_first_heading(content, section)

        # Should preserve intro text
        assert "This is intro text." in result
        assert "More intro." in result
        # New section should appear before First Section
        new_section_pos = result.find("## New Section")
        first_section_pos = result.find("## First Section")
        assert new_section_pos < first_section_pos

    def test_inserts_after_first_heading_no_intro(self):
        """Should insert immediately after first heading when no intro text."""
        content = """# Main Title
## First Section
Content.
"""
        section = """## New Section
New content.
"""
        result = insert_section_after_first_heading(content, section)

        # New section should appear before First Section
        new_section_pos = result.find("## New Section")
        first_section_pos = result.find("## First Section")
        assert new_section_pos < first_section_pos

    def test_prepends_when_no_heading(self):
        """Should prepend section when file has no headings."""
        content = """Just some text
without headings.
"""
        section = """## New Section
New content.
"""
        result = insert_section_after_first_heading(content, section)

        assert result.startswith("## New Section\n")

    def test_ensures_proper_spacing(self):
        """Should ensure proper newline spacing around section."""
        content = """# Title
Intro text.
## First Section
"""
        section = """## New Section
Content."""

        result = insert_section_after_first_heading(content, section)

        # Should have proper spacing
        assert "\n\n## New Section" in result or "## New Section\n\n" in result


class TestUpdateFile:
    """Tests for update_file function."""

    @patch("sync_context_section.Path.exists")
    def test_returns_error_when_file_not_found(self, mock_exists):
        """Should return error tuple when file doesn't exist."""
        mock_exists.return_value = False
        file_path = Path("/test/file.md")

        modified, msg = update_file(file_path, "## New", "## New")

        assert modified is False
        assert "not found" in msg.lower()

    @patch("sync_context_section.has_uncommitted_changes")
    @patch("sync_context_section.Path.exists")
    def test_returns_error_when_uncommitted_changes(self, mock_exists, mock_changes):
        """Should return error when file has uncommitted changes."""
        mock_exists.return_value = True
        mock_changes.return_value = True
        file_path = Path("/test/file.md")

        modified, msg = update_file(file_path, "## New", "## New")

        assert modified is False
        assert "Uncommitted changes" in msg

    @patch("sync_context_section.has_uncommitted_changes")
    @patch("sync_context_section.Path.write_text")
    @patch("sync_context_section.Path.read_text")
    @patch("sync_context_section.Path.exists")
    def test_replaces_existing_section(self, mock_exists, mock_read, mock_write, mock_changes):
        """Should replace section when it already exists."""
        mock_exists.return_value = True
        mock_changes.return_value = False
        mock_read.return_value = """# Title

## Lint Rules
Old content.

## Other Section
Content.
"""
        new_section = """## Lint Rules
New content.
"""
        file_path = Path("/test/file.md")

        modified, msg = update_file(file_path, new_section, "## Lint Rules")

        assert modified is True
        assert "Updated" in msg
        # Check that write was called with content containing new section
        written_content = mock_write.call_args[0][0]
        assert "New content." in written_content
        assert "Old content." not in written_content

    @patch("sync_context_section.has_uncommitted_changes")
    @patch("sync_context_section.Path.write_text")
    @patch("sync_context_section.Path.read_text")
    @patch("sync_context_section.Path.exists")
    def test_inserts_new_section_before_first_h2(
        self, mock_exists, mock_read, mock_write, mock_changes
    ):
        """Should insert section before first ## when section doesn't exist."""
        mock_exists.return_value = True
        mock_changes.return_value = False
        mock_read.return_value = """# Title

Intro text.

## Existing Section
Content.
"""
        new_section = """## New Section
New content.
"""
        file_path = Path("/test/file.md")

        modified, _ = update_file(file_path, new_section, "## New Section")

        assert modified is True
        written_content = mock_write.call_args[0][0]
        # New section should appear before Existing Section
        new_pos = written_content.find("## New Section")
        existing_pos = written_content.find("## Existing Section")
        assert new_pos < existing_pos

    @patch("sync_context_section.has_uncommitted_changes")
    @patch("sync_context_section.Path.write_text")
    @patch("sync_context_section.Path.read_text")
    @patch("sync_context_section.Path.exists")
    def test_appends_when_no_h2_sections(self, mock_exists, mock_read, mock_write, mock_changes):
        """Should append section when no ## sections exist."""
        mock_exists.return_value = True
        mock_changes.return_value = False
        mock_read.return_value = """# Title

Just some content.
"""
        new_section = """## New Section
New content.
"""
        file_path = Path("/test/file.md")

        modified, _ = update_file(file_path, new_section, "## New Section")

        assert modified is True
        written_content = mock_write.call_args[0][0]
        assert "## New Section" in written_content

    @patch("sync_context_section.has_uncommitted_changes")
    @patch("sync_context_section.Path.write_text")
    @patch("sync_context_section.Path.read_text")
    @patch("sync_context_section.Path.exists")
    def test_returns_no_changes_when_content_identical(
        self, mock_exists, mock_read, mock_write, mock_changes
    ):
        """Should not write when content unchanged."""
        mock_exists.return_value = True
        mock_changes.return_value = False
        existing_content = """# Title

## Section
Same content.

"""
        mock_read.return_value = existing_content
        new_section = """## Section
Same content.
"""
        file_path = Path("/test/file.md")

        modified, msg = update_file(file_path, new_section, "## Section")

        assert modified is False
        assert "No changes" in msg
        mock_write.assert_not_called()

    @patch("sync_context_section.has_uncommitted_changes")
    @patch("sync_context_section.Path.read_text")
    @patch("sync_context_section.Path.exists")
    def test_returns_error_when_no_heading(self, mock_exists, mock_read, mock_changes):
        """Should return error when file has no heading."""
        mock_exists.return_value = True
        mock_changes.return_value = False
        mock_read.return_value = "Just content without any headings."
        file_path = Path("/test/file.md")

        modified, msg = update_file(file_path, "## New", "## New")

        assert modified is False
        assert "Missing heading" in msg

    @patch("sync_context_section.has_uncommitted_changes")
    @patch("sync_context_section.Path.read_text")
    @patch("sync_context_section.Path.exists")
    def test_handles_read_error(self, mock_exists, mock_read, mock_changes):
        """Should return error tuple on exception."""
        mock_exists.return_value = True
        mock_changes.return_value = False
        mock_read.side_effect = PermissionError("Access denied")
        file_path = Path("/test/file.md")

        modified, msg = update_file(file_path, "## New", "## New")

        assert modified is False
        assert "Error" in msg


class TestPrintTable:
    """Tests for print_table function."""

    @patch("sync_context_section.HOME", Path("/home/user"))
    def test_prints_formatted_table(self, capsys):
        """Should output formatted ASCII table."""
        results = [
            (Path("/home/user/project/file1.md"), "✅ Updated"),
            (Path("/home/user/project/file2.md"), "ℹ️  No changes"),
        ]

        print_table(results)

        captured = capsys.readouterr()
        # Should contain table borders
        assert "┌" in captured.out
        assert "│" in captured.out
        assert "└" in captured.out
        # Should contain headers
        assert "File" in captured.out
        assert "Result" in captured.out
        # Should contain results
        assert "Updated" in captured.out
        assert "No changes" in captured.out

    @patch("sync_context_section.HOME", Path("/home/user"))
    def test_displays_relative_paths(self, capsys):
        """Should display paths relative to home directory."""
        results = [
            (Path("/home/user/projects/app/CLAUDE.md"), "✅ Updated"),
        ]

        print_table(results)

        captured = capsys.readouterr()
        # Should show relative path with tilde
        assert "~/projects/app" in captured.out

    @patch("sync_context_section.HOME", Path("/home/user"))
    def test_handles_absolute_paths_outside_home(self, capsys):
        """Should handle paths outside home directory."""
        results = [
            (Path("/var/log/app/file.md"), "✅ Updated"),
        ]

        print_table(results)

        captured = capsys.readouterr()
        # Should display absolute path when not relative to home
        assert "/var/log/app" in captured.out


class TestMain:
    """Tests for main function."""

    @patch("sync_context_section.print_table")
    @patch("sync_context_section.update_file")
    @patch("sync_context_section.extract_section")
    @patch("sync_context_section.TEMPLATE_FILE")
    def test_exits_when_template_not_found(
        self, mock_template, mock_extract, mock_update, mock_print_table
    ):
        """Should exit with error when template file not found."""
        mock_template.exists.return_value = False

        with pytest.raises(SystemExit) as exc_info:
            main("## Test Section")

        assert exc_info.value.code == 1

    @patch("sync_context_section.print_table")
    @patch("sync_context_section.update_file")
    @patch("sync_context_section.extract_section")
    @patch("sync_context_section.TEMPLATE_FILE")
    def test_exits_when_section_not_found(
        self, mock_template, mock_extract, mock_update, mock_print_table
    ):
        """Should exit when section not found in template."""
        mock_template.exists.return_value = True
        mock_template.read_text.return_value = "# Content"
        mock_extract.return_value = None

        with pytest.raises(SystemExit) as exc_info:
            main("## Missing Section")

        assert exc_info.value.code == 1

    @patch("sync_context_section.TARGET_FILES", [Path("/test1.md"), Path("/test2.md")])
    @patch("sync_context_section.print_table")
    @patch("sync_context_section.update_file")
    @patch("sync_context_section.extract_section")
    @patch("sync_context_section.TEMPLATE_FILE")
    def test_updates_all_target_files(
        self, mock_template, mock_extract, mock_update, mock_print_table, capsys
    ):
        """Should update all target files and print results."""
        mock_template.exists.return_value = True
        mock_template.read_text.return_value = """## Test Section
Content.
"""
        mock_extract.return_value = """## Test Section
Content.
"""
        mock_update.side_effect = [
            (True, "✅ Updated"),
            (False, "ℹ️  No changes"),
        ]

        main("## Test Section")

        # Should call update_file for each target
        assert mock_update.call_count == 2
        # Should call print_table with results
        mock_print_table.assert_called_once()
        # Should print summary
        captured = capsys.readouterr()
        assert "Updated 1/2 files" in captured.out

    @patch("sync_context_section.TARGET_FILES", [Path("/test.md")])
    @patch("sync_context_section.print_table")
    @patch("sync_context_section.update_file")
    @patch("sync_context_section.extract_section")
    @patch("sync_context_section.TEMPLATE_FILE")
    def test_prints_extraction_info(
        self, mock_template, mock_extract, mock_update, mock_print_table, capsys
    ):
        """Should print info about extracted section."""
        mock_template.exists.return_value = True
        mock_template.read_text.return_value = "Content"
        section_content = "## Test\nContent here.\n"
        mock_extract.return_value = section_content
        mock_update.return_value = (False, "ℹ️  No changes")

        main("## Test")

        captured = capsys.readouterr()
        # Should mention section title and character count
        assert "Test" in captured.out
        assert str(len(section_content)) in captured.out
