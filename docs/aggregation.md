# Gap Dashboard — Aggregation Design

This document describes how `ruralpeds/gap-dashboard` will aggregate GAPS.md
files from all tracked repos into org-wide views.

> **Status:** Planned (GAP-017 in the standard repo). This document is the design spec.

---

## Architecture

```
ruralpeds/gap-dashboard/
├── README.md
├── .github/workflows/
│   └── aggregate.yml          ← runs nightly + on manual trigger
├── scripts/
│   └── aggregate_gaps.py      ← pulls GAPS.md from each tracked repo
├── config/
│   └── repos.yml              ← list of repos to track
├── output/                    ← auto-generated, committed by the action
│   ├── ALL-GAPS.md
│   ├── BY-PRIORITY.md
│   ├── BY-CATEGORY.md
│   └── RECENTLY-COMPLETED.md
└── docs/
    └── adding-a-repo.md
```

---

## `config/repos.yml`

Declares which repos to track. Each entry is one line:

```yaml
repos:
  - ruralpeds/Peds
  - ruralpeds/textbook
  - ruralpeds/rust-sci-core
  - ruralpeds/gap-analysis-standard
  - timothyhartzog/Patient-simulation-julia
```

To add a new repo: open a PR adding a line to this file. The aggregator picks it
up on the next run.

---

## `scripts/aggregate_gaps.py`

Workflow:

1. For each repo in `config/repos.yml`, fetch `GAPS.md` via the GitHub Contents API
2. Parse the Active and Completed tables using the same section parser as `update_gaps.py`
3. Tag each row with its source repo (`ruralpeds/Peds#GAP-001`)
4. Merge all rows into unified tables
5. Write the four output files to `output/`
6. Commit and push to dashboard repo main branch

The action uses a fine-grained PAT stored as an Actions secret with read-only access to all tracked repos.

---

## Output Files

### `ALL-GAPS.md`

Full list of all active gaps across all repos, sorted by Priority then Created:

```markdown
# All Active Gaps — ruralpeds org

| Repo | ID | Title | Priority | Category | Created |
|------|----|-------|----------|----------|---------|
| Peds | GAP-001 | Add NRP decision tree | P0 | content | 2026-04-01 |
| textbook | GAP-002 | Convert _imports books | P1 | infrastructure | 2026-04-10 |
```

### `BY-PRIORITY.md`

Gaps grouped under P0, P1, P2, P3 headings, across all repos.

### `BY-CATEGORY.md`

Gaps grouped under each category heading (safety, content, infrastructure, etc.).

### `RECENTLY-COMPLETED.md`

Gaps completed in the last 30 days, sorted by Completed date descending:

```markdown
# Recently Completed (last 30 days)

| Repo | ID | Title | Completed | PR |
|------|----|-------|-----------|-----|
| Peds | GAP-001 | Add NRP decision tree | 2026-04-28 | ruralpeds/Peds#42 |
```

---

## `aggregate.yml` Trigger Schedule

```yaml
on:
  schedule:
    - cron: '0 5 * * *'     # 05:00 UTC daily
  workflow_dispatch:          # manual trigger
  repository_dispatch:        # can be called by consumer repo actions after merge
    types: [gap-closed]
```

The `repository_dispatch` trigger allows consumer repo gap-lifecycle actions to
notify the dashboard immediately after a merge, rather than waiting for the
nightly cron.

---

## Implementation Notes

- The aggregator is purely a reader — it never writes to consumer repos
- `output/` files are auto-generated; manual edits will be overwritten
- The dashboard repo's own `GAPS.md` tracks infrastructure gaps for the dashboard itself
- Per-repo `GAPS.md` files remain canonical; the dashboard is a read-only mirror
