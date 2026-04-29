# Rural Peds Gap Analysis Standard — Specification

**Version:** 1.0  
**Status:** Active  
**Maintainer:** ruralpeds org  
**Last revised:** 2026-04-28

---

## 1. Purpose

This specification defines a lightweight, uniform system for tracking content gaps
across all ruralpeds repositories. A *gap* is any missing content, feature, or
infrastructure item that has been identified but not yet built. The standard
ensures that every repo's gap list is machine-readable, Claude Code-compatible,
and aggregatable into org-wide dashboards.

---

## 2. Canonical File: GAPS.md

Every participating repo must have a `GAPS.md` file at the repository root.
This file is the single source of truth for that repo's gap list.

### 2.1 File Structure

```
# Gaps — <repo-name>

## Active

| ID | Title | Priority | Category | Created | Notes |
|----|-------|----------|----------|---------|-------|
| GAP-001 | Example gap title | P1 | content | 2026-04-28 | Optional context |

## Completed

| ID | Title | Priority | Category | Completed | PR |
|----|-------|----------|----------|-----------|-----|
| GAP-000 | Example completed gap | P0 | safety | 2026-04-20 | #12 |

## Abandoned

| ID | Title | Reason |
|----|-------|--------|
```

### 2.2 Column Definitions

**Active table:**
- `ID` — Sequential identifier in format `GAP-NNN` (zero-padded to 3 digits). Unique within the repo.
- `Title` — 60 characters or fewer. Plain English, imperative tone ("Add X", "Fix Y", "Build Z").
- `Priority` — One of: `P0` (blocking/critical), `P1` (high), `P2` (standard), `P3` (low/backlog).
- `Category` — One of: `safety`, `quality`, `content`, `infrastructure`, `docs`, `research`, `teaching`, `creative`, `general`.
- `Created` — ISO date (YYYY-MM-DD) when the gap was identified.
- `Notes` — Optional free text. Keep under 120 characters.

**Completed table:**
- All Active columns except `Notes`, plus:
- `Completed` — ISO date of PR merge.
- `PR` — GitHub PR number as a link, e.g., `#42`.

**Abandoned table:**
- `ID`, `Title`, `Reason` — Free-text reason the gap was closed without completion.

### 2.3 Rules

1. IDs are never reused, even after completion or abandonment.
2. The Active table is ordered by Priority (P0 first), then by Created date (oldest first).
3. Never manually edit the Completed or Abandoned tables — the `gap-lifecycle` action owns them.
4. Cross-repo references use `ruralpeds/<repo>#GAP-NNN` syntax in the Notes column.

---

## 3. Priority Definitions

| Priority | Meaning | Examples |
|----------|---------|---------|
| P0 | Blocking — work in other areas is blocked until this is resolved | Missing infrastructure, broken CI, unsafe clinical content |
| P1 | High — should be addressed in the current sprint | Core content gaps, major usability issues |
| P2 | Standard — next sprint or scheduled backlog | Secondary content, minor improvements |
| P3 | Low / nice-to-have — address when bandwidth allows | Polish, experimental features, future ideas |

---

## 4. Category Definitions

| Category | Scope |
|----------|-------|
| `safety` | Clinical safety, patient harm prevention, NRP/AAP compliance |
| `quality` | CMS quality measures, accreditation requirements, SPC |
| `content` | Clinical or educational content (decision trees, textbooks, guides) |
| `infrastructure` | CI/CD, testing, build tooling, repo structure |
| `docs` | Documentation, README, CLAUDE.md, SPEC.md |
| `research` | Literature review, PubMed integration, evidence base |
| `teaching` | Simulation, education guides, cheat sheets, audio scripts |
| `creative` | Theological fiction, audio drama, historical narrative |
| `general` | Does not fit other categories |

---

## 5. Lifecycle

```
Identified → Active (GAP-NNN created in GAPS.md)
Active → In Progress (PR opened; "Addresses GAP-NNN" in PR body)
In Progress → Completed (PR merged; "Closes GAP-NNN" in PR body → auto-moved by action)
Active → Abandoned (manually moved with reason)
```

The `gap-lifecycle` GitHub Actions reusable workflow handles the Active → Completed
transition automatically when a PR is merged containing `Closes GAP-NNN` in its body.

---

## 6. CLAUDE.md Integration

Every participating repo's `CLAUDE.md` must contain the following block (copy from
`templates/CLAUDE.md.snippet`):

```markdown
## Gap Analysis

This repo follows the Rural Peds Gap Analysis Standard v1.0.
Spec: https://github.com/ruralpeds/gap-analysis-standard/blob/main/SPEC.md

- **Canonical list:** `GAPS.md` at repo root.
- **When starting work:** read the GAPS.md Active table first.
- **When completing work:** include `Closes GAP-NNN` in the PR body.
- **When adding a gap:** append to the Active table with the next sequential ID.
- **Never edit** the Completed or Abandoned tables manually.
- **Cross-repo refs:** use `ruralpeds/<repo>#GAP-NNN` in the Notes column.
```

---

## 7. Reusable Workflow

Consumer repos call the gap lifecycle reusable workflow via:

```yaml
# .github/workflows/gaps.yml in consumer repo
name: Gap Lifecycle

on:
  pull_request:
    types: [closed]

jobs:
  lifecycle:
    uses: ruralpeds/gap-analysis-standard/.github/workflows/gap-lifecycle.yml@v1
    with:
      gaps_file: 'GAPS.md'
    secrets: inherit
```

---

## 8. Versioning

This spec is versioned using git tags on `ruralpeds/gap-analysis-standard`:
- `v1` — current stable (floating tag, always points to latest v1.x)
- `v1.0` — initial release

Consumer repos should pin to `@v1` for automatic minor updates, or to `@v1.0`
for maximum stability.

---

## 9. Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-28 | Initial release |
