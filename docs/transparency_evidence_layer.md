# Transparency Evidence Layer

This layer makes the demo's supply-chain transparency story concrete without adding a real blockchain dependency.

It follows three rules:

1. **Real-world facts enter through named external data sources.** ERP, WMS, IoT, supplier portal, and news feeds are represented as `ExternalDataSource` rows.
2. **Every fact becomes a traceability event before it becomes buyer-facing proof.** `TraceabilityEvent` records the observed supply-chain event, validation status, confidence, and source payload.
3. **Blockchain is an anchor, not an oracle.** `BlockchainAnchor` / `LedgerProof` stubs preserve a hash and proof pointer, but the data still needs oracle-style validation before it is trusted.

## Objects

- `ExternalDataSource`: source registry for ERP, WMS, IoT, supplier portal, news, or audit data.
- `TraceabilityEvent`: case-linked event such as shipment delay, OTIF drop, quality alert, or supplier ETA commitment.
- `EvidenceReceipt`: buyer-facing proof summary with confidence score and validation status.
- `BlockchainAnchor`: ledger proof stub for anchoring an evidence receipt hash.

## Operator surface

The operator API exposes:

- `GET /operator/cases/{case_id}/transparency`
- `GET /operator/transparency_report?case_id=...`

The web demo renders a **Data Trust & Transparency** panel explaining why the data is trustworthy, which sources were used, what validation passed, and whether a ledger proof is anchored.

## Current limitation

This is a demo-ready evidence model. It does not submit real blockchain transactions. Replace the `BlockchainAnchor` stub with a production ledger adapter only after a customer requires a real anchoring network.
