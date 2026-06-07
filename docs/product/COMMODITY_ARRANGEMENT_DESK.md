# Commodity Arrangement Desk

The dashboard should keep improving from a headline monitor into an approval-ready **commodity arrangement desk** for approval-ready commodity arrangements.

## UX rule

Show the manager-ready arrangement card first:

```text
commodity/material
  -> source confidence + time period
  -> price range
  -> BOM exposure and ERP/MES fields to check
  -> recommended arrangement
  -> approval owner
  -> governed writeback target
  -> evidence hash / blockchain-ready proof
```

Do **not** lead with a raw RSS feed, raw ERP/MES table, or proof hash without a business summary.

## Arrangement types

| Arrangement | Typical trigger | Approval owner |
| --- | --- | --- |
| `review_buy_timing` | price softening, spot/contract spread, quote-validity change | commodity manager |
| `buffer_or_expedite` | port disruption, supplier delay, ETA risk | supply-chain manager |
| `long_term_agreement` | persistent 6-12 month shortage risk | CFO / supply-chain leader |
| `alternate_supplier_or_substitution` | constrained material or qualified-source risk | engineering + quality |
| `rebalance_allocation` | customer launch or priority program conflict | operations leader |

## Agent loop

1. Ingest live news, commodity radar rows, supplier notes, and ERP/MES/WMS/TMS records.
2. Map events to `NewsRiskSignal`, `CommodityPredictionPacket`, and `BillOfMaterialsExposure`.
3. Create a `CommodityArrangementCard` with source confidence, time period, price range, BOM exposure, ERP/MES fields, recommended action, approval owner, and proof hash.
4. Simulate buy timing, buffer, LTA, expedite, alternate supplier, or customer-allocation outcomes.
5. Require human approval before any ERP/MES/WMS/TMS writeback.
6. Attach `EvidenceReceipt`, `WritebackReceipt`, `decision_hash`, and optional `BlockchainAnchor`.

## API surfaces

```bash
curl http://localhost:8000/news/commodity-arrangements?topic=commodities
curl http://localhost:8000/api/news/commodity-arrangements?topic=commodities
```

The endpoint returns deterministic demo cards when the database is empty, so the Hugging Face / local demo still shows the intended user experience.

## Simple dashboard card fields

```json
{
  "commodity_or_material": "dram",
  "recommended_arrangement": "review_buy_timing",
  "source_confidence": 0.74,
  "time_period": "last 30 days",
  "price_range": "spot -3% to -8%, contract watch",
  "bom_exposure": ["server_dram", "edge_ai_memory"],
  "approval_owner": "commodity_manager",
  "erp_mes_fields_to_check": [
    "erp_material_ids",
    "open_purchase_orders",
    "work_orders",
    "plant_inventory",
    "supplier_confirmations",
    "quote_validity_window"
  ],
  "evidence_hash": "sha256..."
}
```

## Why this improves UX

Supply-chain users do not need another news wall. They need a short, explainable action card that connects 人事時地物 with system data: who approves, what material is affected, when the signal happened, where the exposure sits, which price/lead-time range matters, and what proof will be kept.
