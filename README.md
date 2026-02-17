# Supply Chain Kanban – Foundry-style Ontology + AI Agents (Demo)

Most supply-chain systems see the world as **tables** (ERP rows, WMS rows, MES rows).
Leaders see the world as **objects**: orders, shipments, plants, suppliers, constrained resources.

This repo is a minimal, runnable demonstration of a **Foundry-like pattern** applied to supply chain:

- **Ontology (Semantic layer):** map fragmented facts into real-world objects + relationships
- **Kinetic (Execution layer):** turn dashboards into *actions* (typed write-backs) with audit trails
- **Dynamic (Evolution layer):** evolve the model as new risks/rules appear, without rewriting the whole stack

In short: this is **not** just dashboards. It is an *operational supply-chain object graph*.

## What this demo shows
- Early detection of constraints using market + ops signals
- Multi-agent case creation, scenario simulation, and ranked recommendations
- Ontology-driven object model (orders / shipments / production / cases)
- A minimal Object Graph API (FastAPI)
- Kinetic actions (execute typed actions, mock ERP connector, auditable action log)

## What this is NOT
- Not a production deployment (no HA, no enterprise auth, no full RBAC model)
- Not connected to real ERP/SAP/Oracle by default (uses a mock connector)
- Not fully autonomous execution (human-in-the-loop is the default posture)

## Ontology
See:
- `contracts/supply_chain_ontology.yaml`
- `contracts/supply_chain_ontology.json`

These define:
- **Object types** (Order, Shipment, ProductionRecord, Case, Recommendation, Action, ...)
- **Relationships** (Shipment fulfills Order, Case targets Resource, ...)
- **Action types** (TriggerPurchase, ExpediteShipment, RebalanceAllocation, ...)

## Object Graph API (FastAPI)
The demo includes a minimal API surface:

- `GET /health`
- `GET /ontology` (`/json` / `/yaml`)
- `GET /objects/...` (order, shipment, production, resource)
- `GET /cases/...` (cases, recommendations, scenarios, actions)
- `GET /graph/neighbors?...` (lightweight graph expansion)
- `POST /actions/execute` (typed action execution + audit)

When you run Docker Compose, the API is exposed on port `8000`.

## Quick start
```bash
cp .env.example .env
# API + agent (no UI)
make demo

# Minimal (DB + API only)
make demo-min

# Optional: include Superset UI
make demo-ui

# Full demo (UI + agent) + smoke + checklist
make demo-all
```

- API docs: http://localhost:8000/docs
- Superset UI: http://localhost:8088 (admin credentials in .env)

Health endpoints:
- /healthz (liveness, no DB)
- /health (DB connectivity)
- /readyz (DB + critical tables / views / extensions)

Error responses are standardized:
- JSON shape: {"error": {"code", "message", "details"}, "request_id"}
- Response header: X-Request-Id (echoed or auto-generated)

See `demo/README.md` for a live-demo walkthrough.


## Repo structure (simplified)
- `/demo` – runnable local demo (Docker + Python)
- `/agent_runtime` – DB schema, ingest, agents, Object Graph API, kinetic execution scaffold
- `/ingest` – ERP/MES/WMS CSV drop zones (demo)
- `/seed` – schema + seed data + demo views
- `/signals` – market signal adapters
- `/dashboards` – board & crisis views
- `/governance` – audit & control artifacts
- `/contracts` – ontology + triggers (schema contracts)

## Audience
- Supply chain leaders
- Enterprise architects
- Risk, audit, and compliance teams
- System integrators (SI)


# supply-chain-kanban v0.1

Includes UI, Superset, Power BI, Slack alerts, Scenario Simulator.

# supply-chain-kanban v0.2

Adds AI agent logic for constraint pattern prediction (generic, product-agnostic).

# supply-chain-kanban v0.3

Adds market signal ingestion, learning dashboards, audit narratives, and agent KPI scorecards.

# supply-chain-kanban v0.4

Multi-agent coordination, regulator appendix, live market adapters, ROI tracking, board visuals.

# supply-chain-kanban v0.5

Adds agent negotiation, auto-contract triggers, supplier portals, regulatory automation, crisis simulation.

# supply-chain-kanban demo

Run a local demo showing AI agents detecting constraints, negotiating, and triggering scenarios.

# supply-chain-kanban documentation

This folder contains conceptual and governance documentation for the AI-agent-based supply chain demo.

# supply-chain-kanban v0.6 — Agent Core (Runnable Demo)

This repo is a **minimal, runnable AI-agent core** for supply chain constraint detection.
It creates **cases**, persists **scenario outputs per case**, runs **ingest adapters** (ERP/MES/WMS),
enforces **data quality gates**, and can send **Slack alerts**.

## Quick demo
```bash
make demo
make logs
make psql
```
Then in psql:
```sql
SELECT resource_id, risk_score, status, updated_at FROM agent_cases ORDER BY updated_at DESC;
SELECT * FROM agent_scenarios ORDER BY created_at DESC LIMIT 10;
SELECT * FROM agent_recommendations ORDER BY created_at DESC LIMIT 10;
SELECT * FROM dq_results ORDER BY ts DESC LIMIT 20;
```

## Ingest adapters
Drop CSV files into `./ingest/erp/`, `./ingest/mes/`, `./ingest/wms/` (examples included).
The agent ingests and upserts into canonical tables.

## Data quality gates
Before creating/updating cases, the agent runs blocking checks (nulls, ranges, referential).
Failures are persisted to `dq_results` and cases are paused for the affected scope.

## Scenario outputs
For every case, the agent generates Base / SupplyShock / PriceShock / DoubleHit scenarios and persists them to `agent_scenarios`.


### Governance policy (hot reload)

Card state machine + approval gates live in `governance/policy.yaml` and are loaded at runtime (mtime-based hot reload).

### Dry-run validation

Use `POST /actions/execute?dry_run=1` to validate guardrails without writing audit rows or mutating the DB.

### Governance API (dev)

- `GET /governance/policy` – returns effective governance policy.
- `POST /governance/policy` – updates policy (dev only; set `APP_ENV=dev` or `DEV_MODE=1`).


## Hackathon Mode (Amazon Nova)

- `POST /demo/nova/run` produces a recommendation + proposed actions for a KanbanCard.
- Works offline (mock). Set `HACKATHON_MODE=amazon_nova` + `NOVA_MODEL_ID` to enable Bedrock.
- Use `dry_run=true` to validate proposals against governance without writing.


### UI approval flow endpoints
- POST `/demo/nova/run_and_materialize`
- GET `/cases/{case_id}/recommendations`
- GET `/cases/{case_id}/pending_actions`
- GET `/pending_actions?status=pending`
- PATCH `/pending_actions/{pending_id}/decision`
- POST `/pending_actions/{pending_id}/execute?dry_run=1`


### v13 Enterprise hardening
- **Idempotency scope**: endpoint + subject + card_id (prevents cross-user collisions).
- **RBAC payload rules (policy.yaml)**: enforce role/risk thresholds based on action payload (e.g. UpdateCardStatus.resolved requires supervisor + risk>=X).
