# Blockchain, SiteTrack, and ERP Integration Strategy

## Purpose

This tracking document defines how the Supply Chain Kanban AI Agent should combine blockchain evidence, SiteTrack container tracking, and ERP/WMS/TMS integration.

## Market need

Customers already run ERP, WMS, TMS, supplier portals, spreadsheets, and carrier systems. The product must sit above these systems as a decision and action control plane.

It should not ask customers to replace their systems first.

## Blockchain for supply-chain transparency

Blockchain is useful when several parties need a shared proof trail. It is not a magic source of truth. The physical-world and enterprise-system data must still be reliable.

Professional use cases:

```text
shipment provenance proof
container handoff proof
supplier certification proof
approval proof
execution receipt proof
ESG / due-diligence evidence checkpoint
cross-party dispute evidence
```

Architecture rule:

```text
Default mode: app DB/customer systems remain operational source of record; blockchain anchors evidence.
Advanced mode: permissioned ledger can become the cross-party event source; app DB becomes read model/cache.
```

See `docs/architecture/BLOCKCHAIN_OPERATIONAL_DATABASE_DECISION.md` for the detailed decision.

## SiteTrack as physical-world oracle

SiteTrack should provide objective container/asset movement evidence:

```text
last-seen location
geofence enter/exit
handoff event
offline capture
BLE/edge proof
signed evidence package
confidence score
```

Canonical event example:

```json
{
  "event_type": "container.location_observed",
  "source": "sitetrack",
  "container_id": "CONT-001",
  "shipment_id": "SHIP-1001",
  "observed_at": "2026-05-20T10:00:00Z",
  "location": { "site": "Taichung DC", "zone": "Yard A" },
  "confidence": 0.91,
  "proof_hash": "sha256:..."
}
```

## ERP/WMS/TMS integration

The agent integrates through adapters:

```text
ERP: purchase orders, sales orders, allocations, suppliers, invoices
WMS: inventory, pick/pack/ship, warehouse exceptions
TMS: loads, carriers, ETA, container/trailer state
MES: production constraints and resource availability
Supplier portal: escalation tickets, confirmations, recovery commitments
```

Connector contract:

```text
read_state()
simulate_action()
validate_policy()
execute_action()
return_receipt()
```

## End-to-end example

```text
1. SiteTrack reports container not observed at expected handoff zone.
2. ERP shows customer order depends on the container.
3. TMS ETA is now at risk.
4. Agent opens Kanban case: “Container handoff delay threatens customer promise.”
5. Agent recommends: expedite alternate shipment or supplier escalation.
6. Policy requires manager approval because cost impact exceeds threshold.
7. Manager approves.
8. Agent writes to ERP/TMS/supplier portal.
9. Receipt is stored in audit timeline.
10. Optional hash is anchored to blockchain for cross-party evidence.
```

## Roadmap

```text
P0: canonical event/action/receipt docs
P1: CSV + REST connector adapter
P2: SiteTrack location-oracle adapter
P3: Odoo connector pack
P4: SAP / Oracle / NetSuite adapter specs
P5: blockchain evidence adapter
P6: optional permissioned-ledger operational event source
P6: customer pilot pack with real shipment/container cases
```

## Acceptance criteria

A professional demo should show:

```text
external signal creates/updates a Kanban risk case
case explains business impact
agent recommends a mitigation
approval gate blocks unsafe writeback
approved action executes through connector
receipt appears in audit timeline
optional ledger proof is linked to the receipt
```
