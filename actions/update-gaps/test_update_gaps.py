"""
test_update_gaps.py
Tests for update_gaps.py — Rural Peds Gap Analysis Standard v1.0

Run with:
    pytest actions/update-gaps/test_update_gaps.py -v
"""

import pytest
import textwrap
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).parent))

from update_gaps import (
    find_gap_ids_in_pr_body,
    parse_sections,
    reassemble,
    find_row,
    parse_active_row,
    format_completed_row,
    update_gaps_file,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

SAMPLE_GAPS_MD = textwrap.dedent("""\
    # Gaps — test-repo

    ## Active

    | ID | Title | Priority | Category | Created | Notes |
    |----|-------|----------|----------|---------|-------|
    | GAP-001 | Add NRP decision tree | P0 | content | 2026-04-01 | |
    | GAP-002 | Fix CI pipeline | P1 | infrastructure | 2026-04-05 | blocks deploys |
    | GAP-003 | Write textbook chapter 3 | P2 | teaching | 2026-04-10 | |

    ## Completed

    | ID | Title | Priority | Category | Completed | PR |
    |----|-------|----------|----------|-----------|-----|
    | GAP-000 | Initial setup | P0 | infrastructure | 2026-03-28 | #1 |

    ## Abandoned

    | ID | Title | Reason |
    |----|-------|--------|
""")


@pytest.fixture
def gaps_file(tmp_path):
    f = tmp_path / "GAPS.md"
    f.write_text(SAMPLE_GAPS_MD, encoding="utf-8")
    return f


# ── find_gap_ids_in_pr_body ───────────────────────────────────────────────────

class TestFindGapIds:
    def test_single_closes(self):
        assert find_gap_ids_in_pr_body("Closes GAP-001") == ["GAP-001"]

    def test_multiple_closes(self):
        ids = find_gap_ids_in_pr_body("Closes GAP-001. Closes GAP-002.")
        assert ids == ["GAP-001", "GAP-002"]

    def test_fixes_keyword(self):
        assert find_gap_ids_in_pr_body("Fixes GAP-007") == ["GAP-007"]

    def test_resolves_keyword(self):
        assert find_gap_ids_in_pr_body("Resolves GAP-042") == ["GAP-042"]

    def test_case_insensitive_keyword(self):
        assert find_gap_ids_in_pr_body("closes gap-003") == ["GAP-003"]

    def test_no_gap_reference(self):
        assert find_gap_ids_in_pr_body("Fixed the typo in README.") == []

    def test_gap_in_middle_of_text(self):
        body = "This PR does a bunch of work. Closes GAP-005. See also the design doc."
        assert find_gap_ids_in_pr_body(body) == ["GAP-005"]

    def test_closes_without_gap(self):
        # "Closes #42" should not match
        assert find_gap_ids_in_pr_body("Closes #42") == []

    def test_plural_form(self):
        # "Close" (not Closes) should still match via regex
        assert find_gap_ids_in_pr_body("Close GAP-011") == ["GAP-011"]

    def test_three_gaps(self):
        body = "Closes GAP-001, closes GAP-010, resolves GAP-020"
        ids = find_gap_ids_in_pr_body(body)
        assert set(ids) == {"GAP-001", "GAP-010", "GAP-020"}

    def test_uppercase_gap_id(self):
        assert find_gap_ids_in_pr_body("Closes gap-001") == ["GAP-001"]


# ── parse_sections ────────────────────────────────────────────────────────────

class TestParseSections:
    def test_sections_present(self):
        sections = parse_sections(SAMPLE_GAPS_MD)
        keys = list(sections.keys())
        assert "Active" in keys
        assert "Completed" in keys
        assert "Abandoned" in keys

    def test_preamble_captured(self):
        sections = parse_sections(SAMPLE_GAPS_MD)
        assert "__preamble__" in sections
        preamble = "".join(sections["__preamble__"])
        assert "Gaps — test-repo" in preamble

    def test_reassemble_roundtrip(self):
        sections = parse_sections(SAMPLE_GAPS_MD)
        assert reassemble(sections) == SAMPLE_GAPS_MD


# ── find_row ──────────────────────────────────────────────────────────────────

class TestFindRow:
    def test_finds_existing_row(self):
        sections = parse_sections(SAMPLE_GAPS_MD)
        active_lines = sections["Active"]
        idx = find_row(active_lines, "GAP-001")
        assert idx is not None
        assert "GAP-001" in active_lines[idx]

    def test_returns_none_for_missing(self):
        sections = parse_sections(SAMPLE_GAPS_MD)
        active_lines = sections["Active"]
        assert find_row(active_lines, "GAP-999") is None

    def test_case_insensitive_lookup(self):
        sections = parse_sections(SAMPLE_GAPS_MD)
        active_lines = sections["Active"]
        idx = find_row(active_lines, "gap-001")
        assert idx is not None


# ── parse_active_row ──────────────────────────────────────────────────────────

class TestParseActiveRow:
    def test_parses_full_row(self):
        row = "| GAP-001 | Add NRP decision tree | P0 | content | 2026-04-01 | |"
        parsed = parse_active_row(row)
        assert parsed is not None
        assert parsed["id"] == "GAP-001"
        assert parsed["title"] == "Add NRP decision tree"
        assert parsed["priority"] == "P0"
        assert parsed["category"] == "content"
        assert parsed["created"] == "2026-04-01"
        assert parsed["notes"] == ""

    def test_parses_row_with_notes(self):
        row = "| GAP-002 | Fix CI pipeline | P1 | infrastructure | 2026-04-05 | blocks deploys |"
        parsed = parse_active_row(row)
        assert parsed["notes"] == "blocks deploys"

    def test_returns_none_for_separator(self):
        assert parse_active_row("|----|-------|----------|----------|---------|-------|") is None

    def test_returns_none_for_header(self):
        assert parse_active_row("| ID | Title | Priority | Category | Created | Notes |") is None


# ── format_completed_row ──────────────────────────────────────────────────────

class TestFormatCompletedRow:
    def test_produces_pipe_delimited_row(self):
        row = {
            "id": "GAP-001",
            "title": "Add NRP decision tree",
            "priority": "P0",
            "category": "content",
            "created": "2026-04-01",
            "notes": "",
        }
        result = format_completed_row(row, "2026-04-28", "42")
        assert "GAP-001" in result
        assert "2026-04-28" in result
        assert "#42" in result
        assert result.count("|") >= 5

    def test_no_pr_number_uses_dash(self):
        row = {
            "id": "GAP-002",
            "title": "Fix CI",
            "priority": "P1",
            "category": "infrastructure",
            "created": "2026-04-05",
            "notes": "",
        }
        result = format_completed_row(row, "2026-04-28", "")
        assert "—" in result


# ── update_gaps_file (integration) ───────────────────────────────────────────

class TestUpdateGapsFile:
    def test_moves_single_gap(self, gaps_file):
        n, ids = update_gaps_file(
            gaps_file=gaps_file,
            pr_body="This PR adds the NRP tree. Closes GAP-001.",
            pr_number="10",
            merged_date="2026-04-28",
        )
        assert n == 1
        assert "GAP-001" in ids
        updated = gaps_file.read_text()
        # Should no longer be in Active
        assert "GAP-001" not in updated.split("## Completed")[0].split("## Active")[1]
        # Should be in Completed
        assert "GAP-001" in updated.split("## Completed")[1]

    def test_moves_multiple_gaps(self, gaps_file):
        n, ids = update_gaps_file(
            gaps_file=gaps_file,
            pr_body="Closes GAP-001. Closes GAP-002.",
            pr_number="11",
            merged_date="2026-04-28",
        )
        assert n == 2
        assert set(ids) == {"GAP-001", "GAP-002"}

    def test_no_match_returns_zero(self, gaps_file):
        n, ids = update_gaps_file(
            gaps_file=gaps_file,
            pr_body="Just a regular fix, no gap reference.",
            pr_number="12",
            merged_date="2026-04-28",
        )
        assert n == 0
        assert ids == []
        # File should be unchanged
        assert gaps_file.read_text() == SAMPLE_GAPS_MD

    def test_already_completed_gap_skipped(self, gaps_file):
        # GAP-000 is already in Completed
        n, ids = update_gaps_file(
            gaps_file=gaps_file,
            pr_body="Closes GAP-000.",
            pr_number="13",
            merged_date="2026-04-28",
        )
        assert n == 0

    def test_unknown_gap_id_skipped(self, gaps_file):
        n, ids = update_gaps_file(
            gaps_file=gaps_file,
            pr_body="Closes GAP-999.",
            pr_number="14",
            merged_date="2026-04-28",
        )
        assert n == 0

    def test_file_not_found_raises(self, tmp_path):
        missing = tmp_path / "nonexistent.md"
        with pytest.raises(FileNotFoundError):
            update_gaps_file(
                gaps_file=missing,
                pr_body="Closes GAP-001.",
                pr_number="15",
                merged_date="2026-04-28",
            )

    def test_completed_row_has_pr_link(self, gaps_file):
        update_gaps_file(
            gaps_file=gaps_file,
            pr_body="Closes GAP-003.",
            pr_number="20",
            merged_date="2026-04-28",
        )
        updated = gaps_file.read_text()
        completed_section = updated.split("## Completed")[1]
        assert "#20" in completed_section
        assert "GAP-003" in completed_section

    def test_roundtrip_preserves_other_gaps(self, gaps_file):
        update_gaps_file(
            gaps_file=gaps_file,
            pr_body="Closes GAP-001.",
            pr_number="10",
            merged_date="2026-04-28",
        )
        updated = gaps_file.read_text()
        # GAP-002 and GAP-003 should still be in Active
        active_section = updated.split("## Active")[1].split("##")[0]
        assert "GAP-002" in active_section
        assert "GAP-003" in active_section
