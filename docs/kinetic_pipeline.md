# Kinetic Pipeline: Kanban Card → Action → ERP Connector

This repo implements a **Foundry-style Kinetic boundary**:

> **Object (Kanban Card)** → **Typed Action** → **Connector** → **Audit + Result**

The goal is to demonstrate the *shape* of an enterprise execution loop while staying runnable locally.

## 1) Objects
Objects live in canonical fact tables:
- `erp_orders` (Order)
- `wms_shipments` (Shipment)
- `mes_production` (ProductionRecord)
- `agent_cases` (Case)

The Ontology declares these object types and relationships:
- `contracts/supply_chain_ontology.yaml`

## 2) Actions
Actions are **typed** (not free-form buttons), e.g.:
- `TriggerPurchase`
- `ExpediteShipment`
- `RebalanceAllocation`

They are declared in the Ontology under `action_types`.

## 3) Execution Boundary
Execution is centralized in:
- `agent_runtime/app/execution.py`

It:
1. applies demo guardrails (fail closed)
2. records an action row in `agent_actions`
3. calls the ERP connector
4. writes back the result message

## 4) ERP Connector
The connector interface is:
- `agent_runtime/app/connectors/erp.py`

The demo uses `ERP_CONNECTOR=mock`.

To implement a real connector, add a new class implementing `ERPConnector.execute(...)`, then register it in `get_erp_connector()`.

## 5) API
The Object Graph API exposes execution via:

`POST /actions/execute`

Example:
```json
{
  "case_id": "<uuid>",
  "channel": "ui",
  "action_type": "TriggerPurchase",
  "payload": {"sku": "MEM-16G", "qty": 200, "need_date": "2026-02-20"}
}
```

The response returns an `action_id` and a connector result.

## Why this matters
Most BI tools are *read-only*. A Kinetic layer makes the ontology **read-write**:
- analysis → decision → execution → feedback

This is the key difference between dashboards and operational systems.


## 6) Card Status as a Kinetic Action (UpdateCardStatus)

Card state transitions are modeled as a **typed kinetic action**:

- `action_type`: `UpdateCardStatus`
- `payload`:
  - `card_id` (required)
  - `new_status` (required): `todo|in_progress|blocked|resolved`
  - `blocked_reason` (required if `blocked`)
  - `resolved_at` (required if `resolved`, ISO 8601)

### Guardrails
The system enforces SLA policy guardrails in **two places**:

1) API guardrails (execution boundary):
- `blocked` requires `blocked_reason`
- `resolved` requires `resolved_at`
- `card.case_id` must match `request.case_id`

### State machine + approval gate
`UpdateCardStatus` also enforces a conservative **state machine**:

- `todo` → `in_progress` | `blocked`
- `in_progress` → `blocked` | `resolved`
- `blocked` → `in_progress`
- `resolved` → (no transitions)

And a demo **approval gate** for `resolved`:

- `channel` must be `supervisor`
- the underlying `agent_cases.risk_score` must be **high** (default: `>= 70`)

These are implemented in `agent_runtime/app/execution.py` so they can evolve without DB migrations.

### Auditing violations
Any blocked attempt (illegal transition, missing approval, missing SLA fields, etc.) is still written to `agent_actions` with a `result` string beginning with `blocked:`.

2) DB-level CHECK constraints:
- `status='blocked' → blocked_reason IS NOT NULL`
- `status='resolved' → resolved_at IS NOT NULL`

`UpdateCardStatus` is executed against the canonical DB (`connector=local_db`), while other actions route through the ERP connector.



## Dry run validation

`POST /actions/execute?dry_run=1` will run the same guardrails (including state machine + approval gate) but **will not** write an audit row and **will not** mutate the database or call external connectors. This is intended for UI pre-validation.


## Governance policy (hot reload)

Card status policy (allowed transitions, approval gate threshold/channel, SLA guardrails) is loaded from `governance/policy.yaml` and hot-reloaded based on file mtime. Editing the file changes behavior without migrations.

## Governance policy hot update (dev only)

- `GET /governance/policy` returns the effective policy and file path.
- `POST /governance/policy` (dev only) overwrites the policy YAML and takes effect immediately via hot-reload.

Enable dev mode with `APP_ENV=dev` or `DEV_MODE=1`.
