#!/usr/bin/env python3
"""
update_gaps.py
Rural Peds Gap Analysis Standard v1.0
https://github.com/ruralpeds/gap-analysis-standard

Parses a GAPS.md file, finds the gap ID(s) referenced in a PR body via
"Closes GAP-NNN" patterns, moves those rows from Active to Completed,
and writes the updated file back.

Usage:
    python update_gaps.py \
        --gaps-file GAPS.md \
        --pr-body "Fixes the login bug. Closes GAP-003. Closes GAP-007." \
        --pr-number 42 \
        --merged-date 2026-04-28

Exit codes:
    0 — success (gaps moved or no gaps found — not an error)
    1 — file not found or parse error
    2 — argument error
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path


# ── Patterns ──────────────────────────────────────────────────────────────────

# Matches: Closes GAP-001, Fixes GAP-42, Resolves GAP-999 (case-insensitive)
CLOSES_PATTERN = re.compile(
    r"\b(?:closes?|fixes?|resolves?)\s+(GAP-\d+)\b",
    re.IGNORECASE,
)

# Matches a GAPS.md table row starting with | GAP-NNN |
ROW_PATTERN = re.compile(r"^\|\s*(GAP-\d+)\s*\|(.+)$")


# ── Section parser ────────────────────────────────────────────────────────────

def parse_sections(text: str) -> dict[str, list[str]]:
    """
    Split GAPS.md into named sections keyed by their ## heading.
    Returns a dict: {section_name: [lines]}
    Lines include the heading line itself as the first element.
    """
    sections: dict[str, list[str]] = {}
    current: str | None = None
    lines = text.splitlines(keepends=True)

    for line in lines:
        heading_match = re.match(r"^##\s+(.+)", line)
        if heading_match:
            current = heading_match.group(1).strip()
            sections[current] = [line]
        elif current is not None:
            sections[current].append(line)
        else:
            # Before the first ## heading — store as preamble
            sections.setdefault("__preamble__", []).append(line)

    return sections


def reassemble(sections: dict[str, list[str]]) -> str:
    """Reassemble sections back into a single string in insertion order."""
    return "".join(
        "".join(lines) for lines in sections.values()
    )


# ── Row operations ────────────────────────────────────────────────────────────

def find_row(lines: list[str], gap_id: str) -> int | None:
    """Return the index of the row for gap_id in lines, or None."""
    for i, line in enumerate(lines):
        m = ROW_PATTERN.match(line.rstrip())
        if m and m.group(1).upper() == gap_id.upper():
            return i
    return None


def parse_active_row(line: str) -> dict | None:
    """
    Parse an Active table row into a dict with keys:
    id, title, priority, category, created, notes
    Returns None if the line doesn't look like a data row.
    """
    m = ROW_PATTERN.match(line.rstrip())
    if not m:
        return None
    gap_id = m.group(1).strip()
    rest = [c.strip() for c in m.group(2).split("|")]
    # Active columns after ID: title, priority, category, created, notes
    if len(rest) < 5:
        rest.extend([""] * (5 - len(rest)))
    return {
        "id": gap_id,
        "title": rest[0],
        "priority": rest[1],
        "category": rest[2],
        "created": rest[3],
        "notes": rest[4],
    }


def format_completed_row(row: dict, completed_date: str, pr_number: str) -> str:
    """Format a Completed table row from an Active row dict."""
    pr_link = f"#{pr_number}" if pr_number else "—"
    return (
        f"| {row['id']} "
        f"| {row['title']} "
        f"| {row['priority']} "
        f"| {row['category']} "
        f"| {completed_date} "
        f"| {pr_link} |\n"
    )


# ── Main logic ────────────────────────────────────────────────────────────────

def find_gap_ids_in_pr_body(pr_body: str) -> list[str]:
    """Extract all GAP-NNN IDs referenced in the PR body."""
    return [m.group(1).upper() for m in CLOSES_PATTERN.finditer(pr_body)]


def update_gaps_file(
    gaps_file: Path,
    pr_body: str,
    pr_number: str,
    merged_date: str,
) -> tuple[int, list[str]]:
    """
    Read gaps_file, move closed gaps from Active → Completed.
    Returns (number_of_gaps_moved, list_of_gap_ids_moved).
    Raises FileNotFoundError if gaps_file doesn't exist.
    """
    text = gaps_file.read_text(encoding="utf-8")
    gap_ids = find_gap_ids_in_pr_body(pr_body)

    if not gap_ids:
        print("No 'Closes GAP-NNN' references found in PR body. Nothing to do.")
        return 0, []

    print(f"Found gap references in PR body: {', '.join(gap_ids)}")

    sections = parse_sections(text)
    active_key = next((k for k in sections if k.lower() == "active"), None)
    completed_key = next((k for k in sections if k.lower() == "completed"), None)

    if active_key is None:
        print("WARNING: No '## Active' section found in GAPS.md. Skipping.", file=sys.stderr)
        return 0, []

    moved: list[str] = []

    for gap_id in gap_ids:
        idx = find_row(sections[active_key], gap_id)
        if idx is None:
            print(f"  {gap_id}: not found in Active table — already completed or unknown. Skipping.")
            continue

        row_line = sections[active_key][idx]
        parsed = parse_active_row(row_line)
        if parsed is None:
            print(f"  {gap_id}: could not parse row — skipping.")
            continue

        # Remove from Active
        sections[active_key].pop(idx)

        # Append to Completed
        completed_row = format_completed_row(parsed, merged_date, pr_number)
        if completed_key is not None:
            # Find the end of the table in Completed section and insert before trailing blank lines
            sections[completed_key].append(completed_row)
        else:
            # No Completed section — create one at the end
            sections["Completed"] = [
                "\n## Completed\n\n",
                "| ID | Title | Priority | Category | Completed | PR |\n",
                "|----|-------|----------|----------|-----------|-----|\n",
                completed_row,
            ]

        print(f"  ✓ {gap_id}: moved from Active → Completed (PR #{pr_number}, {merged_date})")
        moved.append(gap_id)

    if moved:
        gaps_file.write_text(reassemble(sections), encoding="utf-8")
        print(f"\nUpdated {gaps_file}: moved {len(moved)} gap(s) to Completed.")
    else:
        print("\nNo gaps were moved (all referenced gaps were already completed or not found).")

    return len(moved), moved


# ── CLI entry point ───────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Move closed gaps from Active to Completed in GAPS.md"
    )
    parser.add_argument(
        "--gaps-file",
        default="GAPS.md",
        help="Path to GAPS.md (default: GAPS.md)",
    )
    parser.add_argument(
        "--pr-body",
        required=True,
        help="Full text of the PR body (used to detect 'Closes GAP-NNN')",
    )
    parser.add_argument(
        "--pr-number",
        required=True,
        help="PR number (used for the Completed table PR link)",
    )
    parser.add_argument(
        "--merged-date",
        default=str(date.today()),
        help="ISO date of the PR merge (default: today)",
    )

    args = parser.parse_args()
    gaps_file = Path(args.gaps_file)

    if not gaps_file.exists():
        print(f"ERROR: {gaps_file} not found.", file=sys.stderr)
        return 1

    try:
        n, ids = update_gaps_file(
            gaps_file=gaps_file,
            pr_body=args.pr_body,
            pr_number=args.pr_number,
            merged_date=args.merged_date,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    # Set GitHub Actions output
    ids_str = ",".join(ids) if ids else ""
    print(f"\n::set-output name=gaps_moved::{n}")
    print(f"::set-output name=gap_ids::{ids_str}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
