# Amazon Nova Hackathon Mode (Devpost-ready)

This repo includes a **Hackathon Mode** that demonstrates a Foundry-style flow:

**KanbanCard (Object)** → **Recommendation (LLM)** → **Proposed Actions** → **Governance + Dry-run** → **Execute + Audit**

## Quick start (mock, no AWS creds)

1. Start stack
2. Open Swagger UI: `http://localhost:8000/docs`
3. Run: `POST /demo/nova/run` with a `card_id`

The mock mode is deterministic and works offline.

## Enable Amazon Nova via Bedrock

Set env vars (see `.env.example`):

- `HACKATHON_MODE=amazon_nova`
- `AWS_REGION=...`
- `NOVA_MODEL_ID=...`

If Bedrock invocation fails (missing creds / wrong request shape), the connector **falls back to mock** so demos never break.

## Demo endpoints

- `POST /demo/nova/run`
  - Generates recommendation + action proposals
  - Validates each proposal using `execute_action(..., dry_run=True)` so you see governance gates without writing.

## Why this is “risk mitigation” + “agentic automation”

- **Risk mitigation**: the model explains why a resource is at risk using recent ops/market signals
- **Agentic automation**: the system proposes *typed* actions and validates them against policy (state machine, approval gates, SLA guardrails)


## Materialize for UI (AI suggestion -> pending actions -> approval -> execute)

- POST `/demo/nova/run_and_materialize` (writes `agent_recommendations` + `pending_actions`)
- GET `/cases/{case_id}/recommendations`
- GET `/cases/{case_id}/pending_actions`
- PATCH `/pending_actions/{pending_id}/decision` (approve/reject)
- POST `/pending_actions/{pending_id}/execute?dry_run=1`


## UI-safe idempotency (avoid duplicates)
For endpoints that create or commit state, you can send an `Idempotency-Key` header.

- `POST /demo/nova/run_and_materialize`:
  - Re-using the same key for the same card returns the same materialization (no duplicate pending actions).
  - Re-using with a different payload returns `409`.

- `PATCH /pending_actions/{id}/decision` and `POST /pending_actions/{id}/execute`:
  - Re-tries with the same key are treated as idempotent.

## RBAC-lite (channel/role)
This repo uses a lightweight RBAC derived from `governance/policy.yaml`:

- `channel=ui` → role `operator`
- `channel=supervisor` → role `supervisor`

Approvals and executions are allowed/denied by policy and violations are audited.


## Idempotency TTL / cleanup

- Default TTL: 24 hours (policy: `idempotency_policy.ttl_hours`).
- A cleanup loop container can periodically delete expired materializations, allowing safe Idempotency-Key reuse.
- In dev you can also call `POST /maintenance/cleanup`.


## JWT / SSO / API gateway integration

RBAC actor resolution precedence:
1. API gateway headers: `X-User-Role`, `X-User-Email`, `X-User-Id` (recommended)
2. Bearer JWT claims (unverified unless `JWT_VERIFY=1` + `JWT_SECRET`)
3. Fallback to `rbac.channels` mapping using `channel`

This makes it easy to put an API gateway/SSO (Okta/AzureAD/Cognito) in front: gateway verifies JWT, then forwards trusted role headers.


## Idempotency conflict handling
If the same Idempotency-Key (scoped by endpoint+subject+card_id) is reused with a different request payload/options, the API returns 409 and records an audit event (action_type: IdempotencyConflict).
