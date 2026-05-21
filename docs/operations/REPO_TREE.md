# Repo Tree Guide

## Top-level rule

The repo is organized by product responsibility, not by demo history.

```text
apps/           runnable applications
contracts/      stable shared schemas/contracts
data/           local seed and sample input data
operations/     operating model assets: policy, dashboards, scenarios
integrations/   optional external-system pack specs
docs/           product and architecture explanations
tests/          quality gate
```

## What belongs where

### `apps/api`

FastAPI runtime. Put only runtime Python code here.

### `apps/web`

Browser Kanban command board. Keep the UI focused on case/approval/execution/audit workflow.

### `contracts`

Stable YAML/JSON contracts that multiple modules rely on.

### `data`

Local demo schema, seed packs, sample CSVs, and sample external payloads.

### `operations`

Human operations assets: dashboards, scenarios, governance policy, planning examples, UI view specs.

### `integrations`

Optional pack specs for alerting, market signals, supplier portals, ERP/WMS/TMS/SiteTrack, and future blockchain adapters.

### `docs`

Decision records, architecture, product model, compliance notes, demo instructions, diagrams.

## Anti-clutter rule

Do not add new top-level folders unless they are one of the product responsibility groups above. Prefer adding a subfolder under the existing structure.


Additional tracking docs:

```text
docs/architecture/BLOCKCHAIN_OPERATIONAL_DATABASE_DECISION.md
docs/product/AI_AGENT_OPERATING_MODEL.md
│   ├── DEBUG_UI_DECISION.md
scripts/run_checks.py
```
