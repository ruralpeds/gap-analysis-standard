#!/usr/bin/env bash
# =============================================================================
# bootstrap-gaps.sh
# Rural Peds Gap Analysis Standard v1.0
# Spec: https://github.com/ruralpeds/gap-analysis-standard/blob/main/SPEC.md
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/ruralpeds/gap-analysis-standard/main/templates/bootstrap-gaps.sh | bash
#
# What it does:
#   1. Creates GAPS.md from the standard template
#   2. Appends the CLAUDE.md gap-analysis block
#   3. Creates .github/workflows/gaps.yml (calls org reusable workflow)
# =============================================================================

set -euo pipefail

ORG_GITHUB="ruralpeds/.github"
STANDARD_REPO="ruralpeds/gap-analysis-standard"
RAW_BASE="https://raw.githubusercontent.com/${STANDARD_REPO}/main"
REPO_NAME=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)")

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Rural Peds Gap Analysis Standard — Bootstrap"
echo "  Repo: ${REPO_NAME}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── Step 1: GAPS.md ──────────────────────────────────────────────────────────
if [ -f "GAPS.md" ]; then
  echo "✓ GAPS.md already exists — skipping."
else
  echo "→ Creating GAPS.md ..."
  curl -fsSL "${RAW_BASE}/templates/GAPS.md" \
    | sed "s/<REPO-NAME>/${REPO_NAME}/g" \
    | sed "s/YYYY-MM-DD/$(date +%Y-%m-%d)/g" \
    > GAPS.md
  echo "✓ GAPS.md created."
fi

echo ""

# ── Step 2: CLAUDE.md snippet ─────────────────────────────────────────────────
SNIPPET_MARKER="## Gap Analysis"
if [ -f "CLAUDE.md" ] && grep -q "${SNIPPET_MARKER}" CLAUDE.md; then
  echo "✓ CLAUDE.md already has Gap Analysis block — skipping."
else
  echo "→ Appending Gap Analysis block to CLAUDE.md ..."
  [ ! -f "CLAUDE.md" ] && echo "# Claude Instructions for ${REPO_NAME}" > CLAUDE.md
  printf '\n---\n\n' >> CLAUDE.md
  curl -fsSL "${RAW_BASE}/templates/CLAUDE.md.snippet" >> CLAUDE.md
  echo "✓ CLAUDE.md updated."
fi

echo ""

# ── Step 3: GitHub Actions workflow ──────────────────────────────────────────
WORKFLOW_PATH=".github/workflows/gaps.yml"
if [ -f "${WORKFLOW_PATH}" ]; then
  echo "✓ ${WORKFLOW_PATH} already exists — skipping."
else
  echo "→ Creating ${WORKFLOW_PATH} ..."
  mkdir -p .github/workflows
  cat > "${WORKFLOW_PATH}" <<EOF
name: Gap Lifecycle

on:
  pull_request:
    types: [closed]

jobs:
  lifecycle:
    uses: ${ORG_GITHUB}/.github/workflows/reusable-gap-lifecycle.yml@main
    with:
      gaps_file: 'GAPS.md'
    secrets: inherit
EOF
  echo "✓ ${WORKFLOW_PATH} created."
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Bootstrap complete!"
echo ""
echo "  Next steps:"
echo "  1. Edit GAPS.md — replace the example row with your real gaps."
echo "  2. Commit all three files:"
echo "     git add GAPS.md CLAUDE.md ${WORKFLOW_PATH}"
echo "     git commit -m 'chore: bootstrap gap analysis standard v1.0'"
echo "     git push"
echo "  3. When a PR closes a gap, include 'Closes GAP-NNN' in the body."
echo ""
echo "  Spec: https://github.com/${STANDARD_REPO}/blob/main/SPEC.md"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
