# Architecture — Supply Chain Kanban AI Agent

## Intent

This repo is a professional supply-chain manager-agent. It should operate like a team lead or department manager, not like a passive dashboard.

The manager-agent watches supply-chain signals, opens risk cases, assigns owners, recommends mitigations, routes approvals, executes governed writebacks, and keeps evidence for review.

## System shape

```text
External Systems
  ERP / WMS / TMS / MES / supplier portals / SiteTrack / market feeds
      |
      v
Integration Adapters
  normalize source-specific payloads
      |
      v
Canonical Event Model
  order, shipment, inventory, supplier, container, exception, location, approval, receipt
      |
      v
Risk Case Engine
  detect issue, score risk, create/update Kanban case
      |
      v
Impact + Recommendation Engine
  quantify impact and propose mitigations
      |
      v
Policy + Approval Gate
  decide whether auto-execute, request approval, or block
      |
      v
Governed Execution
  write back to ERP/WMS/TMS/supplier systems through typed connectors
      |
      v
Receipt + Evidence Layer
  store audit trail and optional blockchain evidence anchor
      |
      v
Kanban Command Board
  human operating surface for team lead / crisis manager
```

## Runtime boundaries

```text
apps/api/       API, policy, case state, execution, audit, connector stubs
apps/web/       browser Kanban command board
contracts/      shared lifecycle/action/ontology contracts
operations/     policy, dashboards, scenarios, planning examples
data/           local schema, seed data, sample ingest payloads
integrations/   optional integration pack specifications
docs/           product, architecture, integration, compliance, and demo docs
```

## Manager-agent responsibilities

The agent should act like a professional supply-chain team lead:

1. **Watch** operating signals from ERP/WMS/TMS/SiteTrack/suppliers/market feeds.
2. **Triage** by impact, urgency, confidence, customer promise, and SLA.
3. **Explain** root cause, evidence, and affected entities.
4. **Recommend** a mitigation with cost/service/risk trade-offs.
5. **Route** approvals based on policy and business impact.
6. **Execute** approved actions through governed connectors.
7. **Prove** what happened through receipts, audit events, and optional blockchain evidence anchors.
8. **Learn** from outcome and postmortem results.

## Kanban as operating model

A card is not a task. A card is a **Supply Chain Risk Case**.

Professional flow:

```text
Signal Intake -> Triage -> Mitigation Planning -> Approval Gate -> Executing -> Resolved / Learning
```

Crisis flow:

```text
Critical Now -> At Risk <24h -> Watchlist -> Awaiting Approval -> Recovery Actions -> Stabilized
```

## Blockchain boundary

Blockchain is an evidence ledger, not the operational database.

Use it for:

- case evidence hash
- approval proof
- SiteTrack handoff/location proof hash
- execution receipt hash
- cross-party provenance checkpoint

Do not use it for:

- live board state
- high-volume event storage
- private commercial details
- replacing ERP/WMS/TMS master data

## SiteTrack boundary

SiteTrack is the physical-world oracle for container and asset movement:

```text
container_id, asset_id, last_seen_at, location_proof, geofence_event,
handoff_event, offline_capture, signature, confidence
```

SiteTrack events should become canonical location/handoff events. The agent then uses them to open or update Kanban cases such as delayed container, wrong-yard handoff, missing shipment, or high-value asset risk.

## ERP integration boundary

The product must integrate with existing ERP systems, not replace them.

Connector responsibilities:

```text
read current order/shipment/inventory/supplier state
simulate a recommended change
enforce policy and approval requirements
execute only approved typed actions
return a receipt with external reference and status
```

Initial connector priorities:

1. CSV/API import pack
2. Odoo connector pack
3. SAP adapter spec
4. Oracle / NetSuite adapter spec
5. WMS/TMS adapter specs
6. SiteTrack location oracle adapter
7. Blockchain evidence adapter


## Local runtime entrypoints

The canonical local browser command is:

```bash
cp .env.example .env
make demo-web
```

Open:

```text
Kanban command board: http://localhost:8080
API docs:              http://localhost:8000/docs
```

API-only mode:

```bash
make demo-min
```

Manager-agent mode:

```bash
make demo-agent
```

Detailed runbook: `docs/demo/RUN_LOCAL_UI.md`.

## UI technology boundary

Current UI is static HTML/CSS/JavaScript under `apps/web/public/` so the repo stays easy to run.

Recommended future professional UI stack:

```text
React + Vite + TypeScript + Tailwind CSS + shadcn/ui
```

Decision doc: `docs/product/UI_FRAMEWORK_DECISION.md`.

## Quality gates

Every architecture change should preserve:

```bash
make test
```

Expected core gate:

```text
python3 scripts/run_checks.py
# includes Python syntax compile checks and pytest
```

## Blockchain operating modes

The architecture supports two modes:

```text
Mode A: evidence layer — app DB is operational system of record; ledger stores proof anchors.
Mode B: operational ledger — permissioned ledger is append-only cross-party event source; app DB is a read model.
```

Default to Mode A for MVP and customer pilots. Use Mode B only when multiple companies require shared operational truth. Details: `docs/architecture/BLOCKCHAIN_OPERATIONAL_DATABASE_DECISION.md`.


## Streamlit AI-agent debug cockpit

Streamlit is the selected near-term tool for AI-agent debugging. It lives under `apps/debug_ui/` and should read the FastAPI API surface first. It is used to inspect recommendation traces, policy decisions, SiteTrack container events, ERP writeback receipts, and blockchain anchor status. It is not the long-term production operator UI.
