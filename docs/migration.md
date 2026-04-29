# Migration Guide — Rural Peds Gap Analysis Standard v1.0

This guide covers how to migrate an existing ruralpeds repo into the Gap Analysis Standard.

---

## Prerequisites

- You have `gh` CLI installed and authenticated as a ruralpeds member
- You have write access to the target repo
- The target repo is cloned locally

---

## Option A — Automated Bootstrap (recommended for repos with no existing GAPS.md)

```bash
cd ~/Documents/github/<repo-name>

curl -fsSL \
  https://raw.githubusercontent.com/ruralpeds/gap-analysis-standard/main/templates/bootstrap-gaps.sh \
  | bash
```

This creates `GAPS.md`, appends the `CLAUDE.md` snippet, and creates `.github/workflows/gaps.yml`.
Then edit `GAPS.md` to replace the placeholder row with your real gaps.

---

## Option B — Manual Migration (for repos with existing gap data)

### Step 1: Create GAPS.md from existing gap data

If the repo has an existing gap analysis in any format (JSON, markdown section, comments in
CLAUDE.md, etc.), convert it into the GAPS.md table format:

```markdown
| GAP-001 | Description of gap | P1 | content | YYYY-MM-DD | |
```

Rules:
- Assign sequential IDs starting at GAP-001 (or continue from the highest existing ID)
- Set Priority based on urgency: P0 = blocking, P1 = this sprint, P2 = next, P3 = backlog
- Use the closest matching Category from: safety, quality, content, infrastructure, docs,
  research, teaching, creative, general
- Created date = today if unknown

### Step 2: Append CLAUDE.md snippet

```bash
echo "" >> CLAUDE.md
echo "---" >> CLAUDE.md
echo "" >> CLAUDE.md
curl -fsSL \
  https://raw.githubusercontent.com/ruralpeds/gap-analysis-standard/main/templates/CLAUDE.md.snippet \
  >> CLAUDE.md
```

### Step 3: Create the workflow file

```bash
mkdir -p .github/workflows
cat > .github/workflows/gaps.yml <<'EOF'
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
EOF
```

### Step 4: Commit and push

```bash
git add GAPS.md CLAUDE.md .github/workflows/gaps.yml
git commit -m "chore: migrate to gap analysis standard v1.0"
git push
```

---

## Repos with existing gap JSON files (Peds, PedNeoSim)

The Peds repo and PedNeoSim.jl have existing gap analysis JSON files
(`GAP_ANALYSIS.json`, `SIMULATION_GAP_ANALYSIS.json`, etc.). To convert:

```bash
python3 - <<'EOF'
import json, sys
from pathlib import Path
from datetime import date

# Load existing JSON gap analysis
gap_json = Path("docs/GAP_ANALYSIS.json")
if not gap_json.exists():
    print("No JSON gap file found. Use manual migration instead.")
    sys.exit(0)

with open(gap_json) as f:
    data = json.load(f)

today = str(date.today())
rows = []

# Adjust these field names to match your actual JSON schema
for i, gap in enumerate(data.get("gap_subjects", []), start=1):
    gap_id = f"GAP-{i:03d}"
    title = gap.get("title", gap.get("name", "Unknown"))[:60]
    priority = gap.get("priority", "P2").upper()
    category = gap.get("category", "content").lower()
    notes = gap.get("notes", "")[:120]
    rows.append(f"| {gap_id} | {title} | {priority} | {category} | {today} | {notes} |")

header = """# Gaps — <REPO-NAME>

## Active

| ID | Title | Priority | Category | Created | Notes |
|----|-------|----------|----------|---------|-------|
"""
print(header + "\n".join(rows))
EOF
```

Redirect the output to `GAPS.md` and review before committing.

---

## Rollout Priority Order (recommended)

Based on repo activity and existing gap data:

1. **ruralpeds/Peds** — pilot repo; has COMSEP/ABP/ACGME gap data ready to seed
2. **timothyhartzog/Patient-simulation-julia** — has `SIMULATION_GAP_ANALYSIS.json`
3. **ruralpeds/textbook** — has existing GAPS.md (18 gaps, seeded April 2026)
4. **ruralpeds/rust-sci-core** — active multi-crate workspace
5. All other ruralpeds repos — use bootstrap-gaps.sh

---

## Verifying the Migration

After pushing:

1. Open a test PR with body `Test migration. Closes GAP-001.`
2. Merge the PR
3. Confirm the `Gap Lifecycle` action runs and moves GAP-001 to Completed
4. Confirm GAP-001 appears in the Completed table with the PR link

If the action fails, check:
- That `.github/workflows/gaps.yml` uses `types: [closed]`
- That the PR was *merged* not just *closed*
- That `GAPS.md` has a properly formatted `## Active` table
- That the repo's Actions permissions allow `contents: write`
