#!/usr/bin/env python3
"""Unit tests for plan_claim.py hook."""

import json
import os
from io import StringIO
from unittest.mock import patch

import pytest

import plan_claim

FRONTMATTER = '---\nsession_id: "abc-123"\n---\n'
PLAN = "# Migrate billing to v2\n\nDetails here.\n"


class TestStripFrontmatter:
    """Test _strip_frontmatter() function."""

    def test_no_frontmatter(self):
        assert plan_claim._strip_frontmatter(PLAN) == PLAN

    def test_strips_frontmatter(self):
        assert plan_claim._strip_frontmatter(FRONTMATTER + PLAN) == "\n" + PLAN

    def test_unclosed_frontmatter_returned_as_is(self):
        text = "---\nsession_id: broken"
        assert plan_claim._strip_frontmatter(text) == text


class TestFrontmatterSessionId:
    """Test _frontmatter_session_id() function."""

    def test_extracts_session_id(self):
        assert plan_claim._frontmatter_session_id(FRONTMATTER + PLAN) == "abc-123"

    def test_no_frontmatter(self):
        assert plan_claim._frontmatter_session_id(PLAN) is None

    def test_frontmatter_without_session_id(self):
        assert plan_claim._frontmatter_session_id('---\ncreated: "now"\n---\n') is None


class TestExtractH1:
    """Test _extract_h1() function."""

    def test_extracts_first_h1(self):
        assert plan_claim._extract_h1(PLAN) == "Migrate billing to v2"

    def test_skips_frontmatter(self):
        assert plan_claim._extract_h1(FRONTMATTER + PLAN) == "Migrate billing to v2"

    def test_ignores_h2(self):
        assert plan_claim._extract_h1("## Subheading only\n") is None

    def test_no_heading(self):
        assert plan_claim._extract_h1("just prose\n") is None

    def test_truncates_long_title(self):
        title = plan_claim._extract_h1("# " + "x" * 200)
        assert title is not None
        assert len(title) == plan_claim.MAX_LABEL_CHARS


class TestPlanTextFromPayload:
    """Test _plan_text_from_payload() function."""

    def test_reads_tool_input_plan(self):
        data = {"tool_input": {"plan": PLAN}}
        assert plan_claim._plan_text_from_payload(data) == PLAN

    def test_ignores_tool_response(self):
        data = {"tool_input": {}, "tool_response": {"plan": PLAN}}
        assert plan_claim._plan_text_from_payload(data) is None

    def test_ignores_blank_plan(self):
        assert plan_claim._plan_text_from_payload({"tool_input": {"plan": "  "}}) is None

    def test_missing_containers(self):
        assert plan_claim._plan_text_from_payload({}) is None


class TestPlanTextFromDisk:
    """Test _plan_text_from_disk() function."""

    @pytest.fixture(autouse=True)
    def plans_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(plan_claim, "PLANS_DIR", tmp_path)
        return tmp_path

    def test_finds_matching_plan(self, plans_dir):
        (plans_dir / "plan.md").write_text(FRONTMATTER + PLAN)
        assert plan_claim._plan_text_from_disk("abc-123") == FRONTMATTER + PLAN

    def test_ignores_other_sessions(self, plans_dir):
        (plans_dir / "plan.md").write_text(FRONTMATTER + PLAN)
        assert plan_claim._plan_text_from_disk("other-session") is None

    def test_most_recent_match_wins(self, plans_dir):
        old, new = plans_dir / "old.md", plans_dir / "new.md"
        old.write_text(FRONTMATTER + "# Old plan\n")
        new.write_text(FRONTMATTER + "# New plan\n")
        os.utime(old, (1000, 1000))
        os.utime(new, (2000, 2000))
        assert plan_claim._plan_text_from_disk("abc-123") == FRONTMATTER + "# New plan\n"

    def test_missing_dir(self, plans_dir):
        plans_dir.rmdir()
        assert plan_claim._plan_text_from_disk("abc-123") is None


class TestMain:
    """Test main() end to end."""

    def _run(self, payload):
        with patch("sys.stdin", StringIO(json.dumps(payload))):
            with patch("subprocess.run") as mock_run:
                with pytest.raises(SystemExit) as excinfo:
                    plan_claim.main()
        assert excinfo.value.code == 0
        return mock_run

    def test_claims_plan_title(self):
        payload = {
            "tool_name": "ExitPlanMode",
            "session_id": "abc-123",
            "tool_input": {"plan": PLAN},
        }
        mock_run = self._run(payload)
        argv = mock_run.call_args.args[0]
        assert argv[1:] == [
            "claim",
            "--client",
            "claude",
            "--session",
            "abc-123",
            "Migrate billing to v2",
        ]

    def test_ignores_other_tools(self):
        payload = {"tool_name": "Edit", "session_id": "abc-123"}
        assert not self._run(payload).called

    def test_silent_on_subprocess_failure(self):
        payload = {
            "tool_name": "ExitPlanMode",
            "session_id": "abc-123",
            "tool_input": {"plan": PLAN},
        }
        with patch("sys.stdin", StringIO(json.dumps(payload))):
            with patch("subprocess.run", side_effect=OSError("boom")):
                with pytest.raises(SystemExit) as excinfo:
                    plan_claim.main()
        assert excinfo.value.code == 0
