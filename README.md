# Gap Analysis Standard

Reusable standard for gap analysis across ruralpeds projects.

## Schema

```yaml
gap_id: "GAP-001"
title: "Clear title"
description: "Detailed description"
priority: "P1|P2|P3"
status: "accepted|proposed|in-progress|completed"
owner: "username"
created: "2026-04-23"
updated: "2026-04-23"
```

## GitHub Actions Workflow

Template in `workflows/gaps-aggregator.yml` for auto-collecting gaps from all repos.

## Files

- `GAPS.md` — canonical source per repo
- `gaps.yml` — structured data
- `workflows/gaps-aggregator.yml` — auto-sync workflow
