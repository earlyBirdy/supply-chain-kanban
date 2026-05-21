# Blockchain Evidence Layer and Operational Database Decision

## Decision

Support two modes, but ship them in this order:

```text
Mode A — Evidence ledger, default v1:
  App DB remains the operational database.
  Blockchain stores proof anchors for evidence, receipts, approvals, and SiteTrack checkpoints.

Mode B — Operational event ledger, advanced consortium mode:
  Permissioned blockchain becomes the append-only cross-party event source.
  App DB becomes a projection/read model for fast Kanban UI, APIs, reports, and debugging.
```

The product should **not** use a public blockchain as the only mutable daily OLTP database. Supply-chain operations need low-latency reads, privacy controls, corrections, retries, ERP compatibility, and simple support/debug workflows.

## Grounding from supply-chain blockchain research

The uploaded EU Blockchain Observatory report says supply-chain transparency starts with traceability, but blockchain adoption depends on reliable external data layers. It specifically highlights that inaccurate data entered into a blockchain creates a “garbage in, garbage out” problem, and that ERP, IoT, APIs, remote sensing, and other off-ledger systems act as the external data/oracle layer for real-world supply-chain events.

Therefore, blockchain can strengthen trust and shared evidence only after source data is validated.

## Mode A — Blockchain as evidence layer

This is the default architecture for MVP, pilots, and ERP-friendly deployments.

```text
ERP / WMS / TMS / SiteTrack / supplier portal
  -> canonical event validator
  -> risk case engine
  -> AI recommendation
  -> approval + governed action
  -> execution receipt
  -> application database
  -> blockchain evidence anchor
```

### What goes on-chain

```text
case proof hash
approval proof hash
execution receipt hash
SiteTrack signed-evidence hash
container handoff checkpoint hash
supplier certificate proof hash
ESG / due-diligence checkpoint hash
correction-event proof hash
```

### What stays off-chain

```text
PII / user identity details
customer-sensitive order details
full ERP documents
pricing and commercial terms
mutable workflow state
large SiteTrack evidence packages
large audit logs
```

### Why Mode A is the default

```text
fast MVP
lower customer integration friction
better privacy and data minimization
easier ERP/WMS/TMS compatibility
easier debugging
works even when ledger adapter is disabled
```

## Mode B — Blockchain as operational database

This is possible only if “operational database” means **append-only operational event ledger**, not a normal mutable relational database.

```text
ERP / WMS / TMS / SiteTrack / supplier portal
  -> canonical event validator
  -> permissioned ledger event append
  -> off-chain projection/read model
  -> Kanban UI / APIs / analytics / Streamlit debug cockpit
  -> governed action execution
  -> receipt event append
```

In this mode, the ledger is the source of truth for cross-party events. The application database is still required, but it becomes a read model/cache used for UI speed, API queries, reports, and local debugging.

### Required design rules

```text
1. Use a permissioned or consortium ledger for enterprise operations.
2. Store append-only canonical events, not mutable rows.
3. Keep a relational read model for Kanban UI, API speed, and support queries.
4. Store sensitive documents off-chain; put only hashes/pointers on-chain.
5. Use correction events instead of editing/deleting old ledger facts.
6. Require source trust scoring before ledger commit.
7. Add idempotency keys for every ERP/SiteTrack/supplier event.
8. Add replay tooling to rebuild the read model from ledger events.
9. Add privacy boundaries by tenant, partner, lane, and document type.
10. Add operational fallback when ledger anchoring is delayed.
```

## Recommended repo implementation

### Phase 1 — Evidence anchor adapter

```text
apps/api/app/blockchain/
  __init__.py
  adapter.py
  evidence_anchor.py
  models.py
  noop_ledger.py
  mock_permissioned_ledger.py
```

Acceptance criteria:

```text
approved action creates receipt
receipt hash is anchored by adapter
receipt shows ledger proof status in audit timeline
system still works when ledger adapter is disabled
Streamlit debug cockpit can display proof status
```

### Phase 2 — Operational event ledger mode

```text
apps/api/app/ledger_events/
  __init__.py
  canonical_event.py
  validator.py
  projector.py
  replay.py
  correction.py
```

Acceptance criteria:

```text
case lifecycle can be rebuilt from ledger events
approval events are immutable
correction events supersede bad source data
read model can be regenerated deterministically
SiteTrack container event can become a ledger event after validation
ERP writeback receipt can become a ledger event after validation
```

### Phase 3 — Consortium pilot

Enable Mode B only for customers who need shared operational truth among multiple parties:

```text
buyer
supplier
logistics provider
warehouse operator
auditor / regulator
```

## Kanban impact

Kanban remains the human operating layer.

```text
Source event -> validated ledger/evidence event -> projected risk case -> Kanban lane -> manager decision -> approved action -> receipt proof
```

The manager should not need to understand blockchain internals. The UI should show simple trust signals:

```text
Evidence: verified
Ledger: anchored
Source: SiteTrack signed event
ERP receipt: confirmed
Correction: none
```

## Streamlit impact

Streamlit is the AI-agent debug cockpit for this design. It should show:

```text
source event payload
source trust score
canonical event validation result
AI recommendation trace
approval-policy decision
execution receipt
blockchain anchor status
projection/read-model status
```

Streamlit must call FastAPI endpoints and must not bypass approval policy.

## Product rule

Blockchain must make the system more trustworthy, not harder to operate.

Default to evidence anchoring. Enable operational-ledger mode only when cross-party trust requirements justify the added complexity.
