# Dataset Description

market_signals.csv simulates external market indicators.

Columns:
- resource_id
- signal_type
- value
- week

Used for early detection of emerging constraints.

## Dashboard ontology enhancement datasets

The dashboard now separates four dataset families so ERP/MES integration, AI automation, blockchain proof, and UI experience stay understandable.

| Dataset family | Tables / objects | Purpose |
| --- | --- | --- |
| Source-system references | `source_system_connectors`, `source_record_references` | Preserve ERP/MES/WMS/TMS/news/CSV/blockchain origin for every normalized object. |
| Supply-chain exposure | `bom_exposures`, `capacity_constraints`, `sandop_exceptions` | Explain what material, SKU, PO, WO, plant, supplier, revenue, or capacity is affected. |
| AI-agent automation | `agent_runs`, `AgentDecision`, `PendingAction` | Trace one automation loop from trigger to prediction, recommendation, approval state, and policy result. |
| Evidence and writeback | `writeback_receipts`, `EvidenceReceipt`, `BlockchainAnchor` | Keep proof after simulation/execution and optionally anchor receipt hashes. |
| User experience | `simple_ui_views` | Declare the persona, primary question, visible objects, action, evidence policy, and layout hint. |

Sample payload: `data/sample_inputs/dashboard_ontology_sample.json`.

Recommended operating rule: use read-only source sync first, prove value on the simple UI, then enable approval-gated writebacks only for explicit action types with receipts.
