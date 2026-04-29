# Rural Peds Gap Analysis Standard

**Version:** 1.0  
**Status:** Active  
**Spec:** [SPEC.md](./SPEC.md)

A lightweight, uniform system for tracking content gaps across all `ruralpeds`
repositories. Every participating repo gets a `GAPS.md` file, a `CLAUDE.md`
snippet that makes Claude Code gap-aware, and a GitHub Actions workflow that
auto-closes gaps when PRs are merged.

---

## Quick Start (30 seconds)

```bash
cd ~/Documents/github/<your-repo>

curl -fsSL \
  https://raw.githubusercontent.com/ruralpeds/gap-analysis-standard/main/templates/bootstrap-gaps.sh \
  | bash
```

Then edit `GAPS.md` to replace the example row with your real gaps, commit, and push.

---

## How It Works

```
You identify a gap → add a row to GAPS.md Active table
You build the fix  → open a PR with "Closes GAP-NNN" in the body
PR is merged       → gap-lifecycle Action auto-moves row to Completed
```

Claude Code reads `GAPS.md` at the start of every session (via the CLAUDE.md
snippet) and knows which gaps are pending, their priorities, and what to work on next.

---

## Repository Layout

```
gap-analysis-standard/
├── SPEC.md                        ← Full specification (versioned)
├── templates/
│   ├── GAPS.md                    ← Copy-paste template for new repos
│   ├── CLAUDE.md.snippet          ← Paste into consumer repo CLAUDE.md
│   └── bootstrap-gaps.sh          ← One-command setup script
├── .github/workflows/
│   ├── gap-lifecycle.yml          ← Reusable workflow (workflow_call)
│   └── hygiene.yml                ← Stale PR/issue cleanup
├── actions/
│   └── update-gaps/
│       ├── action.yml             ← Composite action definition
│       ├── update_gaps.py         ← Python: moves rows Active → Completed
│       └── test_update_gaps.py    ← pytest suite (40+ assertions)
├── julia/
│   └── GapsCLI.jl                 ← Local CLI: gap list / add / next / stats
└── docs/
    ├── migration.md               ← How to migrate existing repos
    └── aggregation.md             ← Design for the gap-dashboard aggregator
```

---

## Consumer Repo Setup (manual)

**1.** Create `GAPS.md` — copy from `templates/GAPS.md` and seed with real gaps.

**2.** Add the CLAUDE.md snippet — copy `templates/CLAUDE.md.snippet` into your `CLAUDE.md`.

**3.** Create `.github/workflows/gaps.yml`:

```yaml
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

**4.** Commit and push all three files.

---

## Gap Schema

| Field | Values | Notes |
|-------|--------|-------|
| ID | GAP-NNN | Sequential, never reused |
| Title | ≤60 chars | Imperative: "Add X", "Fix Y" |
| Priority | P0 / P1 / P2 / P3 | P0 = blocking, P3 = backlog |
| Category | safety, quality, content, infrastructure, docs, research, teaching, creative, general | |
| Created | YYYY-MM-DD | |
| Notes | ≤120 chars | Optional |

---

## Local CLI

```bash
julia julia/GapsCLI.jl list
julia julia/GapsCLI.jl next
julia julia/GapsCLI.jl add "Title" --priority P1 --category content
julia julia/GapsCLI.jl stats
```

---

## Running Tests

```bash
cd actions/update-gaps
pip install pytest --break-system-packages
pytest test_update_gaps.py -v
```

---

## Rollout Status

| Repo | Bootstrapped | GAPS.md seeded | Workflow wired |
|------|-------------|----------------|----------------|
| ruralpeds/gap-analysis-standard | ✅ | ✅ | ✅ |
| ruralpeds/Peds | ⬜ | ⬜ | ⬜ |
| ruralpeds/textbook | ⬜ | partial | ⬜ |
| ruralpeds/rust-sci-core | ⬜ | ⬜ | ⬜ |
| timothyhartzog/Patient-simulation-julia | ⬜ | ⬜ | ⬜ |
